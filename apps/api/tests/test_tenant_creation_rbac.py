import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.user import User
from app.models.tenant import Tenant
from app.models.rbac import Role, Permission
from app.schemas.superadmin import TenantCreateInput
from app.api.v1.endpoints.superadmin import create_tenant
from app.api.deps import get_user_permissions


def test_create_tenant_assigns_admin_role_and_permissions():
    db: Session = SessionLocal()
    try:
        # Fetch or create a system tenant for superuser
        sys_tenant = db.scalar(select(Tenant).limit(1))
        if not sys_tenant:
            sys_tenant = Tenant(id=uuid4(), name="System Tenant Test", document="00000000000000", is_active=True)
            db.add(sys_tenant)
            db.commit()

        superuser = db.scalar(select(User).where(User.is_superuser == True))
        if not superuser:
            superuser = User(
                id=uuid4(),
                tenant_id=sys_tenant.id,
                name="SuperAdmin Test",
                email=f"test_super_{uuid4().hex[:6]}@telesys.com.br",
                password_hash="pwd",
                is_active=True,
                is_superuser=True
            )
            db.add(superuser)
            db.commit()

        input_data = TenantCreateInput(
            name="Tenant Teste RBAC",
            document="12345678000199",
            company_name="Empresa Teste RBAC LTDA",
            trade_name="Teste RBAC",
            cnpj="12.345.678/0001-99",
            admin_name="Admin Tenant",
            admin_email=f"admin_{uuid4().hex[:6]}@tenantrbac.com",
            admin_password="password123",
            plan_name="PRO",
            max_devices=5
        )

        tenant_summary = create_tenant(data=input_data, db=db, current_user=superuser)
        assert tenant_summary.id is not None

        # Verify created admin user
        user_db = db.scalar(select(User).where(User.email == input_data.admin_email))
        assert user_db is not None
        assert len(user_db.roles) > 0

        admin_role = user_db.roles[0]
        assert admin_role.name == "Administrador"

        # Verify permissions returned via deps
        perms = get_user_permissions(db, user_db)
        assert "usuarios.gerenciar" in perms
        assert "vendas.visualizar" in perms
        assert "sistema.configurar" in perms

    finally:
        db.close()
