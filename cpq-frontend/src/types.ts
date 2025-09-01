export type SlaType = "стандарт" | "срочно" | "эконом";
export type Fefco = "0201" | "0203" | "0427" | "0471" | "0501";
export type Material = "Т23 Крафт" | "Микрогофрокартон Крафт" | "Микрогофрокартон Белый";
export type Print = "без печати" | "1+0" | "2+0" | "4+0" | "4+4";

export interface QuoteFormPayload {
  fefco: Fefco;
  x_mm: number; y_mm: number; z_mm: number;
  material: Material;
  print?: Print;
  qty: number;
  sla_type: SlaType;
  company?: string;
  contact_name?: string;
  city?: string;
  phone?: string;
  email?: string;
  tg_username?: string;
}

