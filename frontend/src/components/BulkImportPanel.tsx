import { useState, useCallback, type DragEvent, type ChangeEvent } from 'react';
import api from '../lib/api';

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
        setError('Only .xlsx and .csv files are supported');
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
        setError(typeof detail === 'string' ? detail : 'Upload failed');
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
    <div className="mb-6">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`relative rounded-xl border-2 border-dashed p-6 text-center transition-all ${
          dragOver
            ? 'border-emerald-500 bg-emerald-50'
            : 'border-slate-300 bg-white hover:border-slate-400'
        }`}
      >
        {uploading ? (
          <div className="flex items-center justify-center gap-3">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-emerald-600" />
            <span className="text-sm text-slate-600">Importing products...</span>
          </div>
        ) : (
          <>
            <div className="mb-2 text-3xl">📁</div>
            <p className="text-sm font-medium text-slate-700">
              Drag & drop Excel (.xlsx) or CSV file here
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Columns required: <code>sku</code>, <code>name</code>, <code>category</code>,{' '}
              <code>unit_cost</code>, <code>list_price</code>
            </p>
            <label className="mt-3 inline-block cursor-pointer rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-200">
              Browse files
              <input
                type="file"
                accept=".xlsx,.csv"
                className="hidden"
                onChange={onFileSelect}
              />
            </label>
          </>
        )}
      </div>

      {error && (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex gap-6 text-sm">
            <div>
              <span className="font-semibold text-emerald-700">{result.imported}</span>{' '}
              <span className="text-slate-500">imported</span>
            </div>
            <div>
              <span className="font-semibold text-amber-600">{result.skipped}</span>{' '}
              <span className="text-slate-500">skipped (duplicates)</span>
            </div>
            {result.errors.length > 0 && (
              <div>
                <span className="font-semibold text-red-600">{result.errors.length}</span>{' '}
                <span className="text-slate-500">errors</span>
              </div>
            )}
          </div>
          {result.errors.length > 0 && (
            <ul className="mt-2 list-inside list-disc text-xs text-red-600">
              {result.errors.slice(0, 5).map((e, i) => (
                <li key={i}>
                  Row {e.row}: {e.error}
                </li>
              ))}
              {result.errors.length > 5 && <li>... and {result.errors.length - 5} more</li>}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
