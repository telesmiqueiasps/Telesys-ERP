import { apiFetch } from "@/lib/apiClient";
import {
  ProductFiscalProfile,
  ProductFiscalProfileInput,
  FiscalPendingReport,
} from "@/types/product_fiscal";

export const productFiscalService = {
  async getFiscalProfile(productId: string, companyId: string): Promise<ProductFiscalProfile | null> {
    return apiFetch<ProductFiscalProfile | null>(
      `/products-fiscal/${productId}?company_id=${companyId}`
    );
  },

  async updateFiscalProfile(
    productId: string,
    data: ProductFiscalProfileInput,
    companyId: string
  ): Promise<ProductFiscalProfile> {
    return apiFetch<ProductFiscalProfile>(`/products-fiscal/${productId}?company_id=${companyId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async getFiscalPendingReport(companyId: string): Promise<FiscalPendingReport> {
    return apiFetch<FiscalPendingReport>(`/products-fiscal/pending/report?company_id=${companyId}`);
  },
};
