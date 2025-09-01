import type { QuoteFormPayload } from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

function getCsrfToken(): string | undefined {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : undefined;
}

export interface ApiSuccess {
  ok: true;
  pdf_url: string;
  lead_id: string;
}

export interface ApiError {
  ok: false;
  error: string;
}

export type ApiResponse = ApiSuccess | ApiError;

export async function postQuote(payload: QuoteFormPayload, signal?: AbortSignal): Promise<ApiResponse> {
  // debug: ensure submission executed in tests
  // eslint-disable-next-line no-console
  console.log('postQuote called', payload);
  const res = await fetch(`${API_BASE}/api/quote`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': getCsrfToken() ?? '',
    },
    credentials: 'include',
    body: JSON.stringify(payload),
    signal,
  });

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const text = await res.text().catch(() => '');
    return { ok: false, error: `Unexpected response: ${text || res.statusText}` };
  }
  const json = (await res.json()) as ApiResponse;
  return json;
}

