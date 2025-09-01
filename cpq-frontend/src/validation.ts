import { z } from 'zod';
import type { Fefco, Material, Print, SlaType, QuoteFormPayload } from './types';

export const fefcoOptions: Fefco[] = ["0201", "0203", "0427", "0471", "0501"];
export const materialOptions: Material[] = ["Т23 Крафт", "Микрогофрокартон Крафт", "Микрогофрокартон Белый"];
export const printOptions: Print[] = ["без печати", "1+0", "2+0", "4+0", "4+4"];
export const slaOptions: SlaType[] = ["стандарт", "срочно", "эконом"];

export const quoteSchema = z.object({
  fefco: z.enum(fefcoOptions),
  x_mm: z.number({ required_error: 'Укажите X' }).int().min(20, 'Минимум 20').max(1200, 'Максимум 1200'),
  y_mm: z.number({ required_error: 'Укажите Y' }).int().min(20, 'Минимум 20').max(1200, 'Максимум 1200'),
  z_mm: z.number({ required_error: 'Укажите Z' }).int().min(20, 'Минимум 20').max(1200, 'Максимум 1200'),
  material: z.enum(materialOptions),
  print: z.enum(printOptions).optional().or(z.literal('').transform(() => undefined)),
  qty: z.number({ required_error: 'Укажите количество' }).int().min(1, 'Минимум 1').max(100000, 'Максимум 100000'),
  sla_type: z.enum(slaOptions),
  company: z.string().max(120).optional().or(z.literal('').transform(() => undefined)),
  contact_name: z.string().max(80).optional().or(z.literal('').transform(() => undefined)),
  city: z.string().max(80).optional().or(z.literal('').transform(() => undefined)),
  phone: z.string().optional().or(z.literal('').transform(() => undefined)),
  email: z
    .string()
    .regex(/^[^\s@]+@[^\s@]+\.[^\s@]+$/, 'Неверный email')
    .optional()
    .or(z.literal('').transform(() => undefined)),
  tg_username: z
    .string()
    .regex(/^@?[a-zA-Z0-9_]{5,}$/, 'Неверный Telegram username')
    .optional()
    .or(z.literal('').transform(() => undefined)),
});

export type QuoteFormData = z.infer<typeof quoteSchema>;

export function toPayload(data: QuoteFormData): QuoteFormPayload {
  return data as QuoteFormPayload;
}

