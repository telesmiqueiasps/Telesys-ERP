export interface FiscalScenarioRule {
  id: string;
  tenant_id: string;
  company_id: string;
  fiscal_operation_id: string;
  description: string;
  uf_origin?: string | null;
  uf_destination?: string | null;
  is_same_uf?: boolean | null;
  is_final_consumer?: boolean | null;
  is_tax_contributor?: boolean | null;
  cfop: string;
  cst_csosn_override?: string | null;
  icms_aliquot_override?: number | null;
  fcp_aliquot_override?: number | null;
  effective_from: string;
  effective_to?: string | null;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FiscalOperation {
  id: string;
  tenant_id: string;
  company_id: string;
  code: string;
  name: string;
  operation_type: 'IN' | 'OUT';
  purpose: number; // 1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução/Retorno
  affect_inventory: boolean;
  affect_financial: boolean;
  allowed_doc_models: string; // ex: "55,65"
  description?: string | null;
  is_active: boolean;
  rules: FiscalScenarioRule[];
  created_at: string;
  updated_at: string;
}

export interface FiscalScenarioRuleInput {
  description: string;
  uf_origin?: string | null;
  uf_destination?: string | null;
  is_same_uf?: boolean | null;
  is_final_consumer?: boolean | null;
  is_tax_contributor?: boolean | null;
  cfop: string;
  cst_csosn_override?: string | null;
  icms_aliquot_override?: number | null;
  fcp_aliquot_override?: number | null;
  effective_from: string;
  effective_to?: string | null;
  priority: number;
  is_active?: boolean;
}

export interface FiscalOperationInput {
  code: string;
  name: string;
  operation_type: 'IN' | 'OUT';
  purpose: number;
  affect_inventory: boolean;
  affect_financial: boolean;
  allowed_doc_models: string;
  description?: string | null;
  is_active?: boolean;
  rules?: FiscalScenarioRuleInput[];
}

export interface FiscalScenarioMatchRequest {
  operation_code?: string;
  operation_type: 'IN' | 'OUT';
  uf_origin: string;
  uf_destination: string;
  is_final_consumer: boolean;
  is_tax_contributor: boolean;
  doc_model: string;
  operation_date?: string;
}

export interface FiscalScenarioMatchResult {
  matched: boolean;
  fiscal_operation_id?: string | null;
  operation_name?: string | null;
  purpose?: number | null;
  affect_inventory?: boolean | null;
  affect_financial?: boolean | null;
  rule_id?: string | null;
  rule_description?: string | null;
  cfop?: string | null;
  cst_csosn_override?: string | null;
  icms_aliquot_override?: number | null;
  fcp_aliquot_override?: number | null;
  reason: string;
}
