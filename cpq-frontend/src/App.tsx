import { useEffect, useMemo, useRef, useState } from 'react';
import './index.css';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { IMaskInput } from 'react-imask';
import { FormField, FormRow, ResultCard, StatusBar } from './components/FormPrimitives';
import { fefcoOptions, materialOptions, printOptions, slaOptions, quoteSchema, type QuoteFormData, toPayload } from './validation';
import { postQuote, type ApiResponse } from './api';

type Status = 'idle' | 'loading' | 'success' | 'error';

declare global {
  interface Window {
    dataLayer?: unknown[];
  }
}

function pushEvent(event: unknown) {
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(event);
}

function App() {
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    trigger,
  } = useForm<QuoteFormData>({
    mode: 'all',
    resolver: zodResolver(quoteSchema),
    defaultValues: {
      print: undefined,
    },
  });

  // Keep validation state in sync
  useEffect(() => {
    void trigger();
  });

  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<ApiResponse | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const onSubmit = handleSubmit(async (values: QuoteFormData) => {
    // eslint-disable-next-line no-console
    console.log('onSubmit values', values);
    pushEvent({ event: 'cpq_form_submit' });
    setStatus('loading');
    setResult(null);
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    const payload = toPayload(values);
    const res = await postQuote(payload, abortRef.current.signal).catch((err) => ({ ok: false as const, error: String(err) }));
    if (res.ok) {
      pushEvent({ event: 'cpq_api_ok', lead_id: res.lead_id });
      setResult(res);
      setStatus('success');
    } else {
      pushEvent({ event: 'cpq_api_error', message: res.error });
      setResult(res);
      setStatus('error');
    }
  });

  const fefcoItems = useMemo(() => fefcoOptions, []);
  const materialItems = useMemo(() => materialOptions, []);
  const printItems = useMemo(() => printOptions, []);
  const slaItems = useMemo(() => slaOptions, []);

  return (
    <main className="mx-auto max-w-3xl p-4">
      <h1 className="mb-6 text-2xl font-semibold">Коммерческое предложение — Гофрокороба</h1>

      <form onSubmit={onSubmit} noValidate>
        <fieldset className="rounded-md border p-4">
          <legend className="px-1 text-base font-medium">Параметры коробки</legend>
          <FormRow>
            <FormField id="fefco" label="FEFCO" required error={errors.fefco?.message}>
              <select className="w-full rounded-md border px-3 py-2" {...register('fefco')}> 
                <option value="">— выберите —</option>
                {fefcoItems.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField id="material" label="Материал" required error={errors.material?.message}>
              <select className="w-full rounded-md border px-3 py-2" {...register('material')}>
                <option value="">— выберите —</option>
                {materialItems.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </FormField>
          </FormRow>

          <FormRow columns={3}>
            {(['x_mm', 'y_mm', 'z_mm'] as const).map((dim) => (
              <FormField key={dim} id={dim} label={dim.toUpperCase().replace('_MM', '') + ', мм'} required error={errors[dim]?.message}>
                <input
                  type="number"
                  inputMode="numeric"
                  min={20}
                  max={1200}
                  step={1}
                  className="w-full rounded-md border px-3 py-2"
                  {...register(dim, { valueAsNumber: true })}
                />
              </FormField>
            ))}
          </FormRow>

          <FormRow>
            <FormField id="print" label="Печать" error={errors.print?.message}>
              <select className="w-full rounded-md border px-3 py-2" {...register('print')}>
                <option value="">без печати</option>
                {printItems
                  .filter((p) => p !== 'без печати')
                  .map((v) => (
                    <option key={v} value={v}>
                      {v}
                    </option>
                  ))}
              </select>
            </FormField>

            <FormField id="qty" label="Тираж" required error={errors.qty?.message}>
              <input
                type="number"
                inputMode="numeric"
                min={1}
                max={100000}
                step={1}
                className="w-full rounded-md border px-3 py-2"
                {...register('qty', { valueAsNumber: true })}
              />
            </FormField>
          </FormRow>

          <FormRow>
            <FormField id="sla_type" label="Срок" required error={errors.sla_type?.message}>
              <select className="w-full rounded-md border px-3 py-2" {...register('sla_type')}>
                <option value="">— выберите —</option>
                {slaItems.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </FormField>
          </FormRow>
        </fieldset>

        <fieldset className="mt-6 rounded-md border p-4">
          <legend className="px-1 text-base font-medium">Контакты и доставка</legend>
          <FormRow>
            <FormField id="company" label="Компания" error={errors.company?.message}>
              <input className="w-full rounded-md border px-3 py-2" maxLength={120} {...register('company')} />
            </FormField>
            <FormField id="contact_name" label="Контактное лицо" error={errors.contact_name?.message}>
              <input className="w-full rounded-md border px-3 py-2" maxLength={80} {...register('contact_name')} />
            </FormField>
          </FormRow>
          <FormRow>
            <FormField id="city" label="Город" error={errors.city?.message}>
              <input className="w-full rounded-md border px-3 py-2" maxLength={80} {...register('city')} />
            </FormField>
            <FormField id="phone" label="Телефон" hint="+7 999 999-99-99" error={errors.phone?.message}>
              <IMaskInput
                mask={'+{7} 000 000-00-00'}
                className="w-full rounded-md border px-3 py-2"
                onAccept={(value: string) => setValue('phone', value, { shouldDirty: true, shouldValidate: true })}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue('phone', e.target.value, { shouldDirty: true, shouldValidate: true })}
              />
            </FormField>
          </FormRow>
          <FormRow>
            <FormField id="email" label="Email" error={errors.email?.message}>
              <input type="email" className="w-full rounded-md border px-3 py-2" {...register('email')} />
            </FormField>
            <FormField id="tg_username" label="Telegram" hint="@username" error={errors.tg_username?.message}>
              <input className="w-full rounded-md border px-3 py-2" {...register('tg_username')} />
            </FormField>
          </FormRow>
        </fieldset>

        <fieldset className="mt-6 rounded-md border p-4">
          <legend className="px-1 text-base font-medium">Согласие</legend>
          <div className="flex items-start gap-3">
            <input id="consent" type="checkbox" className="mt-1 h-4 w-4" required />
            <label htmlFor="consent" className="text-sm text-gray-800">
              Согласен на обработку персональных данных
              {' '}
              <a className="underline" href="#" target="_blank" rel="noreferrer noopener">
                политика
              </a>
            </label>
          </div>
        </fieldset>

        <div className="mt-6 flex gap-3">
          <button
            type="submit"
            className="inline-flex items-center rounded-md bg-primary-600 px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-50 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:ring-offset-2"
          >
            Сформировать КП
          </button>
          {status === 'error' && (
            <button
              type="button"
              onClick={() => {
                setStatus('idle');
                setResult(null);
              }}
              className="inline-flex items-center rounded-md border px-4 py-2"
            >
              Повторить
            </button>
          )}
        </div>

        <StatusBar status={status} message={result && !result.ok ? result.error : undefined} />

        {result && result.ok && (
          <ResultCard
            pdfUrl={result.pdf_url}
            leadId={result.lead_id}
            onClick={() => pushEvent({ event: 'cpq_pdf_link_click' })}
          />
        )}
      </form>
    </main>
  );
}

export default App;
