# Infrastructure Migrations

Este diretório gerencia o ciclo de vida e a governança de migrações de banco de dados do Telesys ERP.

## Ferramenta
As migrações são executadas através do **Alembic** integrado ao **SQLAlchemy 2** dentro da aplicação `apps/api`.

## Comandos Principais
A partir do diretório `apps/api`:
- Gerar nova migração automática:
  ```bash
  alembic revision --autogenerate -m "nome_da_migracao"
  ```
- Aplicar migrações pendentes:
  ```bash
  alembic upgrade head
  ```
- Reverter última migração:
  ```bash
  alembic downgrade -1
  ```
- Histórico de migrações:
  ```bash
  alembic history --verbose
  ```
