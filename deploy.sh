#!/bin/bash
# =============================================================================
# VIPCam — Deploy Unificado (Linux GPU / macOS CPU)
#
# Uso:
#   bash deploy.sh              # Auto-detecta plataforma
#   bash deploy.sh --linux      # Força modo Linux (NVIDIA GPU)
#   bash deploy.sh --mac        # Força modo macOS (CPU)
#   bash deploy.sh --status     # Mostra status dos containers
#   bash deploy.sh --stop       # Para todos os containers
#   bash deploy.sh --logs       # Mostra logs do backend
#
# Features identicas em ambas plataformas:
#   - Detecção de pessoas (YOLOv8)
#   - Reconhecimento facial (InsightFace)
#   - Análise de emoções (HSEmotion)
#   - Dashboard real-time (WebSocket)
#   - PostgreSQL + pgvector + Redis
#
# Diferenças de implementação:
#   Linux: NVIDIA GPU, modelos maiores, inferência ~100ms/frame
#   macOS: CPU only, modelos menores, inferência ~500ms/frame
# =============================================================================
set -euo pipefail

# --- Cores ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Helpers ---
log() {
    step=$((step + 1))
    echo -e "\n${CYAN}[${step}/${total_steps}]${NC} ${YELLOW}$1${NC}"
}

ok() {
    echo -e "  ${GREEN}✓ $1${NC}"
}

warn() {
    echo -e "  ${YELLOW}⚠ $1${NC}"
}

fail() {
    echo -e "  ${RED}✗ $1${NC}"
    exit 1
}

# --- Detecção de plataforma ---
detect_platform() {
    local os_type
    os_type="$(uname -s)"

    case "$os_type" in
        Linux)
            # Verificar se tem NVIDIA GPU disponível
            if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
                echo "linux"
            else
                echo "linux-cpu"
            fi
            ;;
        Darwin)
            echo "mac"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# --- Configuração por plataforma ---
setup_linux() {
    MODE="linux"
    MODE_LABEL="Linux (NVIDIA GPU)"
    COMPOSE_FILE="docker-compose.portainer.yml"
    REPO_DIR="${REPO_DIR:-/opt/vipcam}"
    DOCKERFILE_BACKEND="backend/Dockerfile"
    HEALTH_URL="http://127.0.0.1:8001/api/health"
    FRONTEND_URL="http://127.0.0.1:3001"
    ACCESS_URL="https://v3.sensevip.ia.br"
    HAS_NGINX_SYSTEM=true
    NGINX_CONF_SRC="nginx/v3.sensevip.ia.br.conf"
    NGINX_CONF_DST="/etc/nginx/sites-available/v3.sensevip.ia.br"
    HEALTH_TIMEOUT=60
    total_steps=7

    echo -e "  GPU:       ${GREEN}$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'detectada')${NC}"
    echo -e "  VRAM:      $(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null || echo 'N/A')"
    echo -e "  Modelos:   YOLOv8x (1280px) + InsightFace buffalo_l (640px)"
    echo -e "  Inferência: ~100ms/frame"
}

setup_mac() {
    MODE="mac"
    MODE_LABEL="macOS (CPU mode)"
    COMPOSE_FILE="docker-compose.mac.yml"
    REPO_DIR="$(pwd)"
    DOCKERFILE_BACKEND="backend/Dockerfile.cpu"
    HEALTH_URL="http://localhost:3000/api/health"
    FRONTEND_URL="http://localhost:3000"
    ACCESS_URL="http://localhost:3000"
    HAS_NGINX_SYSTEM=false
    HEALTH_TIMEOUT=90
    total_steps=6

    echo -e "  Arch:      $(uname -m)"
    echo -e "  Modelos:   YOLOv8n (640px) + InsightFace buffalo_s (320px)"
    echo -e "  Inferência: ~500ms/frame (CPU)"
    echo -e "  Acesso:    apenas local (127.0.0.1:3000)"
}

