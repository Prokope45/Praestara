# Database Management Scripts

This directory contains utility scripts for managing the Praestara application environment and database.

## Scripts Overview

### 1. setup-env.sh
Automatically creates a `.env` file from `.env.example` with secure, randomly generated secrets.

**Usage:**
```bash
./scripts/setup-env.sh
```

**What it does:**
- Copies `.env.example` to `.env`
- Generates a secure `SECRET_KEY` using Python's secrets module
- Generates a secure `POSTGRES_PASSWORD` using Python's secrets module
- Replaces placeholder values in `.env` with the generated secrets
- Prompts before overwriting an existing `.env` file

**Requirements:**
- Python 3 (or Python 2.7+)
- `.env.example` file must exist

---

### 2. restore-db.sh
Restores a database dump into the PostgreSQL container.

**Usage:**
```bash
./scripts/restore-db.sh <path-to-dump-file>
```

**Example:**
```bash
./scripts/restore-db.sh backups/backup_2026-01-27_210355.sql
```

**What it does:**
- Validates that the dump file exists
- Checks if the database container is running (starts it if needed)
- Waits for the database to be healthy
- Automatically detects dump format (SQL or custom PostgreSQL format)
- Restores the dump using the appropriate tool (`psql` or `pg_restore`)

**Requirements:**
- `.env` file must exist
- Docker and Docker Compose must be installed
- Valid database dump file

---

### 3. dump-db.sh
Creates a database backup and saves it to the `backups/` directory.

**Usage:**
```bash
./scripts/dump-db.sh
```

**What it does:**
- Creates a `backups/` directory if it doesn't exist
- Generates a timestamped backup filename (e.g., `backup_2026-01-27_210355.sql`)
- Checks if the database container is running
- Waits for the database to be healthy
- Creates a SQL dump using `pg_dump`
- Reports the backup file location and size

**Requirements:**
- `.env` file must exist
- Docker and Docker Compose must be installed
- Database container must be running

**Note:** The `backups/` directory is excluded from version control via `.gitignore` to prevent accidentally committing database dumps.

---

### 4. update-db-password.sh
Updates the PostgreSQL password in the database to match the password in your `.env` file, while preserving all data.

**Usage:**
```bash
./scripts/update-db-password.sh
```

**What it does:**
- Reads the `POSTGRES_PASSWORD` from your `.env` file
- Checks if the database container is running (starts it if needed)
- Waits for the database to be healthy
- Updates the PostgreSQL user password using `ALTER USER`
- Preserves all existing data in the database

**Requirements:**
- `.env` file must exist with `POSTGRES_PASSWORD` set
- Docker and Docker Compose must be installed
- Database container must be accessible

**Use Cases:**
- When you clone a project with an existing database volume but different `.env` credentials
- After changing the password in your `.env` file
- When you get "password authentication failed" errors
- To sync database credentials with your environment configuration

**Note:** This script is particularly useful when you have an existing database with data that you want to keep, but need to update the password to match your current `.env` file.

---

## Quick Start

### New Project Setup

1. **Initial Setup:**
   ```bash
   ./scripts/setup-env.sh
   ```

2. **Start your application:**
   ```bash
   docker compose up -d
   ```

3. **Create a backup:**
   ```bash
   ./scripts/dump-db.sh
   ```

4. **Restore from a backup:**
   ```bash
   ./scripts/restore-db.sh backups/backup_2026-01-27_210355.sql
   ```

### Fixing Password Authentication Issues

If you encounter "password authentication failed" errors after cloning or with an existing database:

1. **Update the database password to match your .env:**
   ```bash
   ./scripts/update-db-password.sh
   ```

2. **Restart your services:**
   ```bash
   docker compose restart
   ```

---

## Notes

- All scripts include error handling and informative messages
- Scripts are compatible with both macOS and Linux
- Database dumps are automatically excluded from git commits
- The restore script supports both SQL and PostgreSQL custom format dumps
