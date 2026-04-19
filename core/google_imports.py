import csv
import re
from datetime import datetime
from html import unescape
from io import StringIO
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ranking.models import UserScore
from worldcup.models import Group, Match, Stage, Stadium, Team

FIFA_HOST_STADIUMS = {
    "Atlanta Stadium": {"stadium_city": "Atlanta", "stadium_country": "Estados Unidos"},
    "BC Place Vancouver": {"stadium_city": "Vancouver", "stadium_country": "Canada"},
    "Boston Stadium": {"stadium_city": "Boston", "stadium_country": "Estados Unidos"},
    "Dallas Stadium": {"stadium_city": "Dallas", "stadium_country": "Estados Unidos"},
    "Estadio Guadalajara": {"stadium_city": "Guadalajara", "stadium_country": "Mexico"},
    "Estadio Monterrey": {"stadium_city": "Monterrey", "stadium_country": "Mexico"},
    "Guadalajara Stadium": {"stadium_city": "Guadalajara", "stadium_country": "Mexico"},
    "Houston Stadium": {"stadium_city": "Houston", "stadium_country": "Estados Unidos"},
    "Kansas City Stadium": {"stadium_city": "Kansas City", "stadium_country": "Estados Unidos"},
    "Los Angeles Stadium": {"stadium_city": "Los Angeles", "stadium_country": "Estados Unidos"},
    "Mexico City Stadium": {"stadium_city": "Mexico City", "stadium_country": "Mexico"},
    "Miami Stadium": {"stadium_city": "Miami", "stadium_country": "Estados Unidos"},
    "Monterrey Stadium": {"stadium_city": "Monterrey", "stadium_country": "Mexico"},
    "New York New Jersey Stadium": {"stadium_city": "New York / New Jersey", "stadium_country": "Estados Unidos"},
    "Philadelphia Stadium": {"stadium_city": "Philadelphia", "stadium_country": "Estados Unidos"},
    "San Francisco Bay Area Stadium": {"stadium_city": "San Francisco Bay Area", "stadium_country": "Estados Unidos"},
    "Seattle Stadium": {"stadium_city": "Seattle", "stadium_country": "Estados Unidos"},
    "Toronto Stadium": {"stadium_city": "Toronto", "stadium_country": "Canada"},
    "Vancouver Stadium": {"stadium_city": "Vancouver", "stadium_country": "Canada"},
}

FIFA_STAGE_ORDER = {
    Stage.GROUPS: 1,
    Stage.ROUND_OF_32: 2,
    Stage.ROUND_OF_16: 3,
    Stage.QUARTER: 4,
    Stage.SEMI: 5,
    Stage.THIRD: 6,
    Stage.FINAL: 7,
}

ENGLISH_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

FIFA_DATE_PATTERN = re.compile(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), \d{1,2} [A-Za-z]+ \d{4}")
FIFA_INLINE_FIXTURE_PATTERN = re.compile(
    r"(?P<home>[A-Z][A-Za-zÀ-ÿ'. /-]+?)\s+v\s+(?P<away>[A-Z][A-Za-zÀ-ÿ'. /-]+?)\s+[-–—•·\u00b7\u2022\u2013\u2014\ufffd]\s+(?:(?P<group>Group\s+[A-L])\s+[-–—•·\u00b7\u2022\u2013\u2014\ufffd]\s+)?(?P<stadium>.+)"
)


def google_sheet_to_csv_url(url: str) -> str:
    parsed = urlparse(url)
    if "docs.google.com" not in parsed.netloc or "/spreadsheets/" not in parsed.path:
        return url

    if parsed.path.endswith("/export"):
        query = dict(parse_qsl(parsed.query))
        query.setdefault("format", "csv")
        return urlunparse(parsed._replace(query=urlencode(query)))

    path = parsed.path.split("/edit")[0].rstrip("/") + "/export"
    query = dict(parse_qsl(parsed.query))
    query["format"] = "csv"
    return urlunparse(parsed._replace(path=path, query=urlencode(query)))


def _is_fifa_schedule_url(url: str) -> bool:
    parsed = urlparse(url)
    return "fifa.com" in parsed.netloc and "match-schedule-fixtures-results-teams-stadiums" in parsed.path


