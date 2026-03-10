# Deploy VIPCam — Portainer + v3.sensevip.ia.br

## Pre-requisitos no servidor

- Ubuntu Server com Docker + Docker Compose v2
- NVIDIA Container Toolkit instalado (`nvidia-smi` funcionando dentro de containers)
- Portainer CE rodando (geralmente em `:9443`)
- DNS do domínio `v3.sensevip.ia.br` apontando para o IP público do servidor
- Portas 80 e 443 liberadas no firewall

## Passo 1 — Subir o repositório para o servidor

**Opção A — Git (recomendado):**
```bash
# No servidor
cd /opt
git clone <url-do-repositorio> vipcam
cd vipcam
```

**Opção B — Upload direto:**
```bash
scp -r ./vipcam user@servidor:/opt/vipcam
```

## Passo 2 — Configurar variáveis de ambiente

```bash
cd /opt/vipcam
cp .env.production .env
nano .env
```

Trocar obrigatoriamente:
- `POSTGRES_PASSWORD` — senha forte para o PostgreSQL
- `DATABASE_URL` — mesma senha no connection string
- `JWT_SECRET` — chave aleatória de 32+ caracteres
- `ACME_EMAIL` — email real para certificado SSL
- `CAMERA_*` — URLs RTSP reais das câmeras
- `CORS_ORIGINS` — já está `["https://v3.sensevip.ia.br"]`

Gerar JWT_SECRET:
```bash
openssl rand -hex 32
```

## Passo 3 — Download dos modelos AI

```bash
cd /opt/vipcam
# Criar volume de modelos e baixar
docker run --rm -v vipcam_model_data:/models -v $(pwd)/scripts:/scripts \
  --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 \
  bash -c "apt-get update && apt-get install -y python3.11 python3-pip && \
           pip3 install ultralytics insightface onnxruntime-gpu hsemotion && \
           bash /scripts/download_models.sh /models"
```

## Passo 4 — Deploy via Portainer

### 4.1 — Stack via Portainer UI

1. Acessar Portainer: `https://servidor:9443`
2. Ir em **Stacks** → **Add stack**
3. Nome: `vipcam`
4. **Build method**: escolher uma das opções:

**Opção A — Repository (recomendado):**
- Repository URL: URL do git
- Reference: `main`
- Compose path: `docker-compose.prod.yml`

**Opção B — Upload:**
- Fazer upload do `docker-compose.prod.yml`

**Opção C — Web editor:**
- Colar o conteúdo do `docker-compose.prod.yml`

5. **Environment variables**: Na seção "Environment variables", adicionar todas as variáveis do `.env`:

| Variável | Valor |
|---|---|
| `POSTGRES_PASSWORD` | (senha forte) |
| `ACME_EMAIL` | admin@sensevip.ia.br |
| (demais vars do .env) | ... |

Ou marcar **"Load variables from .env file"** e fazer upload do `.env`.

6. Clicar **Deploy the stack**

### 4.2 — Alternativa via CLI no servidor

```bash
cd /opt/vipcam
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

## Passo 5 — Executar migrations

```bash
# Entrar no container do backend
docker compose -f docker-compose.prod.yml exec backend bash

# Dentro do container
alembic upgrade head
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from scripts_runner import seed
asyncio.run(seed())
" 2>/dev/null || echo "Seed via script..."

# Ou diretamente:
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Seed das câmeras:
```bash
docker compose -f docker-compose.prod.yml exec backend python -m scripts.seed_cameras
```

Ou, se o seed_cameras está fora do backend:
```bash
docker compose -f docker-compose.prod.yml run --rm \
  -v $(pwd)/scripts:/app/scripts \
  backend python /app/scripts/seed_cameras.py
```

## Passo 6 — Verificar

```bash
# Checar se todos os containers estão rodando
docker compose -f docker-compose.prod.yml ps

# Checar logs
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f traefik

# Testar health
curl https://v3.sensevip.ia.br/api/health

# Testar certificado SSL
curl -vI https://v3.sensevip.ia.br 2>&1 | grep "SSL certificate"
```

Acessar no navegador: **https://v3.sensevip.ia.br**

## Passo 7 — Configurar GPU runtime no Portainer

Se o deploy via Portainer não reconhecer `deploy.resources.reservations.devices` (GPU), é necessário:

1. No servidor, editar `/etc/docker/daemon.json`:
```json
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
```

2. Reiniciar Docker:
```bash
sudo systemctl restart docker
```

Isso faz o runtime NVIDIA ser o padrão, eliminando a necessidade da seção `deploy.resources`.

## Arquitetura de rede em produção

```
Internet
    │
    ▼
[v3.sensevip.ia.br]  DNS → IP do servidor
    │
    ▼ :80/:443
┌─────────┐
│ Traefik │  SSL termination (Let's Encrypt auto)
└────┬────┘
     │
     ├── /api/*  /ws/*  /docs  → backend:8000
     │
     └── /*  (tudo mais)       → frontend:3000
```

## Manutenção

```bash
# Atualizar (rebuild)
cd /opt/vipcam
git pull
docker compose -f docker-compose.prod.yml up -d --build

# Ver logs em tempo real
docker compose -f docker-compose.prod.yml logs -f --tail=100

# Backup do banco
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U vipcam vipcam > backup_$(date +%Y%m%d).sql

# Restart de um serviço específico
docker compose -f docker-compose.prod.yml restart backend
```

## Troubleshooting

| Problema | Solução |
|---|---|
| SSL não emite certificado | Verificar DNS aponta para o IP correto, portas 80/443 abertas |
| GPU não detectada no container | Instalar nvidia-container-toolkit, configurar daemon.json |
| Backend não conecta no DB | Verificar POSTGRES_PASSWORD igual no DATABASE_URL |
| WebSocket não conecta | Verificar CORS_ORIGINS inclui `https://v3.sensevip.ia.br` |
| Traefik 404 | Verificar labels nos services, rodar `docker logs vipcam-traefik-1` |
