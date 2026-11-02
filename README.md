# FlowCred — Backend (API)

[![CI](https://github.com/augustoemiliano/FlowCred-Back/actions/workflows/ci.yml/badge.svg)](https://github.com/augustoemiliano/FlowCred-Back/actions/workflows/ci.yml)

API REST do **FlowCred**, um sistema de gestão de propostas de **crédito imobiliário**: cadastro de clientes, propostas por banco e valor do imóvel, acompanhamento das etapas (análise de crédito → laudo → jurídico → contrato → registro → pagamento ao vendedor → finalizado), checklist operacional, upload de documentos, histórico de movimentações e dashboard com indicadores.

O frontend (React + TypeScript) fica no repositório [FlowCred-Front](https://github.com/augustoemiliano/FlowCred-Front).

## Screenshots

> _Espaço reservado para capturas de tela (login, dashboard, lista de propostas, detalhe da proposta)._
>
> <!-- Exemplo: ![Dashboard](docs/screenshots/dashboard.png) -->

## Stack

- **Python 3.12**, **FastAPI**, Uvicorn
- **SQLAlchemy 2** + **Alembic** (SQLite por padrão; PostgreSQL opcional via `POSTGRES_*`)
- **Pydantic v2** / pydantic-settings
- Autenticação **JWT** (PyJWT) com senhas em **bcrypt**
- **pytest** + httpx (testes), **Ruff** (lint/format)
- Docker / Docker Compose, GitHub Actions

## Funcionalidades

- **Autenticação**: login com usuário e senha (`/auth/login`), token JWT Bearer, `/auth/me`; usuário admin criado a partir de variáveis de ambiente.
- **Clientes**: CRUD com busca (nome, e-mail, CPF/CNPJ parcial) e paginação; validação de dígitos verificadores de CPF/CNPJ; documento único; não permite excluir cliente com propostas.
- **Propostas**: CRUD com banco, valor do imóvel, valor financiado (não pode exceder o valor do imóvel), responsável e data da próxima etapa; filtros por banco, etapa, responsável e cliente; paginação.
- **Etapas**: alteração de status com observação, registrada no histórico.
- **Checklist** padrão criado com cada proposta (10 itens da operação), marcável item a item.
- **Documentos**: upload de PDF/PNG/JPEG com validação de tipo pelo conteúdo (magic bytes), limite de tamanho, nome de armazenamento aleatório, download autenticado e exclusão.
- **Histórico de movimentações**: criação, edição, mudança de etapa, checklist e documentos, com usuário e data.
- **Dashboard**: total de propostas, contagem por etapa e por banco, soma do valor financiado.
- **Dados demo** idempotentes (6 clientes e propostas em etapas diferentes) para quem clona o repositório.

## Como rodar localmente (sem Docker)

Pré-requisito: Python 3.12.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

cp .env.example .env          # Windows: copy .env.example .env

alembic upgrade head          # cria o banco SQLite em ./db.local
python -m app.scripts.ensure_admin    # cria o usuário admin (INITIAL_ADMIN_*)
python -m app.scripts.seed_dev_demo   # dados demo (só com SEED_DEV_DATA=1)

uvicorn app.main:app --reload --port 8001
```

- API: http://localhost:8001/api/v1
- Swagger: http://localhost:8001/docs · ReDoc: http://localhost:8001/redoc
- Health check: `GET /api/v1/health`

Smoke test com a API rodando:

```bash
FLOWCRED_SMOKE_BASE=http://127.0.0.1:8001/api/v1 python -m app.scripts.smoke_flowcred
```

> Se aparecer `no such table: users`, faltou o `alembic upgrade head`.

## Como rodar com Docker

```bash
cp .env.example .env
docker compose up --build -d
```

- API em http://localhost:8001 (mapeamento `8001:8000`), Swagger em http://localhost:8001/docs.
- O `entrypoint.sh` aplica as migrações, cria/sincroniza o admin e carrega os dados demo automaticamente.
- SQLite no volume `flowcred_data` (`/app/data/db.local`) e uploads no volume `flowcred_uploads` (`/app/uploads`).
- O container roda com usuário não-root.

Para subir o frontend junto, veja o README do [FlowCred-Front](https://github.com/augustoemiliano/FlowCred-Front) (ele aponta para `localhost:8001`).

## Credenciais de demonstração

| Item | Valor |
|------|-------|
| Usuário / senha | `admin` / `admin` (definidos em `INITIAL_ADMIN_*` no `.env.example`) |
| Cliente demo principal | “Cliente demonstração FlowCred”, CPF `529.982.247-25` |
| Outros dados demo | 5 clientes adicionais com propostas em Laudo, Jurídico, Contrato, Finalizado e Cancelado |

**Apenas para desenvolvimento.** Em produção use `SEED_DEV_DATA=0`, troque a senha do admin e gere um `JWT_SECRET_KEY` aleatório.

## Testes e qualidade

```bash
pytest                 # 39 testes: auth, CORS, clientes, propostas, checklist, documentos, dashboard, seed
ruff check .           # lint
ruff format --check .  # formatação
alembic check          # modelos e migrações em sincronia
```

Os testes usam um SQLite temporário criado via migrações Alembic (não tocam no `db.local`).

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda lint, verificação de migrações, testes e, em seguida, build da imagem com `docker compose` + smoke test da API.

## Variáveis de ambiente

Todas estão documentadas em [`.env.example`](.env.example).

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PROJECT_NAME`, `PROJECT_VERSION`, `API_V1_PREFIX` | `FlowCred API`, `0.1.0`, `/api/v1` | Metadados e prefixo das rotas |
| `DATABASE_URL` | vazio → `sqlite:///./db.local` | URI SQLAlchemy; no Docker é `sqlite:////app/data/db.local` |
| `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | vazio | PostgreSQL opcional (usado se `DATABASE_URL` estiver vazio) |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173,…` | Origens permitidas, separadas por vírgula |
| `JWT_SECRET_KEY` | — (obrigatória, ≥ 16 caracteres) | Segredo HS256 dos tokens |
| `JWT_ALGORITHM` | `HS256` | Algoritmo do JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Validade do token |
| `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD` | `admin` / `admin` | Admin criado/sincronizado por `ensure_admin` |
| `SEED_DEV_DATA` | `1` no exemplo | `1` carrega os dados demo; `0` em produção |
| `UPLOAD_DIR` | `./uploads` | Diretório dos arquivos enviados (`/app/uploads` no Docker) |
| `MAX_UPLOAD_BYTES` | `10485760` | Limite por arquivo (10 MB) |

## Endpoints (prefixo `/api/v1`)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Saúde da API e do banco |
| `POST` | `/auth/login` | Login (`{username, password}`) → `{access_token}` |
| `GET` | `/auth/me` | Usuário autenticado |
| `GET` | `/users` | Usuários ativos (para escolher responsável) |
| `GET` / `POST` | `/clients` | Listar (busca + paginação) / criar |
| `GET` / `PUT` / `DELETE` | `/clients/{id}` | Detalhe / atualizar / excluir |
| `GET` / `POST` | `/proposals` | Listar (filtros `bank`, `status`, `responsible_user_id`, `client_id`) / criar |
| `GET` / `PUT` / `DELETE` | `/proposals/{id}` | Detalhe / atualizar / excluir |
| `PATCH` | `/proposals/{id}/status` | Mudar etapa (com observação) |
| `GET` | `/proposals/{id}/checklist` | Checklist da proposta |
| `PATCH` | `/checklist/{item_id}` | Marcar/desmarcar item |
| `GET` / `POST` | `/proposals/{id}/documents` | Listar / enviar documento (multipart `file`) |
| `GET` | `/documents/{id}/download` | Download autenticado |
| `DELETE` | `/documents/{id}` | Excluir documento |
| `GET` | `/proposals/{id}/history` | Histórico de movimentações |
| `GET` | `/dashboard/summary` | Indicadores do dashboard |

Todas as rotas, exceto `/health` e `/auth/login`, exigem `Authorization: Bearer <token>`.

## Estrutura

```
app/
├── api/
│   ├── deps.py            # dependência de autenticação (usuário atual via JWT)
│   ├── router.py          # agrega as rotas
│   └── routes/            # auth, users, clients, proposals, checklist, documents, dashboard, health
├── constants/             # itens padrão do checklist
├── core/                  # configurações (pydantic-settings) e segurança (JWT, bcrypt)
├── db/                    # engine/sessão SQLAlchemy e Base declarativa
├── models/                # modelos ORM e enums (etapas, ações do histórico)
├── schemas/               # schemas Pydantic de entrada/saída
├── scripts/               # ensure_admin, seed_dev_demo, smoke_flowcred
├── services/              # checklist padrão e registro de histórico
└── utils/                 # validação de CPF/CNPJ e upload seguro
alembic/                   # migrações
tests/                     # pytest
```

## Possíveis evoluções

- Refresh token e política de senha / gestão de usuários pela API
- Rate limit no login e no upload
- Armazenamento de documentos em object storage (S3 ou compatível)
