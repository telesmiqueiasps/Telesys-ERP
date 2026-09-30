import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HomologationTestItem(BaseModel):
    module_code: str = Field(..., example="AUTORIZACAO")
    module_name: str = Field(..., example="Autorização de NF-e (Modelo 55)")
    test_name: str = Field(..., example="Emissão e Assinatura Digital de NF-e 55")
    passed: bool = True
    details: str = Field(..., example="NF-e autorizada com cStat 100 e protNFe gerado com sucesso.")
    duration_ms: float = 0.0


class HomologationSuiteReportResponse(BaseModel):
    company_id: uuid.UUID
    tenant_id: uuid.UUID
    executed_at: str
    total_modules: int = 12
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate_percent: float
    is_fully_homologated: bool
    results: List[HomologationTestItem] = Field(default_factory=list)
