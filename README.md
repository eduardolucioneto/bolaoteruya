# Bolão Copa do Mundo 2026

Projeto Django completo para gestão de um bolão da Copa do Mundo de 2026, com autenticação, cadastro manual de usuários no admin, palpites, resultados oficiais, cálculo de pontuação, ranking e ambiente dockerizado.

## Stack

- Python 3.12+
- Django 5+
- PostgreSQL
- Django Templates
- Bootstrap 5
- Docker + Docker Compose
- pytest / django.test

## Estrutura

```text
.
|-- accounts/
|-- config/
|-- core/
|-- predictions/
|-- ranking/
|-- static/
|-- templates/
|-- worldcup/
|-- Dockerfile
|-- docker-compose.yml
|-- manage.py
`-- requirements.txt
```

## Apps

- `accounts`: autenticação, cadastro, perfil, recuperação e administração de usuários.
- `core`: home, dashboard e configuração global do bolão.
- `worldcup`: grupos, fases, estádios, seleções e partidas.
- `predictions`: palpites, travamento automático e cálculo por partida.
- `ranking`: consolidação da pontuação e posição dos usuários.

## Principais decisões arquiteturais

- `AUTH_USER_MODEL` customizado com e-mail único.
- `Profile` separado para dados complementares do usuário.
- lógica de pontuação em `predictions/services.py`.
- ranking persistido em `ranking.UserScore` para leitura rápida nas telas.
- administração reforçada com ações em lote, exportação CSV e reset de senha.
- datas timezone-aware com `USE_TZ=True`.

## Execução local com Docker

1. Copie `.env.example` para `.env`.
2. Suba os serviços:

```bash
docker compose up --build
```

3. Em outro terminal, rode as migrações:

```bash
docker compose exec web python manage.py migrate
```

4. Popular dados iniciais:

```bash
docker compose exec web python manage.py seed_dev
docker compose exec web python manage.py import_groups_and_stages
docker compose exec web python manage.py seed_teams
docker compose exec web python manage.py populate_initial_matches
```

5. Acesse:

- App: [http://localhost:8000](http://localhost:8000)
- Admin: [http://localhost:8000/admin](http://localhost:8000/admin)

Usuário inicial de desenvolvimento criado pelo seed:

- usuário: `admin`
- senha: `admin123456`

## Execução sem Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_dev
python manage.py runserver
```

Por padrão, o projeto usa `SQLite` em desenvolvimento local (`USE_SQLITE=True`).
Se quiser usar PostgreSQL fora do Docker, altere no `.env`:

```env
USE_SQLITE=False
DATABASE_NAME=bolao
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

## Comandos úteis

```bash
python manage.py seed_dev
python manage.py import_groups_and_stages
python manage.py seed_teams
python manage.py populate_initial_matches
python manage.py lock_expired_predictions
python manage.py recalculate_ranking
```

## Regras de pontuação

- 5 pontos para placar exato
- 3 pontos para acertar vencedor ou empate
- 1 ponto extra para acertar saldo
- 1 ponto extra para acertar gols de um dos lados

Todos os pesos são configuráveis no modelo `PoolConfiguration`.

## Fluxo principal

1. Administrador cria usuários e cadastros-base no admin.
2. Usuários autenticados acessam o dashboard e enviam palpites.
3. Quando o jogo começa, o palpite fica travado.
4. O administrador informa o resultado oficial.
5. O sistema recalcula palpites e ranking.

## Testes

```bash
pytest
```

## Melhorias naturais para próxima iteração

- paginação com filtros persistentes
- fixtures completas da Copa 2026
- ranking por fase materializado separadamente
- tarefa agendada via cron ou Celery Beat para travamento contínuo
- upload real de bandeiras e avatars com storage externo
