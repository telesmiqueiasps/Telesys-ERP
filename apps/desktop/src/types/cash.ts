export type CashRegisterStatus = "OPEN" | "CLOSED";

export type CashMovementType = "OPENING" | "SUPPLY" | "BLEED" | "CLOSING" | "SALE";

export type PaymentMethod = "MONEY" | "PIX" | "CREDIT_CARD" | "DEBIT_CARD" | "BOLETO" | "OTHER";

export interface CashMovement {
  id: string;
  cash_register_id: string;
  tenant_id: string;
  company_id: string;
  user_id: string;
  movement_type: CashMovementType;
  payment_method: PaymentMethod;
  amount: number;
  description?: string | null;
  created_at: string;
}

export interface CashRegister {
  id: string;
  tenant_id: string;
  company_id: string;
  user_id: string;
  opened_at: string;
  closed_at?: string | null;
  initial_balance: number;
  current_balance: number;
  final_declared_balance?: number | null;
  difference_amount?: number | null;
  status: CashRegisterStatus;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CashRegisterDetail extends CashRegister {
  user_name?: string | null;
  movements: CashMovement[];
}

export interface CashRegisterOpenInput {
  initial_balance: number;
  notes?: string;
}

export interface CashRegisterCloseInput {
  final_declared_balance: number;
  notes?: string;
}

export interface CashMovementCreateInput {
  movement_type: "SUPPLY" | "BLEED";
  payment_method: PaymentMethod;
  amount: number;
  description?: string;
}
