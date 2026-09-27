from datetime import datetime
from uuid import UUID
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict


class SyncEventPush(BaseModel):
    event_id: UUID
    tenant_id: UUID
    company_id: UUID
    entity_type: str  # sale, customer, stock_movement, cash_movement, product
    action: str  # CREATE, UPDATE, DELETE
    payload: Dict[str, Any]
    created_at: Optional[datetime] = None


class SyncPushBatchRequest(BaseModel):
    events: List[SyncEventPush]


class SyncEventResult(BaseModel):
    event_id: UUID
    status: str  # SYNCED, FAILED, ALREADY_PROCESSED
    message: Optional[str] = None


class SyncPushBatchResponse(BaseModel):
    results: List[SyncEventResult]
