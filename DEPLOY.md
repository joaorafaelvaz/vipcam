# Deploy VIPCam — Portainer + Nginx + v3.sensevip.ia.br

## Pre-requisitos no servidor

- Ubuntu Server com Docker + Docker Compose v2
- NVIDIA Container Toolkit instalado (`nvidia-smi` funcionando dentro de containers)
- Portainer CE rodando (geralmente em `:9443`)
- Nginx nativo instalado e rodando
- DNS do domínio `v3.sensevip.ia.br` apontando para o IP público do servidor
- Portas 80 e 443 liberadas no firewall

## Passo 1 — Subir o repositório para o servidor

**Opção A — Git (recomendado):**
```bash
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
- `CAMERA_*` — URLs RTSP reais das câmeras
- `CORS_ORIGINS` — já está `["https://v3.sensevip.ia.br"]`

Gerar JWT_SECRET:
```bash
openssl rand -hex 32
```

## Passo 3 — Configurar Nginx

### 3.1 — Emitir certificado SSL com Certbot

```bash
# Instalar Certbot (se ainda não tiver)
sudo apt install certbot python3-certbot-nginx -y

# Criar config temporária para validação
sudo tee /etc/nginx/sites-available/v3.sensevip.ia.br > /dev/null <<'EOF'
server {
    listen 80;
    server_name v3.sensevip.ia.br;
    location / { return 200 'ok'; }
}
EOF

sudo ln -sf /etc/nginx/sites-available/v3.sensevip.ia.br /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Emitir certificado
sudo certbot certonly --nginx -d v3.sensevip.ia.br
```

### 3.2 — Copiar config definitiva do Nginx

```bash
sudo cp /opt/vipcam/nginx/v3.sensevip.ia.br.conf /etc/nginx/sites-available/v3.sensevip.ia.br
sudo nginx -t && sudo systemctl reload nginx
```

O arquivo `nginx/v3.sensevip.ia.br.conf` já está pronto no repositório com:
- Redirect HTTP → HTTPS
- Proxy `/api/*` e `/docs` → backend (127.0.0.1:8000)
- Proxy `/ws/*` → backend com upgrade WebSocket
- Proxy `/*` (tudo mais) → frontend (127.0.0.1:3000)

### 3.3 — Renovação automática do SSL

Certbot já instala o cron/timer de renovação. Verificar:
```bash
sudo certbot renew --dry-run
```

## Passo 4 — Download dos modelos AI

```bash
cd /opt/vipcam
docker run --rm -v vipcam_model_data:/models -v $(pwd)/scripts:/scripts \
  --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 \
  bash -c "apt-get update && apt-get install -y python3.11 python3-pip && \
           pip3 install ultralytics insightface onnxruntime-gpu hsemotion && \
           bash /scripts/download_models.sh /models"
```

## Passo 5 — Deploy via Portainer

### 5.1 — Stack via Portainer UI

1. Acessar Portainer: `https://servidor:9443`
2. Ir em **Stacks** → **Add stack**
3. Nome: `vipcam`
4. **Build method**:

**Opção A — Repository (recomendado):**
- Repository URL: URL do git
- Reference: `main`
- Compose path: `docker-compose.prod.yml`

**Opção B — Web editor:**
- Colar o conteúdo do `docker-compose.prod.yml`

5. **Environment variables**: clicar **"Load variables from .env file"** e fazer upload do `.env`

   Ou adicionar manualmente as variáveis principais:

   | Variável | Valor |
   |---|---|
   | `POSTGRES_PASSWORD` | (senha forte) |
   | `DATABASE_URL` | postgresql+asyncpg://vipcam:SENHA@db:5432/vipcam |
   | `JWT_SECRET` | (resultado do openssl rand) |

6. Clicar **Deploy the stack**

### 5.2 — Alternativa via CLI

```bash
cd /opt/vipcam
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

## Passo 6 — Executar migrations e seed

```bash
# Migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Seed das câmeras
docker compose -f docker-compose.prod.yml run --rm \
  -v $(pwd)/scripts:/scripts \
  backend python /scripts/seed_cameras.py
```

## Passo 7 — Verificar

```bash
# Containers rodando
docker compose -f docker-compose.prod.yml ps

# Logs do backend
docker compose -f docker-compose.prod.yml logs -f backend

# Testar API
curl https://v3.sensevip.ia.br/api/health

# Testar SSL
curl -vI https://v3.sensevip.ia.br 2>&1 | grep "subject:"

# Testar WebSocket (wscat)
npx wscat -c wss://v3.sensevip.ia.br/ws/live
```

Acessar no navegador: **https://v3.sensevip.ia.br**

## Passo 8 — GPU runtime (se necessário)

Se o Portainer não reconhecer `deploy.resources.reservations.devices` (GPU):

1. Editar `/etc/docker/daemon.json`:
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

Isso faz o runtime NVIDIA ser o padrão para todos os containers.

## Arquitetura de rede

```
Internet
    |
    v
[v3.sensevip.ia.br]  DNS -> IP do servidor
    |
    v :80/:443
+----------+
|  Nginx   |  SSL termination (Let's Encrypt / Certbot)
|  (nativo)|
+----+-----+
     |
     |-- /api/*  /ws/*  /docs  ->  127.0.0.1:8000 (backend container)
     |
     +-- /*  (tudo mais)       ->  127.0.0.1:3000 (frontend container)

     Containers (portas bind em 127.0.0.1 apenas):
     +-- db         (PostgreSQL + pgvector, rede interna)
     +-- redis      (Redis, rede interna)
     +-- backend    (FastAPI + GPU pipeline, 127.0.0.1:8000)
     +-- frontend   (Next.js, 127.0.0.1:3000)
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

# Restart de um servico
docker compose -f docker-compose.prod.yml restart backend

# Renovar SSL manualmente (se precisar)
sudo certbot renew
sudo systemctl reload nginx
```

## Troubleshooting

| Problema | Solucao |
|---|---|
| Certbot falha | Verificar DNS aponta para IP correto, porta 80 aberta |
| 502 Bad Gateway | Containers nao estao rodando — checar `docker compose ps` |
| GPU nao detectada | Instalar nvidia-container-toolkit, configurar daemon.json |
| Backend nao conecta no DB | POSTGRES_PASSWORD diferente no DATABASE_URL |
| WebSocket nao conecta | Verificar bloco `location /ws/` no Nginx tem os headers de upgrade |
| CORS bloqueado | CORS_ORIGINS no .env deve ser `["https://v3.sensevip.ia.br"]` |
| Nginx nao inicia | `sudo nginx -t` para ver erro de syntax |
