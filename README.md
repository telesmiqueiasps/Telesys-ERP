# Telesys ERP + PDV

Monorepo fundacional do **Telesys ERP + PDV** — Sistema de gestão empresarial e frente de caixa projetado para alta confiabilidade, performance e arquitetura modular.

---

## 🎯 Objetivo do Projeto
O Telesys ERP + PDV tem como objetivo fornecer uma solução completa de gestão operacional e frente de caixa para estabelecimentos comerciais. O sistema é concebido para operar com máxima agilidade no ponto de venda (PDV Desktop), com retaguarda administrativa unificada e arquitetura preparada para sincronização e escalabilidade.

Nesta fase inicial de fundação:
- Estrutura base de monorepo estabelecida.
- Camada desktop configurada com Tauri v2, React, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, Zustand, React Hook Form e Zod.
- Camada de backend configurada com Python 3.12, FastAPI, SQLAlchemy 2.0 e Alembic.
- Camada de infraestrutura preparada com Docker Compose para PostgreSQL 16.
- Nenhuma regra de negócio ou tabela de domínio foi implementada nesta etapa.

---

## 🏛️ Arquitetura
O projeto adota a arquitetura de **Monorepo Modular**:

- **`apps/desktop`**: Aplicação de frente de caixa/retaguarda local construída com Tauri v2. Utiliza webview leve renderizada com React/Vite, garantindo velocidade nativa, baixo consumo de memória RAM e acesso a periféricos locais.
- **`apps/api`**: Serviço backend construído em Python com FastAPI, responsável pelas rotas REST, contratos assíncronos e acesso à persistência via SQLAlchemy 2.
- **`apps/admin`**: Estrutura reservada para a futura interface administrativa web.
- **`apps/portal`**: Estrutura reservada para portal de autoatendimento e clientes/fornecedores.
- **`packages/*`**: Pacotes compartilhados com contratos TypeScript (`shared-types`), schemas Zod (`validation`) e utilitários de interface (`ui`).
- **`infrastructure/*`**: Receitas de infraestrutura como código (Docker, Alembic, roteiros de deploy).

---

## 🛠️ Tecnologias Principais

| Camada | Tecnologias |
| :--- | :--- |
| **Desktop** | [Tauri v2](https://tauri.app/), [React 18](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vitejs.dev/) |
| **Estilização & UI** | [Tailwind CSS](https://tailwindcss.com/), [shadcn/ui](https://ui.shadcn.com/), [Lucide React](https://lucide.dev/) |
| **Estado & Dados** | [Zustand](https://github.com/pmndrs/zustand), [TanStack Query v5](https://tanstack.com/query/latest) |
| **Validação** | [React Hook Form](https://react-hook-form.com/), [Zod](https://zod.dev/) |
| **Backend API** | [Python 3.12](https://www.python.org/), [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Pydantic v2](https://docs.pydantic.dev/) |
| **Banco de Dados & ORM** | [PostgreSQL 16](https://www.postgresql.org/), [SQLAlchemy 2.0](https://www.sqlalchemy.org/), [Alembic](https://alembic.sqlalchemy.org/) |
| **Infraestrutura** | [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/) |

---

## 📂 Estrutura de Diretórios

```
telesys-erp/
├── apps/
│   ├── desktop/                 # Aplicação Desktop (Tauri + React + Vite + TS)
│   │   ├── src-tauri/           # Configuração e binário Rust do Tauri v2
│   │   ├── src/                 # Componentes React, hooks, store e estilos
│   │   ├── components.json      # Configuração shadcn/ui
│   │   ├── tailwind.config.js   # Tokens de design do Tailwind CSS
│   │   └── package.json
│   ├── api/                     # Backend API (Python + FastAPI)
│   │   ├── app/                 # Código da aplicação (core, models, schemas, endpoints)
│   │   ├── alembic/             # Configuração e histórico de migrações
│   │   ├── alembic.ini          # Arquivo de configuração do Alembic
│   │   ├── requirements.txt     # Dependências Python
│   │   └── pyproject.toml
│   ├── admin/                   # Futuro app web administrativo
│   └── portal/                  # Futuro portal do cliente/fornecedor
├── packages/
│   ├── shared-types/            # Tipos e contratos TypeScript compartilhados
│   ├── ui/                      # Utilitários de interface e ícones compartilhados
│   └── validation/              # Schemas agnósticos de validação Zod
├── infrastructure/
│   ├── docker/                  # Dockerfiles e scripts de inicialização (PostgreSQL)
│   ├── migrations/              # Políticas e governança de migrações
│   └── deployment/              # Documentação e manifestos de implantação
├── docs/                        # Documentação de arquitetura e guias de setup
├── .env.example                 # Exemplo de variáveis de ambiente
├── .gitignore                   # Regras de exclusão do controle de versão
├── docker-compose.yml           # Ambiente PostgreSQL para desenvolvimento local
├── package.json                 # Configuração de workspaces npm
└── README.md
```

---

## 🚀 Como Instalar

### Pré-requisitos
- **Node.js** v20+ ou v22+
- **Python** 3.12+
- **Docker & Docker Compose** (ou PostgreSQL 16 instalado localmente)
- **Rust Toolchain** (opcional para rodar `cargo tauri dev` diretamente; o frontend React/Vite pode ser executado independentemente)

### 1. Clonar o repositório e instalar dependências Node
```bash
# Na raiz do monorepo:
npm install
```

### 2. Configurar variáveis de ambiente
Copie os modelos de ambiente:
```bash
# Na raiz
cp .env.example .env

# Na API
cp apps/api/.env.example apps/api/.env

# No Desktop
cp apps/desktop/.env.example apps/desktop/.env
```

---

## 🐘 Como Iniciar o PostgreSQL

### Via Docker Compose (Recomendado)
```bash
docker compose up -d postgres
```
Para verificar os logs do container:
```bash
docker compose logs -f postgres
```
Para parar o serviço:
```bash
docker compose down
```

*Nota: As credenciais padrão de desenvolvimento estão definidas em `.env.example`: usuário `postgres`, senha `postgres_dev_password`, banco `telesys_erp`, porta `5432`.*

---

## 🐍 Como Executar a API (FastAPI)

1. Acesse o diretório da API:
   ```bash
   cd apps/api
   ```

2. Crie e ative o ambiente virtual Python:
   - **No Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **No Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Inicie o servidor FastAPI em modo recarregamento automático (hot-reload):
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Acesse no navegador:
   - Endpoint de saúde: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
   - Documentação Swagger interativa: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Documentação Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🖥️ Como Executar o Desktop (Tauri + React)

A partir da raiz do monorepo:

### Modo Web (Desenvolvimento rápido com Vite)
Para desenvolver e testar a interface diretamente no navegador:
```bash
npm run dev:desktop
```
Acesse em: [http://localhost:1420](http://localhost:1420).

### Modo Desktop Nativo (Tauri)
*(Requer o Rust toolchain instalado na máquina)*
```bash
npm run tauri -- dev
```
O Tauri compilará a janela nativa integrada ao servidor Vite.

### Compilação de Produção
```bash
npm run build:desktop
```

---

## 🧪 Verificação de Integridade
Para verificar a integridade da tipagem e do build em todos os pacotes:
```bash
npm run typecheck
npm run build
```
