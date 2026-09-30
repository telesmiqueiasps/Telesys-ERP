import { apiFetch } from "@/lib/apiClient";
import {
  CompanyFiscalConfig,
  CompanyFiscalConfigInput,
  FiscalSeries,
  FiscalSeriesInput,
  FiscalCertificateMetadata,
} from "@/types/company_fiscal";

export const companyFiscalService = {
  async getFiscalConfig(companyId: string): Promise<CompanyFiscalConfig> {
    return apiFetch<CompanyFiscalConfig>(`/company-fiscal/config?company_id=${companyId}`);
  },

  async updateFiscalConfig(
    data: CompanyFiscalConfigInput,
    companyId: string
  ): Promise<CompanyFiscalConfig> {
    return apiFetch<CompanyFiscalConfig>(`/company-fiscal/config?company_id=${companyId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async getFiscalSeries(companyId: string): Promise<FiscalSeries[]> {
    return apiFetch<FiscalSeries[]>(`/company-fiscal/series?company_id=${companyId}`);
  },

  async upsertFiscalSeries(
    data: FiscalSeriesInput,
    companyId: string
  ): Promise<FiscalSeries> {
    return apiFetch<FiscalSeries>(`/company-fiscal/series?company_id=${companyId}`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getCertificateMetadata(companyId: string): Promise<FiscalCertificateMetadata | null> {
    return apiFetch<FiscalCertificateMetadata | null>(
      `/company-fiscal/certificate?company_id=${companyId}`
    );
  },

  async uploadCertificate(
    file: File,
    password: string,
    companyId: string
  ): Promise<FiscalCertificateMetadata> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("password", password);

    // Usa fetch diretamente para envio Multipart FormData sem Content-Type JSON
    const token = localStorage.getItem("telesys_token");
    const res = await fetch(`http://localhost:8000/api/v1/company-fiscal/certificate/upload?company_id=${companyId}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token || ""}`,
      },
      body: formData,
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || "Erro ao fazer upload do certificado A1.");
    }

    return res.json();
  },
};
