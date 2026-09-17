#!/bin/bash
set -e

export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

APP_DIR="/home/toro/vk_comments_monitor"
cd "$APP_DIR"


git fetch origin main

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] Found new commits. Updating..."
    git pull origin main
    docker compose up -d --build tatd_bot
    echo "[$(date)] Successfully redeployed."
fi
