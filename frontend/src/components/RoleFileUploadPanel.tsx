import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FileArchive, FileUp, Trash2, UploadCloud } from 'lucide-react';

import { AlertBanner, EmptyState, StatusChip } from './ui';
import api from '../lib/api';
import type { UploadedFileRecord, UploadType } from '../types/api';

interface RoleFileUploadPanelProps {
  title: string;
  description: string;
  allowedTypes: UploadType[];
  showAll?: boolean;
  allowDelete?: boolean;
}

interface UploadTypeInfo {
  type: UploadType;
  label: string;
  extensions: string[];
}

function formatUploadType(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

export default function RoleFileUploadPanel({
  title,
  description,
  allowedTypes,
  showAll = false,
  allowDelete = false,
}: RoleFileUploadPanelProps) {
  const queryClient = useQueryClient();
  const [uploadType, setUploadType] = useState<UploadType>(allowedTypes[0]);
  const [file, setFile] = useState<File | null>(null);
  const [sourceUri, setSourceUri] = useState('');
  const [message, setMessage] = useState('');

  const uploadTypes = useQuery({
    queryKey: ['upload-center', 'types', title],
    queryFn: async () => (await api.get<UploadTypeInfo[]>('/upload-center/types')).data,
  });

  const queryKey = useMemo(() => ['uploads', title, showAll ? 'all' : 'mine'] as const, [title, showAll]);

  const allowedTypeInfo = useMemo(
    () => uploadTypes.data?.filter((item) => allowedTypes.includes(item.type)) ?? [],
    [allowedTypes, uploadTypes.data],
  );

  const selectedTypeInfo = useMemo(
    () => allowedTypeInfo.find((item) => item.type === uploadType),
    [allowedTypeInfo, uploadType],
  );

  const files = useQuery({
    queryKey,
    queryFn: async () => (await api.get<UploadedFileRecord[]>(`/uploads?mine=${showAll ? 'false' : 'true'}`)).data,
  });

  const upload = useMutation({
    mutationFn: async () => {
      if (!file) {
        throw new Error('Please choose a file');
      }
      const formData = new FormData();
      formData.append('upload_type', uploadType);
      formData.append('file', file);
      if (sourceUri.trim()) {
        formData.append('source_uri', sourceUri.trim());
      }
      return api.post('/uploads', formData);
    },
    onSuccess: () => {
      setMessage('File uploaded and logged for decision traceability.');
      setFile(null);
      setSourceUri('');
      queryClient.invalidateQueries({ queryKey });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      setMessage(typeof detail === 'string' ? detail : 'Upload failed.');
    },
  });

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/uploads/${id}`),
    onSuccess: () => {
      setMessage('File removed.');
      queryClient.invalidateQueries({ queryKey });
    },
    onError: () => setMessage('Delete failed.'),
  });

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
              <FileUp className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">{description}</p>
            </div>
          </div>
          <StatusChip status={`${files.data?.length ?? 0} files`} variant="info" size="md" />
        </div>
      </div>

      <div className="grid gap-5 p-5 xl:grid-cols-[360px_minmax(0,1fr)]">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="mb-4 flex items-center gap-2">
            <UploadCloud className="h-4 w-4 text-slate-500" aria-hidden="true" />
            <h3 className="text-sm font-semibold text-slate-900">Governance File Intake</h3>
          </div>

          <div className="space-y-4">
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Document type</span>
              <select
                className="input mt-1"
                value={uploadType}
                onChange={(event) => setUploadType(event.target.value as UploadType)}
              >
                {allowedTypes.map((type) => (
                  <option key={type} value={type}>
                    {formatUploadType(type)}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="font-medium text-slate-700">Source reference</span>
              <input
                className="input mt-1"
                placeholder="Policy memo, source URI, or document owner"
                value={sourceUri}
                onChange={(event) => setSourceUri(event.target.value)}
              />
            </label>

            <label className="block text-sm">
              <span className="font-medium text-slate-700">File</span>
              <input
                className="input mt-1 py-2"
                type="file"
                accept={selectedTypeInfo?.extensions.join(',')}
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>
          </div>

          {selectedTypeInfo ? (
            <p className="mt-3 text-xs text-slate-500">Accepted formats: {selectedTypeInfo.extensions.join(', ')}</p>
          ) : null}

          <button
            type="button"
            className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
            disabled={upload.isPending || !file}
            onClick={() => upload.mutate()}
          >
            <UploadCloud className="h-4 w-4" aria-hidden="true" />
            {upload.isPending ? 'Uploading...' : 'Upload and validate'}
          </button>

          {message ? (
            <div className="mt-4">
              <AlertBanner variant={message.toLowerCase().includes('failed') ? 'danger' : 'success'}>{message}</AlertBanner>
            </div>
          ) : null}
        </div>

        <div className="min-w-0">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Governance File Register</h3>
              <p className="mt-1 text-sm text-slate-600">Uploaded policy and configuration files tied to traceability.</p>
            </div>
            <FileArchive className="h-5 w-5 text-slate-400" aria-hidden="true" />
          </div>

          {files.isLoading ? <p className="text-sm text-slate-600">Loading uploaded files...</p> : null}

          {!files.isLoading && (files.data?.length ?? 0) === 0 ? (
            <EmptyState
              icon={<FileArchive className="h-6 w-6" aria-hidden="true" />}
              title="No governance files"
              description="Uploaded files will appear here after validation."
            />
          ) : null}

          {(files.data?.length ?? 0) > 0 ? (
            <div className="overflow-x-auto rounded-lg border border-slate-200">
              <table className="w-full min-w-[920px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">File</th>
                    <th className="px-4 py-3">Role</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Uploaded</th>
                    <th className="px-4 py-3">Integrity Hash</th>
                    {allowDelete ? <th className="px-4 py-3 text-right">Action</th> : null}
                  </tr>
                </thead>
                <tbody>
                  {files.data?.map((item) => (
                    <tr key={item.id} className="border-b border-slate-100 last:border-0">
                      <td className="px-4 py-3 font-semibold text-slate-900">{formatUploadType(item.upload_type)}</td>
                      <td className="px-4 py-3 text-slate-700">{item.file_name}</td>
                      <td className="px-4 py-3 text-slate-600">{formatUploadType(item.uploaded_by_role)}</td>
                      <td className="px-4 py-3">
                        <StatusChip status={item.status} />
                      </td>
                      <td className="px-4 py-3 text-slate-600">{formatDate(item.created_at)}</td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-600">{item.file_hash.slice(0, 10)}...</td>
                      {allowDelete ? (
                        <td className="px-4 py-3 text-right">
                          <button
                            type="button"
                            className="inline-flex items-center gap-1.5 rounded-lg border border-rose-300 px-3 py-2 text-xs font-semibold text-rose-700 transition hover:bg-rose-50 disabled:opacity-60"
                            disabled={remove.isPending}
                            onClick={() => remove.mutate(item.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                            Remove
                          </button>
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
