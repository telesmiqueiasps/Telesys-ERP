from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, tenants, companies, users, roles, products, stock, customers, suppliers, cash, sales

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(companies.router, prefix="/companies", tags=["Empresas"])
api_router.include_router(users.router, prefix="/users", tags=["Usuários"])
api_router.include_router(roles.router, prefix="/roles", tags=["Cargos e Permissões"])
api_router.include_router(products.router, prefix="/products", tags=["Produtos e Categorias"])
api_router.include_router(stock.router, prefix="/stock", tags=["Estoque e Movimentações"])
api_router.include_router(customers.router, prefix="/customers", tags=["Clientes"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Fornecedores"])
api_router.include_router(cash.router, prefix="/cash", tags=["Caixa e Movimentos"])
api_router.include_router(sales.router, prefix="/sales", tags=["Vendas e PDV"])



