import React from 'react';

interface FormFieldProps {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
  required?: boolean;
}

export function FormField({ id, label, hint, error, children, required }: FormFieldProps) {
  const describedByIds = [hint ? `${id}-hint` : undefined, error ? `${id}-error` : undefined]
    .filter(Boolean)
    .join(' ');
  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-gray-900">
        {label} {required && <span className="text-red-600">*</span>}
      </label>
      <div className="mt-1">
        {React.isValidElement(children)
          ? React.cloneElement(children as React.ReactElement<any>, {
              id,
              'aria-describedby': describedByIds || undefined,
              'aria-invalid': error ? true : undefined,
            })
          : children}
      </div>
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-1 text-xs text-gray-500">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} className="mt-1 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

interface FormRowProps {
  columns?: 1 | 2 | 3;
  children: React.ReactNode;
}

export function FormRow({ columns = 2, children }: FormRowProps) {
  const gridCols = columns === 1 ? 'grid-cols-1' : columns === 2 ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1 md:grid-cols-3';
  return <div className={`grid ${gridCols} gap-4`}>{children}</div>;
}

type Status = 'idle' | 'loading' | 'success' | 'error';

export function StatusBar({ status, message }: { status: Status; message?: string }) {
  const styles: Record<Status, string> = {
    idle: 'sr-only',
    loading: 'bg-blue-50 text-blue-800 border-blue-200',
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200',
  };
  const text =
    status === 'loading' ? 'Отправляем запрос…' : status === 'success' ? 'Готово. PDF отправлен в Telegram.' : message || '';
  return <div role="status" aria-live="polite" className={`mt-4 rounded-md border p-3 text-sm ${styles[status]}`}>{text}</div>;
}

export function ResultCard({ pdfUrl, leadId, onClick }: { pdfUrl: string; leadId?: string; onClick?: () => void }) {
  return (
    <div className="mt-4 rounded-lg border p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">Lead ID: {leadId}</p>
          <a
            className="mt-1 inline-flex items-center rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:ring-offset-2"
            href={pdfUrl}
            target="_blank"
            rel="noreferrer noopener"
            onClick={onClick}
          >
            Скачать PDF
          </a>
        </div>
        <div className="text-sm text-green-700">Отправлено в Telegram</div>
      </div>
    </div>
  );
}

