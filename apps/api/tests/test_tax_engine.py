import unittest
from app.schemas.tax_engine import (
    TaxCalculationInput,
    ProductTaxProfileInput,
    RecipientInput,
    OperationResolvedInput,
    ItemFinancialContextInput,
)
from app.services.tax_engine import TaxEngine


class TestTaxEngine(unittest.TestCase):
    def test_simples_nacional_csosn_101(self):
        inp = TaxCalculationInput(
            company_crt=1,
            company_uf="SP",
            company_pCredSN=2.85,
            product=ProductTaxProfileInput(
                ncm="84713012",
                cst_csosn="101",
                origem="0",
            ),
            operation=OperationResolvedInput(
                operation_code="VENDA_ESTADO",
                operation_name="Venda no Estado",
                cfop="5102",
            ),
            recipient=RecipientInput(uf="SP", is_final_consumer=True, is_tax_contributor=False),
            context=ItemFinancialContextInput(
                vProd=100.0,
                qCom=1.0,
                vUnCom=100.0,
                vFrete=10.0,
                vDesc=5.0,
            ),
        )

        snap = TaxEngine.calculate_item_tax(inp)
        self.assertEqual(snap.vBC_Base, 105.0)  # 100 + 10 - 5
        self.assertEqual(snap.icms.cst_csosn, "101")
        self.assertEqual(snap.icms.vICMS, 0.0)  # Simples não gera ICMS próprio na NFe
        self.assertEqual(snap.icms.pCredSN, 2.85)
        self.assertEqual(snap.icms.vCredICMSSN, 2.99)  # 105.0 * 2.85% = 2.9925 -> 2.99
        self.assertEqual(snap.vItemTotal, 105.0)

    def test_regime_normal_cst_00_with_freight_and_discount(self):
        inp = TaxCalculationInput(
            company_crt=3,
            company_uf="SP",
            product=ProductTaxProfileInput(
                ncm="84713012",
                cst_csosn="00",
                origem="0",
                icms_aliquot=18.0,
                cst_pis="01",
                pis_aliquot=1.65,
                cst_cofins="01",
                cofins_aliquot=7.6,
            ),
            operation=OperationResolvedInput(
                operation_code="VENDA_ESTADO",
                operation_name="Venda no Estado",
                cfop="5102",
            ),
            recipient=RecipientInput(uf="SP", is_final_consumer=False, is_tax_contributor=True),
            context=ItemFinancialContextInput(
                vProd=200.0,
                qCom=2.0,
                vUnCom=100.0,
                vFrete=20.0,
                vDesc=10.0,
            ),
        )

        snap = TaxEngine.calculate_item_tax(inp)
        self.assertEqual(snap.vBC_Base, 210.0)  # 200 + 20 - 10
        self.assertEqual(snap.icms.cst_csosn, "00")
        self.assertEqual(snap.icms.pICMS, 18.0)
        self.assertEqual(snap.icms.vICMS, 37.8)  # 210 * 18% = 37.8
        self.assertEqual(snap.pis.vPIS, 3.47)    # 210 * 1.65% = 3.465 -> 3.47
        self.assertEqual(snap.cofins.vCOFINS, 15.96) # 210 * 7.6% = 15.96
        self.assertEqual(snap.vItemTotal, 210.0)

    def test_interstate_difal_ec87(self):
        inp = TaxCalculationInput(
            company_crt=3,
            company_uf="SP",
            product=ProductTaxProfileInput(
                ncm="84713012",
                cst_csosn="00",
                origem="0",
                icms_aliquot=18.0,  # Destino (RJ)
            ),
            operation=OperationResolvedInput(
                operation_code="VENDA_INTERESTADUAL",
                operation_name="Venda Interestadual Consumidor Final",
                cfop="6108",
            ),
            recipient=RecipientInput(uf="RJ", is_final_consumer=True, is_tax_contributor=False),
            context=ItemFinancialContextInput(
                vProd=1000.0,
                qCom=1.0,
                vUnCom=1000.0,
            ),
        )

        snap = TaxEngine.calculate_item_tax(inp)
        self.assertEqual(snap.difal.pICMS_Inter, 12.0)
        self.assertEqual(snap.difal.pICMS_UF_Dest, 18.0)
        self.assertEqual(snap.difal.vDIFAL_UF_Dest, 60.0)  # 1000 * (18% - 12%) = 60.0

    def test_reforma_tributaria_rtc_ibs_cbs(self):
        inp = TaxCalculationInput(
            company_crt=3,
            company_uf="SP",
            product=ProductTaxProfileInput(
                ncm="84713012",
                cst_csosn="00",
                origem="0",
                icms_aliquot=18.0,
                ibs_aliquot=0.1,
                cbs_aliquot=0.9,
            ),
            operation=OperationResolvedInput(
                operation_code="VENDA_ESTADO",
                operation_name="Venda no Estado",
                cfop="5102",
            ),
            recipient=RecipientInput(uf="SP", is_final_consumer=True, is_tax_contributor=False),
            context=ItemFinancialContextInput(
                vProd=500.0,
                qCom=1.0,
                vUnCom=500.0,
            ),
        )

        snap = TaxEngine.calculate_item_tax(inp)
        self.assertEqual(snap.rtc.vBC_IBS, 500.0)
        self.assertEqual(snap.rtc.vIBS, 0.5)  # 500 * 0.1% = 0.5
        self.assertEqual(snap.rtc.vCBS, 4.5)  # 500 * 0.9% = 4.5
        self.assertEqual(snap.rtc.version, "RTC_2026.1")
        self.assertEqual(snap.rtc.ibs.vIBS, 0.5)
        self.assertEqual(snap.rtc.cbs.vCBS, 4.5)

    def test_reforma_tributaria_ibs_cbs_rich_groups_and_versioning(self):
        """Testa a apuração dos grupos versionados de IBS e CBS com reduções de BC, classificações, alíquotas estaduais/municipais, benefícios e créditos."""
        inp = TaxCalculationInput(
            company_crt=3,
            company_uf="SP",
            product=ProductTaxProfileInput(
                ncm="84713012",
                cst_csosn="00",
                origem="0",
                icms_aliquot=18.0,
                cst_pis="01",
                pis_aliquot=1.65,
                cst_cofins="01",
                cofins_aliquot=7.6,
                # Configurações RTC IBS / CBS
                cst_ibs="20",  # Com redução de base
                cst_cbs="20",
                cClass="010101",
                cBenef_IBS="BENEF_SP_01",
                cBenef_CBS="BENEF_FED_01",
                ibs_state_aliquot=0.10,
                ibs_mun_aliquot=0.05,
                cbs_aliquot=0.90,
                pRed_IBS=20.0,  # 20% de redução na base
                pRed_CBS=10.0,  # 10% de redução na base
                vCred_IBS=0.05,  # Crédito IBS
                vCred_CBS=0.10,  # Crédito CBS
                rtc_version="RTC_2026.1",
            ),
            operation=OperationResolvedInput(
                operation_code="VENDA_ESTADO",
                operation_name="Venda no Estado",
                cfop="5102",
            ),
            recipient=RecipientInput(uf="SP", is_final_consumer=False, is_tax_contributor=True),
            context=ItemFinancialContextInput(
                vProd=1000.0,
                qCom=1.0,
                vUnCom=1000.0,
            ),
        )

        snap = TaxEngine.calculate_item_tax(inp)

        # 1. Preservação dos tributos atuais
        self.assertEqual(snap.vBC_Base, 1000.0)
        self.assertEqual(snap.icms.vICMS, 180.0)
        self.assertEqual(snap.pis.vPIS, 16.5)
        self.assertEqual(snap.cofins.vCOFINS, 76.0)

        # 2. Grupo Versionado RTC
        self.assertEqual(snap.rtc.version, "RTC_2026.1")

        # 3. Apuração IBS (Base 1000, Redução 20% -> BC Efetiva 800)
        ibs = snap.rtc.ibs
        self.assertEqual(ibs.version, "RTC_2026.1")
        self.assertEqual(ibs.cst_ibs, "20")
        self.assertEqual(ibs.cClass, "010101")
        self.assertEqual(ibs.cBenef_IBS, "BENEF_SP_01")
        self.assertEqual(ibs.vBC_IBS, 1000.0)
        self.assertEqual(ibs.pRed_IBS, 20.0)
        self.assertEqual(ibs.vRed_IBS, 200.0)
        self.assertEqual(ibs.vBC_IBS_Efetiva, 800.0)
        self.assertEqual(ibs.pIBS, 0.15)  # 0.10 (Estadual) + 0.05 (Municipal)
        self.assertEqual(ibs.pIBS_State, 0.10)
        self.assertEqual(ibs.pIBS_Mun, 0.05)
        self.assertEqual(ibs.vIBS_Bruto, 1.20)  # 800 * 0.15% = 1.20
        self.assertEqual(ibs.vIBS_State, 0.80)  # 800 * 0.10% = 0.80
        self.assertEqual(ibs.vIBS_Mun, 0.40)    # 1.20 - 0.80 = 0.40
        self.assertEqual(ibs.vCred_IBS, 0.05)
        self.assertEqual(ibs.vIBS, 1.15)        # 1.20 - 0.05 = 1.15

        # 4. Apuração CBS (Base 1000, Redução 10% -> BC Efetiva 900)
        cbs = snap.rtc.cbs
        self.assertEqual(cbs.version, "RTC_2026.1")
        self.assertEqual(cbs.cst_cbs, "20")
        self.assertEqual(cbs.cClass, "010101")
        self.assertEqual(cbs.cBenef_CBS, "BENEF_FED_01")
        self.assertEqual(cbs.vBC_CBS, 1000.0)
        self.assertEqual(cbs.pRed_CBS, 10.0)
        self.assertEqual(cbs.vRed_CBS, 100.0)
        self.assertEqual(cbs.vBC_CBS_Efetiva, 900.0)
        self.assertEqual(cbs.pCBS, 0.90)
        self.assertEqual(cbs.vCBS_Bruto, 8.10)  # 900 * 0.90% = 8.10
        self.assertEqual(cbs.vCred_CBS, 0.10)
        self.assertEqual(cbs.vCBS, 8.00)        # 8.10 - 0.10 = 8.00

        # 5. Atributos diretos de retrocompatibilidade
        self.assertEqual(snap.rtc.vBC_IBS, 1000.0)
        self.assertEqual(snap.rtc.pIBS, 0.15)
        self.assertEqual(snap.rtc.vIBS, 1.15)
        self.assertEqual(snap.rtc.vBC_CBS, 1000.0)
        self.assertEqual(snap.rtc.pCBS, 0.90)
        self.assertEqual(snap.rtc.vCBS, 8.00)

    def test_invalid_combination_negative_base(self):
        inp = TaxCalculationInput(
            company_crt=3,
            company_uf="SP",
            product=ProductTaxProfileInput(ncm="84713012", cst_csosn="00", origem="0", icms_aliquot=18.0),
            operation=OperationResolvedInput(operation_code="VENDA", operation_name="Venda", cfop="5102"),
            recipient=RecipientInput(uf="SP", is_final_consumer=True, is_tax_contributor=False),
            context=ItemFinancialContextInput(vProd=100.0, qCom=1.0, vUnCom=100.0, vDesc=150.0),
        )
        with self.assertRaises(ValueError) as cm:
            TaxEngine.calculate_item_tax(inp)
        self.assertIn("negativa", str(cm.exception))

    def test_invalid_combination_crt3_csosn(self):
        inp = TaxCalculationInput(
            company_crt=3,  # Regime Normal
            company_uf="SP",
            product=ProductTaxProfileInput(ncm="84713012", cst_csosn="101", origem="0"),  # CSOSN do Simples!
            operation=OperationResolvedInput(operation_code="VENDA", operation_name="Venda", cfop="5102"),
            recipient=RecipientInput(uf="SP", is_final_consumer=True, is_tax_contributor=False),
            context=ItemFinancialContextInput(vProd=100.0, qCom=1.0, vUnCom=100.0),
        )
        with self.assertRaises(ValueError) as cm:
            TaxEngine.calculate_item_tax(inp)
        self.assertIn("Regime Normal (CRT 3) não pode utilizar código CSOSN", str(cm.exception))

    def test_invalid_combination_missing_tax_rate(self):
        inp = TaxCalculationInput(
            company_crt=3,
            company_uf="SP",
            product=ProductTaxProfileInput(ncm="84713012", cst_csosn="00", origem="0", icms_aliquot=None),  # Alíquota Ausente!
            operation=OperationResolvedInput(operation_code="VENDA", operation_name="Venda", cfop="5102"),
            recipient=RecipientInput(uf="SP", is_final_consumer=True, is_tax_contributor=False),
            context=ItemFinancialContextInput(vProd=100.0, qCom=1.0, vUnCom=100.0),
        )
        with self.assertRaises(ValueError) as cm:
            TaxEngine.calculate_item_tax(inp)
        self.assertIn("Alíquota de ICMS não cadastrada", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

