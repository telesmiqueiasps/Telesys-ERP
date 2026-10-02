import logging
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.company import Company
from app.models.user import User
from app.models.rbac import Permission, Role
from app.models.product import Product, ProductCategory, ProductUnit, ProductBarcode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PERMISSIONS = [
    # Vendas / PDV
    {"code": "vendas.visualizar", "name": "Visualizar Vendas", "module": "vendas", "description": "Permite visualizar histórico de vendas"},
    {"code": "vendas.criar", "name": "Realizar Vendas", "module": "vendas", "description": "Permite registrar vendas no PDV"},
    {"code": "vendas.cancelar", "name": "Cancelar Vendas", "module": "vendas", "description": "Permite cancelar vendas realizadas"},
    {"code": "vendas.desconto", "name": "Aplicar Descontos em Vendas", "module": "vendas", "description": "Permite aplicar descontos no carrinho"},

    # Estoque & Produtos
    {"code": "estoque.visualizar", "name": "Visualizar Estoque", "module": "estoque", "description": "Permite visualizar saldos de estoque"},
    {"code": "estoque.ajuste", "name": "Realizar Ajuste de Estoque", "module": "estoque", "description": "Permite alterar saldos manualmente"},
    {"code": "estoque.movimento", "name": "Registrar Movimentações", "module": "estoque", "description": "Permite dar entradas e saídas de estoque"},
    {"code": "produtos.visualizar", "name": "Visualizar Produtos", "module": "produtos", "description": "Permite visualizar catálogo de produtos"},
    {"code": "produtos.editar", "name": "Gerenciar Produtos", "module": "produtos", "description": "Permite cadastrar e alterar produtos"},

    # Compras
    {"code": "compras.gerenciar", "name": "Gerenciar Compras e Entradas", "module": "compras", "description": "Permite importar XML e dar entrada de notas de compra"},

    # Financeiro
    {"code": "financeiro.visualizar", "name": "Visualizar Financeiro", "module": "financeiro", "description": "Permite visualizar contas e movimentações de caixa"},
    {"code": "financeiro.baixar", "name": "Baixar Títulos Financeiros", "module": "financeiro", "description": "Permite dar baixa em contas a pagar/receber"},

    # Relatórios e Clientes
    {"code": "relatorios.visualizar", "name": "Visualizar Relatórios e BI", "module": "relatorios", "description": "Permite visualizar relatórios gerenciais e estatísticas"},
    {"code": "clientes.gerenciar", "name": "Gerenciar Clientes e Fornecedores", "module": "cadastros", "description": "Permite cadastrar e alterar clientes e fornecedores"},

    # Administração, Usuários e Filiais (Exclusivo do Admin do Tenant)
    {"code": "usuarios.gerenciar", "name": "Gerenciar Usuários, Cargos e Filiais", "module": "usuarios", "description": "Permite criar/editar usuários, cargos, permissões e filiais"},
    {"code": "sistema.configurar", "name": "Configurações Globais de Sistema", "module": "sistema", "description": "Permite alterar parâmetros globais do sistema e fiscais"},
]

DEFAULT_UNITS = [
    {"code": "UN", "name": "Unidade", "allow_decimal": False},
    {"code": "KG", "name": "Quilograma", "allow_decimal": True},
    {"code": "CX", "name": "Caixa", "allow_decimal": False},
    {"code": "LT", "name": "Litro", "allow_decimal": True},
    {"code": "M", "name": "Metro", "allow_decimal": True},
]

DEFAULT_CATEGORIES = [
    {"name": "Bebidas", "description": "Refrigerantes, sucos, águas e bebidas alcoólicas"},
    {"name": "Alimentos", "description": "Alimentos secos, grãos e enlatados"},
    {"name": "Higiene e Limpeza", "description": "Produtos de limpeza doméstica e higiene pessoal"},
    {"name": "Diversos", "description": "Produtos variados"},
]


