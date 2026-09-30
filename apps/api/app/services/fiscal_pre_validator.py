import re
from typing import List, Optional
from app.models.nfe_document import NfeDocument, NfeItem
from app.schemas.rejections import PreValidationResult, ValidationErrorItem
from app.services.sefaz_rejections_catalog import SefazRejectionsCatalog


def validate_cnpj(cnpj: str) -> bool:
    """Valida formato e dígito verificador de CNPJ (14 dígitos)."""
    cnpj_clean = re.sub(r"\D", "", cnpj or "")
    if len(cnpj_clean) != 14:
        return False
    if len(set(cnpj_clean)) == 1:
        return False

    # Primeiro dígito verificador
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total1 = sum(int(digit) * weight for digit, weight in zip(cnpj_clean[:12], weights1))
    rem1 = total1 % 11
    dv1 = 0 if rem1 < 2 else 11 - rem1
    if int(cnpj_clean[12]) != dv1:
        return False

    # Segundo dígito verificador
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total2 = sum(int(digit) * weight for digit, weight in zip(cnpj_clean[:13], weights2))
    rem2 = total2 % 11
    dv2 = 0 if rem2 < 2 else 11 - rem2
    return int(cnpj_clean[13]) == dv2


def validate_cpf(cpf: str) -> bool:
    """Valida formato e dígito verificador de CPF (11 dígitos)."""
    cpf_clean = re.sub(r"\D", "", cpf or "")
    if len(cpf_clean) != 11:
        return False
    if len(set(cpf_clean)) == 1:
        return False

    # Primeiro dígito
    total1 = sum(int(digit) * weight for digit, weight in zip(cpf_clean[:9], range(10, 1, -1)))
    rem1 = (total1 * 10) % 11
    dv1 = 0 if rem1 == 10 or rem1 == 11 else rem1
    if int(cpf_clean[9]) != dv1:
        return False

    # Segundo dígito
    total2 = sum(int(digit) * weight for digit, weight in zip(cpf_clean[:10], range(11, 1, -1)))
    rem2 = (total2 * 10) % 11
    dv2 = 0 if rem2 == 10 or rem2 == 11 else rem2
    return int(cpf_clean[10]) == dv2


def validate_access_key_dv(key: str) -> bool:
    """Valida se a chave de acesso de 44 dígitos possui o dígito verificador correto (módulo 11)."""
    key_clean = re.sub(r"\D", "", key or "")
    if len(key_clean) != 44:
        return False

    first_43 = key_clean[:43]
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = sum(int(digit) * weights[i % 8] for i, digit in enumerate(reversed(first_43)))
    remainder = total % 11

    expected_cdv = 0 if remainder in (0, 1) else 11 - remainder
    return int(key_clean[43]) == expected_cdv


