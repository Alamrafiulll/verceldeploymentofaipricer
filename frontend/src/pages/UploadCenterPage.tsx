import { useCallback, useEffect, useMemo, useState } from 'react';

import { getSession } from '../lib/auth';
import API from '../lib/api';
import { AlertBanner, EmptyState, SectionHeader, StatusChip } from '../components/ui';

interface UploadTypeInfo {
  type: string;
  label: string;
  extensions: string[];
}

interface ExtractionEntity {
  type: string;
  count: number;
  samples: string[];
}

interface ExtractionPayload {
  summary: string;
  detected_type: string;
  entities: ExtractionEntity[];
  entities_count: number;
  confidence: number;
  suggested_rules: string[];
  text_preview: string;
}

interface UploadReviewPayload {
  file_id: string;
  file_name: string;
  upload_type: string;
  status: string;
  review_id: string | null;
  review_status: string;
  review_notes: string | null;
  next_step: string;
  current_extraction: ExtractionPayload;
  original_extraction: Record<string, unknown>;
  corrected_extraction: Record<string, unknown> | null;
  extraction?: ExtractionPayload;
  message?: string;
}

interface FileRecord {
  id: string;
  file_name: string;
  upload_type: string;
  status: string;
  extraction_summary: string | null;
  extracted_entities_count: number | null;
  review_status: string | null;
  created_at: string | null;
  uploaded_by_role: string;
  next_step: string;
}

interface ReviewDraft {
  summary: string;
  detected_type: string;
  confidence: string;
  entities: ExtractionEntity[];
  suggested_rules_text: string;
  review_notes: string;
}

function createDraft(review: UploadReviewPayload): ReviewDraft {
  return {
    summary: review.current_extraction.summary,
    detected_type: review.current_extraction.detected_type,
    confidence: review.current_extraction.confidence.toFixed(2),
    entities: review.current_extraction.entities.map((entity) => ({
      type: entity.type,
      count: entity.count,
      samples: [...entity.samples],
    })),
    suggested_rules_text: review.current_extraction.suggested_rules.join('\n'),
    review_notes: review.review_notes ?? '',
  };
}

