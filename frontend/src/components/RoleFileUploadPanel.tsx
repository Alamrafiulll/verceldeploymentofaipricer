import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

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

  const formatUploadType = (value: string) =>
    value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

  const uploadTypes = useQuery({
    queryKey: ['upload-center', 'types', title],
    queryFn: async () => (await api.get<UploadTypeInfo[]>('/upload-center/types')).data,
  });

  const queryKey = useMemo(
    () => ['uploads', title, showAll ? 'all' : 'mine'] as const,
    [title, showAll],
  );

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
    queryFn: async () =>
      (await api.get<UploadedFileRecord[]>(`/uploads?mine=${showAll ? 'false' : 'true'}`)).data,
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
    <section className="space-y-4 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
      <h3 className="font-display text-lg font-semibold">{title}</h3>
      <p className="text-sm text-slate-600">{description}</p>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
        <select
          className="input"
          value={uploadType}
          onChange={(event) => setUploadType(event.target.value as UploadType)}
        >
          {allowedTypes.map((type) => (
            <option key={type} value={type}>
              {formatUploadType(type)}
            </option>
          ))}
        </select>
        <input
          className="input md:col-span-2"
          placeholder="Policy source reference or source URI (optional)"
          value={sourceUri}
          onChange={(event) => setSourceUri(event.target.value)}
        />
        <input
          className="input py-2"
          type="file"
          accept={selectedTypeInfo?.extensions.join(',')}
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </div>

      {selectedTypeInfo ? (
        <p className="text-xs text-slate-500">
          Accepted formats: {selectedTypeInfo.extensions.join(', ')}
        </p>
      ) : null}

      <button
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
        disabled={upload.isPending || !file}
        onClick={() => upload.mutate()}
      >
        {upload.isPending ? 'Uploading...' : 'Upload and Validate'}
      </button>

      {files.isLoading ? <p className="text-sm text-slate-600">Loading uploaded files...</p> : null}

      {!files.isLoading && (files.data?.length ?? 0) === 0 ? (
        <p className="text-sm text-slate-600">
          No files uploaded yet. Add a document to start policy ingestion or governance review.
        </p>
      ) : null}

      {(files.data?.length ?? 0) > 0 ? (
        <div className="overflow-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b text-left text-slate-600">
                <th className="py-2 pr-3">Type</th>
                <th className="py-2 pr-3">File</th>
                <th className="py-2 pr-3">Role</th>
                <th className="py-2 pr-3">Uploaded</th>
                <th className="py-2 pr-3">Integrity Hash</th>
                {allowDelete ? <th className="py-2 pr-3">Action</th> : null}
              </tr>
            </thead>
            <tbody>
              {files.data?.map((item) => (
                <tr key={item.id} className="border-b border-slate-100">
                  <td className="py-2 pr-3">{formatUploadType(item.upload_type)}</td>
                  <td className="py-2 pr-3">{item.file_name}</td>
                  <td className="py-2 pr-3">{item.uploaded_by_role}</td>
                  <td className="py-2 pr-3">{new Date(item.created_at).toLocaleString()}</td>
                  <td className="py-2 pr-3 font-mono text-xs">{item.file_hash.slice(0, 10)}...</td>
                  {allowDelete ? (
                    <td className="py-2 pr-3">
                      <button
                        className="rounded-md bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-60"
                        disabled={remove.isPending}
                        onClick={() => remove.mutate(item.id)}
                      >
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

      {message ? <div className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700">{message}</div> : null}
    </section>
  );
}