setup_linux_cpu() {
    # Linux sem GPU — usa mesma config do Mac mas com compose adaptado
    MODE="linux-cpu"
    MODE_LABEL="Linux (CPU mode — sem NVIDIA GPU)"
    COMPOSE_FILE="docker-compose.mac.yml"
    REPO_DIR="$(pwd)"
    DOCKERFILE_BACKEND="backend/Dockerfile.cpu"
    HEALTH_URL="http://localhost:3000/api/health"
    FRONTEND_URL="http://localhost:3000"
    ACCESS_URL="http://localhost:3000"
    HAS_NGINX_SYSTEM=false
    HEALTH_TIMEOUT=90
    total_steps=6

    echo -e "  ${YELLOW}NVIDIA GPU não detectada — rodando em CPU${NC}"
    echo -e "  Modelos:   YOLOv8n (640px) + InsightFace buffalo_s (320px)"
    echo -e "  Inferência: ~500ms/frame (CPU)"
}

# --- Detectar docker compose ---
detect_compose() {
    if docker compose version >/dev/null 2>&1; then
        DC="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        DC="docker-compose"
    else
        fail "docker compose não encontrado. Instale o Docker primeiro."
    fi
}

# --- Comandos auxiliares ---
cmd_status() {
    detect_compose
    echo -e "${CYAN}=== Status dos containers ===${NC}"
    for f in docker-compose.portainer.yml docker-compose.mac.yml; do
        if [ -f "$f" ]; then
            running=$($DC -f "$f" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true)
            if [ -n "$running" ] && echo "$running" | grep -q "Up\|running"; then
                echo -e "\n${YELLOW}$f:${NC}"
                echo "$running"
            fi
        fi
    done
}

cmd_stop() {
    detect_compose
    echo -e "${CYAN}Parando containers...${NC}"
    for f in docker-compose.portainer.yml docker-compose.mac.yml; do
        if [ -f "$f" ]; then
            $DC -f "$f" down --remove-orphans 2>/dev/null || true
        fi
    done
    ok "Containers parados"
}

cmd_logs() {
    detect_compose
    local compose_file=""
    for f in docker-compose.portainer.yml docker-compose.mac.yml; do
        if [ -f "$f" ]; then
            running=$($DC -f "$f" ps 2>/dev/null || true)
            if echo "$running" | grep -q "backend"; then
                compose_file="$f"
                break
            fi
        fi
    done
    if [ -z "$compose_file" ]; then
        fail "Nenhum container backend rodando"
    fi
    $DC -f "$compose_file" logs -f backend
}

# --- Parse de argumentos ---
FORCE_MODE=""
for arg in "$@"; do
    case "$arg" in
        --linux)   FORCE_MODE="linux" ;;
        --mac)     FORCE_MODE="mac" ;;
        --status)  cmd_status; exit 0 ;;
        --stop)    cmd_stop; exit 0 ;;
        --logs)    cmd_logs; exit 0 ;;
        --help|-h)
            echo "Uso: bash deploy.sh [opção]"
            echo ""
            echo "Opções:"
            echo "  (sem opção)   Auto-detecta plataforma e faz deploy"
            echo "  --linux       Força deploy Linux (NVIDIA GPU)"
            echo "  --mac         Força deploy macOS (CPU)"
            echo "  --status      Mostra status dos containers"
            echo "  --stop        Para todos os containers"
            echo "  --logs        Mostra logs do backend (follow)"
            echo "  --help        Mostra esta ajuda"
            exit 0
            ;;
        *)
            echo -e "${RED}Opção desconhecida: $arg${NC}"
            echo "Use --help para ver opções disponíveis"
            exit 1
            ;;
    esac
done

# --- Verificar Docker ---
if ! docker info >/dev/null 2>&1; then
    fail "Docker não está rodando. Inicie o Docker primeiro."
fi

detect_compose

# --- Selecionar plataforma ---
step=0

echo -e "${BOLD}${CYAN}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║     VIPCam — Deploy Unificado            ║"
echo "  ║     Barbearia VIP Face Analytics         ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

if [ -n "$FORCE_MODE" ]; then
    PLATFORM="$FORCE_MODE"
    echo -e "  Modo:      ${BOLD}forçado (--${FORCE_MODE})${NC}"
