# FlowCred — Backend

API REST para o **FlowCred**, sistema de gestão de propostas de crédito imobiliário (MVP portfólio).

**Documentação unificada** (comportamento do sistema, regras de negócio, APIs e tutoriais Git + uso da plataforma): [../DOCUMENTACAO-FlowCred.md](../DOCUMENTACAO-FlowCred.md)

## Tecnologias

- Python 3.12, FastAPI, Uvicorn  
- PostgreSQL 16, SQLAlchemy 2, Alembic, Psycopg 3  
- JWT (PyJWT), bcrypt, Pydantic v2  
- Docker Compose (API + Postgres + volume de uploads)

## Funcionalidades

- Autenticação (`/auth/login`, `/auth/me`) com usuário admin opcional no boot  
- CRUD de clientes com busca e paginação  
- CRUD de propostas, filtros, alteração de status, histórico automático  
- Checklist por proposta + `PATCH /checklist/{item_id}`  
- Upload seguro de documentos (PDF/PNG/JPEG) com metadados e download autenticado  
- Dashboard agregado (`/dashboard/summary`)

## Como rodar com Docker

No diretório `FlowCred-Back`:

```bash
cp .env.example .env
# Ajuste JWT_SECRET_KEY e senhas. Opcional: INITIAL_ADMIN_* para criar admin na primeira subida.
docker compose up --build -d
```

- API: http://localhost:8000  
- Swagger: http://localhost:8000/docs  
- Health: `GET /api/v1/health`

Arquivos enviados ficam em `UPLOAD_DIR` (padrão `/app/uploads`, volume `flowcred_uploads`).

## Variáveis de ambiente

Ver `.env.example`. Principais:

| Variável | Descrição |
|----------|-------------|
| `POSTGRES_*` | Conexão Postgres |
| `JWT_SECRET_KEY` | Segredo HS256 (obrigatório) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiração do access token |
| `BACKEND_CORS_ORIGINS` | Lista separada por vírgulas |
| `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD` | Cria admin uma vez (entrypoint) |
| `UPLOAD_DIR` / `MAX_UPLOAD_BYTES` | Armazenamento e limite de upload |

## Endpoints principais (prefixo `/api/v1`)

- `POST /auth/login` · `GET /auth/me`  
- `POST|GET|PUT|DELETE /clients` · `GET /clients/{id}`  
- `POST|GET /proposals` · `GET|PUT /proposals/{id}` · `PATCH /proposals/{id}/status`  
- `GET /proposals/{id}/checklist` · `PATCH /checklist/{item_id}`  
- `POST|GET /proposals/{id}/documents` · `GET /documents/{id}/download`  
- `GET /proposals/{id}/history`  
- `GET /dashboard/summary`

## Credenciais de teste

Se `INITIAL_ADMIN_EMAIL` e `INITIAL_ADMIN_PASSWORD` estiverem no `.env` (como no exemplo), o primeiro `docker compose up` cria o usuário. Caso contrário:

```bash
docker compose exec backend python -m app.scripts.ensure_admin
```

(use as mesmas variáveis no `.env`)

## Imagens das telas

*(Placeholder para screenshots do frontend.)*

## Próximos passos sugeridos

- Refresh tokens e política de senha  
- Testes automatizados (pytest)  
- Rate limit em login e upload  
- CI (lint + migrations check)
