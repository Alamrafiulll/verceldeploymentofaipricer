import { useMemo, useState, type Dispatch, type ReactNode, type SetStateAction } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  ClipboardList,
  DatabaseZap,
  FileSearch,
  Gauge,
  History,
  KeyRound,
  ListChecks,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal,
  Trash2,
  UserPlus,
  Users,
} from 'lucide-react';

import AdminRulesEditor from '../components/AdminRulesEditor';
import AuditLogTable from '../components/AuditLogTable';
import RoleFileUploadPanel from '../components/RoleFileUploadPanel';
import { AlertBanner, EmptyState, SectionHeader, StatusChip, SummaryCard } from '../components/ui';
import api from '../lib/api';
import { getSession } from '../lib/auth';
import type {
  AIRecommendationTrace,
  AdminUser,
  AuditLog,
  DataQuality,
  GovernanceSummary,
  ModelRun,
  ReviewQueueItem,
  Role,
  Rule,
  UploadType,
  UserAccountStatus,
} from '../types/api';

type AdminView = 'control' | 'rules-files' | 'people' | 'observability';

const moneyFormatter = new Intl.NumberFormat('en-MY', {
  style: 'currency',
  currency: 'MYR',
  maximumFractionDigits: 2,
});

const ADMIN_UPLOAD_TYPES: UploadType[] = [
  'user_role_config',
  'pricing_policy',
  'audit_log_archive',
  'model_configuration',
  'rule_mapping_template',
  'campaign_memo',
  'trading_terms',
  'rebate_agreement',
  'contract_pricing',
  'margin_target_sheet',
];

const WORKSTREAMS: Array<{
  id: AdminView;
  label: string;
  description: string;
  icon: ReactNode;
}> = [
  {
    id: 'control',
    label: 'Control Center',
    description: 'Health, queues, and priorities',
    icon: <Gauge className="h-4 w-4" aria-hidden="true" />,
  },
  {
    id: 'rules-files',
    label: 'Rules & Files',
    description: 'Guardrails and document governance',
    icon: <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />,
  },
  {
    id: 'people',
    label: 'People',
    description: 'Employee access and passwords',
    icon: <Users className="h-4 w-4" aria-hidden="true" />,
  },
  {
    id: 'observability',
    label: 'Observability',
    description: 'Model runs, AI trace, and audit',
    icon: <Activity className="h-4 w-4" aria-hidden="true" />,
  },
];

const ROLE_OPTIONS: Role[] = ['sales', 'approver', 'executive', 'admin'];
const STATUS_OPTIONS: UserAccountStatus[] = ['active', 'inactive'];

const money = (value?: number | null) =>
  value === null || value === undefined ? '-' : moneyFormatter.format(value);

const label = (value?: string | null) =>
  value ? value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()) : '-';

const formatDate = (value?: string | null) => (value ? new Date(value).toLocaleString() : '-');

const formatPercent = (value?: number | null) =>
  value === null || value === undefined ? '-' : `${(value * 100).toFixed(1)}%`;

function isSuccessfulModelRun(status: string) {
  const normalized = status.toLowerCase();
  return normalized === 'success' || normalized === 'succeeded' || normalized === 'completed';
}

function toErrorMessage(error: any, fallback: string): string {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first?.loc && first?.msg) {
      const field = String(first.loc[first.loc.length - 1] ?? 'field');
      return `${field}: ${first.msg}`;
    }
    if (first?.msg) return String(first.msg);
  }
  return fallback;
}

