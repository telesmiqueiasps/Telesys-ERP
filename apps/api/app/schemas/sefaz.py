import enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class SefazErrorCategory(str, enum.Enum):
    NONE = "NONE"
    TIMEOUT = "TIMEOUT"
    HTTP_ERROR = "HTTP_ERROR"
    SEFAZ_REJECTION = "SEFAZ_REJECTION"
    SEFAZ_OFFLINE = "SEFAZ_OFFLINE"
    CERTIFICATE_ERROR = "CERTIFICATE_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"


class SefazRequest(BaseModel):
    xml_content: str = Field("", description="Conteúdo XML assinado ou rascunho da NF-e / NFC-e")
    payload_xml: Optional[str] = Field(None, description="Alias para xml_content")
    service_name: str = Field("NFeAutorizacao", description="Nome do serviço SEFAZ (NFeAutorizacao, NFeConsultaProtocolo)")
    uf: str = Field(..., min_length=2, max_length=2, example="SP")
    environment: int = Field(2, description="1=Produção, 2=Homologação")
    doc_model: str = Field("55", description="55=NF-e, 65=NFC-e")
    
    # Certificado A1 em bytes e senha para transmissão SSL/TLS MTLS
    certificate_pfx_bytes: Optional[bytes] = Field(None, description="Certificado A1 PKCS12 em bytes")
    certificate_password: Optional[str] = Field(None, description="Senha do certificado A1")
    
    timeout_seconds: float = Field(15.0, ge=1.0, le=60.0)
    max_retries: int = Field(3, ge=0, le=5)
    use_mock_in_homologation: bool = Field(True, description="Usar simulador SEFAZ v4.00 quando em homologação ou falha de rede")


class SefazResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    success: bool
    status_code: int = Field(..., description="Código de status SEFAZ (cStat - ex: 100, 103, 104, 108, 204)")
    reason: str = Field(..., description="Descrição da resposta SEFAZ (xMotivo)")
    
    protocol_number: Optional[str] = Field(None, description="Número do protocolo de autorização (nProt)")
    access_key: Optional[str] = Field(None, description="Chave de acesso de 44 dígitos (chNFe)")
    digest_value: Optional[str] = Field(None, description="Valor do DigestValue retornado (digVal)")
    
    received_at: datetime = Field(default_factory=datetime.now)
    raw_response_xml: Optional[str] = Field(None, description="XML bruto da resposta SOAP retornado pela SEFAZ")
    
    error_category: SefazErrorCategory = SefazErrorCategory.NONE
    retry_count: int = Field(0, description="Número de tentativas de retry realizadas")
    environment: int = Field(2, description="Ambiente 1 ou 2")

    @property
    def cStat(self) -> int:
        return self.status_code

    @property
    def xMotivo(self) -> str:
        return self.reason

    @property
    def nProt(self) -> Optional[str]:
        return self.protocol_number

    @property
    def digVal(self) -> Optional[str]:
        return self.digest_value
