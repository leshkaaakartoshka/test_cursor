import { describe, expect, it } from 'vitest';
import { quoteSchema } from '../validation';

const base = {
  fefco: '0201',
  x_mm: 300,
  y_mm: 200,
  z_mm: 150,
  material: 'Микрогофрокартон Крафт',
  qty: 1000,
  sla_type: 'стандарт',
};

describe('quoteSchema', () => {
  it('valid base', () => {
    const res = quoteSchema.safeParse(base);
    expect(res.success).toBe(true);
  });

  it('min/max bounds dimensions', () => {
    expect(quoteSchema.safeParse({ ...base, x_mm: 20 }).success).toBe(true);
    expect(quoteSchema.safeParse({ ...base, x_mm: 1200 }).success).toBe(true);
    expect(quoteSchema.safeParse({ ...base, x_mm: 19 }).success).toBe(false);
    expect(quoteSchema.safeParse({ ...base, x_mm: 1201 }).success).toBe(false);
  });

  it('qty bounds', () => {
    expect(quoteSchema.safeParse({ ...base, qty: 1 }).success).toBe(true);
    expect(quoteSchema.safeParse({ ...base, qty: 100000 }).success).toBe(true);
    expect(quoteSchema.safeParse({ ...base, qty: 0 }).success).toBe(false);
    expect(quoteSchema.safeParse({ ...base, qty: 100001 }).success).toBe(false);
  });

  it('invalid email', () => {
    const res = quoteSchema.safeParse({ ...base, email: 'bad' });
    expect(res.success).toBe(false);
  });

  it('valid email', () => {
    const res = quoteSchema.safeParse({ ...base, email: 'a@b.c' });
    expect(res.success).toBe(true);
  });

  it('tg username regex', () => {
    expect(quoteSchema.safeParse({ ...base, tg_username: '@ab' }).success).toBe(false);
    expect(quoteSchema.safeParse({ ...base, tg_username: '@valid_123' }).success).toBe(true);
    expect(quoteSchema.safeParse({ ...base, tg_username: 'valid_123' }).success).toBe(true);
  });

  it('print optional', () => {
    expect(quoteSchema.safeParse({ ...base, print: undefined }).success).toBe(true);
    expect(quoteSchema.safeParse({ ...base, print: '1+0' }).success).toBe(true);
    expect(quoteSchema.safeParse({ ...base, print: '' as any }).success).toBe(true);
  });

  it('invalid print value rejected', () => {
    expect(quoteSchema.safeParse({ ...base, print: '5+5' as any }).success).toBe(false);
  });

  it('required fields present', () => {
    expect(quoteSchema.safeParse({ ...base, fefco: undefined as any }).success).toBe(false);
    expect(quoteSchema.safeParse({ ...base, material: undefined as any }).success).toBe(false);
  });

  it('non-numeric inputs rejected', () => {
    expect(quoteSchema.safeParse({ ...base, x_mm: Number('NaN') }).success).toBe(false);
  });
});

