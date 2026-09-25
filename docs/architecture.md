# Arquitetura do Telesys ERP + PDV

## 1. Visão Geral
O **Telesys ERP + PDV** é concebido como um sistema corporativo modular de alta performance, resiliente a operações locais (offline-first no PDV/Desktop) e escalável na nuvem (gestão administrativa, retaguarda e integrações fiscais).

## 2. Estratégia de Monorepo
O monorepo utiliza o gerenciador de workspaces padrão do npm para o ecossistema TypeScript/JavaScript e ambientes virtuais isolados para os serviços Python:

- **Isolamento de Responsabilidades**: Cada aplicação (`apps/`) consome pacotes compartilhados (`packages/`) sem duplicação de regras e tipos.
- **Tipagem Unificada**: Contratos de dados compartilhados entre frontend e backend, garantindo segurança na evolução dos schemas.
- **Governança de Infraestrutura**: Toda a definição conteinerizada e receitas de implantação residem em `infrastructure/`.

## 3. Componentes da Solução

```
+------------------------------------------------------------------+
|                          Camada Cliente                          |
|                                                                  |
|   +--------------------------+     +-------------------------+   |
|   |  Desktop / PDV (Tauri)   |     |  Admin Web (Futuro)     |   |
|   |  - React + TypeScript    |     |  - React + TypeScript   |   |
|   |  - Tailwind + shadcn/ui  |     |  - Tailwind + shadcn/ui |   |
|   |  - TanStack Query        |     |                         |   |
|   |  - Zustand + Hook Form   |     +-------------------------+   |
|   +--------------------------+                                   |
+------------------------------------------------------------------+
                                 │
                            HTTP / REST
                                 ▼
+------------------------------------------------------------------+
|                          Camada Servidor                         |
|                                                                  |
|   +----------------------------------------------------------+   |
|   |                      FastAPI Backend                     |   |
|   |  - Python 3.12 Assíncrono                                |   |
|   |  - SQLAlchemy 2.0 (ORM)                                  |   |
|   |  - Alembic (Migrações Declarativas)                      |   |
|   |  - Pydantic v2 (Validação e Serialização)                |   |
|   +----------------------------------------------------------+   |
+------------------------------------------------------------------+
                                 │
                              SQL / TCP
                                 ▼
+------------------------------------------------------------------+
|                          Camada de Dados                         |
|                                                                  |
|   +----------------------------------------------------------+   |
|   |                   PostgreSQL 16+ Docker                  |   |
|   |  - Extensões: uuid-ossp, pgcrypto                        |   |
|   |  - Volume Persistente: telesys_postgres_data             |   |
|   +----------------------------------------------------------+   |
+------------------------------------------------------------------+
```

## 4. Pilha Tecnológica
| Componente | Tecnologia | Finalidade |
| :--- | :--- | :--- |
| **Desktop Shell** | Tauri v2 + Rust | Executável leve, rápido e de baixo consumo de memória |
| **Frontend UI** | React 18 + TypeScript + Vite | Interface reativa, modular e tipada |
| **Estilização** | Tailwind CSS + shadcn/ui | Sistema de design moderno, acessível e responsivo |
| **Ícones** | Lucide React | Conjunto visual consistente |
| **Estado Local** | Zustand | Gerenciamento de estado do shell da aplicação |
| **Data Fetching** | TanStack Query v5 | Cache, refetch e sincronização de requisições |
| **Formulários** | React Hook Form + Zod | Formulários declarativos com validação estrita |
| **Backend API** | FastAPI + Python 3.12 | API RESTful assíncrona de alta vazão |
| **ORM** | SQLAlchemy 2.0 | Mapeamento relacional declarativo tipado |
| **Migrações** | Alembic | Versionamento estrutural e idempotente do banco de dados |
| **Banco de Dados** | PostgreSQL 16 Alpine | Banco de dados relacional robusto com extensões nativas |
| **Conteinerização**| Docker + Docker Compose | Padronização dos ambientes de desenvolvimento e produção |
