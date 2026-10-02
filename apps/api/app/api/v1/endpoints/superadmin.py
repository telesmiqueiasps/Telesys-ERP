import uuid
from typing import List, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func

from app.api import deps
from app.core.security import get_password_hash
from app.models.user import User
from app.models.tenant import Tenant
from app.models.company import Company
from app.models.license import License, LicenseStatus, Device, DeviceStatus
from app.models.rbac import Role, Permission
from app.schemas.license import LicenseResponse, DeviceResponse
from app.schemas.superadmin import (
    TenantAdminSummary,
    TenantCreateInput,
    TenantStatusUpdate,
    LicenseUpdateInput,
    SuperAdminMetrics,
)

router = APIRouter()


def _verify_superuser(user: User):
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso exclusivo para administradores da plataforma (SuperAdmin)."
        )


def _build_license_response(lic: License | None) -> LicenseResponse | None:
    if not lic:
        return None

    devices_list = lic.devices if lic.devices else []
    active_count = sum(1 for d in devices_list if d.status == DeviceStatus.AUTHORIZED.value)

    device_responses = [
        DeviceResponse(
            id=d.id,
            tenant_id=d.tenant_id,
            license_id=d.license_id,
            device_id=d.device_id,
            device_name=d.device_name,
            os_info=d.os_info,
            app_version=d.app_version,
            status=d.status,
            last_heartbeat_at=d.last_heartbeat_at,
            created_at=d.created_at,
        )
        for d in devices_list
    ]

    return LicenseResponse(
        id=lic.id,
        tenant_id=lic.tenant_id,
        license_key=lic.license_key,
        plan_name=lic.plan_name,
        status=lic.status,
        max_devices=lic.max_devices,
        expires_at=lic.expires_at,
        offline_grace_days=lic.offline_grace_days,
        active_devices_count=active_count,
        devices=device_responses,
        created_at=lic.created_at,
    )


@router.get("/metrics", response_model=SuperAdminMetrics, summary="Métricas Globais da Plataforma")
def get_platform_metrics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    _verify_superuser(current_user)

    tenants = db.scalars(select(Tenant)).all()
    devices = db.scalars(select(Device)).all()
    licenses = db.scalars(select(License)).all()

    total_tenants = len(tenants)
    active_tenants = sum(1 for t in tenants if t.is_active)
    blocked_tenants = total_tenants - active_tenants

    total_devices = len(devices)
    active_devices = sum(1 for d in devices if d.status == DeviceStatus.AUTHORIZED.value)

    # Estimativa simples de MRR (MEI=99, PRO=199, ENTERPRISE=499)
    mrr_map = {"MEI": 99.0, "PRO": 199.0, "ENTERPRISE": 499.0}
    estimated_mrr = sum(
        mrr_map.get(lic.plan_name.upper(), 199.0)
        for lic in licenses
        if lic.status == LicenseStatus.ACTIVE.value
    )

    return SuperAdminMetrics(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        blocked_tenants=blocked_tenants,
        total_devices=total_devices,
        active_devices=active_devices,
        estimated_mrr=estimated_mrr,
    )