else
    PLATFORM=$(detect_platform)
    echo -e "  Modo:      ${BOLD}auto-detectado${NC}"
fi

case "$PLATFORM" in
    linux)     setup_linux ;;
    mac)       setup_mac ;;
    linux-cpu) setup_linux_cpu ;;
    *)         fail "Plataforma não suportada: $(uname -s). Use --linux ou --mac." ;;
esac

echo -e "  Plataforma: ${BOLD}${MODE_LABEL}${NC}"
echo -e "  Compose:   ${COMPOSE_FILE}"
echo ""

# Confirmação
read -p "  Iniciar deploy? [S/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "  Deploy cancelado."
    exit 0
fi

# =============================================================================
# DEPLOY
# =============================================================================

cd "$REPO_DIR" || fail "Diretório $REPO_DIR não encontrado"

# --- 1. Git pull ---
log "Atualizando repositório..."

if git rev-parse --git-dir >/dev/null 2>&1; then
    git fetch origin 2>/dev/null || true
    BEFORE=$(git rev-parse HEAD)
    git pull --ff-only origin main 2>/dev/null || warn "git pull falhou (talvez não esteja na branch main)"
    AFTER=$(git rev-parse HEAD)

    if [ "$BEFORE" != "$AFTER" ]; then
        COMMITS=$(git log --oneline "${BEFORE}..${AFTER}" 2>/dev/null | head -5)
        if [ -n "$COMMITS" ]; then
            echo "  Novos commits:"
            echo "$COMMITS" | sed 's/^/    /'
        fi
    else
        echo "  Nenhuma mudança no repositório."
    fi
    ok "Repositório atualizado"
else
    warn "Não é um repositório git — usando código local"
fi

# --- 2. Build ---
log "Construindo imagens Docker (${MODE_LABEL})..."

if [ "$MODE" = "linux" ]; then
    # Linux GPU: build separado para melhor feedback
    echo "  Backend (CUDA)..."
    docker build -t vipcam-backend -f "$DOCKERFILE_BACKEND" backend/ \
        || fail "Build do backend falhou"
    echo "  Frontend..."
    docker build -t vipcam-frontend -f frontend/Dockerfile frontend/ \
        || fail "Build do frontend falhou"
else
    # Mac/CPU: build paralelo via compose
    echo "  Isto pode demorar na primeira vez (~10min)..."
    $DC -f "$COMPOSE_FILE" build --parallel 2>&1 | tail -5
fi
ok "Imagens construídas"

# --- 3. Banco e Redis ---
log "Subindo banco e Redis..."

$DC -f "$COMPOSE_FILE" up -d db redis
echo "  Aguardando banco ficar saudável..."
for i in $(seq 1 30); do
    if $DC -f "$COMPOSE_FILE" exec -T db pg_isready -U vipcam -d vipcam >/dev/null 2>&1; then
        break
    fi
    sleep 1
done
ok "PostgreSQL + Redis prontos"

# --- 4. Migrations ---
log "Executando migrations..."

if [ "$MODE" = "linux" ]; then
    $DC -f "$COMPOSE_FILE" run --rm --no-deps \
        -e DATABASE_URL="postgresql+asyncpg://vipcam:vipcam_dev_2024@db:5432/vipcam" \
        --entrypoint "" \
        backend \
        alembic upgrade head 2>&1 | tail -3 \
        || warn "Migration falhou ou não havia mudanças"
else
    $DC -f "$COMPOSE_FILE" run --rm --no-deps \
        --entrypoint "" \
        backend \
        alembic upgrade head 2>&1 | tail -3 \
        || warn "Migration falhou ou não havia mudanças"
fi
ok "Migrations executadas"

# --- 5. Subir tudo ---
log "Subindo todos os serviços..."

$DC -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
$DC -f "$COMPOSE_FILE" up -d
ok "Containers iniciados"

# Limpar imagens órfãs
docker image prune -f >/dev/null 2>&1 || true

