# Guia de Configuração e Ambiente Local

Este guia detalha o passo a passo para inicializar o monorepo do **Telesys ERP + PDV** em sua máquina.

## Pré-requisitos
- **Node.js**: Versão 20 LTS ou 22 LTS (instalado: Node v22.14.0, npm 10.9.2)
- **Python**: Versão 3.12+ (instalado: Python 3.12.4)
- **Rust / Cargo**: Necessário para compilar o executável nativo do Tauri (via [rustup.rs](https://rustup.rs))
- **Docker & Docker Compose**: Para o container do PostgreSQL (ou PostgreSQL 16+ instalado localmente)

## Passo a Passo de Inicialização

### 1. Clonar e Instalar Dependências do Monorepo
Na raiz do projeto:
```bash
npm install
```

### 2. Configurar Variáveis de Ambiente
Copie os arquivos de exemplo para `.env`:
```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/desktop/.env.example apps/desktop/.env
```

### 3. Iniciar o Banco de Dados (PostgreSQL)
Se utilizar Docker:
```bash
docker compose up -d postgres
```
O banco estará acessível em `localhost:5432` com usuário `postgres` e base `telesys_erp`.

### 4. Inicializar a API FastAPI
No diretório `apps/api`:
```bash
cd apps/api

# Criar ambiente virtual
python -m venv .venv

# Ativar no Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Ou no Linux/macOS:
# source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar a API em modo desenvolvimento
uvicorn app.main:app --reload --port 8000
```
Documentação interativa Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Executar o Aplicativo Desktop
No diretório `apps/desktop` (ou na raiz via script do workspace):
```bash
# Executar a interface web com Vite
npm run dev --workspace=@telesys/desktop

# Ou executar o Tauri completo (requer Rust instalado)
npm run tauri -- dev
```
