export interface CompanyFiscalConfig {
  id: string;
  tenant_id: string;
  company_id: string;
  environment: "HOMOLOGATION" | "PRODUCTION";
  tax_regime: "SIMPLES_NACIONAL" | "MEI" | "REGIME_NORMAL";
  crt: number;
  state_tax_number?: string;
  municipal_tax_number?: string;
  ibge_city_code?: string;
  nfc_csc_id?: string;
  nfc_csc_secret?: string;
  nfse_provider?: string;
  nfse_environment: "HOMOLOGATION" | "PRODUCTION";
  contingency_mode: "NONE" | "OFFLINE_NFC" | "EPEC";
  contingency_reason?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyFiscalConfigInput {
  environment: "HOMOLOGATION" | "PRODUCTION";
  tax_regime: "SIMPLES_NACIONAL" | "MEI" | "REGIME_NORMAL";
  crt: number;
  state_tax_number?: string;
  municipal_tax_number?: string;
  ibge_city_code?: string;
  nfc_csc_id?: string;
  nfc_csc_secret?: string;
  nfse_provider?: string;
  nfse_environment: "HOMOLOGATION" | "PRODUCTION";
  contingency_mode: "NONE" | "OFFLINE_NFC" | "EPEC";
  contingency_reason?: string;
}

export interface FiscalSeries {
  id: string;
  tenant_id: string;
  company_id: string;
  doc_model: string;
  series: number;
  current_number: number;
  environment: "HOMOLOGATION" | "PRODUCTION";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FiscalSeriesInput {
  doc_model: string;
  series: number;
  current_number: number;
  environment: "HOMOLOGATION" | "PRODUCTION";
  is_active: boolean;
}

export interface FiscalCertificateMetadata {
  id: string;
  company_id: string;
  filename: string;
  subject_cn: string;
  subject_cnpj?: string;
  issuer: string;
  serial_number: string;
  valid_from: string;
  valid_until: string;
  is_expired: boolean;
  is_valid: boolean;
  days_until_expiration: number;
  is_active: boolean;
}
