import { useCallback, useEffect, useMemo, useState, type DragEvent } from 'react';
import {
  CheckCircle2,
  Download,
  FileCheck2,
  FileJson,
  FileText,
  FileUp,
  FolderOpen,
  Plus,
  RefreshCw,
  Trash2,
  UploadCloud,
} from 'lucide-react';

import { getSession } from '../lib/auth';
import API from '../lib/api';
import { AlertBanner, EmptyState, SectionHeader, StatusChip, SummaryCard } from '../components/ui';
import { downloadJson, downloadUploadTemplate } from '../lib/downloads';

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

function titleCase(value: string) {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatDate(value: string | null) {
  if (!value) return '-';
  return new Date(value).toLocaleString();
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function safeDownloadName(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'extraction';
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

  const selectedInfo = useMemo(
    () => types.find((type) => type.type === selectedType),
    [selectedType, types],
  );

  const canApprove = role === 'admin' || role === 'approver';
  const activeCount = useMemo(() => files.filter((record) => record.status === 'active').length, [files]);
  const reviewCount = useMemo(
    () => files.filter((record) => record.status === 'draft' || record.status === 'needs_review').length,
    [files],
  );
  const entityCount = useMemo(
    () => files.reduce((sum, record) => sum + (record.extracted_entities_count ?? 0), 0),
    [files],
  );

  const refreshFiles = useCallback(async () => {
    try {
      const res = await API.get<FileRecord[]>('/upload-center/files');
      setFiles(res.data);
    } catch {
      /* keep current list */
    }
  }, []);

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
        setError('Unable to load upload center configuration.');
      }
    };
    void load();
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

  const exportReview = useCallback(async (record?: FileRecord) => {
    const fileId = record?.id ?? activeReview?.file_id;
    if (!fileId) return;
    setReviewError(null);
    try {
      const res = await API.get<UploadReviewPayload>(`/upload-center/files/${fileId}/review`);
      const fileName = `${safeDownloadName(record?.file_name ?? res.data.file_name)}-extraction.json`;
      downloadJson(fileName, res.data);
    } catch (err: any) {
      setReviewError(err?.response?.data?.detail || 'Unable to export extraction JSON.');
    }
  }, [activeReview?.file_id]);

  const validateAndSetFile = (candidate: File | null) => {
    if (!candidate) {
      setFile(null);
      return;
    }
    const ext = candidate.name.includes('.') ? `.${candidate.name.split('.').pop()?.toLowerCase()}` : '';
    const allowed = selectedInfo?.extensions ?? [];
    if (allowed.length > 0 && !allowed.includes(ext)) {
      setError(`.${ext.replace('.', '') || 'unknown'} is not valid for ${selectedInfo?.label}. Accepted: ${allowed.join(', ')}`);
      setFile(null);
      return;
    }
    setError(null);
    setUploadMessage(null);
    setFile(candidate);
  };

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
      setError(err?.response?.data?.detail || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragOver(false);
    validateAndSetFile(event.dataTransfer.files?.[0] ?? null);
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

  return (
    <div className="space-y-6">
      <SectionHeader
        kicker="File intelligence"
        icon={<FileUp className="h-5 w-5 text-indigo-500" aria-hidden="true" />}
        title="Upload Center"
        subtitle="Upload business documents, validate extracted fields, and activate trusted files for pricing workflows."
        action={
          <button
            type="button"
            onClick={() => void refreshFiles()}
            className="btn-outline inline-flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4 animate-spin-slow" aria-hidden="true" />
            Refresh
          </button>
        }
      />

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <SummaryCard 
          title="Uploads" 
          value={files.length} 
          subtitle="Files visible to your role" 
          icon={<FolderOpen className="h-4 w-4 text-indigo-500" aria-hidden="true" />} 
        />
        <SummaryCard 
          title="Needs Review" 
          value={reviewCount} 
          subtitle="Draft or review queue files" 
          variant={reviewCount > 0 ? 'warning' : 'success'} 
          icon={<FileCheck2 className="h-4 w-4 text-amber-500" aria-hidden="true" />} 
        />
        <SummaryCard 
          title="Entities Extracted" 
          value={entityCount} 
          subtitle={`${activeCount} active files`} 
          variant="info" 
          icon={<FileText className="h-4 w-4 text-sky-500" aria-hidden="true" />} 
        />
      </div>

      {error && <AlertBanner variant="danger">{error}</AlertBanner>}
      {uploadMessage && <AlertBanner variant="success" title="Upload Successful">{uploadMessage}</AlertBanner>}

      <div className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
        <aside className="space-y-6">
          {/* Document Type Selector Card */}
          <section className="glass-card rounded-2xl p-6 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 to-purple-500 opacity-60" />
            <div className="mb-4">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">1. Choose Document Type</h2>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Your role controls which file categories can be uploaded.</p>
            </div>

            {types.length === 0 ? (
              <EmptyState title="No upload categories" description="No upload categories are available for your role." />
            ) : (
              <div className="space-y-2">
                {types.map((type) => (
                  <button
                    key={type.type}
                    type="button"
                    className={`w-full rounded-xl border p-3.5 text-left transition-all duration-300 ${
                      selectedType === type.type
                        ? 'border-indigo-500/30 bg-gradient-to-r from-indigo-600/90 to-purple-600/90 text-white shadow-md shadow-indigo-600/10 scale-[1.01]'
                        : 'border-slate-200/50 bg-slate-500/5 text-slate-700 dark:border-slate-800/40 dark:text-slate-300 hover:border-indigo-500/30 hover:bg-slate-500/10'
                    }`}
                    onClick={() => {
                      setSelectedType(type.type);
                      setUploadMessage(null);
                      setError(null);
                      setFile(null);
                    }}
                  >
                    <span className="block text-sm font-bold tracking-tight">{type.label}</span>
                    <span className={`mt-1 block text-xs font-medium ${selectedType === type.type ? 'text-indigo-200' : 'text-slate-400 dark:text-slate-500'}`}>
                      {type.extensions.map(e => e.toUpperCase()).join(', ')}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </section>

          {/* Upload File Card */}
          {selectedInfo && (
            <section className="glass-card rounded-2xl p-6 shadow-xl relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-purple-500 to-pink-500 opacity-60" />
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-base font-bold text-slate-900 dark:text-white">2. Upload Source File</h2>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{selectedInfo.label}</p>
                </div>
                <button
                  type="button"
                  onClick={() => downloadUploadTemplate(selectedInfo.type, selectedInfo.label)}
                  className="btn-outline py-1.5 px-3 text-xs inline-flex items-center gap-1.5"
                >
                  <Download className="h-3.5 w-3.5" aria-hidden="true" />
                  Template
                </button>
              </div>

              <div
                className={`rounded-xl border-2 border-dashed px-5 py-8 text-center transition-all duration-300 ${
                  dragOver 
                    ? 'border-indigo-500 bg-indigo-500/10 dark:bg-indigo-500/20 shadow-inner' 
                    : 'border-slate-300 dark:border-slate-800 bg-slate-500/5 hover:border-indigo-500 dark:hover:border-indigo-500 hover:bg-slate-500/10'
                }`}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
              >
                <div className="mx-auto w-12 h-12 rounded-full bg-indigo-500/10 dark:bg-indigo-500/20 flex items-center justify-center mb-3">
                  <UploadCloud className="h-6 w-6 text-indigo-500 animate-pulse" aria-hidden="true" />
                </div>
                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  {file ? file.name : `Drop ${selectedInfo.label} here`}
                </p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 font-medium">
                  {file ? formatBytes(file.size) : `Accepted: ${selectedInfo.extensions.join(', ')}`}
                </p>
                <label className="mt-4 inline-flex cursor-pointer rounded-xl bg-slate-900 dark:bg-indigo-600 dark:hover:bg-indigo-500 hover:bg-slate-800 text-white px-4 py-2.5 text-xs font-bold transition duration-200 hover:shadow-lg hover:shadow-indigo-500/10 active:scale-[0.98]">
                  Browse files
                  <input
                    type="file"
                    className="hidden"
                    accept={selectedInfo.extensions.join(',')}
                    onChange={(event) => validateAndSetFile(event.target.files?.[0] ?? null)}
                  />
                </label>
              </div>

              <button
                type="button"
                disabled={!file || uploading}
                onClick={handleUpload}
                className="mt-4 w-full btn-primary py-3 text-sm font-bold flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Analyzing and uploading...
                  </>
                ) : (
                  <>
                    <FileCheck2 className="h-4 w-4" />
                    Upload and Analyze
                  </>
                )}
              </button>
            </section>
          )}
        </aside>

        {/* Review Panel */}
        <section className="min-w-0 glass-card rounded-2xl shadow-xl relative overflow-hidden flex flex-col">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-pink-500 via-indigo-500 to-teal-500 opacity-60" />
          
          <div className="border-b border-slate-200/50 dark:border-slate-800/40 p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">3. Review Extraction</h2>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Confirm the summary, business entities, and suggested rules before downstream pricing uses the file.
                </p>
              </div>
              {activeReview && (
                <button
                  type="button"
                  onClick={() => void exportReview()}
                  className="btn-outline inline-flex items-center gap-2 py-2 px-3 text-xs"
                >
                  <FileJson className="h-4 w-4 text-indigo-500" aria-hidden="true" />
                  Export JSON
                </button>
              )}
            </div>
          </div>

          <div className="p-6 flex-1 space-y-6">
            {reviewLoading && (
              <div className="flex flex-col items-center justify-center py-12 space-y-3">
                <RefreshCw className="h-8 w-8 text-indigo-500 animate-spin" />
                <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">Loading extraction payload...</p>
              </div>
            )}
            
            {reviewError && <AlertBanner variant="danger">{reviewError}</AlertBanner>}
            {reviewMessage && <AlertBanner variant="success">{reviewMessage}</AlertBanner>}

            {!activeReview ? (
              <div className="py-8">
                <EmptyState
                  icon={<FileText className="h-8 w-8 text-slate-400" aria-hidden="true" />}
                  title="No file selected"
                  description="Upload a document or choose a record from history to review extracted pricing intelligence."
                />
              </div>
            ) : (
              <div className="space-y-6">
                {/* File summary spotlight */}
                <div className="rounded-2xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 p-5 relative overflow-hidden">
                  <div className="absolute top-0 left-0 bottom-0 w-[4px] bg-indigo-500" />
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-bold text-slate-900 dark:text-white">{activeReview.file_name}</p>
                      <p className="mt-1.5 text-xs leading-relaxed text-slate-600 dark:text-slate-300 font-medium">
                        {activeReview.current_extraction.summary}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <StatusChip status={activeReview.status} />
                      <StatusChip status={activeReview.review_status} />
                    </div>
                  </div>
                  
                  <div className="mt-5 grid gap-4 sm:grid-cols-3">
                    <ReviewMetric label="Detected type" value={activeReview.current_extraction.detected_type} />
                    <ReviewMetric label="Confidence" value={`${(activeReview.current_extraction.confidence * 100).toFixed(0)}%`} />
                    <ReviewMetric label="Entities" value={`${activeReview.current_extraction.entities_count}`} />
                  </div>
                  
                  <p className="mt-4 text-xs text-slate-500 dark:text-slate-400 font-semibold flex items-center gap-1.5">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-500" />
                    <span>Next step:</span> 
                    <span className="text-slate-800 dark:text-slate-200 font-bold">{activeReview.next_step}</span>
                  </p>
                </div>

                {/* Extracted business entities cards */}
                {activeReview.current_extraction.entities.length > 0 && (
                  <div>
                    <p className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                      Extracted Business Entities
                    </p>
                    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                      {activeReview.current_extraction.entities.map((entity, index) => (
                        <div key={`${entity.type}-${index}`} className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-white/40 dark:bg-slate-900/40 p-4 transition-all duration-300 hover:border-indigo-500/30">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">
                            {entity.type}
                          </p>
                          <p className="mt-1 text-2xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 dark:from-white dark:to-slate-300 bg-clip-text text-transparent">
                            {entity.count}
                          </p>
                          <p className="mt-1.5 truncate text-[10px] text-slate-400 dark:text-slate-500 font-medium">
                            {entity.samples.join(', ') || 'No samples'}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Corrected fields input form */}
                {reviewDraft && (
                  <div className="space-y-6 pt-4 border-t border-slate-200/50 dark:border-slate-800/40">
                    <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                      <label className="space-y-2 text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        <span>Plain-language summary</span>
                        <textarea
                          className="input min-h-32"
                          value={reviewDraft.summary}
                          onChange={(event) =>
                            setReviewDraft((prev) => (prev ? { ...prev, summary: event.target.value } : prev))
                          }
                        />
                      </label>
                      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
                        <label className="space-y-2 text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          <span>Detected document type</span>
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
                        <label className="space-y-2 text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                          <span>Confidence score</span>
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

                    {/* Interactive entity editor */}
                    <div>
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                          Correct Business Entities
                        </p>
                        <button
                          type="button"
                          onClick={addEntityRow}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-2.5 py-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                        >
                          <Plus className="h-3.5 w-3.5" aria-hidden="true" />
                          Add Entity
                        </button>
                      </div>
                      
                      <div className="space-y-3">
                        {reviewDraft.entities.map((entity, index) => (
                          <div
                            key={`entity-row-${index}`}
                            className="grid gap-3 rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 p-3.5 md:grid-cols-[1.2fr_0.45fr_1.6fr_auto]"
                          >
                            <input
                              className="input py-2"
                              placeholder="Entity type"
                              value={entity.type}
                              onChange={(event) => updateEntity(index, 'type', event.target.value)}
                            />
                            <input
                              className="input py-2"
                              type="number"
                              min={0}
                              value={entity.count}
                              onChange={(event) => updateEntity(index, 'count', event.target.value)}
                            />
                            <input
                              className="input py-2"
                              placeholder="Samples separated by commas"
                              value={entity.samples.join(', ')}
                              onChange={(event) => updateEntity(index, 'samples', event.target.value)}
                            />
                            <button
                              type="button"
                              onClick={() => removeEntityRow(index)}
                              className="inline-flex items-center justify-center rounded-xl border border-rose-300/30 bg-rose-500/5 px-3.5 py-2 text-rose-600 hover:bg-rose-500 hover:text-white transition-all duration-200"
                              aria-label="Remove entity"
                            >
                              <Trash2 className="h-4 w-4" aria-hidden="true" />
                            </button>
                          </div>
                        ))}
                        {reviewDraft.entities.length === 0 && (
                          <p className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 p-4 text-xs font-medium text-slate-500 dark:text-slate-400 text-center">
                            No entities captured yet. Add rows if manual correction is required.
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <label className="space-y-2 text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        <span>Suggested business rules</span>
                        <textarea
                          className="input min-h-32"
                          value={reviewDraft.suggested_rules_text}
                          onChange={(event) =>
                            setReviewDraft((prev) =>
                              prev ? { ...prev, suggested_rules_text: event.target.value } : prev,
                            )
                          }
                          placeholder="One suggested rule per line"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        <span>Review notes</span>
                        <textarea
                          className="input min-h-32"
                          value={reviewDraft.review_notes}
                          onChange={(event) =>
                            setReviewDraft((prev) => (prev ? { ...prev, review_notes: event.target.value } : prev))
                          }
                          placeholder="Record corrections, assumptions, or business context"
                        />
                      </label>
                    </div>

                    <details className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 overflow-hidden transition-all duration-200">
                      <summary className="cursor-pointer text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 p-4 transition-colors select-none">
                        Source Text Preview
                      </summary>
                      <div className="p-4 border-t border-slate-200/30 dark:border-slate-800/30 bg-slate-950/40 dark:bg-slate-950/80">
                        <pre className="max-h-72 overflow-auto whitespace-pre-wrap font-mono text-[10px] leading-relaxed text-slate-600 dark:text-indigo-300/80 sidebar-scroll">
                          {activeReview.current_extraction.text_preview || 'No text preview available.'}
                        </pre>
                      </div>
                    </details>

                    {/* Action buttons */}
                    <div className="flex flex-wrap gap-2.5 border-t border-slate-200/50 dark:border-slate-800/40 pt-5">
                      <ReviewActionButton disabled={reviewSaving} onClick={() => saveReview('save_draft')}>
                        {reviewSaving ? 'Saving...' : 'Save Draft'}
                      </ReviewActionButton>
                      <ReviewActionButton
                        disabled={reviewSaving}
                        onClick={() => saveReview('confirm_and_save')}
                        variant="primary"
                      >
                        {reviewSaving ? 'Saving...' : 'Confirm and Save'}
                      </ReviewActionButton>
                      <ReviewActionButton
                        disabled={reviewSaving}
                        onClick={() => saveReview('submit_for_review')}
                        variant="warning"
                      >
                        {reviewSaving ? 'Saving...' : 'Send for Review'}
                      </ReviewActionButton>
                      {canApprove && (
                        <>
                          <ReviewActionButton
                            disabled={reviewSaving}
                            onClick={() => saveReview('activate')}
                            variant="success"
                          >
                            {reviewSaving ? 'Saving...' : 'Activate'}
                          </ReviewActionButton>
                          <ReviewActionButton
                            disabled={reviewSaving}
                            onClick={() => saveReview('reject')}
                            variant="danger"
                          >
                            {reviewSaving ? 'Saving...' : 'Reject'}
                          </ReviewActionButton>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      </div>

      {/* History Card */}
      <section className="glass-card rounded-2xl shadow-xl overflow-hidden relative">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-teal-500 to-indigo-500 opacity-60" />
        <div className="p-6 border-b border-slate-200/50 dark:border-slate-800/40">
          <h2 className="text-base font-bold text-slate-900 dark:text-white">Upload History</h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Review previous files, continue extraction edits, or export the audit payload.</p>
        </div>

        {files.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={<FolderOpen className="h-8 w-8 text-slate-400" aria-hidden="true" />}
              title="No uploads yet"
              description="Upload your first business document to start document understanding and downstream pricing analysis."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <th className="px-6 py-4">File</th>
                  <th className="px-6 py-4">Category</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Entities</th>
                  <th className="px-6 py-4">Uploaded</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {files.map((record) => (
                  <tr key={record.id} className="border-b border-slate-100/50 dark:border-slate-800/30 hover:bg-slate-500/5 transition-colors last:border-0">
                    <td className="px-6 py-4">
                      <p className="font-bold text-slate-800 dark:text-slate-200">{record.file_name}</p>
                      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 font-medium">{record.next_step}</p>
                    </td>
                    <td className="px-6 py-4 text-xs font-semibold text-slate-600 dark:text-slate-300">
                      {titleCase(record.upload_type)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1.5">
                        <StatusChip status={record.status} />
                        {record.review_status ? <StatusChip status={record.review_status} /> : null}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs font-bold text-slate-700 dark:text-slate-300">
                      {record.extracted_entities_count ?? '-'}
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-500 dark:text-slate-400">
                      {formatDate(record.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => void loadReview(record.id)}
                          className="btn-outline py-1.5 px-3 text-xs"
                        >
                          Review
                        </button>
                        <button
                          type="button"
                          onClick={() => void exportReview(record)}
                          className="btn-outline inline-flex items-center gap-1.5 py-1.5 px-3 text-xs"
                        >
                          <Download className="h-3.5 w-3.5" aria-hidden="true" />
                          Export
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <AlertBanner variant="tip" title="Governance Workflow">
        Save draft for incomplete extraction, confirm and save when the parsed content is correct, send for review when
        governance approval is needed, and activate only when the file should influence pricing decisions.
      </AlertBanner>
    </div>
  );
}

function ReviewMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-white/40 dark:bg-slate-900/40 p-3.5">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-1 truncate text-xs font-bold text-slate-800 dark:text-slate-100">{value}</p>
    </div>
  );
}

function ReviewActionButton({
  children,
  onClick,
  disabled,
  variant = 'default',
}: {
  children: string;
  onClick: () => void;
  disabled?: boolean;
  variant?: 'default' | 'primary' | 'warning' | 'success' | 'danger';
}) {
  const classes = {
    default: 'border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60',
    primary: 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-600/10 hover:from-indigo-50 hover:to-violet-500 hover:shadow-lg active:scale-[0.98]',
    warning: 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md shadow-amber-500/10 hover:from-amber-400 hover:to-orange-400 hover:shadow-lg active:scale-[0.98]',
    success: 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md shadow-emerald-600/10 hover:from-emerald-500 hover:to-teal-500 hover:shadow-lg active:scale-[0.98]',
    danger: 'bg-gradient-to-r from-rose-600 to-red-600 text-white shadow-md shadow-rose-600/10 hover:from-rose-500 hover:to-red-500 hover:shadow-lg active:scale-[0.98]',
  };

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-xs font-bold transition-all duration-200 disabled:opacity-40 disabled:pointer-events-none ${classes[variant]}`}
    >
      {variant === 'success' ? <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}
