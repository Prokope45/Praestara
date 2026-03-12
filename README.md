<header class="header">
<img src="frontend/public/assets/images/praestara-logo.png" alt="Praestara Logo" class="logo">
<h1 class="site-title">Praestara</h1>
</header>

<style>
.header {
  display: flex;
  align-items: center; /* Vertically centers items */
  gap: 10px; /* Adds space between logo and text */
}

.logo {
  height: 50px; /* Adjust as needed */
}

.site-title {
  margin: 0;
  font-size: 24px;
}
</style>

**Praestara** is a startup initiative developed by [Kansas State University](https://www.k-state.edu/) neuroscience and computer science students. The platform supports research participants in their journey toward personal growth by helping them clarify their self-concept (identifying core values and aspirations), align daily tasks with their purpose, and achieve meaningful goals over time.

Users begin by reflecting on areas of life they wish to improve, establishing a purpose orientation that serves as a guiding framework. Daily notes and sessions with providers then track progress toward this purpose. Through consistent engagement, users cultivate awareness of their personal values, observe how their actions align with those values, and assess the impact on their well-being. Over time, they can reflect on outcomes to see how they reinforce their values, creating a continuous cycle of value-action-outcome reflection, and in retrospect, outcome-action-value learning.

> **Disclaimer**
> This project is indended to be a lifestyle enhancer and as a tool to be used in study. As it currently stands, it is not intended to be used in clinical use.

## Technology Stack and Features

> **Notice**
> This project was cloned from and built using the official opensource [FastAPI Full-Stack Template](https://github.com/fastapi/full-stack-fastapi-template) repo.

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
    - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
    - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
    - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
- 🚀 [React](https://react.dev) for the frontend.
    - 💃 Using TypeScript, hooks, Vite, and other parts of a modern frontend stack.
    - 🎨 [Material UI](https://mui.com) for the frontend components.
    - 🤖 An automatically generated frontend client.
    - 🧪 [Playwright](https://playwright.dev) for End-to-End testing.
    - 🦇 Dark mode support.
- 🐋 [Docker Compose](https://www.docker.com) for development and production.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email based password recovery.
- ✅ Tests with [Pytest](https://pytest.org).
- 📞 [Traefik](https://traefik.io) as a reverse proxy / load balancer.
- 🚢 Deployment instructions using Docker Compose, including how to set up a frontend Traefik proxy to handle automatic HTTPS certificates.
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

## First Local Setup

First run `./scripts/setup-env.sh`, which creates a copy of the `.env.example` as `.env` and automatically creates new keys for the secret and database password (must occur on fresh setup; if DB exists there will be password issues with `postgres` user, visit [DB documentation](scripts/README.md) for more info).

Then in `.env` set `FIRST_SUPERUSER` with your email and enter a password for `FIRST_SUPERUSER_PASSWORD`. Then run `make build` (or `docker compose build`) to build the images, then `docker compose up -d db` to make sure the database container is running. Restore the database using the dump file: `./scripts/restore-db.sh <<PATH TO DB DUMP FILE>>` such as `./scripts/restore-db.sh data-dump.sql`.

Finally, run `docker compose watch` to run the rest of the containers and visit `localhost:5173` to see webapp.

### Build System

The project now uses a centralized build system in the [`build/`](build/) directory. This includes:

- **Docker Compose files**: Moved to [`build/`](build/) for better organization
- **Makefile**: Provides shortcuts for common build and deployment commands
- **Documentation**: See [`build/build.md`](build/build.md) for detailed usage

#### Quick Start with Makefile

Instead of running raw `docker-compose` commands, use the Makefile shortcuts:

```bash
# Start all services (production mode)
make up

# Start all services (development mode with Traefik proxy)
make dev-up

# Restart containers when changes are detected.
make watch

# View logs
make logs

# Stop all services
make down

# Build images
make build

# Run database migrations
make dev-migrate

# Run backend tests
make dev-test

# Connect to PostgreSQL
make dev-db-shell

# Full cleanup (containers, images, volumes)
make clean-all
```

See [`build/build.md`](build/build.md) for a complete list of available commands.

### Configure

You can then update configs in the `.env` files to customize your configurations.

Before deploying it, make sure you change at least the values for:

- `SECRET_KEY`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_PASSWORD`

You can (and should) pass these as environment variables from secrets.

Read the [deployment.md](./deployment.md) docs for more details.

### Generate Secret Keys

Some environment variables in the `.env` file have a default value of `changethis`.

You have to change them with a secret key, to generate secret keys you can run the following command:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the content and use that as password / secret key. And run that again to generate another secure key.

## Backend Development

Backend docs: [backend/README.md](./backend/README.md).

## Frontend Development

Frontend docs: [frontend/README.md](./frontend/README.md).

## Deployment

Deployment docs: [deployment.md](./docs/deployment.md).

## Development

General development docs: [development.md](./docs/development.md).

This includes using Docker Compose, custom local domains, `.env` configurations, etc.
