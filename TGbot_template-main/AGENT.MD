# AGENT.MD — technical brief

> **Repository:** `TGbot_template`
> **Goal:** Modernize the legacy Telegram-bot template by adopting Clean Architecture and **SOLID** principles with a strong focus on **Dependency Inversion** and **Dependency Injection**. Replace Peewee with **SQLAlchemy Core**, integrate **Alembic**, and run migrations automatically when the stack starts. Upgrade to **Python 3.12+**, **aiogram 3.+**, and require **Pydantic v2**.

---

## 1 — Why we are doing this

1. The production bot is based on an outdated template.
2. A clean, extensible architecture is required before changing live code.
3. The refactor will serve as a migration proof-of-concept and a reference implementation for the team.

---

## 2 — High-level goals

| # | Goal                           | Definition of Done                                                                                                                            |
| - | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | **Layered Clean Architecture** | Code is organised by responsibility (presentation, application, domain, infrastructure) and layer boundaries are respected.                   |
| 2 | **Dependency Inversion & DI**  | Outer layers depend only on abstractions; concrete implementations are provided via a lightweight DI container (e.g., `dependency-injector`). |
| 3 | **Domain layer**               | Business logic resides in an isolated layer with no framework imports.                                                                        |
| 4 | **Repository + Unit of Work**  | All database access goes through repositories; transactions are managed by a Unit of Work.                                                    |
| 5 | **SQLAlchemy Core & Alembic**  | Peewee is completely removed; SQLAlchemy Core is used; Alembic migrations run automatically at stack start-up.                                |
| 6 | **Behaviour unchanged**        | Every existing bot command continues to work exactly as before.                                                                               |
| 7 | **Single launch path**         | The whole stack is started with `docker-compose up`, and migrations are applied before the bot runs.                                          |

---

## 3 — Constraints & guard-rails

* **Python ≥ 3.12** (`python:3.12-slim`).
* **aiogram 3.+** (latest stable release).
* **Pydantic v2** is mandatory for DTOs/settings.
* Keep external dependencies minimal beyond those listed below.
* Do **not** rename existing environment variables in `.env.example`.
* Unit tests are **not** required in this iteration.

---

## 4 — Implementation outline

1. **DI container**

   * Register repositories, Unit of Work, and services; inject them into aiogram handlers.

2. **Data layer refactor**

   * Remove all Peewee models.
   * Define tables and queries with SQLAlchemy Core.
   * Provide an `AbstractRepository` interface and a SQLAlchemy implementation.
   * Implement a `UnitOfWork` that manages the session and commit/rollback.

3. **Alembic integration**

   * Initialise the migrations folder; configure `alembic.ini` to use the same DB URL as the bot (via environment variables).
   * Ensure `alembic upgrade head` executes automatically before the bot process starts.

4. **Maintain existing commands**

   * Verify that all current commands and flows behave exactly the same after migration.

---

## 5 — Dependency list

Runtime and dev packages required for a modern, compatible bot:

```
aiogram==3.20.0.post0
aiohttp>=3.11,<3.12
redis==6.2.0
pydantic-settings==2.10.1
pydantic==2.11.7
loguru==0.7.3
peewee-async==1.1.0
aioschedule==0.5.2
aiocache==0.12.3
certifi==2025.6.15
python-dotenv==1.1.1
SQLAlchemy==2.0.41
ujson==5.10.0
msgpack==1.1.1
multidict>=6.5,<7.0
dependency-injector==4.48.1
aiosqlite>=0.21.0,<0.22.0
asyncpg>=0.30.0,<0.31.0

# formatting, static analysis, testing
mypy==1.16.1
ruff==0.12.0
black==25.1.0
pytest==8.4.1
pytest-asyncio==1.0.0
```

---

## 6 — Acceptance checklist

* [ ] `docker-compose up --build` completes without errors.
* [ ] Alembic automatically applies all migrations at start-up.
* [ ] The bot responds to every previously available command with unchanged behaviour.
* [ ] Architectural boundaries are respected and concrete implementations are provided via DI.
* [ ] All data access passes through SQLAlchemy Core repositories inside a Unit of Work.
* [ ] No Peewee code or artefacts remain in the project.

---

### When in doubt…

* Start simple, then refine.
* Each layer should be replaceable with minimal impact on others.
* Document public interfaces concisely; keep private helpers terse.