# --- 6. Nginx (Linux only) ---
if [ "$HAS_NGINX_SYSTEM" = true ]; then
    log "Verificando Nginx do sistema..."

    if [ -f "$NGINX_CONF_SRC" ]; then
        if ! diff -q "$NGINX_CONF_SRC" "$NGINX_CONF_DST" >/dev/null 2>&1; then
            echo "  Nginx conf mudou — atualizando..."
            sudo cp "$NGINX_CONF_SRC" "$NGINX_CONF_DST"
            sudo ln -sf "$NGINX_CONF_DST" /etc/nginx/sites-enabled/ 2>/dev/null || true
            if sudo nginx -t 2>/dev/null; then
                sudo systemctl reload nginx
                ok "Nginx atualizado e recarregado"
            else
                fail "Nginx config inválida — revise $NGINX_CONF_DST"
            fi
        else
            ok "Nginx sem mudanças"
        fi
    else
        ok "Nginx conf não encontrado no repo — ignorando"
    fi
fi

# --- 7. Health check ---
log "Verificando saúde do sistema..."

echo "  Aguardando sistema iniciar..."
HEALTHY=false
for i in $(seq 1 "$HEALTH_TIMEOUT"); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        HEALTHY=true
        break
    fi
    sleep 2
done

if $HEALTHY; then
    ok "Backend respondendo (${HEALTH_URL} → 200)"
else
    warn "Backend ainda não respondeu em $((HEALTH_TIMEOUT * 2))s"
    echo "  Acompanhe os logs: $DC -f $COMPOSE_FILE logs -f backend"
fi

# Frontend
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    ok "Frontend respondendo (${FRONTEND_URL} → 200)"
else
    warn "Frontend retornou HTTP ${HTTP_CODE} (pode estar iniciando)"
fi

# --- Resumo ---
echo ""
echo -e "${CYAN}=== Status dos containers ===${NC}"
$DC -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null \
    || $DC -f "$COMPOSE_FILE" ps

echo ""
echo -e "${GREEN}Deploy concluído! (${MODE_LABEL})${NC}"
echo ""
echo -e "  App:       ${CYAN}${ACCESS_URL}${NC}"
echo -e "  API:       ${CYAN}${HEALTH_URL}${NC}"
echo -e "  Swagger:   ${CYAN}${ACCESS_URL}/docs${NC}"
echo -e "  Logs:      ${CYAN}$DC -f $COMPOSE_FILE logs -f backend${NC}"
echo -e "  Status:    ${CYAN}bash deploy.sh --status${NC}"
echo -e "  Parar:     ${CYAN}bash deploy.sh --stop${NC}"
echo ""

if [ "$MODE" = "mac" ] || [ "$MODE" = "linux-cpu" ]; then
    echo -e "  ${YELLOW}CPU mode — inferência mais lenta (~500ms/frame vs ~100ms GPU)${NC}"
fi

# Tabela comparativa
echo ""
echo -e "${CYAN}=== Configuração ativa ===${NC}"
echo -e "  ┌──────────────────────┬─────────────────────────┐"
echo -e "  │ Componente           │ Valor                   │"
echo -e "  ├──────────────────────┼─────────────────────────┤"
if [ "$MODE" = "linux" ]; then
    echo -e "  │ Runtime              │ ${GREEN}NVIDIA GPU (CUDA)${NC}       │"
    echo -e "  │ YOLO                 │ yolov8x.pt (1280px)     │"
    echo -e "  │ InsightFace          │ buffalo_l (640px)        │"
    echo -e "  │ FPS target           │ 5                       │"
    echo -e "  │ Inferência           │ ~100ms/frame            │"
else
    echo -e "  │ Runtime              │ ${YELLOW}CPU only${NC}                │"
    echo -e "  │ YOLO                 │ yolov8n.pt (640px)      │"
    echo -e "  │ InsightFace          │ buffalo_s (320px)        │"
    echo -e "  │ FPS target           │ 2                       │"
    echo -e "  │ Inferência           │ ~500ms/frame            │"
fi
echo -e "  │ PostgreSQL           │ 16 + pgvector           │"
echo -e "  │ Redis                │ 7-alpine (256MB)        │"
echo -e "  │ HSEmotion            │ enet_b2_8               │"
echo -e "  └──────────────────────┴─────────────────────────┘"