@router.get("/tenants", response_model=List[TenantAdminSummary], summary="Listar Todos os Tenants (Clientes)")
def list_tenants(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    _verify_superuser(current_user)

    stmt = select(Tenant).order_by(Tenant.created_at.desc())
    tenants = db.scalars(stmt).all()

    result = []
    for t in tenants:
        comp_count = db.scalar(select(func.count(Company.id)).where(Company.tenant_id == t.id)) or 0
        usr_count = db.scalar(select(func.count(User.id)).where(User.tenant_id == t.id)) or 0
        dev_count = db.scalar(select(func.count(Device.id)).where(Device.tenant_id == t.id)) or 0

        lic_stmt = (
            select(License)
            .options(selectinload(License.devices))
            .where(License.tenant_id == t.id)
        )
        lic = db.scalar(lic_stmt)

        result.append(
            TenantAdminSummary(
                id=t.id,
                name=t.name,
                document=t.document,
                is_active=t.is_active,
                created_at=t.created_at,
                companies_count=comp_count,
                users_count=usr_count,
                devices_count=dev_count,
                license=_build_license_response(lic),
            )
        )

    return result


@router.post("/tenants", response_model=TenantAdminSummary, summary="Cadastrar Novo Cliente Tenant")
def create_tenant(
    data: TenantCreateInput,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    _verify_superuser(current_user)

    # Verificar e-mail duplicado
    existing_user = db.scalar(select(User).where(User.email == data.admin_email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário cadastrado com este e-mail."
        )

    tenant_id = uuid.uuid4()
    company_id = uuid.uuid4()
    user_id = uuid.uuid4()
    license_id = uuid.uuid4()

    # 1. Tenant
    new_tenant = Tenant(
        id=tenant_id,
        name=data.name,
        document=data.document,
        is_active=True,
    )
    db.add(new_tenant)

    # 2. Company
    new_company = Company(
        id=company_id,
        tenant_id=tenant_id,
        name=data.company_name,
        trade_name=data.trade_name,
        cnpj=data.cnpj,
        is_active=True,
    )
    db.add(new_company)

    # 3. Master User
    hashed_pwd = get_password_hash(data.admin_password)
    new_user = User(
        id=user_id,
        tenant_id=tenant_id,
        name=data.admin_name,
        email=data.admin_email,
        password_hash=hashed_pwd,
        is_active=True,
        is_superuser=False,
    )
    db.add(new_user)

    # 3.1 Role & Permissions (Seed 6 default system roles: Administrador, Gestor, Supervisor, Operador de Caixa, Financeiro, Estoquista)
    from app.initial_data import seed_tenant_default_roles
    roles_map = seed_tenant_default_roles(db, tenant_id)
    new_user.roles.append(roles_map["Administrador"])

    # 4. License
    key_suffix = str(tenant_id).replace("-", "")[:8].upper()
    new_license = License(
        id=license_id,
        tenant_id=tenant_id,
        license_key=f"TELESYS-{data.plan_name.upper()}-{key_suffix}",
        plan_name=data.plan_name.upper(),
        status=LicenseStatus.ACTIVE.value,
        max_devices=data.max_devices,
        offline_grace_days=14,
    )
    db.add(new_license)

    db.commit()
    db.refresh(new_tenant)

    return TenantAdminSummary(
        id=new_tenant.id,
        name=new_tenant.name,
        document=new_tenant.document,
        is_active=new_tenant.is_active,
        created_at=new_tenant.created_at,
        companies_count=1,
        users_count=1,
        devices_count=0,
        license=_build_license_response(new_license),
    )


@router.put("/tenants/{tenant_id}/status", response_model=TenantAdminSummary, summary="Alterar Status do Tenant (Bloqueio/Desbloqueio)")
def update_tenant_status(
    tenant_id: uuid.UUID,
    data: TenantStatusUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    _verify_superuser(current_user)

    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant não encontrado."
        )

    tenant.is_active = data.is_active

    # Atualizar status da licença vinculada
    lic_stmt = (
        select(License)
        .options(selectinload(License.devices))
        .where(License.tenant_id == tenant_id)
    )
    lic = db.scalar(lic_stmt)
    if lic:
        lic.status = LicenseStatus.ACTIVE.value if data.is_active else LicenseStatus.BLOCKED.value

    db.commit()
    db.refresh(tenant)

    comp_count = db.scalar(select(func.count(Company.id)).where(Company.tenant_id == tenant.id)) or 0
    usr_count = db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant.id)) or 0
    dev_count = db.scalar(select(func.count(Device.id)).where(Device.tenant_id == tenant.id)) or 0

    return TenantAdminSummary(
        id=tenant.id,
        name=tenant.name,
        document=tenant.document,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        companies_count=comp_count,
        users_count=usr_count,
        devices_count=dev_count,
        license=_build_license_response(lic),
    )


@router.put("/licenses/{license_id}", response_model=LicenseResponse, summary="Atualizar Licença e Plano do Cliente")
def update_license(
    license_id: uuid.UUID,
    data: LicenseUpdateInput,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    _verify_superuser(current_user)

    lic_stmt = (
        select(License)
        .options(selectinload(License.devices))
        .where(License.id == license_id)
    )
    lic = db.scalar(lic_stmt)
    if not lic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licença não encontrada."
        )

    if data.plan_name:
        lic.plan_name = data.plan_name.upper()
    if data.status:
        lic.status = data.status
    if data.max_devices is not None:
        lic.max_devices = data.max_devices
    if data.offline_grace_days is not None:
        lic.offline_grace_days = data.offline_grace_days
    if data.expires_at is not None:
        lic.expires_at = data.expires_at

    db.commit()
    db.refresh(lic)
    return _build_license_response(lic)
