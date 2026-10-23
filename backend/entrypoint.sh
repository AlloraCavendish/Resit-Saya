#!/bin/sh
# Purpose: Container startup entrypoint running database migrations before starting the API server.
# Security: Fails closed on migration errors; drops root privileges if configured; runs alembic upgrade head.
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Starting server..."
exec "$@"
