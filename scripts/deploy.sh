#!/bin/bash
# =============================================================================
# VIPCam — Script de deploy/update para o servidor de producao
#
# Uso:
#   ssh usuario@servidor
#   cd /opt/vipcam
#   bash scripts/deploy.sh
#
# O que faz (sequencial):
#   1. Pull do repositorio
#   2. Build da imagem backend (CUDA + modelos Python)
#   3. Build da imagem frontend (Next.js multi-stage)
#   4. Roda migrations do banco
#   5. Reinicia os containers via docker compose
#   6. Atualiza Nginx se houve mudanca no conf
#   7. Verifica health do sistema
# =============================================================================
set -euo pipefail

# --- Configuracao ---
REPO_DIR="${REPO_DIR:-/opt/vipcam}"
COMPOSE_FILE="docker-compose.portainer.yml"
NGINX_CONF_SRC="nginx/v3.sensevip.ia.br.conf"
NGINX_CONF_DST="/etc/nginx/sites-available/v3.sensevip.ia.br"
BACKEND_PORT=8001
FRONTEND_PORT=3001
HEALTH_URL="http://127.0.0.1:${BACKEND_PORT}/api/health"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step=0
total_steps=7

log() {
    step=$((step + 1))
    echo -e "\n${CYAN}[${step}/${total_steps}]${NC} ${YELLOW}$1${NC}"
}

ok() {
    echo -e "  ${GREEN}✓ $1${NC}"
}

fail() {
    echo -e "  ${RED}✗ $1${NC}"
    exit 1
}

cd "$REPO_DIR" || fail "Diretorio $REPO_DIR nao encontrado"

# Detectar docker compose v1 vs v2
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
else
    DC="docker-compose"
fi

# =============================================================================
log "Atualizando repositorio..."
# =============================================================================
git fetch origin
BEFORE=$(git rev-parse HEAD)
git pull --ff-only origin main || fail "git pull falhou — resolva conflitos manualmente"
AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" = "$AFTER" ]; then
    echo -e "  ${YELLOW}Nenhuma mudanca no repositorio.${NC}"
    read -p "  Continuar mesmo assim? [s/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Ss]$ ]] || exit 0
fi

COMMITS=$(git log --oneline "${BEFORE}..${AFTER}" 2>/dev/null | head -10)
if [ -n "$COMMITS" ]; then
    echo -e "  Novos commits:"
    echo "$COMMITS" | sed 's/^/    /'
fi
ok "Repositorio atualizado"

# =============================================================================
log "Construindo imagem do backend..."
# =============================================================================
docker build \
    -t vipcam-backend \
    -f backend/Dockerfile \
    backend/ \
    || fail "Build do backend falhou"
ok "vipcam-backend construida"

# =============================================================================
log "Construindo imagem do frontend..."
# =============================================================================
docker build \
    -t vipcam-frontend \
    -f frontend/Dockerfile \
    frontend/ \
    || fail "Build do frontend falhou"
ok "vipcam-frontend construida"

# =============================================================================
log "Executando migrations do banco..."
# =============================================================================
# Sobe apenas o banco se nao estiver rodando
$DC -f "$COMPOSE_FILE" up -d db redis
echo "  Aguardando banco ficar saudavel..."
for i in $(seq 1 30); do
    if $DC -f "$COMPOSE_FILE" exec -T db pg_isready -U vipcam -d vipcam >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

$DC -f "$COMPOSE_FILE" run --rm --no-deps \
    -e DATABASE_URL="postgresql+asyncpg://vipcam:d08688ea560642be34fc15@127.0.0.1:5433/vipcam" \
    --entrypoint "" \
    backend \
    alembic upgrade head \
    || echo -e "  ${YELLOW}⚠ Migration falhou ou nao havia mudancas${NC}"
ok "Migrations executadas"

# =============================================================================
log "Reiniciando containers..."
# =============================================================================
$DC -f "$COMPOSE_FILE" down --remove-orphans
$DC -f "$COMPOSE_FILE" up -d
ok "Containers reiniciados"

# Limpar imagens antigas sem tag
echo "  Removendo imagens orfas..."
docker image prune -f >/dev/null 2>&1 || true

# =============================================================================
log "Verificando Nginx..."
# =============================================================================
if [ -f "$NGINX_CONF_SRC" ]; then
    if ! diff -q "$NGINX_CONF_SRC" "$NGINX_CONF_DST" >/dev/null 2>&1; then
        echo "  Nginx conf mudou — atualizando..."
        sudo cp "$NGINX_CONF_SRC" "$NGINX_CONF_DST"
        sudo ln -sf "$NGINX_CONF_DST" /etc/nginx/sites-enabled/ 2>/dev/null || true
        if sudo nginx -t 2>/dev/null; then
            sudo systemctl reload nginx
            ok "Nginx atualizado e recarregado"
        else
            fail "Nginx config invalida — revise $NGINX_CONF_DST"
        fi
    else
        ok "Nginx sem mudancas"
    fi
else
    ok "Nginx conf nao encontrado no repo — ignorando"
fi

# =============================================================================
log "Verificando saude do sistema..."
# =============================================================================
echo "  Aguardando backend iniciar..."
HEALTHY=false
for i in $(seq 1 60); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        HEALTHY=true
        break
    fi
    sleep 2
done

if $HEALTHY; then
    ok "Backend respondendo (GET /api/health → 200)"
else
    echo -e "  ${RED}⚠ Backend nao respondeu em 120s${NC}"
    echo "  Ultimas linhas do log:"
    $DC -f "$COMPOSE_FILE" logs --tail=20 backend 2>/dev/null | sed 's/^/    /'
fi

# Verificar frontend
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${FRONTEND_PORT}" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    ok "Frontend respondendo (porta ${FRONTEND_PORT} → 200)"
else
    echo -e "  ${YELLOW}⚠ Frontend retornou HTTP ${HTTP_CODE}${NC}"
fi

# Resumo dos containers
echo ""
echo -e "${CYAN}=== Status dos containers ===${NC}"
$DC -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null \
    || $DC -f "$COMPOSE_FILE" ps

echo ""
echo -e "${GREEN}Deploy concluido!${NC}"
echo -e "  Acesse: ${CYAN}https://v3.sensevip.ia.br${NC}"
echo -e "  Logs:   ${CYAN}$DC -f $COMPOSE_FILE logs -f backend${NC}"
