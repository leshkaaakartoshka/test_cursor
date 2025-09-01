import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function fillBase() {
  fireEvent.change(screen.getByLabelText(/FEFCO/i), { target: { value: '0201' } });
  fireEvent.change(screen.getByLabelText(/Материал/i), { target: { value: 'Микрогофрокартон Крафт' } });
  fireEvent.change(screen.getByLabelText(/X, мм/i), { target: { value: '300' } });
  fireEvent.change(screen.getByLabelText(/Y, мм/i), { target: { value: '200' } });
  fireEvent.change(screen.getByLabelText(/Z, мм/i), { target: { value: '150' } });
  fireEvent.change(screen.getByLabelText(/Тираж/i), { target: { value: '1000' } });
  fireEvent.change(screen.getByLabelText(/Срок/i), { target: { value: 'стандарт' } });
  fireEvent.click(screen.getByLabelText(/Согласен/i));
}

describe('integration', () => {
  it('handles 200 OK', async () => {
    server.use(
      http.post('*/api/quote', async () => {
        return HttpResponse.json({ ok: true, pdf_url: 'https://x/pdf/web-123.pdf', lead_id: 'web-123' });
      }),
    );
    render(<App />);
    fillBase();
    fireEvent.click(screen.getByRole('button', { name: /сформировать/i }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(/Готово/));
    expect(screen.getByRole('link', { name: /Скачать PDF/i })).toHaveAttribute('href', 'https://x/pdf/web-123.pdf');
  });

  it('handles 400 error', async () => {
    server.use(
      http.post('*/api/quote', async () => {
        return HttpResponse.json({ ok: false, error: 'Неверные данные' }, { status: 400 });
      }),
    );
    render(<App />);
    fillBase();
    fireEvent.click(screen.getByRole('button', { name: /сформировать/i }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(/Неверные данные/));
  });

  it('handles 502 error', async () => {
    server.use(
      http.post('*/api/quote', async () => {
        return HttpResponse.json({ ok: false, error: 'Временная ошибка PDF' }, { status: 502 });
      }),
    );
    render(<App />);
    fillBase();
    fireEvent.click(screen.getByRole('button', { name: /сформировать/i }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(/Временная ошибка PDF/));
  });

  it('handles 404 error', async () => {
    server.use(
      http.post('*/api/quote', async () => {
        return HttpResponse.json({ ok: false, error: 'Прайс не найден' }, { status: 404 });
      }),
    );
    render(<App />);
    fillBase();
    fireEvent.click(screen.getByRole('button', { name: /сформировать/i }));
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(/Прайс не найден/));
  });
});

