# FlowCred — Backend

API REST para o **FlowCred**, sistema de gestão de propostas de crédito imobiliário (MVP portfólio).

**Documentação unificada** (comportamento do sistema, regras de negócio, APIs e tutoriais Git + uso da plataforma): [../DOCUMENTACAO-FlowCred.md](../DOCUMENTACAO-FlowCred.md)

## Tecnologias

- Python 3.12, FastAPI, Uvicorn  
- SQLAlchemy 2, Alembic (SQLite por omissão; Postgres opcional via `POSTGRES_*`)  
- JWT (PyJWT), bcrypt, Pydantic v2  
- Docker Compose (API + volume SQLite em `/app/data` + volume de uploads)

## Funcionalidades

- Autenticação (`/auth/login`, `/auth/me`) com utilizador e senha; admin opcional no boot (`INITIAL_ADMIN_*`)  
- CRUD de clientes com busca e paginação  
- CRUD de propostas, filtros, alteração de status, histórico automático  
- Checklist por proposta + `PATCH /checklist/{item_id}`  
- Upload seguro de documentos (PDF/PNG/JPEG) com metadados e download autenticado  
- Dashboard agregado (`/dashboard/summary`)

## Como rodar com Docker

No diretório `FlowCred-Back`:

```bash
cp .env.example .env
# Ajuste JWT_SECRET_KEY. Opcional: INITIAL_ADMIN_USERNAME / INITIAL_ADMIN_PASSWORD (ver .env.example).
docker compose up --build -d
```

- API (host): http://localhost:8001 (mapeamento `8001:8000` no Compose para evitar conflito com algo na 8000)  
- Swagger: http://localhost:8001/docs  
- Health: `GET /api/v1/health`  
- Base de dados: ficheiro SQLite no volume `flowcred_data` (`/app/data/db.local` no container)

Arquivos enviados ficam em `UPLOAD_DIR` (padrão `/app/uploads`, volume `flowcred_uploads`).

### Dev local sem Docker (uvicorn)

Na primeira vez, crie o esquema e o utilizador admin (usa o `.env` com `DATABASE_URL` e `INITIAL_ADMIN_*`):

```bash
alembic upgrade head
python -m app.scripts.ensure_admin
python -m app.scripts.seed_dev_demo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

`seed_dev_demo` só faz efeito com `SEED_DEV_DATA=1` no `.env` (já vem no `.env.example`): cria **um cliente demo** (CPF `52998224725`) e **uma proposta** de exemplo, de forma idempotente — assim quem clona o repo já vê cliente na lista e pode abrir a proposta no front.

Com a API a correr, smoke test rápido:

```bash
FLOWCRED_SMOKE_BASE=http://127.0.0.1:8001/api/v1 python -m app.scripts.smoke_flowcred
```

Se aparecer `no such table: users`, faltou o `alembic upgrade head`. O Docker faz migrações + `ensure_admin` + `seed_dev_demo` automaticamente no `entrypoint.sh`.

## Variáveis de ambiente

Ver `.env.example`. Principais:

| Variável | Descrição |
|----------|-------------|
| `DATABASE_URL` | Se definido, usa esta URI (ex.: `sqlite:////app/data/db.local` no Docker). |
| `POSTGRES_*` | Opcional: conexão Postgres se `DATABASE_URL` estiver vazio e estes campos preenchidos. |
| `JWT_SECRET_KEY` | Segredo HS256 (obrigatório) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do access token |
| `BACKEND_CORS_ORIGINS` | Lista separada por vírgulas |
| `INITIAL_ADMIN_USERNAME` / `INITIAL_ADMIN_PASSWORD` | Cria ou sincroniza o admin (entrypoint) |
| `SEED_DEV_DATA` | `1` = cliente + proposta demo (idempotente); use `0` em produção |
| `UPLOAD_DIR` / `MAX_UPLOAD_BYTES` | Armazenamento e limite de upload |

## Endpoints principais (prefixo `/api/v1`)

- `POST /auth/login` · `GET /auth/me`  
- `POST|GET|PUT|DELETE /clients` · `GET /clients/{id}`  
- `POST|GET /proposals` · `GET|PUT /proposals/{id}` · `PATCH /proposals/{id}/status`  
- `GET /proposals/{id}/checklist` · `PATCH /checklist/{item_id}`  
- `POST|GET /proposals/{id}/documents` · `GET /documents/{id}/download`  
- `GET /proposals/{id}/history`  
- `GET /dashboard/summary`

## Credenciais e dados de teste

- **Login (UI / API):** utilizador `admin`, senha `admin` (definidos em `INITIAL_ADMIN_*` no `.env.example`). **Só para desenvolvimento.**
- **Cliente demo (seed):** nome “Cliente demonstração FlowCred”, CPF `52998224725`, e-mail `cliente.demo@flowcred.local`.
- **Proposta demo:** banco `Banco demonstração (FlowCred seed)` — aparece na lista e no dashboard.

Em produção desligue o seed (`SEED_DEV_DATA=0`) e troque as credenciais; o `.env` é carregado pelo Compose a partir do ficheiro que copiar do `.env.example`.

Se não quiser usar o entrypoint:

```bash
docker compose exec backend python -m app.scripts.ensure_admin
```

(as mesmas variáveis `INITIAL_ADMIN_*` precisam de estar no ambiente do container)

## Imagens das telas

*(Placeholder para screenshots do frontend.)*

## Próximos passos sugeridos

- Refresh tokens e política de senha  
- Testes automatizados (pytest)  
- Rate limit em login e upload  
- CI (lint + migrations check)