def seed_tenant_default_roles(db: Session, tenant_id: Any) -> dict:
    """
    Cadastra os 6 cargos padrão do sistema para o tenant informado:
    - Administrador (Dono do Sistema no Tenant - acesso total incluindo usuarios.gerenciar)
    - Gestor (Gestor da Empresa - acesso operacional total, sem criar usuários/filiais)
    - Supervisor (Supervisor de Loja)
    - Operador de Caixa (Frente de Caixa / PDV)
    - Financeiro (Contas a Pagar/Receber e Caixa)
    - Estoquista (Controle de Estoque e Compras)
    """
    # 1. Carregar/Garantir Permissões
    perms_by_code = {}
    for p_data in SYSTEM_PERMISSIONS:
        perm = db.scalar(select(Permission).where(Permission.code == p_data["code"]))
        if not perm:
            perm = Permission(**p_data)
            db.add(perm)
            db.flush()
        perms_by_code[perm.code] = perm

    # 2. Definições dos Cargos Padrão
    roles_definitions = [
        {
            "name": "Administrador",
            "description": "Acesso total às funcionalidades, gerenciamento de usuários, cargos e filiais",
            "codes": list(perms_by_code.keys()),
        },
        {
            "name": "Gestor",
            "description": "Acesso operacional completo ao sistema (Vendas, Estoque, Financeiro, Fiscal e Relatórios), exceto gerenciar usuários/filiais",
            "codes": [code for code in perms_by_code.keys() if code != "usuarios.gerenciar"],
        },
        {
            "name": "Supervisor",
            "description": "Supervisão de loja, descontos, cancelamentos, consulta de estoque e relatórios",
            "codes": [
                "vendas.visualizar", "vendas.criar", "vendas.cancelar", "vendas.desconto",
                "estoque.visualizar", "estoque.ajuste", "produtos.visualizar",
                "financeiro.visualizar", "relatorios.visualizar", "clientes.gerenciar"
            ],
        },
        {
            "name": "Operador de Caixa",
            "description": "Acesso à frente de caixa (PDV), emissão de vendas e descontos autorizados",
            "codes": [
                "vendas.visualizar", "vendas.criar", "vendas.desconto", "vendas.cancelar"
            ],
        },
        {
            "name": "Financeiro",
            "description": "Gestão de contas a pagar/receber, baixas financeiras, caixa e relatórios",
            "codes": [
                "financeiro.visualizar", "financeiro.baixar", "relatorios.visualizar", "clientes.gerenciar"
            ],
        },
        {
            "name": "Estoquista",
            "description": "Gestão de catálogo de produtos, ajustes de estoque e entradas de compras/XML",
            "codes": [
                "estoque.visualizar", "estoque.ajuste", "estoque.movimento",
                "produtos.visualizar", "produtos.editar", "compras.gerenciar"
            ],
        },
    ]

    created_roles = {}
    for r_def in roles_definitions:
        role = db.scalar(
            select(Role).where(Role.tenant_id == tenant_id, Role.name == r_def["name"])
        )
        role_perms = [perms_by_code[c] for c in r_def["codes"] if c in perms_by_code]
        if not role:
            role = Role(
                tenant_id=tenant_id,
                name=r_def["name"],
                description=r_def["description"],
                is_system=True,
                permissions=role_perms,
            )
            db.add(role)
            db.flush()
        else:
            role.permissions = role_perms
        created_roles[role.name] = role

    return created_roles


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

    # 2. Seed Default Units
    units_map = {}
    for u_data in DEFAULT_UNITS:
        unit = db.scalar(select(ProductUnit).where(ProductUnit.code == u_data["code"]))
        if not unit:
            unit = ProductUnit(**u_data)
            db.add(unit)
            db.flush()
            logger.info(f"Unidade de medida criada: {unit.code}")
        units_map[unit.code] = unit

    # 3. Seed Default Tenant
    tenant = db.scalar(select(Tenant).where(Tenant.name == "Empresa Matriz Padrão"))
    if not tenant:
        tenant = Tenant(
            name="Empresa Matriz Padrão",
            document="00000000000100",
            is_active=True
        )
        db.add(tenant)
        db.flush()
        logger.info(f"Tenant inicial criado: {tenant.name}")

    # 4. Seed Default Company
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

    # 5. Seed Default Tenant System Roles
    roles_map = seed_tenant_default_roles(db, tenant.id)
    admin_role = roles_map["Administrador"]

    # 7. Seed Super Admin User
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

    # 8. Seed Sample Products
    sample_products = [
        {
            "name": "Coca-Cola 2L PET",
            "code": "BEB-001",
            "price": 10.50,
            "cost": 6.80,
            "stock_qty": 50.0,
            "min_stock_qty": 10.0,
            "category_name": "Bebidas",
            "unit_code": "UN",
            "barcode": "7894900011517"
        },
        {
            "name": "Arroz Tipo 1 5kg",
            "code": "ALI-001",
            "price": 28.90,
            "cost": 21.50,
            "stock_qty": 30.0,
            "min_stock_qty": 5.0,
            "category_name": "Alimentos",
            "unit_code": "UN",
            "barcode": "7896000000012"
        },
        {
            "name": "Feijão Carioca 1kg",
            "code": "ALI-002",
            "price": 7.90,
            "cost": 5.20,
            "stock_qty": 40.0,
            "min_stock_qty": 10.0,
            "category_name": "Alimentos",
            "unit_code": "UN",
            "barcode": "7896000000029"
        },
        {
            "name": "Água Mineral Sem Gás 500ml",
            "code": "BEB-002",
            "price": 2.50,
            "cost": 1.10,
            "stock_qty": 100.0,
            "min_stock_qty": 20.0,
            "category_name": "Bebidas",
            "unit_code": "UN",
            "barcode": "7891000000035"
        }
    ]

    for p_data in sample_products:
        prod = db.scalar(
            select(Product).where(
                Product.tenant_id == tenant.id,
                Product.name == p_data["name"]
            )
        )
        if not prod:
            cat = categories_map.get(p_data["category_name"])
            unit = units_map.get(p_data["unit_code"])
            prod = Product(
                tenant_id=tenant.id,
                company_id=company.id,
                category_id=cat.id if cat else None,
                unit_id=unit.id if unit else None,
                code=p_data["code"],
                name=p_data["name"],
                price=p_data["price"],
                cost=p_data["cost"],
                stock_qty=p_data["stock_qty"],
                min_stock_qty=p_data["min_stock_qty"],
                is_active=True
            )
            prod.barcodes.append(ProductBarcode(barcode=p_data["barcode"]))
            db.add(prod)
            logger.info(f"Produto demonstrativo criado: {prod.name} ({p_data['barcode']})")

    db.commit()
    logger.info("Seed de banco de dados concluído com sucesso!")


if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
    db.close()
