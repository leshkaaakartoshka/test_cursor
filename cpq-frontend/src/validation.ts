import { z } from 'zod';
import type { Fefco, Material, Print, SlaType, QuoteFormPayload } from './types';

export const fefcoOptions: Fefco[] = ["0201", "0203", "0427", "0471", "0501"];
export const materialOptions: Material[] = ["Т23 Крафт", "Микрогофрокартон Крафт", "Микрогофрокартон Белый"];
export const printOptions: Print[] = ["без печати", "1+0", "2+0", "4+0", "4+4"];
export const slaOptions: SlaType[] = ["стандарт", "срочно", "эконом"];

export const quoteSchema = z.object({
  fefco: z.enum(fefcoOptions),
  x_mm: z.number({ message: 'Укажите X' }).int().min(20, 'Минимум 20').max(1200, 'Максимум 1200'),
  y_mm: z.number({ message: 'Укажите Y' }).int().min(20, 'Минимум 20').max(1200, 'Максимум 1200'),
  z_mm: z.number({ message: 'Укажите Z' }).int().min(20, 'Минимум 20').max(1200, 'Максимум 1200'),
  material: z.enum(materialOptions),
  print: z.enum(printOptions).optional(),
  qty: z.number({ message: 'Укажите количество' }).int().min(1, 'Минимум 1').max(100000, 'Максимум 100000'),
  sla_type: z.enum(slaOptions),
  company: z.string().max(120).optional(),
  contact_name: z.string().max(80).optional(),
  city: z.string().max(80).optional(),
  phone: z.string().optional(),
  email: z.string().email('Неверный email').optional(),
  tg_username: z.string().regex(/^@?[a-zA-Z0-9_]{5,}$/, 'Неверный Telegram username').optional(),
});

export type QuoteFormData = z.infer<typeof quoteSchema>;

export function toPayload(data: QuoteFormData): QuoteFormPayload {
  return {
    ...data,
    print: (data.print as any) === '' ? undefined : data.print,
    company: (data.company as any) === '' ? undefined : data.company,
    contact_name: (data.contact_name as any) === '' ? undefined : data.contact_name,
    city: (data.city as any) === '' ? undefined : data.city,
    phone: (data.phone as any) === '' ? undefined : data.phone,
    email: (data.email as any) === '' ? undefined : data.email,
    tg_username: (data.tg_username as any) === '' ? undefined : data.tg_username,
  };
}

