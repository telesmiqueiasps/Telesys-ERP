import uuid
import pytest
from app.services.sefaz_rejections_catalog import SefazRejectionsCatalog
from app.services.fiscal_pre_validator import (
    FiscalPreValidator,
    validate_cnpj,
    validate_cpf,
    validate_access_key_dv,
)
from app.models.nfe_document import NfeDocument, NfeItem


def test_sefaz_rejections_catalog():
    catalog = SefazRejectionsCatalog.list_catalog()
    assert len(catalog) >= 12

    # Test exact code lookup
    entry_208 = SefazRejectionsCatalog.get_rejection(208)
    assert entry_208 is not None
    assert "CNPJ do emitente inválido" in entry_208.official_message
    assert "emit.CNPJ" in entry_208.affected_fields
    assert entry_208.operational_solution is not None

    entry_610 = SefazRejectionsCatalog.get_rejection(610)
    assert entry_610 is not None
    assert "Total da NF difere" in entry_610.official_message

    # Test non-existent code
    assert SefazRejectionsCatalog.get_rejection(9999) is None


def test_cnpj_cpf_validation_helpers():
    # Valid CNPJs
    assert validate_cnpj("11.222.333/0001-81") is True
    assert validate_cnpj("11222333000181") is True

    # Invalid CNPJs
    assert validate_cnpj("11222333000180") is False  # Wrong DV
    assert validate_cnpj("00000000000000") is False  # All zeros
    assert validate_cnpj("12345") is False           # Short length

    # Valid CPFs
    assert validate_cpf("52998224725") is True

    # Invalid CPFs
    assert validate_cpf("11111111111") is False
    assert validate_cpf("12345678900") is False


def test_access_key_dv_validation_helper():
    key_43 = "3526091122233300018155001000000100112345678"
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = sum(int(digit) * weights[i % 8] for i, digit in enumerate(reversed(key_43)))
    rem = total % 11
    cdv = 0 if rem in (0, 1) else 11 - rem
    full_key = f"{key_43}{cdv}"

    assert validate_access_key_dv(full_key) is True
    assert validate_access_key_dv(f"{key_43}{(cdv + 1) % 10}") is False


def test_fiscal_pre_validator_valid_nfe():
    key_43 = "3526091122233300018155001000000100112345678"
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = sum(int(digit) * weights[i % 8] for i, digit in enumerate(reversed(key_43)))
    rem = total % 11
    cdv = 0 if rem in (0, 1) else 11 - rem
    valid_key = f"{key_43}{cdv}"

    nfe = NfeDocument(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        number=100,
        series=1,
        nature_of_operation="VENDA",
        issuer_cnpj="11222333000181",
        issuer_name="Empresa Teste LTDA",
        issuer_uf="SP",
        access_key=valid_key,
        recipient_cnpj_cpf="11222333000181",
        recipient_name="Cliente Teste",
        recipient_uf="SP",
        recipient_is_tax_contributor=False,
        vNF=150.00,
        items=[
            NfeItem(
                item_number=1,
                product_code="PROD01",
                description="Roteador Wi-Fi 6",
                cfop="5102",
                ncm="85176277",
                cest="2100100",
                qCom=1.0,
                vUnCom=150.00,
                vProd=150.00,
                vUnTrib=150.00,
                tax_snapshot_json={"icms": {"csosn": "102"}},
            )
        ],
    )

    result = FiscalPreValidator.validate(
        nfe=nfe,
        emit_cnpj="11222333000181",
        emit_crt=1,
        emit_ie="123456789",
    )

    assert result.is_valid is True
    assert len(result.errors) == 0


def test_fiscal_pre_validator_invalid_cases():
    nfe = NfeDocument(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        number=101,
        series=1,
        nature_of_operation="VENDA",
        issuer_cnpj="11222333000181",
        issuer_name="Empresa Teste LTDA",
        issuer_uf="SP",
        access_key="35260911222333000181550010000001001123456781",
        recipient_cnpj_cpf="11222333000181",
        recipient_name="Cliente Teste",
        recipient_uf="SP",
        recipient_is_tax_contributor=True,  # Contribuinte ICMS exige IE
        recipient_ie="",                    # Erro Rejeição 232!
        vNF=100.00,
        items=[
            NfeItem(
                item_number=1,
                product_code="PROD02",
                description="Cabo de Rede",
                cfop="5102",
                ncm="8544",                 # Erro: NCM deve ter 8 dígitos!
                cest="",
                qCom=1.0,
                vUnCom=100.00,
                vProd=100.00,
                vUnTrib=100.00,
                tax_snapshot_json={"icms": {}},  # Sem CSOSN nem CST
            )
        ],
    )

    result = FiscalPreValidator.validate(
        nfe=nfe,
        emit_cnpj="12345",  # Erro Rejeição 208!
        emit_crt=1,
        emit_ie="",        # Erro Rejeição 230!
    )

    assert result.is_valid is False
    codes = [e.code for e in result.errors]
    assert "208" in codes             # CNPJ emitente inválido
    assert "230" in codes             # IE emitente ausente
    assert "232" in codes             # IE dest ausente para indIEDest=1
    assert "INVALID_NCM" in codes     # NCM < 8 dígitos
    assert "MISSING_CSOSN" in codes   # Faltando CSOSN para CRT=1
