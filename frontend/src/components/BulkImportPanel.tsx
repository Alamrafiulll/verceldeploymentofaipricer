import { useState, useCallback, type DragEvent, type ChangeEvent } from 'react';
import { AlertCircle, Download, FileSpreadsheet, UploadCloud } from 'lucide-react';

import api from '../lib/api';
import { downloadProductImportTemplate } from '../lib/downloads';

interface ImportResult {
  imported: number;
  skipped: number;
  errors: { row: string; error: string }[];
  total_rows: number;
}

interface BulkImportPanelProps {
  onSuccess?: () => void;
}

export default function BulkImportPanel({ onSuccess }: BulkImportPanelProps) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (!ext || !['xlsx', 'csv'].includes(ext)) {
        setError('Only .xlsx and .csv files are supported for product import.');
        setResult(null);
        return;
      }

      setUploading(true);
      setError(null);
      setResult(null);

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await api.post<ImportResult>('/bulk-import/products', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        setResult(res.data);
        if (res.data.imported > 0) {
          onSuccess?.();
        }
      } catch (err: any) {
        const detail = err?.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Upload failed. Check the template and try again.');
      } finally {
        setUploading(false);
      }
    },
    [onSuccess],
  );

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files?.[0];
      if (file) void handleFile(file);
    },
    [handleFile],
  );

  const onFileSelect = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) void handleFile(file);
      e.target.value = '';
    },
    [handleFile],
  );

  return (
    <section className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="h-4 w-4 text-slate-500" aria-hidden="true" />
            <h2 className="text-base font-semibold text-slate-950">Bulk Product Import</h2>
          </div>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            Import products from a clean CSV or Excel file. Duplicate SKUs are skipped and row errors are returned.
          </p>
        </div>
        <button
          type="button"
          onClick={downloadProductImportTemplate}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          Template
        </button>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`relative rounded-lg border border-dashed p-6 text-center transition-all ${
          dragOver ? 'border-slate-500 bg-slate-100' : 'border-slate-300 bg-slate-50 hover:border-slate-400'
        }`}
      >
        {uploading ? (
          <div className="flex items-center justify-center gap-3">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-slate-800" />
            <span className="text-sm font-medium text-slate-700">Importing products...</span>
          </div>
        ) : (
          <>
            <UploadCloud className="mx-auto h-9 w-9 text-slate-500" aria-hidden="true" />
            <p className="mt-3 text-sm font-semibold text-slate-800">Drop Excel or CSV file here</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Required columns: <code>sku</code>, <code>name</code>, <code>category</code>, <code>unit_cost</code>,{' '}
              <code>list_price</code>
            </p>
            <label className="mt-4 inline-flex cursor-pointer items-center justify-center rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800">
              Browse file
              <input type="file" accept=".xlsx,.csv" className="hidden" onChange={onFileSelect} />
            </label>
          </>
        )}
      </div>

      {error && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="grid gap-3 text-sm sm:grid-cols-4">
            <Metric label="Imported" value={result.imported} className="text-emerald-700" />
            <Metric label="Skipped" value={result.skipped} className="text-amber-700" />
            <Metric label="Errors" value={result.errors.length} className="text-rose-700" />
            <Metric label="Rows" value={result.total_rows} className="text-slate-900" />
          </div>
          {result.errors.length > 0 && (
            <ul className="mt-3 space-y-1 text-xs text-rose-700">
              {result.errors.slice(0, 5).map((item) => (
                <li key={`${item.row}-${item.error}`}>
                  Row {item.row}: {item.error}
                </li>
              ))}
              {result.errors.length > 5 && <li>And {result.errors.length - 5} more errors.</li>}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

function Metric({ label, value, className }: { label: string; value: number; className: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${className}`}>{value}</p>
    </div>
  );
}