def _fetch_text(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    if _is_fifa_schedule_url(url):
        headers["User-Agent"] = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8-sig")


def _strip_html(value: str) -> str:
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", "\n", value)
    return unescape(value).replace("\xa0", " ")


def _normalize_lines(value: str) -> list[str]:
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
    filtered = [line for line in lines if line]
    deduped = []
    for line in filtered:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return deduped


def _parse_english_date(value: str):
    match = re.fullmatch(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (\d{1,2}) ([A-Za-z]+) (\d{4})", value.strip())
    if not match:
        return None
    day, month_name, year = match.groups()
    month = ENGLISH_MONTHS.get(month_name.lower())
    if not month:
        return None
    return datetime(int(year), month, int(day))


def _extract_group(value: str) -> str:
    match = re.search(r"Group\s+([A-L])", value, flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""


def _extract_stage_data(value: str) -> tuple[str, str]:
    normalized = value.strip().lower()
    if "group stage" in normalized or "group fixtures" in normalized:
        return "Fase de grupos", Stage.GROUPS
    if "round of 32" in normalized:
        return "16 avos de final", Stage.ROUND_OF_32
    if "round of 16" in normalized:
        return "Oitavas de final", Stage.ROUND_OF_16
    if "quarter-final" in normalized or "quarter-finals" in normalized or "quarter finals" in normalized:
        return "Quartas de final", Stage.QUARTER
    if "semi-final" in normalized or "semi-finals" in normalized or "semi finals" in normalized:
        return "Semifinal", Stage.SEMI
    if "third-place play-off" in normalized or "third place play-off" in normalized or "third-place match" in normalized or "bronze final" in normalized:
        return "Terceiro lugar", Stage.THIRD
    if normalized == "final" or normalized.endswith(" final fixtures") or normalized.endswith(" final"):
        return "Final", Stage.FINAL
    return "", ""


def _is_fixture_line(value: str) -> bool:
    return " v " in value and not value.startswith("View the FIFA World Cup") and not value.startswith("Tickets -")


def _is_group_line(value: str) -> bool:
    return bool(re.fullmatch(r"Group\s+[A-L]", value, flags=re.IGNORECASE))


def _is_stadium_line(value: str) -> bool:
    return value in FIFA_HOST_STADIUMS


def _parse_inline_fixture(line: str):
    match = FIFA_INLINE_FIXTURE_PATTERN.search(line)
    if not match:
        return None

    stadium_name = match.group("stadium").strip()
    stadium_data = FIFA_HOST_STADIUMS.get(stadium_name)
    if not stadium_data:
        return None

    return {
        "home_team": match.group("home").strip(),
        "away_team": match.group("away").strip(),
        "group": _extract_group(match.group("group") or ""),
        "stadium_name": stadium_name,
        "stadium_city": stadium_data["stadium_city"],
        "stadium_country": stadium_data["stadium_country"],
    }


def _parse_split_fixture(lines: list[str], index: int):
    line = lines[index]
    if " v " not in line:
        return None, index

    home_team, away_team = [part.strip() for part in line.split(" v ", 1)]
    group = ""
    stadium_name = ""
    cursor = index + 1

    while cursor < len(lines):
        candidate = lines[cursor]
        if FIFA_DATE_PATTERN.fullmatch(candidate) or _extract_stage_data(candidate)[0] or _is_fixture_line(candidate):
            break
        if _is_group_line(candidate):
            group = _extract_group(candidate)
        elif _is_stadium_line(candidate):
            stadium_name = candidate
        cursor += 1

    if not stadium_name:
        return None, index

    stadium_data = FIFA_HOST_STADIUMS[stadium_name]
    return (
        {
            "home_team": home_team,
            "away_team": away_team,
            "group": group,
            "stadium_name": stadium_name,
            "stadium_city": stadium_data["stadium_city"],
            "stadium_country": stadium_data["stadium_country"],
        },
        cursor - 1,
    )


def fetch_fifa_matches_rows(url: str) -> list[dict[str, str]]:
    text = _strip_html(_fetch_text(url))
    lines = _normalize_lines(text)

    rows = []
    current_date = ""
    current_stage_name = ""
    current_stage_type = ""
    index = 0

    while index < len(lines):
        line = lines[index]

        stage_name, stage_type = _extract_stage_data(line)
        if stage_name:
            current_stage_name = stage_name
            current_stage_type = stage_type
            index += 1
            continue

        if FIFA_DATE_PATTERN.fullmatch(line):
            current_date = line
            index += 1
            continue

        if current_date and current_stage_name:
            fixture = _parse_inline_fixture(line)
            end_index = index
            if fixture is None and _is_fixture_line(line):
                fixture, end_index = _parse_split_fixture(lines, index)

            if fixture is not None:
                rows.append(
                    {
                        "match_number": str(len(rows) + 1),
                        "stage": current_stage_name,
                        "stage_type": current_stage_type,
                        "stage_order": str(FIFA_STAGE_ORDER[current_stage_type]),
                        "group": fixture["group"],
                        "home_team": fixture["home_team"],
                        "away_team": fixture["away_team"],
                        "stadium_name": fixture["stadium_name"],
                        "stadium_city": fixture["stadium_city"],
                        "stadium_country": fixture["stadium_country"],
                        "start_time": current_date,
                    }
                )
                index = end_index + 1
                continue

        index += 1

    if not rows:
        raise ValidationError("Nao foi possivel extrair jogos da pagina da FIFA informada.")
    return rows


def fetch_csv_rows(url: str) -> list[dict[str, str]]:
    if _is_fifa_schedule_url(url):
        return fetch_fifa_matches_rows(url)

    csv_url = google_sheet_to_csv_url(url)
    content = _fetch_text(csv_url)
    reader = csv.DictReader(StringIO(content))
    return [{(key or "").strip(): (value or "").strip() for key, value in row.items()} for row in reader]


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "sim", "yes", "y"}


def _parse_datetime(value: str, default_hour: int = 15, default_minute: int = 0):
    dt = parse_datetime(value)
    if dt is None:
        dt = _parse_english_date(value)
        if dt is not None:
            dt = datetime(dt.year, dt.month, dt.day, default_hour, default_minute)
    if dt is None:
        for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
            try:
                dt = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
    if dt is None:
        raise ValidationError(f"Data/hora invalida: {value}")
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _normalize_stage_type(value: str) -> str:
    normalized = (value or "").strip().lower()
    mapping = {
        "grupos": Stage.GROUPS,
        "groups": Stage.GROUPS,
        "16 avos": Stage.ROUND_OF_32,
        "round_of_32": Stage.ROUND_OF_32,
        "oitavas": Stage.ROUND_OF_16,
        "round_of_16": Stage.ROUND_OF_16,
        "quartas": Stage.QUARTER,
        "quarter": Stage.QUARTER,
        "semifinal": Stage.SEMI,
        "semi": Stage.SEMI,
        "terceiro lugar": Stage.THIRD,
        "third": Stage.THIRD,
        "final": Stage.FINAL,
    }
    return mapping.get(normalized, Stage.GROUPS)


@transaction.atomic
def import_groups_from_rows(rows: list[dict[str, str]]) -> int:
    count = 0
    for row in rows:
        name = row.get("name", "").strip()
        if not name:
            continue
        Group.objects.update_or_create(
            name=name[:1],
            defaults={"description": row.get("description", "")},
        )
        count += 1
    return count


@transaction.atomic
def import_matches_from_rows(rows: list[dict[str, str]]) -> int:
    count = 0
    for row in rows:
        match_number = row.get("match_number", "").strip()
        stage_name = row.get("stage", "").strip()
        home_team_name = row.get("home_team", "").strip()
        away_team_name = row.get("away_team", "").strip()
        stadium_name = row.get("stadium_name", "").strip()
        stadium_city = row.get("stadium_city", "").strip()
        start_time = row.get("start_time", "").strip()

        if not all([match_number, stage_name, home_team_name, away_team_name, stadium_name, stadium_city, start_time]):
            raise ValidationError("Cada linha de jogos precisa conter match_number, stage, home_team, away_team, stadium_name, stadium_city e start_time.")

        group = None
        if row.get("group"):
            group, _ = Group.objects.get_or_create(name=row["group"].strip()[:1])

        stage_defaults = {"order": int(row.get("stage_order") or 99), "stage_type": _normalize_stage_type(row.get("stage_type", ""))}
        stage, created = Stage.objects.get_or_create(name=stage_name, defaults=stage_defaults)
        if not created:
            updated = False
            if row.get("stage_order") and stage.order != int(row["stage_order"]):
                stage.order = int(row["stage_order"])
                updated = True
            normalized_stage_type = _normalize_stage_type(row.get("stage_type", ""))
            if row.get("stage_type") and stage.stage_type != normalized_stage_type:
                stage.stage_type = normalized_stage_type
                updated = True
            if updated:
                stage.save(update_fields=["order", "stage_type"])

        home_fifa_code = (row.get("fifa_code_home") or home_team_name)[:3].upper()
        home_team = Team.objects.filter(fifa_code=home_fifa_code).first()
        if not home_team:
            home_defaults = {} if group is None else {"group": group}
            home_team, _ = Team.objects.get_or_create(
                name=home_team_name,
                defaults={"fifa_code": home_fifa_code, **home_defaults},
            )
        elif group and home_team.group_id != group.id:
            home_team.group = group
            home_team.save(update_fields=["group"])

        away_fifa_code = (row.get("fifa_code_away") or away_team_name)[:3].upper()
        away_team = Team.objects.filter(fifa_code=away_fifa_code).first()
        if not away_team:
            away_defaults = {} if group is None else {"group": group}
            away_team, _ = Team.objects.get_or_create(
                name=away_team_name,
                defaults={"fifa_code": away_fifa_code, **away_defaults},
            )
        elif group and away_team.group_id != group.id:
            away_team.group = group
            away_team.save(update_fields=["group"])

        stadium, _ = Stadium.objects.get_or_create(
            name=stadium_name,
            city=stadium_city,
            defaults={
                "country": row.get("stadium_country") or "Estados Unidos",
                "capacity": int(row["stadium_capacity"]) if row.get("stadium_capacity") else None,
            },
        )

        official_home = row.get("official_home_score")
        official_away = row.get("official_away_score")
        finished = _parse_bool(row.get("finished", ""))
        status = row.get("status") or (Match.STATUS_FINISHED if finished else Match.STATUS_SCHEDULED)

        Match.objects.update_or_create(
            match_number=int(match_number),
            defaults={
                "stage": stage,
                "group": group,
                "home_team": home_team,
                "away_team": away_team,
                "stadium": stadium,
                "start_time": _parse_datetime(start_time),
                "status": status,
                "official_home_score": int(official_home) if official_home not in {"", None} else None,
                "official_away_score": int(official_away) if official_away not in {"", None} else None,
                "finished": finished,
                "notes": row.get("notes", ""),
            },
        )
        count += 1
    return count


@transaction.atomic
def import_ranking_from_rows(rows: list[dict[str, str]]) -> int:
    user_model = get_user_model()
    count = 0
    for row in rows:
        username = row.get("username", "").strip()
        email = row.get("email", "").strip()
        if not username and not email:
            continue

        user = user_model.objects.filter(username=username).first() if username else user_model.objects.filter(email=email).first()
        if not user:
            raise ValidationError(f"Usuario nao encontrado para a linha do ranking: {username or email}")

        UserScore.objects.update_or_create(
            user=user,
            defaults={
                "total_points": int(row.get("total_points") or 0),
                "exact_hits": int(row.get("exact_hits") or 0),
                "outcome_hits": int(row.get("outcome_hits") or 0),
                "position": int(row.get("position") or 0),
            },
        )
        count += 1
    return count


def import_google_data(*, groups_url: str = "", matches_url: str = "", ranking_url: str = "") -> dict[str, int]:
    results = {"groups": 0, "matches": 0, "ranking": 0}
    if groups_url:
        results["groups"] = import_groups_from_rows(fetch_csv_rows(groups_url))
    if matches_url:
        results["matches"] = import_matches_from_rows(fetch_csv_rows(matches_url))
    if ranking_url:
        results["ranking"] = import_ranking_from_rows(fetch_csv_rows(ranking_url))
    return results
