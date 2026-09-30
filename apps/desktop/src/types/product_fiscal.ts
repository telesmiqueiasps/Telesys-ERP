export interface ProductFiscalProfile {
  id: string;
  tenant_id: string;
  company_id: string;
  product_id: string;
  ncm?: string;
  cest?: string;
  origin: number;
  gtin_commercial?: string;
  gtin_taxable?: string;
  unit_commercial?: string;
  unit_taxable?: string;
  conversion_factor: number;
  cst_csosn?: string;
  cfop_default_inside: string;
  cfop_default_outside: string;
  icms_rate: number;
  icms_st_rate: number;
  fcp_rate: number;
  ipi_cst?: string;
  ipi_rate: number;
  pis_cst?: string;
  pis_rate: number;
  cofins_cst?: string;
  cofins_rate: number;
  ibs_cst?: string;
  ibs_rate: number;
  cbs_cst?: string;
  cbs_rate: number;
  effective_from: string;
  effective_to?: string;
  source_reference?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductFiscalProfileInput {
  ncm?: string;
  cest?: string;
  origin: number;
  gtin_commercial?: string;
  gtin_taxable?: string;
  unit_commercial?: string;
  unit_taxable?: string;
  conversion_factor: number;
  cst_csosn?: string;
  cfop_default_inside: string;
  cfop_default_outside: string;
  icms_rate: number;
  icms_st_rate: number;
  fcp_rate: number;
  ipi_cst?: string;
  ipi_rate: number;
  pis_cst?: string;
  pis_rate: number;
  cofins_cst?: string;
  cofins_rate: number;
  ibs_cst?: string;
  ibs_rate: number;
  cbs_cst?: string;
  cbs_rate: number;
  source_reference?: string;
}

export interface FiscalPendingItem {
  product_id: string;
  product_name: string;
  code?: string;
  barcodes: string[];
  has_profile: boolean;
  pending_reasons: string[];
}

export interface FiscalPendingReport {
  total_products: number;
  pending_count: number;
  ok_count: number;
  items: FiscalPendingItem[];
}
