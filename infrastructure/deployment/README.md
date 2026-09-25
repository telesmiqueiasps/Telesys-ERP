# Infrastructure Deployment

Este diretório contém receitas, manifestos e orientações para deploy do Telesys ERP nos ambientes de Staging e Produção.

## Componentes para Deploy
1. **API (FastAPI)**: Imagem Docker conteinerizada (`infrastructure/docker/Dockerfile.api`).
2. **PostgreSQL**: Instância gerenciada (ex: AWS RDS, DigitalOcean Managed Database) ou cluster conteinerizado de alta disponibilidade.
3. **Desktop (Tauri)**: Binários nativos gerados via pipeline CI/CD (GitHub Actions / Tauri Action) para Windows (`.msi`, `.exe`), Linux (`.AppImage`, `.deb`) e macOS (`.dmg`).
