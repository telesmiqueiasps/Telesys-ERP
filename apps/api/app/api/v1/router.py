from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, tenants, companies, users, roles

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(companies.router, prefix="/companies", tags=["Empresas"])
api_router.include_router(users.router, prefix="/users", tags=["Usuários"])
api_router.include_router(roles.router, prefix="/roles", tags=["Cargos e Permissões"])