class FiscalPreValidator:
    """Pré-validador Fiscal para NF-e Modelo 55 antes da transmissão à SEFAZ."""

    @classmethod
    def validate(
        cls,
        nfe: NfeDocument,
        emit_cnpj: str,
        emit_crt: int = 1,
        emit_ie: Optional[str] = None,
    ) -> PreValidationResult:
        errors: List[ValidationErrorItem] = []
        warnings: List[ValidationErrorItem] = []

        # 1. Validação do CNPJ Emitente (Rejeição 208)
        if not validate_cnpj(emit_cnpj):
            catalog_208 = SefazRejectionsCatalog.get_rejection(208)
            errors.append(
                ValidationErrorItem(
                    field="emit.CNPJ",
                    code="208",
                    message="CNPJ do emitente é inválido (formato ou dígito verificador).",
                    official_solution=catalog_208.operational_solution if catalog_208 else None,
                )
            )

        # 2. Validação da IE Emitente (Rejeição 230)
        if not emit_ie or emit_ie.strip().upper() == "ISENTO":
            # Para modelo 55 o emitente deve ter IE cadastrada
            catalog_230 = SefazRejectionsCatalog.get_rejection(230)
            errors.append(
                ValidationErrorItem(
                    field="emit.IE",
                    code="230",
                    message="IE do emitente não informada ou inválida para NF-e modelo 55.",
                    official_solution=catalog_230.operational_solution if catalog_230 else None,
                )
            )

        # 3. Validação do Destinatário (CNPJ/CPF e IE)
        dest_doc = getattr(nfe, "recipient_cnpj_cpf", None) or getattr(nfe, "recipient_document", None) or ""
        dest_doc_clean = re.sub(r"\D", "", str(dest_doc))
        if dest_doc_clean:
            if len(dest_doc_clean) == 14 and not validate_cnpj(dest_doc_clean):
                errors.append(
                    ValidationErrorItem(
                        field="dest.CNPJ",
                        code="INVALID_DEST_CNPJ",
                        message="CNPJ do destinatário possui dígito verificador inválido.",
                        official_solution="Corrija o CNPJ do destinatário no cadastro do cliente.",
                    )
                )
            elif len(dest_doc_clean) == 11 and not validate_cpf(dest_doc_clean):
                errors.append(
                    ValidationErrorItem(
                        field="dest.CPF",
                        code="INVALID_DEST_CPF",
                        message="CPF do destinatário possui dígito verificador inválido.",
                        official_solution="Corrija o CPF do destinatário no cadastro do cliente.",
                    )
                )

        # Rejeição 232: IE Destinatário
        ind_ie_dest = str(getattr(nfe, "recipient_ind_ie", None) or ("1" if getattr(nfe, "recipient_is_tax_contributor", False) else "9"))
        dest_ie = getattr(nfe, "recipient_ie", "") or ""
        if ind_ie_dest == "1" and (not dest_ie or dest_ie.strip().upper() == "ISENTO"):
            catalog_232 = SefazRejectionsCatalog.get_rejection(232)
            errors.append(
                ValidationErrorItem(
                    field="dest.IE",
                    code="232",
                    message="Destinatário indicado como Contribuinte (indIEDest=1), mas a IE não foi informada.",
                    official_solution=catalog_232.operational_solution if catalog_232 else None,
                )
            )

        # 4. Validação da Chave de Acesso (Módulo 11)
        if nfe.access_key:
            if not validate_access_key_dv(nfe.access_key):
                errors.append(
                    ValidationErrorItem(
                        field="chNFe",
                        code="INVALID_ACCESS_KEY_DV",
                        message="Dígito verificador da Chave de Acesso da NF-e está incorreto.",
                        official_solution="Regere a chave de acesso utilizando o algoritmo Módulo 11 oficial.",
                    )
                )

        # 5. Validação dos Itens (NCM, CEST, CRT vs CST/CSOSN)
        items: List[NfeItem] = list(nfe.items) if nfe.items else []
        if not items:
            errors.append(
                ValidationErrorItem(
                    field="det",
                    code="EMPTY_ITEMS",
                    message="A NF-e deve possuir pelo menos um item cadastrado.",
                    official_solution="Adicione itens de produtos ou serviços à nota fiscal antes da transmissão.",
                )
            )

        calc_sum_vprod = 0.0

        for idx, item in enumerate(items, start=1):
            ncm_clean = re.sub(r"\D", "", item.ncm or "")
            if len(ncm_clean) != 8:
                errors.append(
                    ValidationErrorItem(
                        field=f"det[{idx}].prod.NCM",
                        code="INVALID_NCM",
                        message=f"Item {idx}: NCM '{item.ncm}' deve possuir exatamente 8 dígitos numéricos.",
                        official_solution="Ajuste o NCM do produto no cadastro para um código válido de 8 dígitos de acordo com a Tabela NCM.",
                    )
                )

            if item.cest:
                cest_clean = re.sub(r"\D", "", item.cest or "")
                if len(cest_clean) != 7:
                    errors.append(
                        ValidationErrorItem(
                            field=f"det[{idx}].prod.CEST",
                            code="INVALID_CEST",
                            message=f"Item {idx}: CEST '{item.cest}' deve possuir exatamente 7 dígitos numéricos.",
                            official_solution="Corrija o CEST do produto para um formato válido de 7 dígitos.",
                        )
                    )

            # Regras de CRT vs CST/CSOSN
            tax_snap = getattr(item, "tax_snapshot_json", None) or getattr(item, "tax_snapshot", None) or {}
            icms_info = tax_snap.get("icms", {})
            csosn = icms_info.get("csosn")
            cst = icms_info.get("cst")

            if emit_crt == 1:
                # Simples Nacional exige CSOSN
                if not csosn and not cst:
                    errors.append(
                        ValidationErrorItem(
                            field=f"det[{idx}].imposto.ICMS",
                            code="MISSING_CSOSN",
                            message=f"Item {idx}: Empresa no Simples Nacional exige preenchimento de CSOSN no ICMS.",
                            official_solution="Defina o CSOSN apropriado (ex: 101, 102, 500) para o item.",
                        )
                    )
            else:
                # Regime Normal exige CST de 2 dígitos
                if not cst:
                    errors.append(
                        ValidationErrorItem(
                            field=f"det[{idx}].imposto.ICMS",
                            code="MISSING_CST",
                            message=f"Item {idx}: Empresa no Regime Normal exige preenchimento do CST de ICMS de 2 dígitos.",
                            official_solution="Defina o CST apropriado (ex: 00, 10, 20, 60, 90) para o item.",
                        )
                    )

            item_vprod = float(getattr(item, "vProd", None) or getattr(item, "total_amount", 0.0) or 0.0)
            calc_sum_vprod += item_vprod

        # 6. Validação do Total da NF (Rejeição 610)
        doc_total = float(getattr(nfe, "vNF", None) or getattr(nfe, "total_amount", 0.0) or 0.0)
        # Permite pequena diferença por causa de arredondamento de impostos (0.05)
        if abs(doc_total - calc_sum_vprod) > 0.05 and len(items) > 0:
            catalog_610 = SefazRejectionsCatalog.get_rejection(610)
            warnings.append(
                ValidationErrorItem(
                    field="total.ICMSTot.vNF",
                    code="610",
                    message=f"Valor total da NF (R$ {doc_total:.2f}) difere da soma dos itens (R$ {calc_sum_vprod:.2f}).",
                    official_solution=catalog_610.operational_solution if catalog_610 else None,
                )
            )

        return PreValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
