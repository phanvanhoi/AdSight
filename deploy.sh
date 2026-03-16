#!/bin/bash
set -e

# ============================
# AdSight Deploy Script
# ============================

APP_DIR="/opt/adsight"
REPO_URL="CHANGE_ME_YOUR_GITHUB_REPO_URL"
BRANCH="main"
COMPOSE_FILE="docker-compose.prod.yml"

echo "=========================================="
echo "  AdSight - Production Deployment"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# -------------------------------------------
# 1. First-time setup (if app dir doesn't exist)
# -------------------------------------------
if [ ! -d "$APP_DIR" ]; then
    echo -e "${YELLOW}[1/5] First-time setup - Cloning repository...${NC}"
    sudo mkdir -p "$APP_DIR"
    sudo chown "$USER:$USER" "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
    git checkout "$BRANCH"

    # Create .env.production from example
    cp .env.production.example .env.production

    # Generate secure secrets
    echo -e "${YELLOW}Generating secure passwords...${NC}"
    DB_PASS=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    APP_SECRET=$(openssl rand -hex 32)
    MINIO_ACCESS=$(openssl rand -hex 16)
    MINIO_SECRET=$(openssl rand -hex 32)

    # Update .env.production with generated secrets
    sed -i "s/CHANGE_ME_STRONG_DB_PASSWORD/$DB_PASS/g" .env.production
    sed -i "s/CHANGE_ME_TO_A_RANDOM_STRING_64_CHARS/$APP_SECRET/" .env.production
    sed -i "s/CHANGE_ME_TO_A_RANDOM_JWT_SECRET_64_CHARS/$JWT_SECRET/" .env.production
    sed -i "s/CHANGE_ME_MINIO_ACCESS/$MINIO_ACCESS/" .env.production
    sed -i "s/CHANGE_ME_MINIO_SECRET/$MINIO_SECRET/" .env.production

    echo -e "${GREEN}Secrets generated and saved to .env.production${NC}"
    echo -e "${YELLOW}IMPORTANT: Save these credentials somewhere safe!${NC}"
    echo "  DB Password: $DB_PASS"
    echo "  JWT Secret:  $JWT_SECRET"
    echo "  MinIO Access: $MINIO_ACCESS"
    echo "  MinIO Secret: $MINIO_SECRET"
else
    # -------------------------------------------
    # 2. Pull latest code
    # -------------------------------------------
    echo -e "${YELLOW}[1/5] Pulling latest code...${NC}"
    cd "$APP_DIR"
    git fetch origin
    git reset --hard "origin/$BRANCH"
fi

# -------------------------------------------
# 3. Build and deploy
# -------------------------------------------
echo -e "${YELLOW}[2/5] Building Docker images...${NC}"
docker compose -f "$COMPOSE_FILE" build --no-cache

echo -e "${YELLOW}[3/5] Starting services...${NC}"
docker compose -f "$COMPOSE_FILE" up -d

echo -e "${YELLOW}[4/6] Waiting for services to be healthy...${NC}"
sleep 15

# Run migrations
echo -e "${YELLOW}[5/6] Running database migrations...${NC}"
docker compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head || echo -e "${YELLOW}Migration skipped or failed — check logs${NC}"

# Check health
echo -e "${YELLOW}[6/6] Checking service status...${NC}"
docker compose -f "$COMPOSE_FILE" ps

# Check if API is responding
echo ""
if curl -sf http://localhost:8080/docs > /dev/null 2>&1; then
    echo -e "${GREEN}=========================================="
    echo "  Deploy SUCCESS!"
    echo "  Frontend: http://YOUR_VPS_IP:8080"
    echo "  API Docs: http://YOUR_VPS_IP:8080/docs"
    echo "  MinIO Console: http://YOUR_VPS_IP:9001"
    echo "==========================================${NC}"
else
    echo -e "${YELLOW}Services are still starting up..."
    echo "Run 'docker compose -f $COMPOSE_FILE logs -f' to monitor${NC}"
fi
