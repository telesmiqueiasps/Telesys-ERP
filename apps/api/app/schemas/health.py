from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    project: str = Field(..., example="Telesys ERP API")
    version: str = Field(..., example="0.1.0")
    database: str = Field(..., example="connected")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
