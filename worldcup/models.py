from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Group(models.Model):
    name = models.CharField(max_length=1, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "grupo"
        verbose_name_plural = "grupos"

    def __str__(self) -> str:
        return f"Grupo {self.name}"


class Stage(models.Model):
    GROUPS = "groups"
    ROUND_OF_32 = "round_of_32"
    ROUND_OF_16 = "round_of_16"
    QUARTER = "quarter"
    SEMI = "semi"
    THIRD = "third"
    FINAL = "final"
    STAGE_TYPES = [
        (GROUPS, "Grupos"),
        (ROUND_OF_32, "16 avos"),
        (ROUND_OF_16, "Oitavas"),
        (QUARTER, "Quartas"),
        (SEMI, "Semifinal"),
        (THIRD, "Terceiro lugar"),
        (FINAL, "Final"),
    ]

    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(unique=True)
    stage_type = models.CharField(max_length=20, choices=STAGE_TYPES, default=GROUPS)

    class Meta:
        ordering = ["order"]
        verbose_name = "fase"
        verbose_name_plural = "fases"

    def __str__(self) -> str:
        return self.name


class Stadium(models.Model):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Estados Unidos")
    capacity = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["country", "city", "name"]
        verbose_name = "estádio"
        verbose_name_plural = "estádios"

    def __str__(self) -> str:
        return f"{self.name} - {self.city}"


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    fifa_code = models.CharField(max_length=3, unique=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True, related_name="teams")
    position = models.PositiveSmallIntegerField("posição no grupo", blank=True, null=True)
    flag = models.ImageField(upload_to="flags/", blank=True, null=True)
    active = models.BooleanField(default=True)

    TEAM_NAMES_PTBR = {
        "Argentina": "Argentina",
        "Australia": "Austrália",
        "Belgium": "Bélgica",
        "Brasil": "Brasil",
        "Cameroon": "Camarões",
        "Canada": "Canadá",
        "Costa Rica": "Costa Rica",
        "Croatia": "Croácia",
        "Czechia": "República Tcheca",
        "Denmark": "Dinamarca",
        "Ecuador": "Equador",
        "Egypt": "Egito",
        "England": "Inglaterra",
        "France": "França",
        "Germany": "Alemanha",
        "Ghana": "Gana",
        "Haiti": "Haiti",
        "IR Iran": "Irã",
        "Iran": "Irã",
        "Iraq": "Iraque",
        "Japan": "Japão",
        "Jordan": "Jordânia",
        "Korea Republic": "Coreia do Sul",
        "Mexico": "México",
        "Morocco": "Marrocos",
        "Netherlands": "Holanda",
        "New Zealand": "Nova Zelândia",
        "Norway": "Noruega",
        "Panama": "Panamá",
        "Paraguay": "Paraguai",
        "Poland": "Polônia",
        "Portugal": "Portugal",
        "Qatar": "Catar",
        "Saudi Arabia": "Arábia Saudita",
        "Scotland": "Escócia",
        "Senegal": "Senegal",
        "Serbia": "Sérvia",
        "South Africa": "África do Sul",
        "South Korea": "Coreia do Sul",
        "Spain": "Espanha",
        "Sweden": "Suécia",
        "Switzerland": "Suíça",
        "Tunisia": "Tunísia",
        "Turkey": "Turquia",
        "Türkiye": "Turquia",
        "United States": "Estados Unidos",
        "Uruguay": "Uruguai",
        "Wales": "País de Gales",
        "Algeria": "Argélia",
        "Bosnia and Herzegovina": "Bósnia-Herzegovina",
        "Cabo Verde": "Cabo Verde",
        "Colombia": "Colômbia",
        "Congo DR": "República Democrática do Congo",
        "Curaçao": "Curaçao",
        "Côte d'Ivoire": "Costa do Marfim",
        "Alemanha": "Alemanha",
        "Espanha": "Espanha",
        "França": "França",
        "México": "México",
        "Uzbequistão": "Uzbequistão",
        "Uzbekistan": "Uzbequistão",
    }

    TEAM_CODES = {
        "Argentina": "ar", "Australia": "au", "Belgium": "be", "Brasil": "br",
        "Cameroon": "cm", "Canada": "ca", "Costa Rica": "cr", "Croatia": "hr",
        "Czechia": "cz", "Denmark": "dk", "Ecuador": "ec", "Egypt": "eg",
        "England": "gb-eng", "France": "fr", "Germany": "de", "Ghana": "gh",
        "Haiti": "ht", "IR Iran": "ir", "Iran": "ir", "Iraq": "iq", "Japan": "jp",
        "Jordan": "jo", "Korea Republic": "kr", "Mexico": "mx", "Morocco": "ma",
        "Netherlands": "nl", "New Zealand": "nz", "Norway": "no", "Panama": "pa",
        "Paraguay": "py", "Poland": "pl", "Portugal": "pt", "Qatar": "qa",
        "Saudi Arabia": "sa", "Scotland": "gb-sct", "Senegal": "sn", "Serbia": "rs",
        "South Africa": "za", "South Korea": "kr", "Spain": "es", "Sweden": "se",
        "Switzerland": "ch", "Tunisia": "tn", "Turkey": "tr", "Türkiye": "tr",
        "United States": "us", "Uruguay": "uy", "Wales": "gb-wls",
        "Algeria": "dz", "Bosnia and Herzegovina": "ba", "Cabo Verde": "cv",
        "Colombia": "co", "Congo DR": "cd", "Curaçao": "cw", "Côte d'Ivoire": "ci",
        "Alemanha": "de", "Espanha": "es", "França": "fr", "México": "mx",
        "Uzbequistão": "uz", "Uzbekistan": "uz", "Estados Unidos": "us",
    }

    class Meta:
        ordering = ["group", "position", "name"]
        verbose_name = "seleção"
        verbose_name_plural = "seleções"

    def __str__(self) -> str:
        return self.name

    @property
    def name_ptbr(self) -> str:
        return self.TEAM_NAMES_PTBR.get(self.name, self.name)

    @property
    def flag_url(self):
        if self.flag:
            return self.flag.url
        code = self.TEAM_CODES.get(self.name)
        if code:
            return f"https://flagcdn.com/w80/{code}.png"
        return None


class MatchQuerySet(models.QuerySet):
    def open_for_predictions(self):
        return self.filter(status=Match.STATUS_SCHEDULED, start_time__gt=timezone.now()).order_by("start_time")

    def finished(self):
        return self.filter(finished=True).order_by("-start_time")


class Match(models.Model):
    STATUS_SCHEDULED = "scheduled"
    STATUS_LIVE = "live"
    STATUS_FINISHED = "finished"
    STATUS_POSTPONED = "postponed"
    STATUSES = [
        (STATUS_SCHEDULED, "Agendada"),
        (STATUS_LIVE, "Ao vivo"),
        (STATUS_FINISHED, "Encerrada"),
        (STATUS_POSTPONED, "Adiada"),
    ]

    stage = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name="matches")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True, related_name="matches")
    match_number = models.PositiveIntegerField(unique=True)
    home_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="home_matches")
    away_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="away_matches")
    stadium = models.ForeignKey(Stadium, on_delete=models.PROTECT, related_name="matches")
    start_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUSES, default=STATUS_SCHEDULED)
    official_home_score = models.PositiveSmallIntegerField(blank=True, null=True)
    official_away_score = models.PositiveSmallIntegerField(blank=True, null=True)
    finished = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    objects = MatchQuerySet.as_manager()

    class Meta:
        ordering = ["start_time", "match_number"]
        verbose_name = "partida"
        verbose_name_plural = "partidas"
        indexes = [
            models.Index(fields=["start_time", "status"]),
            models.Index(fields=["stage", "group"]),
        ]

    def __str__(self) -> str:
        return f"Jogo {self.match_number}: {self.home_team} x {self.away_team}"

    def clean(self) -> None:
        if self.home_team_id and self.home_team_id == self.away_team_id:
            raise ValidationError("Mandante e visitante não podem ser a mesma seleção.")
        if self.finished and (self.official_home_score is None or self.official_away_score is None):
            raise ValidationError("Partidas encerradas precisam de placar oficial.")

    @property
    def is_locked(self) -> bool:
        return timezone.now() >= self.start_time

    @property
    def accepts_predictions(self) -> bool:
        return not self.is_locked and self.status == self.STATUS_SCHEDULED