export default function AdminPage() {
  const queryClient = useQueryClient();
  const currentUserId = getSession()?.user.id ?? null;
  const [activeView, setActiveView] = useState<AdminView>('control');
  const [userForm, setUserForm] = useState({
    name: '',
    email: '',
    password: '123456',
    role: 'sales' as Role,
    account_status: 'active' as UserAccountStatus,
  });
  const [status, setStatus] = useState('');
  const [resetPasswordByUser, setResetPasswordByUser] = useState<Record<string, string>>({});

  const rules = useQuery({
    queryKey: ['admin', 'rules'],
    queryFn: async () => (await api.get<Rule[]>('/admin/rules')).data,
  });
  const logs = useQuery({
    queryKey: ['admin', 'audit-logs'],
    queryFn: async () => (await api.get<AuditLog[]>('/admin/audit-logs')).data,
  });
  const modelRuns = useQuery({
    queryKey: ['admin', 'model-runs'],
    queryFn: async () => (await api.get<ModelRun[]>('/admin/model-runs')).data,
  });
  const users = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: async () => (await api.get<AdminUser[]>('/admin/users')).data,
  });
  const aiRecommendations = useQuery({
    queryKey: ['admin', 'ai-recommendations'],
    queryFn: async () => (await api.get<AIRecommendationTrace[]>('/admin/ai-recommendations')).data,
  });
  const governanceSummary = useQuery({
    queryKey: ['admin', 'governance-summary'],
    queryFn: async () => (await api.get<GovernanceSummary>('/admin/governance-summary')).data,
  });
  const reviewQueue = useQuery({
    queryKey: ['admin', 'document-review-queue'],
    queryFn: async () => (await api.get<ReviewQueueItem[]>('/admin/document-review-queue')).data,
  });
  const dataQuality = useQuery({
    queryKey: ['admin', 'data-quality'],
    queryFn: async () => (await api.get<DataQuality>('/admin/data-quality')).data,
  });

  const saveRule = useMutation({
    mutationFn: async (payload: {
      channel: string;
      category: string;
      margin_floor_percent: number;
      max_discount_percent: number;
      approval_required_below_margin_buffer: number;
    }) => api.post('/admin/rules', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'rules'] });
      setStatus('Pricing guardrail saved.');
    },
    onError: () => setStatus('Failed to save pricing guardrail.'),
  });

  const createUser = useMutation({
    mutationFn: async () => api.post('/admin/users', userForm),
    onSuccess: () => {
      setStatus('Employee created.');
      setUserForm((prev) => ({ ...prev, name: '', email: '' }));
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'audit-logs'] });
    },
    onError: (error: any) => setStatus(toErrorMessage(error, 'User creation failed.')),
  });

  const updateUserStatus = useMutation({
    mutationFn: async (payload: { userId: string; account_status: UserAccountStatus }) =>
      api.patch(`/admin/users/${payload.userId}/status`, { account_status: payload.account_status }),
    onSuccess: () => {
      setStatus('Employee status updated.');
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'audit-logs'] });
    },
    onError: () => setStatus('Failed to update employee status.'),
  });

  const deleteUser = useMutation({
    mutationFn: async (userId: string) => api.delete(`/admin/users/${userId}`),
    onSuccess: () => {
      setStatus('Employee deleted.');
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'audit-logs'] });
    },
    onError: (error: any) => setStatus(error?.response?.data?.detail ?? 'Failed to delete employee.'),
  });

  const resetPassword = useMutation({
    mutationFn: async (payload: { userId: string; newPassword?: string }) =>
      api.post<{ user_id: string; email: string; generated_password: string }>(
        `/admin/users/${payload.userId}/reset-password`,
        {
          new_password: payload.newPassword?.trim() || null,
        },
      ),
    onSuccess: (response) => {
      setStatus(`Password reset for ${response.data.email}. Visible password: ${response.data.generated_password}`);
      queryClient.invalidateQueries({ queryKey: ['admin', 'audit-logs'] });
    },
    onError: () => setStatus('Failed to reset password.'),
  });

  const canCreateUser = userForm.name.trim() && userForm.email.trim() && userForm.password.length >= 6;
  const governance = governanceSummary.data;
  const quality = dataQuality.data;
  const ruleRows = rules.data ?? [];
  const logRows = logs.data ?? [];
  const modelRunRows = modelRuns.data ?? [];
  const userRows = users.data ?? [];
  const recommendationRows = aiRecommendations.data ?? [];
  const queueRows = reviewQueue.data ?? [];

  const totalIssues = useMemo(() => {
    if (!governance && !quality) return 0;
    return (
      (governance?.pending_upload_reviews ?? 0) +
      (governance?.pending_policy_reviews ?? 0) +
      (governance?.model_run_failures ?? 0) +
      (governance?.unmatched_competitor_records ?? 0) +
      (quality?.upload_parse_failures ?? 0) +
      (quality?.uploads_needing_review ?? 0) +
      (quality?.reviews_pending_activation ?? 0) +
      (quality?.recommendations_with_fallback ?? 0)
    );
  }, [governance, quality]);

  const attentionItems = useMemo(
    () => [
      {
        label: 'Upload Reviews',
        value: governance?.pending_upload_reviews ?? 0,
        detail: 'Files waiting for governance review',
        view: 'rules-files' as AdminView,
        icon: <FileSearch className="h-4 w-4" aria-hidden="true" />,
      },
      {
        label: 'Policy Reviews',
        value: governance?.pending_policy_reviews ?? 0,
        detail: 'Draft policies pending activation',
        view: 'rules-files' as AdminView,
        icon: <ClipboardList className="h-4 w-4" aria-hidden="true" />,
      },
      {
        label: 'Model Failures',
        value: governance?.model_run_failures ?? 0,
        detail: 'Model runs needing investigation',
        view: 'observability' as AdminView,
        icon: <BrainCircuit className="h-4 w-4" aria-hidden="true" />,
      },
      {
        label: 'Unmatched Competitors',
        value: governance?.unmatched_competitor_records ?? 0,
        detail: 'Market rows that need product mapping',
        view: 'rules-files' as AdminView,
        icon: <DatabaseZap className="h-4 w-4" aria-hidden="true" />,
      },
    ],
    [governance],
  );

  const qualitySignals = useMemo(
    () => [
      {
        label: 'Parse failures',
        value: quality?.upload_parse_failures ?? 0,
        variant: (quality?.upload_parse_failures ?? 0) > 0 ? 'warning' : 'success',
      },
      {
        label: 'Needs review',
        value: quality?.uploads_needing_review ?? 0,
        variant: (quality?.uploads_needing_review ?? 0) > 0 ? 'warning' : 'success',
      },
      {
        label: 'Pending activation',
        value: quality?.reviews_pending_activation ?? 0,
        variant: (quality?.reviews_pending_activation ?? 0) > 0 ? 'warning' : 'success',
      },
      {
        label: 'Fallback recommendations',
        value: quality?.recommendations_with_fallback ?? 0,
        variant: (quality?.recommendations_with_fallback ?? 0) > 0 ? 'warning' : 'success',
      },
    ] as const,
    [quality],
  );

  const refreshAdmin = () => {
    queryClient.invalidateQueries({ queryKey: ['admin'] });
    queryClient.invalidateQueries({ queryKey: ['uploads'] });
    setStatus('Admin data refreshed.');
  };

  const statusIsError = status.toLowerCase().includes('failed') || status.toLowerCase().includes('error');

  return (
    <div className="space-y-6">
      <SectionHeader
        kicker="Admin control center"
        icon={<ShieldCheck className="h-5 w-5" aria-hidden="true" />}
        title="Governance Operations"
        subtitle="Control pricing rules, trusted files, employee access, model observability, and audit traceability."
        badge={totalIssues > 0 ? `${totalIssues} open signals` : 'Healthy'}
        action={
          <button
            type="button"
            onClick={refreshAdmin}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Refresh
          </button>
        }
      />

      {status ? <AlertBanner variant={statusIsError ? 'danger' : 'success'}>{status}</AlertBanner> : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_380px]">
        <section className="rounded-lg border border-slate-900 bg-slate-950 p-5 text-white shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Governance State</p>
              <h2 className="mt-2 text-2xl font-semibold">{totalIssues > 0 ? 'Attention Required' : 'Controlled'}</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
                Admins own the control layer that keeps pricing recommendations explainable, governed, and auditable.
              </p>
            </div>
            <span className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-white/10 text-white">
              {totalIssues > 0 ? (
                <AlertTriangle className="h-6 w-6" aria-hidden="true" />
              ) : (
                <CheckCircle2 className="h-6 w-6" aria-hidden="true" />
              )}
            </span>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <DarkMetric label="Open Signals" value={totalIssues.toString()} />
            <DarkMetric label="Rules" value={ruleRows.length.toString()} />
            <DarkMetric label="Employees" value={userRows.length.toString()} />
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-slate-500" aria-hidden="true" />
            <h2 className="text-base font-semibold text-slate-950">Data Quality Pulse</h2>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {qualitySignals.map((signal) => (
              <MiniSignal key={signal.label} label={signal.label} value={signal.value} variant={signal.variant} />
            ))}
          </div>
          <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Clause Confidence</p>
            <p className="mt-1 text-2xl font-semibold text-slate-950">
              {quality ? quality.average_clause_confidence.toFixed(2) : '-'}
            </p>
          </div>
        </section>
      </div>

      {governance ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-5">
          <SummaryCard
            title="Upload Reviews"
            value={governance.pending_upload_reviews}
            subtitle="Files waiting for review"
            variant={governance.pending_upload_reviews > 0 ? 'warning' : 'success'}
            icon={<FileSearch className="h-4 w-4" aria-hidden="true" />}
            onClick={() => setActiveView('rules-files')}
          />
          <SummaryCard
            title="Policy Reviews"
            value={governance.pending_policy_reviews}
            subtitle="Draft policies pending activation"
            variant={governance.pending_policy_reviews > 0 ? 'warning' : 'success'}
            icon={<ClipboardList className="h-4 w-4" aria-hidden="true" />}
            onClick={() => setActiveView('rules-files')}
          />
          <SummaryCard
            title="AI Trace Count"
            value={governance.ai_trace_count}
            subtitle="Stored recommendation traces"
            icon={<BrainCircuit className="h-4 w-4" aria-hidden="true" />}
            onClick={() => setActiveView('observability')}
          />
          <SummaryCard
            title="Model Failures"
            value={governance.model_run_failures}
            subtitle="Runs needing investigation"
            variant={governance.model_run_failures > 0 ? 'warning' : 'success'}
            icon={<Activity className="h-4 w-4" aria-hidden="true" />}
            onClick={() => setActiveView('observability')}
          />
          <SummaryCard
            title="Unmatched Competitors"
            value={governance.unmatched_competitor_records}
            subtitle="Rows needing product matching"
            variant={governance.unmatched_competitor_records > 0 ? 'warning' : 'success'}
            icon={<DatabaseZap className="h-4 w-4" aria-hidden="true" />}
            onClick={() => setActiveView('rules-files')}
          />
        </div>
      ) : (
        <LoadingPanel label="Loading governance summary..." />
      )}

      <WorkstreamNav activeView={activeView} onChange={setActiveView} />

      {activeView === 'control' ? (
        <ControlCenter
          attentionItems={attentionItems}
          quality={quality}
          reviewQueue={queueRows}
          onOpenView={setActiveView}
        />
      ) : null}

      {activeView === 'rules-files' ? (
        <div className="space-y-5">
          {rules.data ? (
            <AdminRulesEditor
              rules={rules.data}
              onSave={async (payload) => {
                await saveRule.mutateAsync(payload);
              }}
              loading={saveRule.isPending}
            />
          ) : (
            <LoadingPanel label="Loading pricing guardrails..." />
          )}

          <RoleFileUploadPanel
            title="Governance Uploads"
            description="Policy documents, campaign memos, trading terms, contracts, margin targets, and model configuration files."
            allowedTypes={ADMIN_UPLOAD_TYPES}
            showAll
            allowDelete
          />

          <ReviewQueueSection rows={queueRows} loading={reviewQueue.isLoading} />
        </div>
      ) : null}

      {activeView === 'people' ? (
        <PeopleWorkspace
          users={userRows}
          loading={users.isLoading}
          currentUserId={currentUserId}
          userForm={userForm}
          setUserForm={setUserForm}
          canCreateUser={Boolean(canCreateUser)}
          createPending={createUser.isPending}
          onCreate={() => createUser.mutate()}
          updatePending={updateUserStatus.isPending}
          onUpdateStatus={(userId, account_status) => updateUserStatus.mutate({ userId, account_status })}
          resetPasswordByUser={resetPasswordByUser}
          setResetPasswordByUser={setResetPasswordByUser}
          resetPending={resetPassword.isPending}
          onReset={(userId, newPassword) => resetPassword.mutate({ userId, newPassword })}
          deletePending={deleteUser.isPending}
          onDelete={(userId) => deleteUser.mutate(userId)}
        />
      ) : null}

      {activeView === 'observability' ? (
        <div className="space-y-5">
          <ObservabilityOverview
            modelRuns={modelRunRows}
            aiRecommendations={recommendationRows}
            auditLogs={logRows}
            loading={modelRuns.isLoading || aiRecommendations.isLoading || logs.isLoading}
          />
          <ModelRunsTable rows={modelRunRows} loading={modelRuns.isLoading} />
          <AITraceTable rows={recommendationRows} loading={aiRecommendations.isLoading} />
          <AuditLogTable rows={logRows} />
        </div>
      ) : null}
    </div>
  );
}