export default function UploadCenterPage() {
  const role = getSession()?.user.role;
  const [types, setTypes] = useState<UploadTypeInfo[]>([]);
  const [selectedType, setSelectedType] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [activeReview, setActiveReview] = useState<UploadReviewPayload | null>(null);
  const [reviewDraft, setReviewDraft] = useState<ReviewDraft | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewSaving, setReviewSaving] = useState(false);
  const [reviewMessage, setReviewMessage] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [typesRes, filesRes] = await Promise.all([
          API.get<UploadTypeInfo[]>('/upload-center/types'),
          API.get<FileRecord[]>('/upload-center/files'),
        ]);
        setTypes(typesRes.data);
        setFiles(filesRes.data);
        if (typesRes.data.length > 0) {
          setSelectedType(typesRes.data[0].type);
        }
      } catch {
        /* ignore */
      }
    };
    void load();
  }, []);

  const refreshFiles = useCallback(async () => {
    try {
      const res = await API.get<FileRecord[]>('/upload-center/files');
      setFiles(res.data);
    } catch {
      /* ignore */
    }
  }, []);

  const loadReview = useCallback(async (fileId: string) => {
    setReviewLoading(true);
    setReviewError(null);
    try {
      const res = await API.get<UploadReviewPayload>(`/upload-center/files/${fileId}/review`);
      setActiveReview(res.data);
      setReviewDraft(createDraft(res.data));
      setReviewMessage(null);
    } catch (err: any) {
      setReviewError(err?.response?.data?.detail || 'Unable to load the extraction review.');
    } finally {
      setReviewLoading(false);
    }
  }, []);

  const selectedInfo = useMemo(
    () => types.find((type) => type.type === selectedType),
    [selectedType, types],
  );

  const handleUpload = async () => {
    if (!file || !selectedType) return;
    setUploading(true);
    setError(null);
    setUploadMessage(null);
    setReviewMessage(null);
    setReviewError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('upload_type', selectedType);
      const res = await API.post<UploadReviewPayload>('/upload-center/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setActiveReview(res.data);
      setReviewDraft(createDraft(res.data));
      setUploadMessage(res.data.message ?? 'File uploaded successfully.');
      setFile(null);
      void refreshFiles();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
    if (event.dataTransfer.files?.[0]) {
      setFile(event.dataTransfer.files[0]);
      setUploadMessage(null);
    }
  };

  const updateEntity = (index: number, field: 'type' | 'count' | 'samples', value: string) => {
    if (!reviewDraft) return;
    setReviewDraft((prev) => {
      if (!prev) return prev;
      const nextEntities = [...prev.entities];
      const current = nextEntities[index];
      if (!current) return prev;
      if (field === 'count') {
        current.count = Number(value) || 0;
      } else if (field === 'samples') {
        current.samples = value
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean);
      } else {
        current.type = value;
      }
      nextEntities[index] = { ...current };
      return { ...prev, entities: nextEntities };
    });
  };

  const addEntityRow = () => {
    setReviewDraft((prev) =>
      prev
        ? {
            ...prev,
            entities: [...prev.entities, { type: '', count: 0, samples: [] }],
          }
        : prev,
    );
  };

  const removeEntityRow = (index: number) => {
    setReviewDraft((prev) =>
      prev
        ? {
            ...prev,
            entities: prev.entities.filter((_, currentIndex) => currentIndex !== index),
          }
        : prev,
    );
  };

  const saveReview = async (
    action: 'save_draft' | 'confirm_and_save' | 'submit_for_review' | 'activate' | 'reject',
  ) => {
    if (!activeReview || !reviewDraft) return;
    setReviewSaving(true);
    setReviewError(null);
    setReviewMessage(null);
    try {
      const payload = {
        summary: reviewDraft.summary,
        detected_type: reviewDraft.detected_type,
        confidence: Number(reviewDraft.confidence) || 0,
        entities: reviewDraft.entities.map((entity) => ({
          type: entity.type,
          count: entity.count,
          samples: entity.samples,
        })),
        suggested_rules: reviewDraft.suggested_rules_text
          .split('\n')
          .map((rule) => rule.trim())
          .filter(Boolean),
        review_notes: reviewDraft.review_notes,
        action,
      };
      const res = await API.patch<UploadReviewPayload>(
        `/upload-center/files/${activeReview.file_id}/review`,
        payload,
      );
      setActiveReview(res.data);
      setReviewDraft(createDraft(res.data));
      setReviewMessage(`Document updated: ${res.data.status.replace(/_/g, ' ')}.`);
      void refreshFiles();
    } catch (err: any) {
      setReviewError(err?.response?.data?.detail || 'Unable to save the extraction review.');
    } finally {
      setReviewSaving(false);
    }
  };

  const canApprove = role === 'admin' || role === 'approver';

  return (
    <div className="space-y-6 p-1">
      <SectionHeader
        icon="📁"
        title="Upload Center"
        subtitle="Upload business documents, review what the system understood, and confirm the next workflow step."
      />

      <AlertBanner variant="tip" title="What To Do Next">
        Choose the document category, upload the file, then confirm or correct the extraction before it becomes active in the pricing workflow.
      </AlertBanner>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="mb-3 text-sm font-semibold text-slate-700">Step 1: Choose document category</p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {types.map((type) => (
            <button
              key={type.type}
              type="button"
              className={`rounded-lg border-2 px-3 py-2.5 text-left transition-all ${
                selectedType === type.type
                  ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
              onClick={() => {
                setSelectedType(type.type);
                setUploadMessage(null);
              }}
            >
              <p className="text-xs font-semibold text-slate-800">{type.label}</p>
              <p className="mt-0.5 text-[10px] text-slate-500">{type.extensions.join(', ')}</p>
            </button>
          ))}
        </div>
        {types.length === 0 && (
          <p className="text-sm text-slate-400">No upload categories are available for your role.</p>
        )}
      </div>

      {selectedInfo && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="mb-1 text-sm font-semibold text-slate-700">
            Step 2: Upload {selectedInfo.label}
          </p>
          <p className="mb-3 text-xs text-slate-500">
            Accepted formats: {selectedInfo.extensions.join(', ')}
          </p>
          <div
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
              dragOver
                ? 'border-emerald-400 bg-emerald-50'
                : 'border-slate-300 bg-slate-50 hover:border-slate-400'
            }`}
            onDragOver={(event) => {
              event.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <span className="text-3xl">📄</span>
            <p className="mt-2 text-sm font-medium text-slate-600">
              {file ? file.name : `Drag and drop your ${selectedInfo.label} here`}
            </p>
            {file && <p className="text-xs text-slate-400">({(file.size / 1024).toFixed(1)} KB)</p>}
            <label className="mt-3 cursor-pointer rounded-lg bg-slate-200 px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-300">
              Browse Files
              <input
                type="file"
                className="hidden"
                accept={selectedInfo.extensions.join(',')}
                onChange={(event) => {
                  setFile(event.target.files?.[0] || null);
                  setUploadMessage(null);
                }}
              />
            </label>
          </div>
          <button
            type="button"
            disabled={!file || uploading}
            onClick={handleUpload}
            className="mt-4 w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:opacity-50"
          >
            {uploading ? 'Analyzing and Uploading...' : 'Upload and Analyze'}
          </button>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>
      )}

      {uploadMessage && (
        <AlertBanner variant="success" title="Upload Successful">
          {uploadMessage}
        </AlertBanner>
      )}

      {activeReview && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-800">Step 3: What the system understood</h3>
            <p className="mt-2 text-sm text-slate-600">{activeReview.current_extraction.summary}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
              <StatusChip status={activeReview.status} />
              <StatusChip status={activeReview.review_status} />
              <span className="text-slate-500">
                Detected type: <strong>{activeReview.current_extraction.detected_type}</strong>
              </span>
              <span className="text-slate-500">
                Confidence:{' '}
                <strong>{(activeReview.current_extraction.confidence * 100).toFixed(0)}%</strong>
              </span>
              <span className="text-slate-500">
                Business entities found:{' '}
                <strong>{activeReview.current_extraction.entities_count}</strong>
              </span>
            </div>
            <p className="mt-3 text-sm text-slate-600">
              <span className="font-semibold text-slate-700">Next step:</span> {activeReview.next_step}
            </p>

            {activeReview.current_extraction.entities.length > 0 && (
              <div className="mt-4">
                <p className="mb-2 text-xs font-medium text-slate-500">Extracted business entities</p>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {activeReview.current_extraction.entities.map((entity, index) => (
                    <div key={`${entity.type}-${index}`} className="rounded-lg bg-slate-50 p-3">
                      <p className="text-[11px] font-medium text-slate-500">{entity.type}</p>
                      <p className="text-lg font-bold text-slate-800">{entity.count}</p>
                      <p className="mt-1 truncate text-[10px] text-slate-400">
                        {entity.samples.join(', ')}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-slate-800">Step 4: Review and confirm</h3>
                <p className="text-xs text-slate-500">
                  Edit the extracted summary, entities, and suggested rules before the document moves forward.
                </p>
              </div>
              {reviewLoading && <p className="text-xs text-slate-500">Loading review...</p>}
            </div>

            {reviewError && (
              <div className="mt-3">
                <AlertBanner variant="danger">{reviewError}</AlertBanner>
              </div>
            )}
            {reviewMessage && (
              <div className="mt-3">
                <AlertBanner variant="success">{reviewMessage}</AlertBanner>
              </div>
            )}

            {reviewDraft && (
              <div className="mt-4 space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="space-y-1 text-sm">
                    <span className="text-slate-600">Plain-language summary</span>
                    <textarea
                      className="input min-h-28"
                      value={reviewDraft.summary}
                      onChange={(event) =>
                        setReviewDraft((prev) =>
                          prev ? { ...prev, summary: event.target.value } : prev,
                        )
                      }
                    />
                  </label>
                  <div className="space-y-4">
                    <label className="space-y-1 text-sm">
                      <span className="text-slate-600">Detected document type</span>
                      <input
                        className="input"
                        value={reviewDraft.detected_type}
                        onChange={(event) =>
                          setReviewDraft((prev) =>
                            prev ? { ...prev, detected_type: event.target.value } : prev,
                          )
                        }
                      />
                    </label>
                    <label className="space-y-1 text-sm">
                      <span className="text-slate-600">Recommendation confidence</span>
                      <input
                        className="input"
                        type="number"
                        min={0}
                        max={1}
                        step={0.01}
                        value={reviewDraft.confidence}
                        onChange={(event) =>
                          setReviewDraft((prev) =>
                            prev ? { ...prev, confidence: event.target.value } : prev,
                          )
                        }
                      />
                    </label>
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-semibold text-slate-700">Business entities</p>
                    <button
                      type="button"
                      onClick={addEntityRow}
                      className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700"
                    >
                      Add Entity
                    </button>
                  </div>
                  <div className="space-y-3">
                    {reviewDraft.entities.map((entity, index) => (
                      <div
                        key={`entity-row-${index}`}
                        className="grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3 md:grid-cols-[1.4fr_0.6fr_1.6fr_auto]"
                      >
                        <input
                          className="input"
                          placeholder="Entity type"
                          value={entity.type}
                          onChange={(event) => updateEntity(index, 'type', event.target.value)}
                        />
                        <input
                          className="input"
                          type="number"
                          min={0}
                          value={entity.count}
                          onChange={(event) => updateEntity(index, 'count', event.target.value)}
                        />
                        <input
                          className="input"
                          placeholder="Samples separated by commas"
                          value={entity.samples.join(', ')}
                          onChange={(event) => updateEntity(index, 'samples', event.target.value)}
                        />
                        <button
                          type="button"
                          onClick={() => removeEntityRow(index)}
                          className="rounded-md border border-rose-300 px-3 py-2 text-xs font-medium text-rose-700"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                    {reviewDraft.entities.length === 0 && (
                      <p className="text-sm text-slate-500">No entities captured yet. Add rows if you need manual corrections.</p>
                    )}
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <label className="space-y-1 text-sm">
                    <span className="text-slate-600">Suggested business rules</span>
                    <textarea
                      className="input min-h-28"
                      value={reviewDraft.suggested_rules_text}
                      onChange={(event) =>
                        setReviewDraft((prev) =>
                          prev ? { ...prev, suggested_rules_text: event.target.value } : prev,
                        )
                      }
                      placeholder="One suggested rule per line"
                    />
                  </label>
                  <label className="space-y-1 text-sm">
                    <span className="text-slate-600">Review notes</span>
                    <textarea
                      className="input min-h-28"
                      value={reviewDraft.review_notes}
                      onChange={(event) =>
                        setReviewDraft((prev) =>
                          prev ? { ...prev, review_notes: event.target.value } : prev,
                        )
                      }
                      placeholder="Record any corrections, assumptions, or business context here"
                    />
                  </label>
                </div>

                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Source Text Preview
                  </p>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">
                    {activeReview.current_extraction.text_preview || 'No text preview available.'}
                  </p>
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={reviewSaving}
                    onClick={() => saveReview('save_draft')}
                    className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-50"
                  >
                    {reviewSaving ? 'Saving...' : 'Save Draft'}
                  </button>
                  <button
                    type="button"
                    disabled={reviewSaving}
                    onClick={() => saveReview('confirm_and_save')}
                    className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                  >
                    {reviewSaving ? 'Saving...' : 'Confirm and Save'}
                  </button>
                  <button
                    type="button"
                    disabled={reviewSaving}
                    onClick={() => saveReview('submit_for_review')}
                    className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-800 disabled:opacity-50"
                  >
                    {reviewSaving ? 'Saving...' : 'Send for Review'}
                  </button>
                  {canApprove && (
                    <>
                      <button
                        type="button"
                        disabled={reviewSaving}
                        onClick={() => saveReview('activate')}
                        className="rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-800 disabled:opacity-50"
                      >
                        {reviewSaving ? 'Saving...' : 'Activate Document'}
                      </button>
                      <button
                        type="button"
                        disabled={reviewSaving}
                        onClick={() => saveReview('reject')}
                        className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-800 disabled:opacity-50"
                      >
                        {reviewSaving ? 'Saving...' : 'Reject Document'}
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 text-sm font-semibold text-slate-800">Upload history</h3>
        {files.length === 0 ? (
          <EmptyState
            icon="📂"
            title="No uploads yet"
            description="Upload your first business document to start smart document understanding and downstream pricing analysis."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs text-slate-500">
                  <th className="pb-2 font-medium">File</th>
                  <th className="pb-2 font-medium">Category</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Entities</th>
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {files.map((record) => (
                  <tr key={record.id} className="border-b border-slate-50">
                    <td className="py-2">
                      <p className="font-medium text-slate-800">{record.file_name}</p>
                      <p className="text-xs text-slate-500">{record.next_step}</p>
                    </td>
                    <td className="py-2 text-slate-600">
                      {record.upload_type.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())}
                    </td>
                    <td className="py-2">
                      <div className="flex flex-wrap gap-2">
                        <StatusChip status={record.status} />
                        {record.review_status ? (
                          <StatusChip status={record.review_status} />
                        ) : null}
                      </div>
                    </td>
                    <td className="py-2 text-slate-600">{record.extracted_entities_count ?? '-'}</td>
                    <td className="py-2 text-xs text-slate-500">
                      {record.created_at ? new Date(record.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="py-2">
                      <button
                        type="button"
                        onClick={() => void loadReview(record.id)}
                        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700"
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
