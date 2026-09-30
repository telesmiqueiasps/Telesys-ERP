import uuid
from typing import List, Tuple
from app.schemas.tax_engine import (
    TaxCalculationInput,
    TaxSnapshot,
    TaxICMSSnapshot,
    TaxFCPSnapshot,
    TaxSTSnapshot,
    TaxDIFALSnapshot,
    TaxIPISnapshot,
    TaxPISSnapshot,
    TaxCOFINSSnapshot,
    TaxIBSSnapshot,
    TaxCBSSnapshot,
    TaxRTCSnapshot,
)


class TaxEngine:
    @staticmethod
    def calculate_item_tax(data: TaxCalculationInput) -> TaxSnapshot:
        """
        Motor de Cálculo Fiscal Imutável e Auditável.
        Realiza a apuração determinística dos tributos a partir das entradas e valida combinações inválidas.
        """
        audit: List[str] = []
        warnings: List[str] = []

        crt = data.company_crt
        company_uf = data.company_uf.upper()
        prod = data.product
        op = data.operation
        rec = data.recipient
        ctx = data.context

        # --- 1. Validações Iniciais do Contexto Financeiro ---
        if ctx.vProd <= 0:
            raise ValueError("O valor bruto do produto (vProd) deve ser maior que zero.")

        vBC_Base = round(ctx.vProd + ctx.vFrete + ctx.vSeguro + ctx.vOutro - ctx.vDesc, 2)
        if vBC_Base < 0:
            raise ValueError(f"Base de cálculo negativa ({vBC_Base}). O valor do desconto supera o valor bruto e despesas da operação.")

        audit.append(f"1. Base de Cálculo Bruta: vProd({ctx.vProd}) + vFrete({ctx.vFrete}) + vSeguro({ctx.vSeguro}) + vOutro({ctx.vOutro}) - vDesc({ctx.vDesc}) = {vBC_Base}")

        # --- 2. Determinação de CST / CSOSN ---
        cst_csosn = (op.cst_csosn_override or prod.cst_csosn).strip()
        origem = prod.origem.strip()
        cfop = op.cfop.strip()

        # Validações de incompatibilidade de CRT x CST/CSOSN
        if crt in [1, 2]:  # Simples Nacional
            if len(cst_csosn) == 2:
                # Se informado CST de 2 dígitos em empresa do Simples, efetua mapeamento seguro para CSOSN equivalente
                cst_map = {
                    "00": "102", "10": "201", "20": "102", "40": "400", "41": "400",
                    "50": "400", "60": "500", "90": "900"
                }
                csosn_mapped = cst_map.get(cst_csosn, "102")
                warnings.append(f"CST '{cst_csosn}' convertido automaticamente para CSOSN '{csosn_mapped}' referente a empresa do Simples Nacional (CRT {crt}).")
                cst_csosn = csosn_mapped
            elif len(cst_csosn) == 3 and cst_csosn not in ["101", "102", "103", "201", "202", "300", "400", "500", "900"]:
                raise ValueError(f"CSOSN '{cst_csosn}' é inválido para empresa no Simples Nacional.")
        elif crt == 3:  # Regime Normal
            if len(cst_csosn) == 3:
                raise ValueError(f"Empresa no Regime Normal (CRT 3) não pode utilizar código CSOSN '{cst_csosn}' do Simples Nacional. Utilize CST de 2 dígitos (ex: 00, 10, 20, 40, 60).")
            elif cst_csosn not in ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"]:
                raise ValueError(f"CST ICMS '{cst_csosn}' é inválido para empresa no Regime Normal.")

        audit.append(f"2. Enquadramento Categoriático: CRT={crt}, Origem={origem}, CST/CSOSN={cst_csosn}, CFOP={cfop}")

        # --- 3. Apuração de ICMS e Crédito Simples Nacional ---
        icms_snap = TaxICMSSnapshot(cst_csosn=cst_csosn)

        if crt in [1, 2]:  # Simples Nacional
            if cst_csosn == "101":
                pCredSN = data.company_pCredSN or 0.0
                if pCredSN <= 0:
                    warnings.append("CSOSN 101 utilizado sem alíquota de crédito de ICMS do Simples (pCredSN) cadastrada.")
                vCred = round(vBC_Base * (pCredSN / 100.0), 2)
                icms_snap = TaxICMSSnapshot(
                    cst_csosn=cst_csosn,
                    vBC_ICMS=vBC_Base,
                    pCredSN=pCredSN,
                    vCredICMSSN=vCred
                )
                audit.append(f"3. ICMS Simples Nacional (CSOSN 101): Permite crédito de {pCredSN}% -> vCredICMSSN = {vCred}")
            else:
                icms_snap = TaxICMSSnapshot(cst_csosn=cst_csosn, vBC_ICMS=0.0, pICMS=0.0, vICMS=0.0)
                audit.append(f"3. ICMS Simples Nacional (CSOSN {cst_csosn}): Sem apuração direta de ICMS próprio na nota.")

        elif crt == 3:  # Regime Normal
            if cst_csosn == "00":  # Tributada integralmente
                pICMS = op.icms_aliquot_override if op.icms_aliquot_override is not None else prod.icms_aliquot
                if pICMS is None:
                    raise ValueError("Alíquota de ICMS não cadastrada para produto/operação tributada (CST 00) no Regime Normal.")
                
                vBC = vBC_Base
                vICMS = round(vBC * (pICMS / 100.0), 2)
                icms_snap = TaxICMSSnapshot(cst_csosn=cst_csosn, modBC=3, vBC_ICMS=vBC, pICMS=pICMS, vICMS=vICMS)
                audit.append(f"3. ICMS Regime Normal (CST 00): vBC_ICMS={vBC} * pICMS({pICMS}%) = vICMS({vICMS})")
            elif cst_csosn in ["40", "41", "50"]:  # Isenta, Não Tributada, Suspensão
                icms_snap = TaxICMSSnapshot(cst_csosn=cst_csosn, vBC_ICMS=0.0, pICMS=0.0, vICMS=0.0)
                audit.append(f"3. ICMS Regime Normal (CST {cst_csosn}): Operação Isenta/Não Tributada. vICMS = 0.0")
            elif cst_csosn == "60":  # Cobrado anteriormente por ST
                icms_snap = TaxICMSSnapshot(cst_csosn=cst_csosn, vBC_ICMS=0.0, pICMS=0.0, vICMS=0.0)
                audit.append("3. ICMS Regime Normal (CST 60): ICMS retido por ST anteriormente. vICMS = 0.0")
            else:
                pICMS = op.icms_aliquot_override if op.icms_aliquot_override is not None else (prod.icms_aliquot or 0.0)
                vBC = vBC_Base
                vICMS = round(vBC * (pICMS / 100.0), 2)
                icms_snap = TaxICMSSnapshot(cst_csosn=cst_csosn, modBC=3, vBC_ICMS=vBC, pICMS=pICMS, vICMS=vICMS)
                audit.append(f"3. ICMS Regime Normal (CST {cst_csosn}): vBC_ICMS={vBC} * pICMS({pICMS}%) = vICMS({vICMS})")

        # --- 4. Apuração de FCP (Fundo de Combate à Pobreza) ---
        pFCP = op.fcp_aliquot_override if op.fcp_aliquot_override is not None else (prod.fcp_aliquot or 0.0)
        fcp_snap = TaxFCPSnapshot()

        if pFCP > 0:
            if cst_csosn in ["40", "41", "50"]:
                warnings.append(f"FCP de {pFCP}% desconsiderado devido à operação ser isenta (CST {cst_csosn}).")
            else:
                vBC_FCP = vBC_Base
                vFCP = round(vBC_FCP * (pFCP / 100.0), 2)
                fcp_snap = TaxFCPSnapshot(vBC_FCP=vBC_FCP, pFCP=pFCP, vFCP=vFCP)
                audit.append(f"4. FCP Apurado: vBC_FCP={vBC_FCP} * pFCP({pFCP}%) = vFCP({vFCP})")

        # --- 5. Apuração de ICMS-ST ---
        st_snap = TaxSTSnapshot()
        pMVAST = prod.mva_st or 0.0
        pICMSST = prod.icms_st_aliquot or 0.0

        if pMVAST > 0 or pICMSST > 0:
            if pICMSST <= 0:
                raise ValueError("Alíquota de ICMS-ST (icms_st_aliquot) obrigatória para operação com Substituição Tributária (MVA presente).")
            vBC_ST = round(vBC_Base * (1.0 + (pMVAST / 100.0)), 2)
            vICMSST_bruto = round(vBC_ST * (pICMSST / 100.0), 2)
            vICMSST = max(0.0, round(vICMSST_bruto - icms_snap.vICMS, 2))
            st_snap = TaxSTSnapshot(vBC_ICMSST=vBC_ST, pMVAST=pMVAST, pICMSST=pICMSST, vICMSST=vICMSST)
            audit.append(f"5. ICMS-ST Apurado: vBC_ST={vBC_ST} (MVA {pMVAST}%) -> vICMSST = {vICMSST}")

        # --- 6. Apuração de DIFAL (EC 87/2015) ---
        difal_snap = TaxDIFALSnapshot()
        is_interstate = company_uf != rec.uf.upper()

        if is_interstate and rec.is_final_consumer and not rec.is_tax_contributor:
            pICMS_Dest = prod.icms_aliquot or 18.0  # Alíquota interna da UF destino
            pICMS_Inter = 4.0 if origem in ["1", "2", "3", "8"] else 12.0
            pDIFAL_Rate = max(0.0, pICMS_Dest - pICMS_Inter)
            
            vBC_DIFAL = vBC_Base
            vDIFAL_Total = round(vBC_DIFAL * (pDIFAL_Rate / 100.0), 2)
            
            difal_snap = TaxDIFALSnapshot(
                vBC_DIFAL=vBC_DIFAL,
                pICMS_UF_Dest=pICMS_Dest,
                pICMS_Inter=pICMS_Inter,
                pICMS_Inter_Part=100.0,
                vDIFAL_UF_Dest=vDIFAL_Total,
                vDIFAL_UF_Remet=0.0
            )
            audit.append(f"6. DIFAL EC 87/2015 Apurado (Interestadual Consumidor Final Não-Contribuinte): pInter={pICMS_Inter}%, pDest={pICMS_Dest}% -> vDIFAL Destino = {vDIFAL_Total}")

        # --- 7. Apuração de IPI ---
        cst_ipi = (prod.cst_ipi or "99").strip()
        ipi_snap = TaxIPISnapshot(cst_ipi=cst_ipi)

        if cst_ipi in ["00", "50"]:  # Tributado
            pIPI = prod.ipi_aliquot
            if pIPI is None:
                raise ValueError(f"Alíquota de IPI obrigatória para CST IPI '{cst_ipi}'.")
            vBC_IPI = round(ctx.vProd + ctx.vFrete + ctx.vSeguro + ctx.vOutro, 2)
            vIPI = round(vBC_IPI * (pIPI / 100.0), 2)
            ipi_snap = TaxIPISnapshot(cst_ipi=cst_ipi, vBC_IPI=vBC_IPI, pIPI=pIPI, vIPI=vIPI)
            audit.append(f"7. IPI Apurado (CST {cst_ipi}): vBC_IPI={vBC_IPI} * pIPI({pIPI}%) = vIPI({vIPI})")

        # --- 8. Apuração de PIS e COFINS ---
        cst_pis = (prod.cst_pis or "07").strip()
        cst_cofins = (prod.cst_cofins or "07").strip()
        
        pis_snap = TaxPISSnapshot(cst_pis=cst_pis)
        if cst_pis in ["01", "02"]:
            pPIS = prod.pis_aliquot
            if pPIS is None:
                raise ValueError(f"Alíquota de PIS obrigatória para CST PIS '{cst_pis}'.")
            vBC_PIS = vBC_Base
            vPIS = round(vBC_PIS * (pPIS / 100.0), 2)
            pis_snap = TaxPISSnapshot(cst_pis=cst_pis, vBC_PIS=vBC_PIS, pPIS=pPIS, vPIS=vPIS)
            audit.append(f"8. PIS Apurado (CST {cst_pis}): vBC_PIS={vBC_PIS} * pPIS({pPIS}%) = vPIS({vPIS})")

        cofins_snap = TaxCOFINSSnapshot(cst_cofins=cst_cofins)
        if cst_cofins in ["01", "02"]:
            pCOFINS = prod.cofins_aliquot
            if pCOFINS is None:
                raise ValueError(f"Alíquota de COFINS obrigatória para CST COFINS '{cst_cofins}'.")
            vBC_COFINS = vBC_Base
            vCOFINS = round(vBC_COFINS * (pCOFINS / 100.0), 2)
            cofins_snap = TaxCOFINSSnapshot(cst_cofins=cst_cofins, vBC_COFINS=vBC_COFINS, pCOFINS=pCOFINS, vCOFINS=vCOFINS)
            audit.append(f"8. COFINS Apurado (CST {cst_cofins}): vBC_COFINS={vBC_COFINS} * pCOFINS({pCOFINS}%) = vCOFINS({vCOFINS})")

        # --- 9. Reforma Tributária RTC (IBS e CBS Versionados com Classificações, Reduções e Benefícios) ---
        rtc_ver = getattr(prod, "rtc_version", None) or "RTC_2026.1"
        cClass = getattr(prod, "cClass", None)
        
        # 9.1 IBS (Imposto sobre Bens e Serviços)
        cst_ibs = (getattr(prod, "cst_ibs", None) or "01").strip()
        cBenef_IBS = getattr(prod, "cBenef_IBS", None)
        vBC_IBS = vBC_Base
        pRed_IBS = float(getattr(prod, "pRed_IBS", 0.0) or 0.0)
        vRed_IBS = round(vBC_IBS * (pRed_IBS / 100.0), 2)
        vBC_IBS_Efetiva = round(vBC_IBS - vRed_IBS, 2)
        
        pIBS = float(prod.ibs_aliquot or 0.0)
        pIBS_State = float(getattr(prod, "ibs_state_aliquot", 0.0) or 0.0)
        pIBS_Mun = float(getattr(prod, "ibs_mun_aliquot", 0.0) or 0.0)
        
        if pIBS > 0 and pIBS_State == 0.0 and pIBS_Mun == 0.0:
            pIBS_State = round(pIBS / 2.0, 4)
            pIBS_Mun = round(pIBS - pIBS_State, 4)
        elif pIBS == 0.0 and (pIBS_State > 0 or pIBS_Mun > 0):
            pIBS = round(pIBS_State + pIBS_Mun, 4)
            
        vIBS_Bruto = round(vBC_IBS_Efetiva * (pIBS / 100.0), 2)
        vIBS_State = round(vBC_IBS_Efetiva * (pIBS_State / 100.0), 2)
        vIBS_Mun = round(vIBS_Bruto - vIBS_State, 2)
        
        vCred_IBS = float(getattr(prod, "vCred_IBS", 0.0) or 0.0)
        vDesc_IBS = float(getattr(prod, "vDesc_IBS", 0.0) or 0.0)
        vIBS = max(0.0, round(vIBS_Bruto - vCred_IBS - vDesc_IBS, 2))
        
        ibs_snap = TaxIBSSnapshot(
            version=rtc_ver,
            cst_ibs=cst_ibs,
            cClass=cClass,
            cBenef_IBS=cBenef_IBS,
            vBC_IBS=vBC_IBS,
            pRed_IBS=pRed_IBS,
            vRed_IBS=vRed_IBS,
            vBC_IBS_Efetiva=vBC_IBS_Efetiva,
            pIBS=pIBS,
            pIBS_State=pIBS_State,
            pIBS_Mun=pIBS_Mun,
            vIBS_Bruto=vIBS_Bruto,
            vIBS_State=vIBS_State,
            vIBS_Mun=vIBS_Mun,
            vCred_IBS=vCred_IBS,
            vDesc_IBS=vDesc_IBS,
            vIBS=vIBS,
        )

        # 9.2 CBS (Contribuição sobre Bens e Serviços)
        cst_cbs = (getattr(prod, "cst_cbs", None) or "01").strip()
        cBenef_CBS = getattr(prod, "cBenef_CBS", None)
        vBC_CBS = vBC_Base
        pRed_CBS = float(getattr(prod, "pRed_CBS", 0.0) or 0.0)
        vRed_CBS = round(vBC_CBS * (pRed_CBS / 100.0), 2)
        vBC_CBS_Efetiva = round(vBC_CBS - vRed_CBS, 2)
        
        pCBS = float(prod.cbs_aliquot or 0.0)
        vCBS_Bruto = round(vBC_CBS_Efetiva * (pCBS / 100.0), 2)
        vCred_CBS = float(getattr(prod, "vCred_CBS", 0.0) or 0.0)
        vDesc_CBS = float(getattr(prod, "vDesc_CBS", 0.0) or 0.0)
        vCBS = max(0.0, round(vCBS_Bruto - vCred_CBS - vDesc_CBS, 2))
        
        cbs_snap = TaxCBSSnapshot(
            version=rtc_ver,
            cst_cbs=cst_cbs,
            cClass=cClass,
            cBenef_CBS=cBenef_CBS,
            vBC_CBS=vBC_CBS,
            pRed_CBS=pRed_CBS,
            vRed_CBS=vRed_CBS,
            vBC_CBS_Efetiva=vBC_CBS_Efetiva,
            pCBS=pCBS,
            vCBS_Bruto=vCBS_Bruto,
            vCred_CBS=vCred_CBS,
            vDesc_CBS=vDesc_CBS,
            vCBS=vCBS,
        )

        rtc_snap = TaxRTCSnapshot(
            version=rtc_ver,
            ibs=ibs_snap,
            cbs=cbs_snap,
            vBC_IBS=vBC_IBS,
            pIBS=pIBS,
            vIBS=vIBS,
            vBC_CBS=vBC_CBS,
            pCBS=pCBS,
            vCBS=vCBS,
        )

        if pIBS > 0 or pCBS > 0 or pRed_IBS > 0 or pRed_CBS > 0 or vCred_IBS > 0 or vCred_CBS > 0:
            audit.append(
                f"9. RTC Reforma Tributária Apurada ({rtc_ver}): "
                f"IBS(cst={cst_ibs}, cClass={cClass or 'N/A'}, pIBS={pIBS}%, red={pRed_IBS}%, vIBS={vIBS}, cred={vCred_IBS}), "
                f"CBS(cst={cst_cbs}, cClass={cClass or 'N/A'}, pCBS={pCBS}%, red={pRed_CBS}%, vCBS={vCBS}, cred={vCred_CBS})"
            )

        # --- 10. Totalização Final do Item ---
        vItemTotal = round(vBC_Base + st_snap.vICMSST + ipi_snap.vIPI + fcp_snap.vFCP, 2)
        audit.append(f"10. Totalização do Item: vBC_Base({vBC_Base}) + vICMSST({st_snap.vICMSST}) + vIPI({ipi_snap.vIPI}) + vFCP({fcp_snap.vFCP}) = vItemTotal({vItemTotal})")

        return TaxSnapshot(
            calculation_id=str(uuid.uuid4()),
            origem=origem,
            cfop=cfop,
            vProd=ctx.vProd,
            vFrete=ctx.vFrete,
            vSeguro=ctx.vSeguro,
            vOutro=ctx.vOutro,
            vDesc=ctx.vDesc,
            vBC_Base=vBC_Base,
            icms=icms_snap,
            fcp=fcp_snap,
            st=st_snap,
            difal=difal_snap,
            ipi=ipi_snap,
            pis=pis_snap,
            cofins=cofins_snap,
            rtc=rtc_snap,
            vTotTribAprox=0.0,
            vItemTotal=vItemTotal,
            audit_trail=audit,
            warnings=warnings,
        )
