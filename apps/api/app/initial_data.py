import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.company import Company
from app.models.user import User
from app.models.rbac import Permission, Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PERMISSIONS = [
    # Vendas / PDV
    {"code": "vendas.visualizar", "name": "Visualizar Vendas", "module": "vendas", "description": "Permite visualizar histórico de vendas"},
    {"code": "vendas.criar", "name": "Realizar Vendas", "module": "vendas", "description": "Permite registrar vendas no PDV"},
    {"code": "vendas.cancelar", "name": "Cancelar Vendas", "module": "vendas", "description": "Permite cancelar vendas realizadas"},
    {"code": "vendas.desconto", "name": "Aplicar Descontos em Vendas", "module": "vendas", "description": "Permite aplicar descontos no carrinho"},

    # Estoque
    {"code": "estoque.visualizar", "name": "Visualizar Estoque", "module": "estoque", "description": "Permite visualizar saldos de estoque"},
    {"code": "estoque.ajuste", "name": "Realizar Ajuste de Estoque", "module": "estoque", "description": "Permite alterar saldos manualmente"},
    {"code": "estoque.movimento", "name": "Registrar Movimentações", "module": "estoque", "description": "Permite dar entradas e saídas de estoque"},

    # Produtos
    {"code": "produtos.visualizar", "name": "Visualizar Produtos", "module": "produtos", "description": "Permite visualizar catálogo de produtos"},
    {"code": "produtos.editar", "name": "Gerenciar Produtos", "module": "produtos", "description": "Permite cadastrar e alterar produtos"},

    # Financeiro
    {"code": "financeiro.visualizar", "name": "Visualizar Financeiro", "module": "financeiro", "description": "Permite visualizar contas e movimentações de caixa"},
    {"code": "financeiro.baixar", "name": "Baixar Títulos Financeiros", "module": "financeiro", "description": "Permite dar baixa em contas a pagar/receber"},

    # Usuários e Sistema
    {"code": "usuarios.gerenciar", "name": "Gerenciar Usuários e Cargos", "module": "usuarios", "description": "Permite gerenciar usuários, empresas e funções"},
    {"code": "sistema.configurar", "name": "Configurações de Sistema", "module": "sistema", "description": "Permite alterar parâmetros globais do sistema"},
]


def init_db(db: Session) -> None:
    logger.info("Iniciando seed de banco de dados...")

    # 1. Seed Permissions
    permissions_map = {}
    for p_data in SYSTEM_PERMISSIONS:
        perm = db.scalar(select(Permission).where(Permission.code == p_data["code"]))
        if not perm:
            perm = Permission(**p_data)
            db.add(perm)
            db.flush()
            logger.info(f"Permissão criada: {perm.code}")
        permissions_map[perm.code] = perm

    # 2. Seed Default Tenant
    tenant = db.scalar(select(Tenant).where(Tenant.name == "Empresa Matriz Padrão"))
    if not tenant:
        tenant = Tenant(
            name="Empresa Matriz Padrão",
            document="00000000000100",
            is_active=True
        )
        db.add(tenant)
        db.flush()
        logger.info(f"Tenant inicial criado: {tenant.name} ({tenant.id})")

    # 3. Seed Default Company
    company = db.scalar(select(Company).where(Company.tenant_id == tenant.id))
    if not company:
        company = Company(
            tenant_id=tenant.id,
            name="Telesys ERP Matriz",
            trade_name="Telesys Automação Comercial",
            cnpj="00.000.000/0001-00",
            is_active=True
        )
        db.add(company)
        db.flush()
        logger.info(f"Empresa inicial criada: {company.name}")

    # 4. Seed Default Admin Role
    admin_role = db.scalar(select(Role).where(Role.tenant_id == tenant.id, Role.name == "Administrador"))
    if not admin_role:
        admin_role = Role(
            tenant_id=tenant.id,
            name="Administrador",
            description="Acesso total às funcionalidades do sistema",
            is_system=True,
            permissions=list(permissions_map.values())
        )
        db.add(admin_role)
        db.flush()
        logger.info("Cargo Administrador criado")

    # 5. Seed Super Admin User
    admin_user = db.scalar(select(User).where(User.email == "admin@telesys.com.br"))
    if not admin_user:
        admin_user = User(
            tenant_id=tenant.id,
            name="Administrador do Sistema",
            email="admin@telesys.com.br",
            password_hash=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
            roles=[admin_role]
        )
        db.add(admin_user)
        logger.info("Usuário Super Admin criado: admin@telesys.com.br / admin123")

    db.commit()
    logger.info("Seed de banco de dados concluído com sucesso!")


if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
    db.close()
