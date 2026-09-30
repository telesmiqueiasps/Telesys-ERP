from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, tenants, companies, users, roles, products, stock, customers, suppliers, cash, sales, sync, purchases, finance, audit, licenses, superadmin, backups, reports, updates, products_fiscal, company_fiscal, fiscal_operation, tax_engine, nfe, sefaz_adapter, fiscal_event, rejections, nfce, nfse, special_operations, fiscal_reports, fiscal_update_center, fiscal_homologation

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(companies.router, prefix="/companies", tags=["Empresas"])
api_router.include_router(users.router, prefix="/users", tags=["Usuários"])
api_router.include_router(roles.router, prefix="/roles", tags=["Cargos e Permissões"])
api_router.include_router(products.router, prefix="/products", tags=["Produtos e Categorias"])
api_router.include_router(products_fiscal.router, prefix="/products-fiscal", tags=["Perfil Fiscal do Produto"])
api_router.include_router(company_fiscal.router, prefix="/company-fiscal", tags=["Configurações Fiscais da Empresa e Séries"])
api_router.include_router(fiscal_operation.router, prefix="/fiscal-operations", tags=["Operações Fiscais e Matriz de Cenários"])
api_router.include_router(tax_engine.router, prefix="/tax-engine", tags=["Calculadora e Motor Fiscal (Tax Engine)"])
api_router.include_router(nfe.router, prefix="/nfe", tags=["Nota Fiscal Eletrônica (NF-e Modelo 55)"])
api_router.include_router(nfce.router, prefix="/nfce", tags=["Nota Fiscal de Consumidor Eletrônica (NFC-e Modelo 65)"])
api_router.include_router(nfse.router, prefix="/nfse", tags=["Nota Fiscal de Serviços Eletrônica (NFS-e)"])
api_router.include_router(special_operations.router, prefix="/special-operations", tags=["Operações Fiscais Especiais e Não-Vendas"])
api_router.include_router(fiscal_reports.router, prefix="/fiscal-reports", tags=["Relatórios Fiscais, Livros e Exportação"])
api_router.include_router(fiscal_update_center.router, prefix="/fiscal-update-center", tags=["Centro de Atualizações Fiscais e Notas Técnicas SEFAZ"])
api_router.include_router(fiscal_homologation.router, prefix="/fiscal-homologation", tags=["Suíte de Homologação e Validação Fiscal E2E"])
api_router.include_router(sefaz_adapter.router, prefix="/sefaz", tags=["Adaptador SEFAZ WebServices"])
api_router.include_router(fiscal_event.router, prefix="/fiscal-events", tags=["Eventos Fiscais (Cancelamento, CC-e, Inutilização)"])
api_router.include_router(rejections.router, prefix="/rejections", tags=["Catálogo de Rejeições e Pré-Validador SEFAZ"])
api_router.include_router(stock.router, prefix="/stock", tags=["Estoque e Movimentações"])
api_router.include_router(customers.router, prefix="/customers", tags=["Clientes"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Fornecedores"])
api_router.include_router(cash.router, prefix="/cash", tags=["Caixa e Movimentos"])
api_router.include_router(sales.router, prefix="/sales", tags=["Vendas e PDV"])
api_router.include_router(sync.router, prefix="/sync", tags=["Sync Engine"])
api_router.include_router(purchases.router, prefix="/purchases", tags=["Compras e Entradas"])
api_router.include_router(finance.router, prefix="/finance", tags=["Módulo Financeiro"])
api_router.include_router(audit.router, prefix="/audit", tags=["Auditoria e Rastreabilidade"])
api_router.include_router(licenses.router, prefix="/licenses", tags=["Licenciamento e Dispositivos"])
api_router.include_router(superadmin.router, prefix="/superadmin", tags=["SuperAdmin / Gestão da Plataforma"])
api_router.include_router(backups.router, prefix="/backups", tags=["Backup e Restauração"])
api_router.include_router(reports.router, prefix="/reports", tags=["Relatórios BI e DRE Gerencial"])
api_router.include_router(updates.router, prefix="/updates", tags=["Auto-Updater e Versionamento"])









