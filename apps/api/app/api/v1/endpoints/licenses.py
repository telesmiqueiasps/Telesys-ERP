import uuid
from typing import List, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func

from app.api import deps
from app.models.user import User
from app.models.license import License, LicenseStatus, Device, DeviceStatus
from app.schemas.license import (
    LicenseActivateInput,
    LicenseHeartbeatInput,
    LicenseResponse,
    DeviceResponse,
)

router = APIRouter()


def _get_or_create_tenant_license(db: Session, tenant_id: uuid.UUID) -> License:
    stmt = (
        select(License)
        .options(selectinload(License.devices))
        .where(License.tenant_id == tenant_id)
    )
    lic = db.scalar(stmt)
    if not lic:
        # Criar licença padrão para o tenant se ainda não possuir
        key_suffix = str(tenant_id).replace("-", "")[:8].upper()
        lic = License(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            license_key=f"TELESYS-PRO-{key_suffix}",
            plan_name="PRO",
            status=LicenseStatus.ACTIVE.value,
            max_devices=5,
            offline_grace_days=14,
        )
        db.add(lic)
        db.commit()
        db.refresh(lic)
    return lic


def _build_license_response(lic: License) -> LicenseResponse:
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


@router.get("/current", response_model=LicenseResponse, summary="Obter Licença Atual do Tenant")
def get_current_license(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna a licença ativa e os dispositivos vinculados ao tenant.
    """
    lic = _get_or_create_tenant_license(db, current_user.tenant_id)
    return _build_license_response(lic)


@router.post("/activate", response_model=LicenseResponse, summary="Ativar Licença ou Registrar Dispositivo")
def activate_license(
    data: LicenseActivateInput,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Valida e ativa uma chave de licença para o tenant e vincula o dispositivo desktop atual.
    """
    # Buscar licença por chave
    stmt = (
        select(License)
        .options(selectinload(License.devices))
        .where(License.license_key == data.license_key)
    )
    lic = db.scalar(stmt)

    if not lic:
        # Se for uma nova chave inserida manualmente, atualizar a licença existente do tenant
        lic = _get_or_create_tenant_license(db, current_user.tenant_id)
        lic.license_key = data.license_key
        lic.status = LicenseStatus.ACTIVE.value
    else:
        if lic.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta chave de licença pertence a outra conta."
            )

    if lic.status != LicenseStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Licença não está ativa. Status atual: {lic.status}"
        )

    # Verificar se dispositivo já está cadastrado
    stmt_device = select(Device).where(
        Device.license_id == lic.id,
        Device.device_id == data.device_id,
    )
    existing_device = db.scalar(stmt_device)

    now = datetime.now(timezone.utc)
    if existing_device:
        existing_device.device_name = data.device_name
        existing_device.os_info = data.os_info
        existing_device.app_version = data.app_version
        existing_device.status = DeviceStatus.AUTHORIZED.value
        existing_device.last_heartbeat_at = now
    else:
        # Checar limite de dispositivos ativos
        active_devices = [d for d in lic.devices if d.status == DeviceStatus.AUTHORIZED.value]
        if len(active_devices) >= lic.max_devices:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limite de {lic.max_devices} dispositivos ativos atingido para esta licença."
            )

        new_device = Device(
            id=uuid.uuid4(),
            tenant_id=lic.tenant_id,
            license_id=lic.id,
            device_id=data.device_id,
            device_name=data.device_name,
            os_info=data.os_info,
            app_version=data.app_version,
            status=DeviceStatus.AUTHORIZED.value,
            last_heartbeat_at=now,
        )
        db.add(new_device)

    db.commit()
    db.refresh(lic)
    return _build_license_response(lic)


@router.post("/heartbeat", summary="Enviar Heartbeat do Dispositivo")
def device_heartbeat(
    data: LicenseHeartbeatInput,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Atualiza o timestamp de heartbeat do dispositivo desktop.
    """
    stmt = select(Device).where(
        Device.tenant_id == current_user.tenant_id,
        Device.device_id == data.device_id,
    )
    dev = db.scalar(stmt)
    if not dev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não registrado."
        )

    if dev.status == DeviceStatus.REVOKED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este dispositivo foi revogado."
        )

    dev.last_heartbeat_at = datetime.now(timezone.utc)
    db.commit()

    return {"status": dev.status, "last_heartbeat_at": dev.last_heartbeat_at}


@router.get("/devices", response_model=List[DeviceResponse], summary="Listar Dispositivos Registrados")
def list_devices(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna todos os terminais/dispositivos cadastrados no tenant.
    """
    stmt = select(Device).where(Device.tenant_id == current_user.tenant_id).order_by(Device.created_at.desc())
    devices = db.scalars(stmt).all()
    return [
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
        for d in devices
    ]


@router.post("/devices/{device_id}/revoke", response_model=DeviceResponse, summary="Revogar Acesso do Dispositivo")
def revoke_device(
    device_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Revoga o acesso de um terminal desktop específico.
    """
    stmt = select(Device).where(
        Device.id == device_id,
        Device.tenant_id == current_user.tenant_id,
    )
    dev = db.scalar(stmt)
    if not dev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado."
        )

    dev.status = DeviceStatus.REVOKED.value
    db.commit()
    db.refresh(dev)

    return DeviceResponse(
        id=dev.id,
        tenant_id=dev.tenant_id,
        license_id=dev.license_id,
        device_id=dev.device_id,
        device_name=dev.device_name,
        os_info=dev.os_info,
        app_version=dev.app_version,
        status=dev.status,
        last_heartbeat_at=dev.last_heartbeat_at,
        created_at=dev.created_at,
    )
