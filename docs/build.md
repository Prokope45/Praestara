# Praestara Build System

This directory contains the Docker Compose configuration files and a Makefile to simplify build and deployment commands.

## Files

- `docker-compose.yml` - Main production Docker Compose configuration
- `docker-compose.override.yml` - Local development overrides
- `docker-compose.traefik.yml` - Traefik reverse proxy configuration (production)
- `Makefile` - Build shortcuts and common commands

## Quick Start

### 1. Start All Services (Production)

```bash
make -C build up
```

This will start:
- PostgreSQL database
- Backend API service
- Frontend service
- Adminer (database admin UI)

### 2. Start All Services (Development)

```bash
make -C build dev-up
```

This includes additional development services:
- Traefik proxy (local mode)
- Mailcatcher (for email testing)
- Playwright (for E2E tests)

### 3. View Logs

```bash
make -C build logs
```

### 4. Stop All Services

```bash
make -C build down
```

## Common Commands

### Build Images

```bash
make -C build build
```

### Restart Services

```bash
make -C build restart
```

### Clean Up

```bash
make -C build clean
```

Removes containers but keeps volumes (database data).

### Full Cleanup

```bash
make -C build clean-all
```

Removes everything including volumes and images.

## Development Workflow

### Run Database Migrations

```bash
make -C build dev-migrate
```

### Run Backend Tests

```bash
make -C build dev-test
```

### Connect to Database

```bash
make -C build dev-db-shell
```

### Open Backend Shell

```bash
make -C build dev-shell
```

## Traefik Production Stack

For production deployments with Traefik reverse proxy:

```bash
make -C build traefik-up
```

Stop Traefik:

```bash
make -C build traefik-down
```

## Code Quality

### Format Code

```bash
make -C build format
```

### Lint Code

```bash
make -C build lint
```

## Frontend Development

### Build Frontend Image

```bash
make -C build frontend-build
```

### Start Frontend Dev Server

```bash
make -C build frontend-dev
```

## Environment Variables

The build system uses `.env` files from the project root. Make sure to have a properly configured `.env` file before running any commands.

See `.env.example` for the required environment variables.

## Directory Structure

```
Praestara/
├── build/
│   ├── docker-compose.yml          # Main compose file
│   ├── docker-compose.override.yml # Dev overrides
│   ├── docker-compose.traefik.yml  # Traefik config
│   ├── Makefile                    # Build shortcuts
│   └── build.md                    # This documentation
├── backend/
├── frontend/
├── .env                            # Environment variables
└── README.md
```

## Migration Notes

After moving the docker-compose files to the `build/` directory:

1. All `docker-compose` commands should now use `-C build` flag:
   ```bash
   docker-compose -C build up
   ```

2. Or use the Makefile shortcuts:
   ```bash
   make -C build up
   ```

3. The `.env` file remains in the project root and is loaded automatically.

## Troubleshooting

### Services Won't Start

1. Check that `.env` file exists and is properly configured
2. Run `make -C build logs` to see error messages
3. Try `make -C build clean` and then `make -C build up`

### Database Issues

1. Ensure PostgreSQL container is healthy
2. Run migrations with `make -C build dev-migrate`
3. Check database connectivity with `make -C build dev-db-shell`

### Port Conflicts

If ports 80, 443, 5432, 8000, 8080, 5173 are in use, you'll need to:
1. Stop the services using those ports
2. Or configure Traefik to use different ports

## Best Practices

1. **Always use `make -C build up`** instead of raw `docker-compose` commands
2. **Check logs with `make -C build logs`** when debugging
3. **Run migrations before starting the backend** to avoid database errors
4. **Use `make -C build clean`** before major changes to reset the environment

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Makefile Best Practices](https://www.gnu.org/software/make/manual/make.html)
- [Praestara Development Guide](../development.md)
- [Praestara Deployment Guide](../deployment.md)
