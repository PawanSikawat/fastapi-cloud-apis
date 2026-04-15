#!/usr/bin/env bash
# Deploy a project to FastAPI Cloud.
#
# Usage: ./deploy.sh <project-name>
#   e.g. ./deploy.sh qr-code-generator

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="${1:?Usage: ./deploy.sh <project-name>}"
PROJECT_DIR="$REPO_ROOT/projects/$PROJECT_NAME"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: project '$PROJECT_NAME' not found at $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

echo "Deploying $PROJECT_NAME to FastAPI Cloud..."
uv run fastapi cloud deploy
