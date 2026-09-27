export interface NfeSupplierXml {
  document: string;
  name: string;
  trade_name?: string | null;
  state_registration?: string | null;
  phone?: string | null;
  address_street?: string | null;
  address_number?: string | null;
  address_neighborhood?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
}

export interface NfeItemXmlParsed {
  item_number: number;
  cProd: string;
  cEAN?: string | null;
  xProd: string;
  ncm?: string | null;
  cest?: string | null;
  uCom: string;
  qCom: number;
  vUnCom: number;
  vProd: number;
  matched_product_id?: string | null;
  matched_product_name?: string | null;
}

export interface NfeDupXmlParsed {
  nDup: string;
  dVenc: string;
  vDup: number;
}

export interface NfeParseResponse {
  chNFe: string;
  nNF: string;
  serie: string;
  dhEmi?: string | null;
  supplier: NfeSupplierXml;
  items: NfeItemXmlParsed[];
  duplicatas: NfeDupXmlParsed[];
  total_vProd: number;
  total_vNF: number;
}

export interface NfeConfirmItemInput {
  item_number: number;
  cProd: string;
  cEAN?: string | null;
  name: string;
  ncm?: string | null;
  uCom: string;
  quantity: number;
  unit_cost: number;
  action: "CREATE_NEW" | "LINK_EXISTING";
  linked_product_id?: string | null;
}

export interface NfeConfirmImportInput {
  chNFe: string;
  nNF: string;
  supplier: NfeSupplierXml;
  items: NfeConfirmItemInput[];
  duplicatas: NfeDupXmlParsed[];
  generate_payables: boolean;
}
