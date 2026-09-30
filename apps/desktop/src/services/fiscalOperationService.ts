import { apiFetch } from "@/lib/apiClient";
import {
  FiscalOperation,
  FiscalOperationInput,
  FiscalScenarioRule,
  FiscalScenarioRuleInput,
  FiscalScenarioMatchRequest,
  FiscalScenarioMatchResult,
} from "@/types/fiscal_operation";

export const fiscalOperationService = {
  async getOperations(companyId: string): Promise<FiscalOperation[]> {
    return apiFetch<FiscalOperation[]>(`/fiscal-operations?company_id=${companyId}`);
  },

  async createOperation(companyId: string, payload: FiscalOperationInput): Promise<FiscalOperation> {
    return apiFetch<FiscalOperation>(`/fiscal-operations?company_id=${companyId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateOperation(
    companyId: string,
    operationId: string,
    payload: Partial<FiscalOperationInput>
  ): Promise<FiscalOperation> {
    return apiFetch<FiscalOperation>(`/fiscal-operations/${operationId}?company_id=${companyId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async addRule(
    companyId: string,
    operationId: string,
    payload: FiscalScenarioRuleInput
  ): Promise<FiscalScenarioRule> {
    return apiFetch<FiscalScenarioRule>(`/fiscal-operations/${operationId}/rules?company_id=${companyId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateRule(
    companyId: string,
    ruleId: string,
    payload: Partial<FiscalScenarioRuleInput>
  ): Promise<FiscalScenarioRule> {
    return apiFetch<FiscalScenarioRule>(`/fiscal-operations/rules/${ruleId}?company_id=${companyId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async deleteRule(companyId: string, ruleId: string): Promise<void> {
    return apiFetch<void>(`/fiscal-operations/rules/${ruleId}?company_id=${companyId}`, {
      method: "DELETE",
    });
  },

  async matchScenario(
    companyId: string,
    payload: FiscalScenarioMatchRequest
  ): Promise<FiscalScenarioMatchResult> {
    return apiFetch<FiscalScenarioMatchResult>(`/fiscal-operations/match-scenario?company_id=${companyId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
