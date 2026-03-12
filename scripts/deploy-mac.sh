#!/bin/bash
# =============================================================================
# VIPCam — Deploy para macOS (Apple Silicon / Intel)
#
# Uso:
#   cd /path/to/vipcam
#   bash scripts/deploy-mac.sh
#
# Requisitos:
#   - Docker Desktop para Mac (com Rosetta para Apple Silicon)
#   - Git
#
# Diferenças do deploy de produção:
#   - Sem NVIDIA GPU — tudo roda em CPU
#   - YOLO em 640px (não 1280), InsightFace em 320 (não 640)
#   - FPS target: 2 (CPU é ~5x mais lento)
#   - Tudo acessível via http://localhost:3000 (nginx reverse proxy)
#   - DB e Redis não expostos externamente
# =============================================================================
set -euo pipefail

COMPOSE_FILE="docker-compose.mac.yml"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step=0
total_steps=6

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

# Verificar Docker
if ! docker info >/dev/null 2>&1; then
    fail "Docker não está rodando. Abra o Docker Desktop primeiro."
fi

# Detectar docker compose v1 vs v2
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
else
    DC="docker-compose"
fi

echo -e "${CYAN}=== VIPCam — Deploy macOS (CPU mode) ===${NC}"
echo -e "  Compose: ${COMPOSE_FILE}"
echo -e "  Arch: $(uname -m)"
echo ""

# =============================================================================
log "Atualizando repositório..."
# =============================================================================
if git rev-parse --git-dir >/dev/null 2>&1; then
    git fetch origin 2>/dev/null || true
    BEFORE=$(git rev-parse HEAD)
    git pull --ff-only origin main 2>/dev/null || echo -e "  ${YELLOW}⚠ git pull falhou (talvez não esteja na branch main)${NC}"
    AFTER=$(git rev-parse HEAD)
    if [ "$BEFORE" != "$AFTER" ]; then
        COMMITS=$(git log --oneline "${BEFORE}..${AFTER}" 2>/dev/null | head -5)
        if [ -n "$COMMITS" ]; then
            echo "  Novos commits:"
            echo "$COMMITS" | sed 's/^/    /'
        fi
    fi
    ok "Repositório atualizado"
else
    echo -e "  ${YELLOW}Não é um repositório git — pulando pull${NC}"
    ok "Usando código local"
fi

# =============================================================================
log "Construindo imagens Docker (CPU)..."
# =============================================================================
echo "  Isto pode demorar na primeira vez (~10min)..."
$DC -f "$COMPOSE_FILE" build --parallel 2>&1 | tail -5
ok "Imagens construídas"

# =============================================================================
log "Subindo banco e Redis..."
# =============================================================================
$DC -f "$COMPOSE_FILE" up -d db redis
echo "  Aguardando banco ficar saudável..."
for i in $(seq 1 30); do
    if $DC -f "$COMPOSE_FILE" exec -T db pg_isready -U vipcam -d vipcam >/dev/null 2>&1; then
        break
    fi
    sleep 1
done
ok "PostgreSQL + Redis prontos"

# =============================================================================
log "Executando migrations..."
# =============================================================================
$DC -f "$COMPOSE_FILE" run --rm --no-deps \
    --entrypoint "" \
    backend \
    alembic upgrade head 2>&1 | tail -3 \
    || echo -e "  ${YELLOW}⚠ Migration falhou ou não havia mudanças${NC}"
ok "Migrations executadas"

# =============================================================================
log "Subindo todos os serviços..."
# =============================================================================
$DC -f "$COMPOSE_FILE" up -d
ok "Containers iniciados"

# Limpar imagens orfãs
docker image prune -f >/dev/null 2>&1 || true

# =============================================================================
log "Verificando saúde do sistema..."
# =============================================================================
echo "  Aguardando sistema iniciar (CPU demora mais)..."
HEALTHY=false
for i in $(seq 1 90); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/api/health" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        HEALTHY=true
        break
    fi
    sleep 2
done

if $HEALTHY; then
    ok "Sistema respondendo (http://localhost:3000/api/health → 200)"
else
    echo -e "  ${YELLOW}⚠ Backend ainda não respondeu — modelos AI podem demorar para carregar${NC}"
    echo "  Acompanhe os logs: $DC -f $COMPOSE_FILE logs -f backend"
fi

# Frontend
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    ok "Frontend respondendo (http://localhost:3000 → 200)"
else
    echo -e "  ${YELLOW}⚠ Frontend retornou HTTP ${HTTP_CODE} (pode estar iniciando)${NC}"
fi

# Status
echo ""
echo -e "${CYAN}=== Status ===${NC}"
$DC -f "$COMPOSE_FILE" ps 2>/dev/null

echo ""
echo -e "${GREEN}Deploy concluído!${NC}"
echo ""
echo -e "  App:       ${CYAN}http://localhost:3000${NC}"
echo -e "  API:       ${CYAN}http://localhost:3000/api/health${NC}"
echo -e "  Swagger:   ${CYAN}http://localhost:3000/docs${NC}"
echo -e "  Logs:      ${CYAN}$DC -f $COMPOSE_FILE logs -f backend${NC}"
echo ""
echo -e "  ${YELLOW}Acesso apenas local (127.0.0.1) — para testes${NC}"
echo -e "  ${YELLOW}CPU mode — inferência mais lenta (~500ms/frame vs ~100ms GPU)${NC}"
echo -e "  ${YELLOW}YOLO 640px, InsightFace 320px, FPS target: 2${NC}"