function WorkstreamNav({ activeView, onChange }: { activeView: AdminView; onChange: (view: AdminView) => void }) {
  return (
    <div className="grid gap-2 rounded-lg border border-slate-200 bg-white p-2 shadow-sm md:grid-cols-4">
      {WORKSTREAMS.map((item) => {
        const active = activeView === item.id;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onChange(item.id)}
            className={`rounded-lg p-3 text-left transition ${
              active ? 'bg-slate-950 text-white shadow-sm' : 'text-slate-700 hover:bg-slate-50'
            }`}
          >
            <span className="flex items-center gap-2 text-sm font-semibold">
              {item.icon}
              {item.label}
            </span>
            <span className={`mt-1 block text-xs ${active ? 'text-slate-300' : 'text-slate-500'}`}>
              {item.description}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function ControlCenter({
  attentionItems,
  quality,
  reviewQueue,
  onOpenView,
}: {
  attentionItems: Array<{
    label: string;
    value: number;
    detail: string;
    view: AdminView;
    icon: ReactNode;
  }>;
  quality?: DataQuality;
  reviewQueue: ReviewQueueItem[];
  onOpenView: (view: AdminView) => void;
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_390px]">
      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 p-5">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
              <ListChecks className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Admin Priority Queue</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                The items below are the fastest way to decide what needs governance attention.
              </p>
            </div>
          </div>
        </div>
        <div className="divide-y divide-slate-100">
          {attentionItems.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => onOpenView(item.view)}
              className="flex w-full items-center justify-between gap-4 p-5 text-left transition hover:bg-slate-50"
            >
              <span className="flex min-w-0 items-start gap-3">
                <span
                  className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${
                    item.value > 0
                      ? 'border-amber-200 bg-amber-50 text-amber-700'
                      : 'border-emerald-200 bg-emerald-50 text-emerald-700'
                  }`}
                >
                  {item.icon}
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold text-slate-950">{item.label}</span>
                  <span className="mt-1 block text-sm text-slate-600">{item.detail}</span>
                </span>
              </span>
              <span className="flex items-center gap-3">
                <span className={`text-2xl font-semibold ${item.value > 0 ? 'text-amber-700' : 'text-emerald-700'}`}>
                  {item.value}
                </span>
                <ArrowRight className="h-4 w-4 text-slate-400" aria-hidden="true" />
              </span>
            </button>
          ))}
        </div>
      </section>

      <div className="space-y-5">
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-slate-500" aria-hidden="true" />
            <h2 className="text-base font-semibold text-slate-950">Control Readiness</h2>
          </div>
          <div className="mt-4 space-y-3">
            <ReadinessRow label="Clause extraction confidence" value={quality?.average_clause_confidence ?? null} />
            <ReadinessRow
              label="Policy review backlog"
              value={quality ? quality.reviews_pending_activation === 0 ? 1 : 0.35 : null}
            />
            <ReadinessRow
              label="Model fallback pressure"
              value={quality ? quality.recommendations_with_fallback === 0 ? 1 : 0.45 : null}
            />
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <FileSearch className="h-4 w-4 text-slate-500" aria-hidden="true" />
            <h2 className="text-base font-semibold text-slate-950">Recent Review Items</h2>
          </div>
          {reviewQueue.length === 0 ? (
            <p className="mt-3 text-sm leading-6 text-slate-600">No documents are waiting in the review queue.</p>
          ) : (
            <div className="mt-3 space-y-2">
              {reviewQueue.slice(0, 4).map((item) => (
                <button
                  key={`${item.item_type}-${item.item_id}`}
                  type="button"
                  onClick={() => onOpenView('rules-files')}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 p-3 text-left hover:bg-white"
                >
                  <span className="block truncate text-sm font-semibold text-slate-900">{item.label}</span>
                  <span className="mt-1 flex items-center justify-between gap-3">
                    <span className="text-xs text-slate-500">{label(item.item_type)}</span>
                    <StatusChip status={item.status} />
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function PeopleWorkspace({
  users,
  loading,
  currentUserId,
  userForm,
  setUserForm,
  canCreateUser,
  createPending,
  onCreate,
  updatePending,
  onUpdateStatus,
  resetPasswordByUser,
  setResetPasswordByUser,
  resetPending,
  onReset,
  deletePending,
  onDelete,
}: {
  users: AdminUser[];
  loading: boolean;
  currentUserId: string | null;
  userForm: {
    name: string;
    email: string;
    password: string;
    role: Role;
    account_status: UserAccountStatus;
  };
  setUserForm: Dispatch<
    SetStateAction<{
      name: string;
      email: string;
      password: string;
      role: Role;
      account_status: UserAccountStatus;
    }>
  >;
  canCreateUser: boolean;
  createPending: boolean;
  onCreate: () => void;
  updatePending: boolean;
  onUpdateStatus: (userId: string, status: UserAccountStatus) => void;
  resetPasswordByUser: Record<string, string>;
  setResetPasswordByUser: Dispatch<SetStateAction<Record<string, string>>>;
  resetPending: boolean;
  onReset: (userId: string, newPassword?: string) => void;
  deletePending: boolean;
  onDelete: (userId: string) => void;
}) {
  const activeUsers = users.filter((user) => user.account_status === 'active').length;
  const adminUsers = users.filter((user) => user.role === 'admin').length;

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard title="Employees" value={users.length} subtitle="Total user accounts" icon={<Users className="h-4 w-4" aria-hidden="true" />} />
        <SummaryCard title="Active Accounts" value={activeUsers} subtitle="Can access the app" variant="success" icon={<CheckCircle2 className="h-4 w-4" aria-hidden="true" />} />
        <SummaryCard title="Admins" value={adminUsers} subtitle="Governance operators" variant="info" icon={<ShieldCheck className="h-4 w-4" aria-hidden="true" />} />
      </div>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 p-5">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
              <UserPlus className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Create Employee</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Add internal users with the correct workflow role and account state.
              </p>
            </div>
          </div>
        </div>
        <div className="grid gap-4 p-5 lg:grid-cols-[1fr_1fr_180px_160px_160px_auto]">
          <LabeledInput
            label="Name"
            value={userForm.name}
            onChange={(value) => setUserForm((prev) => ({ ...prev, name: value }))}
            placeholder="Employee name"
          />
          <LabeledInput
            label="Email"
            value={userForm.email}
            onChange={(value) => setUserForm((prev) => ({ ...prev, email: value }))}
            placeholder="name@company.com"
          />
          <LabeledInput
            label="Password"
            type="password"
            value={userForm.password}
            onChange={(value) => setUserForm((prev) => ({ ...prev, password: value }))}
            placeholder="Minimum 6 characters"
          />
          <label className="block text-sm">
            <span className="font-medium text-slate-700">Role</span>
            <select
              className="input mt-1"
              value={userForm.role}
              onChange={(event) => setUserForm((prev) => ({ ...prev, role: event.target.value as Role }))}
            >
              {ROLE_OPTIONS.map((role) => (
                <option key={role} value={role}>
                  {label(role)}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="font-medium text-slate-700">Status</span>
            <select
              className="input mt-1"
              value={userForm.account_status}
              onChange={(event) =>
                setUserForm((prev) => ({ ...prev, account_status: event.target.value as UserAccountStatus }))
              }
            >
              {STATUS_OPTIONS.map((accountStatus) => (
                <option key={accountStatus} value={accountStatus}>
                  {label(accountStatus)}
                </option>
              ))}
            </select>
          </label>
          <div className="flex items-end">
            <button
              type="button"
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
              disabled={createPending || !canCreateUser}
              onClick={onCreate}
            >
              <UserPlus className="h-4 w-4" aria-hidden="true" />
              {createPending ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
                <Users className="h-5 w-5" aria-hidden="true" />
              </span>
              <div>
                <h2 className="text-lg font-semibold text-slate-950">Employee Directory</h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Manage account status, password resets, and access removal.
                </p>
              </div>
            </div>
            <StatusChip status={`${users.length} users`} variant="info" size="md" />
          </div>
        </div>

        {loading ? <LoadingPanel label="Loading employees..." /> : null}

        {!loading && users.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={<Users className="h-6 w-6" aria-hidden="true" />}
              title="No employees"
              description="Create the first employee account to start role-based access."
            />
          </div>
        ) : null}

        {!loading && users.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1180px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                  <th className="px-5 py-3">Employee</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Created</th>
                  <th className="px-5 py-3">Reset Password</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => {
                  const isSelf = user.id === currentUserId;
                  const resetValue = resetPasswordByUser[user.id] ?? '';
                  return (
                    <tr key={user.id} className="border-b border-slate-100 align-top last:border-0">
                      <td className="px-5 py-4">
                        <p className="font-semibold text-slate-900">{user.name}</p>
                        <p className="mt-1 text-sm text-slate-600">{user.email}</p>
                      </td>
                      <td className="px-5 py-4">
                        <StatusChip
                          status={user.role}
                          variant={user.role === 'admin' ? 'danger' : user.role === 'executive' ? 'info' : 'success'}
                        />
                      </td>
                      <td className="px-5 py-4">
                        <select
                          className="input min-w-[140px]"
                          value={user.account_status}
                          disabled={isSelf || updatePending}
                          onChange={(event) => onUpdateStatus(user.id, event.target.value as UserAccountStatus)}
                        >
                          {STATUS_OPTIONS.map((accountStatus) => (
                            <option key={accountStatus} value={accountStatus}>
                              {label(accountStatus)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-5 py-4 text-slate-600">{formatDate(user.created_at)}</td>
                      <td className="px-5 py-4">
                        <div className="flex min-w-[300px] gap-2">
                          <input
                            className="input"
                            placeholder="New password"
                            type="password"
                            value={resetValue}
                            onChange={(event) =>
                              setResetPasswordByUser((prev) => ({ ...prev, [user.id]: event.target.value }))
                            }
                          />
                          <button
                            type="button"
                            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                            disabled={resetPending || isSelf || !resetValue.trim()}
                            onClick={() => onReset(user.id, resetValue)}
                          >
                            <KeyRound className="h-3.5 w-3.5" aria-hidden="true" />
                            {isSelf ? 'Self' : 'Reset'}
                          </button>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button
                          type="button"
                          className="inline-flex items-center gap-1.5 rounded-lg border border-rose-300 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-50 disabled:opacity-50"
                          disabled={deletePending || isSelf}
                          onClick={() => onDelete(user.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}

function ReviewQueueSection({ rows, loading }: { rows: ReviewQueueItem[]; loading: boolean }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
              <FileSearch className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Document Review Queue</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Review uploaded policies, pricebooks, campaigns, contracts, and extracted document controls.
              </p>
            </div>
          </div>
          <StatusChip status={`${rows.length} items`} variant={rows.length > 0 ? 'warning' : 'success'} size="md" />
        </div>
      </div>

      {loading ? <LoadingPanel label="Loading review queue..." /> : null}

      {!loading && rows.length === 0 ? (
        <div className="p-5">
          <EmptyState
            icon={<FileSearch className="h-6 w-6" aria-hidden="true" />}
            title="Review queue is clear"
            description="New governance documents will appear here after upload or extraction review."
          />
        </div>
      ) : null}

      {!loading && rows.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[920px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-5 py-3">Type</th>
                <th className="px-5 py-3">Label</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Source Reference</th>
                <th className="px-5 py-3">Next Step</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => (
                <tr key={`${item.item_type}-${item.item_id}`} className="border-b border-slate-100 last:border-0">
                  <td className="px-5 py-3 font-semibold text-slate-900">{label(item.item_type)}</td>
                  <td className="px-5 py-3 text-slate-700">{item.label}</td>
                  <td className="px-5 py-3">
                    <StatusChip status={item.status} />
                  </td>
                  <td className="px-5 py-3 text-slate-600">{item.source_reference ?? '-'}</td>
                  <td className="px-5 py-3 text-slate-600">{item.next_step ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function ObservabilityOverview({
  modelRuns,
  aiRecommendations,
  auditLogs,
  loading,
}: {
  modelRuns: ModelRun[];
  aiRecommendations: AIRecommendationTrace[];
  auditLogs: AuditLog[];
  loading: boolean;
}) {
  const failureRuns = modelRuns.filter((run) => !isSuccessfulModelRun(run.status)).length;
  const fallbackRuns = modelRuns.filter((run) => run.fallback_used).length;

  if (loading) {
    return <LoadingPanel label="Loading observability signals..." />;
  }

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <SummaryCard
        title="Model Runs"
        value={modelRuns.length}
        subtitle="Recorded model executions"
        icon={<Activity className="h-4 w-4" aria-hidden="true" />}
      />
      <SummaryCard
        title="Failures"
        value={failureRuns}
        subtitle="Non-success model runs"
        variant={failureRuns > 0 ? 'warning' : 'success'}
        icon={<AlertTriangle className="h-4 w-4" aria-hidden="true" />}
      />
      <SummaryCard
        title="Fallback Used"
        value={fallbackRuns}
        subtitle="Runs using fallback logic"
        variant={fallbackRuns > 0 ? 'warning' : 'success'}
        icon={<BrainCircuit className="h-4 w-4" aria-hidden="true" />}
      />
      <SummaryCard
        title="Audit Events"
        value={auditLogs.length}
        subtitle={`${aiRecommendations.length} AI traces`}
        icon={<History className="h-4 w-4" aria-hidden="true" />}
      />
    </div>
  );
}

function ModelRunsTable({ rows, loading }: { rows: ModelRun[]; loading: boolean }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
              <Activity className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Model Runs</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Model execution status, provider, fallback usage, latency, and linked quote references.
              </p>
            </div>
          </div>
          <StatusChip status={`${rows.length} runs`} variant="info" size="md" />
        </div>
      </div>

      {loading ? <LoadingPanel label="Loading model runs..." /> : null}

      {!loading && rows.length === 0 ? (
        <div className="p-5">
          <EmptyState
            icon={<Activity className="h-6 w-6" aria-hidden="true" />}
            title="No model runs"
            description="Pricing recommendations will create model run records."
          />
        </div>
      ) : null}

      {!loading && rows.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-5 py-3">Run</th>
                <th className="px-5 py-3">Provider</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Fallback</th>
                <th className="px-5 py-3">Latency</th>
                <th className="px-5 py-3">Quote</th>
                <th className="px-5 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((run) => (
                <tr key={run.id} className="border-b border-slate-100 last:border-0">
                  <td className="px-5 py-3">
                    <p className="font-semibold text-slate-900">{label(run.run_type)}</p>
                    <p className="mt-1 text-xs text-slate-500">{run.model_version ?? run.model_name}</p>
                  </td>
                  <td className="px-5 py-3 text-slate-600">{run.model_provider ?? run.model_name}</td>
              <td className="px-5 py-3">
                    <StatusChip status={run.status} variant={isSuccessfulModelRun(run.status) ? 'success' : 'warning'} />
                  </td>
                  <td className="px-5 py-3">
                    <StatusChip status={run.fallback_used ? 'yes' : 'no'} variant={run.fallback_used ? 'warning' : 'success'} />
                  </td>
                  <td className="px-5 py-3 text-slate-600">{run.latency_ms ? `${run.latency_ms} ms` : '-'}</td>
                  <td className="px-5 py-3 font-mono text-xs text-slate-600">
                    {run.related_quote_id ? run.related_quote_id.slice(0, 8) : '-'}
                  </td>
                  <td className="px-5 py-3 text-slate-600">{formatDate(run.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function AITraceTable({ rows, loading }: { rows: AIRecommendationTrace[]; loading: boolean }) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700">
              <BrainCircuit className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">AI Decision Traceability</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Recommendation price range, confidence, risk, value positioning, and approval state.
              </p>
            </div>
          </div>
          <StatusChip status={`${rows.length} traces`} variant="info" size="md" />
        </div>
      </div>

      {loading ? <LoadingPanel label="Loading AI traces..." /> : null}

      {!loading && rows.length === 0 ? (
        <div className="p-5">
          <EmptyState
            icon={<BrainCircuit className="h-6 w-6" aria-hidden="true" />}
            title="No AI traces"
            description="AI recommendation trace records will appear after pricing requests."
          />
        </div>
      ) : null}

      {!loading && rows.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1040px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-5 py-3">Product</th>
                <th className="px-5 py-3">Recommended Range</th>
                <th className="px-5 py-3">Confidence</th>
                <th className="px-5 py-3">Risk</th>
                <th className="px-5 py-3">Value Position</th>
                <th className="px-5 py-3">Approval</th>
                <th className="px-5 py-3">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const riskVariant = row.risk_level
                  ? row.risk_level === 'high'
                    ? 'danger'
                    : row.risk_level === 'medium'
                      ? 'warning'
                      : 'success'
                  : 'info';
                return (
                  <tr key={row.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-5 py-3">
                      <p className="font-mono text-xs font-semibold text-slate-900">{row.product_id.slice(0, 8)}</p>
                      <p className="mt-1 text-xs text-slate-500">{row.model_version}</p>
                    </td>
                    <td className="px-5 py-3 text-slate-700">
                      {money(row.recommended_price_low)} - {money(row.recommended_price_high)}
                    </td>
                    <td className="px-5 py-3 text-slate-700">{formatPercent(row.confidence)}</td>
                    <td className="px-5 py-3">
                      <StatusChip status={label(row.risk_level)} variant={riskVariant} />
                    </td>
                    <td className="px-5 py-3 text-slate-600">{label(row.value_positioning_label)}</td>
                    <td className="px-5 py-3">
                      <StatusChip status={row.approval_status} />
                    </td>
                    <td className="px-5 py-3 text-slate-600">{formatDate(row.timestamp)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function LabeledInput({
  label: fieldLabel,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-slate-700">{fieldLabel}</span>
      <input
        className="input mt-1"
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function DarkMetric({ label: metricLabel, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">{metricLabel}</p>
      <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

function MiniSignal({
  label: signalLabel,
  value,
  variant,
}: {
  label: string;
  value: number;
  variant: 'success' | 'warning';
}) {
  const valueClass = variant === 'warning' ? 'text-amber-700' : 'text-emerald-700';

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{signalLabel}</p>
      <p className={`mt-1 text-xl font-semibold ${valueClass}`}>{value}</p>
    </div>
  );
}

function ReadinessRow({ label: rowLabel, value }: { label: string; value: number | null }) {
  const percentage = value === null ? 0 : Math.max(0, Math.min(100, value * 100));
  const color = percentage >= 80 ? 'bg-emerald-500' : percentage >= 50 ? 'bg-amber-500' : 'bg-rose-500';

  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3 text-sm">
        <span className="text-slate-600">{rowLabel}</span>
        <span className="font-semibold text-slate-900">{value === null ? '-' : `${percentage.toFixed(0)}%`}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

function LoadingPanel({ label: loadingLabel }: { label: string }) {
  return (
    <div className="flex min-h-28 items-center justify-center rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-600 shadow-sm">
      <span className="mr-3 h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-slate-800" />
      {loadingLabel}
    </div>
  );
}
