import uuid
from typing import TYPE_CHECKING, List
from datetime import datetime
from sqlalchemy import String, UUID, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class LicenseStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"
    REVOKED = "REVOKED"


class DeviceStatus(str, enum.Enum):
    AUTHORIZED = "AUTHORIZED"
    REVOKED = "REVOKED"


class License(Base, TimestampMixin):
    """
    Registro de Licença/Plano associado ao Tenant.
    """
    __tablename__ = "licenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    license_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )
    plan_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PRO"
    )  # 'MEI', 'PRO', 'ENTERPRISE'
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LicenseStatus.ACTIVE.value,
        index=True
    )
    max_devices: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    offline_grace_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    devices: Mapped[List["Device"]] = relationship(
        "Device",
        back_populates="license",
        cascade="all, delete-orphan"
    )


class Device(Base, TimestampMixin):
    """
    Registro do Dispositivo / Terminal Desktop instalado.
    """
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    license_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("licenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    device_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    os_info: Mapped[str | None] = mapped_column(String(100), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(50), nullable=True, default="1.0.0")
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DeviceStatus.AUTHORIZED.value
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    license: Mapped["License"] = relationship("License", back_populates="devices")
