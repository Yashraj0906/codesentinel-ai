#!/bin/bash
# ============================================================
# render_start.sh -- Startup script for Render deployment
# ============================================================
# Render provides DATABASE_URL as postgres:// but SQLAlchemy
# needs postgresql+asyncpg:// — this script converts it.
# ============================================================

# Fix DATABASE_URL format for SQLAlchemy asyncpg
if [[ "$DATABASE_URL" == postgres://* ]]; then
    export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql+asyncpg:\/\/}"
fi

if [[ "$DATABASE_URL" == postgresql://* ]] && [[ "$DATABASE_URL" != postgresql+asyncpg://* ]]; then
    export DATABASE_URL="${DATABASE_URL/postgresql:\/\//postgresql+asyncpg:\/\/}"
fi

echo "Starting CodeSentinel AI API..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
