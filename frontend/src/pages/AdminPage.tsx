import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import AdminRulesEditor from '../components/AdminRulesEditor';
import AuditLogTable from '../components/AuditLogTable';
import RoleFileUploadPanel from '../components/RoleFileUploadPanel';
import { AlertBanner, SectionHeader, SummaryCard } from '../components/ui';
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
  UserAccountStatus,
} from '../types/api';

const money = (value?: number | null) => (value === null || value === undefined ? '-' : `RM ${value.toFixed(2)}`);
const label = (value?: string | null) =>
  value ? value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()) : '-';

export default function AdminPage() {
  const queryClient = useQueryClient();
  const currentUserId = getSession()?.user.id ?? null;
  const [userForm, setUserForm] = useState({
    name: '',
    email: '',
    password: '123456',
    role: 'sales' as Role,
    account_status: 'active' as UserAccountStatus,
  });
  const [status, setStatus] = useState('');
  const [resetPasswordByUser, setResetPasswordByUser] = useState<Record<string, string>>({});

  const toErrorMessage = (error: any, fallback: string): string => {
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
  };

  const rules = useQuery({ queryKey: ['admin', 'rules'], queryFn: async () => (await api.get<Rule[]>('/admin/rules')).data });
  const logs = useQuery({ queryKey: ['admin', 'audit-logs'], queryFn: async () => (await api.get<AuditLog[]>('/admin/audit-logs')).data });
  const modelRuns = useQuery({ queryKey: ['admin', 'model-runs'], queryFn: async () => (await api.get<ModelRun[]>('/admin/model-runs')).data });
  const users = useQuery({ queryKey: ['admin', 'users'], queryFn: async () => (await api.get<AdminUser[]>('/admin/users')).data });
  const aiRecommendations = useQuery({ queryKey: ['admin', 'ai-recommendations'], queryFn: async () => (await api.get<AIRecommendationTrace[]>('/admin/ai-recommendations')).data });
  const governanceSummary = useQuery({ queryKey: ['admin', 'governance-summary'], queryFn: async () => (await api.get<GovernanceSummary>('/admin/governance-summary')).data });
  const reviewQueue = useQuery({ queryKey: ['admin', 'document-review-queue'], queryFn: async () => (await api.get<ReviewQueueItem[]>('/admin/document-review-queue')).data });
  const dataQuality = useQuery({ queryKey: ['admin', 'data-quality'], queryFn: async () => (await api.get<DataQuality>('/admin/data-quality')).data });

  const saveRule = useMutation({
    mutationFn: async (payload: { channel: string; category: string; margin_floor_percent: number; max_discount_percent: number; approval_required_below_margin_buffer: number }) => api.post('/admin/rules', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'rules'] });
      setStatus('Rule saved.');
    },
    onError: () => setStatus('Failed to save rule.'),
  });
  const createUser = useMutation({
    mutationFn: async () => api.post('/admin/users', userForm),
    onSuccess: () => {
      setStatus('User created.');
      setUserForm((prev) => ({ ...prev, name: '', email: '' }));
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'audit-logs'] });
    },
    onError: (error: any) => setStatus(toErrorMessage(error, 'User creation failed.')),
  });
  const updateUserStatus = useMutation({
    mutationFn: async (payload: { userId: string; account_status: UserAccountStatus }) => api.patch(`/admin/users/${payload.userId}/status`, { account_status: payload.account_status }),
    onSuccess: () => {
      setStatus('User status updated.');
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
    onError: () => setStatus('Failed to update user status.'),
  });
  const deleteUser = useMutation({
    mutationFn: async (userId: string) => api.delete(`/admin/users/${userId}`),
    onSuccess: () => {
      setStatus('User deleted.');
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'audit-logs'] });
    },
    onError: (error: any) => setStatus(error?.response?.data?.detail ?? 'Failed to delete user.'),
  });
  const resetPassword = useMutation({
    mutationFn: async (payload: { userId: string; newPassword?: string }) =>
      api.post<{ user_id: string; email: string; generated_password: string }>(`/admin/users/${payload.userId}/reset-password`, {
        new_password: payload.newPassword?.trim() || null,
      }),
    onSuccess: (response) => {
      setStatus(`Password reset for ${response.data.email}. Visible password: ${response.data.generated_password}`);
      queryClient.invalidateQueries({ queryKey: ['admin', 'audit-logs'] });
    },
    onError: () => setStatus('Failed to reset password.'),
  });

  const canCreateUser = userForm.name.trim() && userForm.email.trim() && userForm.password.length >= 6;

  return (
    <div className="space-y-5">
      <SectionHeader
        icon="🛡️"
        title="Admin Governance Workspace"
        subtitle="Manage upload governance, pricing rules, review queues, model observability, and decision traceability from one place."
      />

      {governanceSummary.data ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-5">
          <SummaryCard title="Upload Reviews" value={governanceSummary.data.pending_upload_reviews} subtitle="Files waiting for review" variant={governanceSummary.data.pending_upload_reviews > 0 ? 'warning' : 'success'} />
          <SummaryCard title="Policy Reviews" value={governanceSummary.data.pending_policy_reviews} subtitle="Draft policies pending activation" variant={governanceSummary.data.pending_policy_reviews > 0 ? 'warning' : 'success'} />
          <SummaryCard title="AI Trace Count" value={governanceSummary.data.ai_trace_count} subtitle="Stored recommendation traces" />
          <SummaryCard title="Model Failures" value={governanceSummary.data.model_run_failures} subtitle="Runs needing investigation" variant={governanceSummary.data.model_run_failures > 0 ? 'warning' : 'success'} />
          <SummaryCard title="Unmatched Competitors" value={governanceSummary.data.unmatched_competitor_records} subtitle="Rows needing product matching" variant={governanceSummary.data.unmatched_competitor_records > 0 ? 'warning' : 'success'} />
        </div>
      ) : null}

      {dataQuality.data ? (
        <AlertBanner variant="tip" title="Why This Matters">
          {dataQuality.data.uploads_needing_review} uploads need review, {dataQuality.data.recommendations_with_fallback} recommendations used fallback logic, and average clause confidence is {dataQuality.data.average_clause_confidence.toFixed(2)}.
        </AlertBanner>
      ) : null}

      {rules.data ? (
        <AdminRulesEditor
          rules={rules.data}
          onSave={async (payload) => {
            await saveRule.mutateAsync(payload);
          }}
          loading={saveRule.isPending}
        />
      ) : null}

      <section className="space-y-4 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
        <h3 className="font-display text-lg font-semibold">Create Employee</h3>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
          <input className="input" placeholder="Name" value={userForm.name} onChange={(event) => setUserForm((prev) => ({ ...prev, name: event.target.value }))} />
          <input className="input" placeholder="Email" value={userForm.email} onChange={(event) => setUserForm((prev) => ({ ...prev, email: event.target.value }))} />
          <input className="input" placeholder="Password" value={userForm.password} minLength={6} onChange={(event) => setUserForm((prev) => ({ ...prev, password: event.target.value }))} />
          <select className="input" value={userForm.role} onChange={(event) => setUserForm((prev) => ({ ...prev, role: event.target.value as Role }))}>
            <option value="sales">sales</option>
            <option value="approver">approver</option>
            <option value="executive">executive</option>
            <option value="admin">admin</option>
          </select>
          <select className="input" value={userForm.account_status} onChange={(event) => setUserForm((prev) => ({ ...prev, account_status: event.target.value as UserAccountStatus }))}>
            <option value="active">active</option>
            <option value="inactive">inactive</option>
          </select>
        </div>
        <button className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" disabled={createUser.isPending || !canCreateUser} onClick={() => createUser.mutate()}>
          {createUser.isPending ? 'Creating...' : 'Create User'}
        </button>
      </section>

      <section className="rounded-2xl border border-white/70 bg-white p-5 shadow-card">
        <h3 className="font-display text-lg font-semibold">Governance Upload Center</h3>
        <RoleFileUploadPanel
          title="Governance Upload"
          description="Upload policy documents, campaign memos, trading terms, contract pricing, rule templates, and model configuration files for admin review."
          allowedTypes={[
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
          ]}
          showAll
          allowDelete
        />
      </section>

      {reviewQueue.data ? (
        <section className="rounded-2xl border border-white/70 bg-white p-5 shadow-card">
          <h3 className="font-display text-lg font-semibold">Document Review Queue</h3>
          <div className="mt-3 overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-600">
                  <th className="py-2 pr-3">Type</th>
                  <th className="py-2 pr-3">Label</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2 pr-3">Source Reference</th>
                  <th className="py-2 pr-3">Next Step</th>
                </tr>
              </thead>
              <tbody>
                {reviewQueue.data.map((item) => (
                  <tr key={`${item.item_type}-${item.item_id}`} className="border-b border-slate-100">
                    <td className="py-2 pr-3">{label(item.item_type)}</td>
                    <td className="py-2 pr-3">{item.label}</td>
                    <td className="py-2 pr-3">{label(item.status)}</td>
                    <td className="py-2 pr-3">{item.source_reference ?? '-'}</td>
                    <td className="py-2 pr-3 text-slate-600">{item.next_step ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      <section className="space-y-4 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
        <h3 className="font-display text-lg font-semibold">Employee Directory</h3>
        {!users.data || users.data.length === 0 ? (
          <p className="text-sm text-slate-600">No users found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Email</th>
                  <th className="pb-2">Role</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Created</th>
                  <th className="pb-2">Reset Password</th>
                  <th className="pb-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.data.map((user) => (
                  <tr key={user.id} className="border-t border-slate-200 align-top">
                    <td className="py-2">{user.name}</td>
                    <td className="py-2">{user.email}</td>
                    <td className="py-2">{user.role}</td>
                    <td className="py-2">
                      <select className="input" value={user.account_status} disabled={user.id === currentUserId} onChange={(event) => updateUserStatus.mutate({ userId: user.id, account_status: event.target.value as UserAccountStatus })}>
                        <option value="active">active</option>
                        <option value="inactive">inactive</option>
                      </select>
                    </td>
                    <td className="py-2">{new Date(user.created_at).toLocaleString()}</td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        <input className="input min-w-[180px]" placeholder="New password" value={resetPasswordByUser[user.id] ?? ''} onChange={(event) => setResetPasswordByUser((prev) => ({ ...prev, [user.id]: event.target.value }))} />
                        <button className="rounded-md bg-slate-700 px-3 py-1.5 text-xs font-semibold text-white" disabled={resetPassword.isPending || user.id === currentUserId || !(resetPasswordByUser[user.id] ?? '').trim()} onClick={() => resetPassword.mutate({ userId: user.id, newPassword: resetPasswordByUser[user.id] })}>
                          {user.id === currentUserId ? 'Self' : 'Reset'}
                        </button>
                      </div>
                    </td>
                    <td className="py-2">
                      <button className="rounded-md bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white" disabled={deleteUser.isPending} onClick={() => deleteUser.mutate(user.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {logs.data ? <AuditLogTable rows={logs.data} /> : null}

      <section className="rounded-2xl border border-white/70 bg-white p-5 shadow-card">
        <h3 className="font-display text-lg font-semibold">Model Runs</h3>
        {!modelRuns.data || modelRuns.data.length === 0 ? (
          <p className="text-sm text-slate-600">No model runs recorded yet.</p>
        ) : (
          <div className="mt-3 overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-600">
                  <th className="py-2 pr-3">Type</th>
                  <th className="py-2 pr-3">Provider</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2 pr-3">Fallback</th>
                  <th className="py-2 pr-3">Quote</th>
                  <th className="py-2 pr-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {modelRuns.data.map((run) => (
                  <tr key={run.id} className="border-b border-slate-100">
                    <td className="py-2 pr-3">{run.run_type}</td>
                    <td className="py-2 pr-3">{run.model_provider ?? run.model_name}</td>
                    <td className="py-2 pr-3">{run.status}</td>
                    <td className="py-2 pr-3">{run.fallback_used ? 'Yes' : 'No'}</td>
                    <td className="py-2 pr-3">{run.related_quote_id ? run.related_quote_id.slice(0, 8) : '-'}</td>
                    <td className="py-2 pr-3">{new Date(run.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-white/70 bg-white p-5 shadow-card">
        <h3 className="font-display text-lg font-semibold">AI Decision Traceability</h3>
        {!aiRecommendations.data || aiRecommendations.data.length === 0 ? (
          <p className="mt-3 text-sm text-slate-600">No AI recommendations traced yet.</p>
        ) : (
          <div className="mt-3 overflow-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-left text-slate-600">
                  <th className="py-2 pr-3">Product</th>
                  <th className="py-2 pr-3">Price Range</th>
                  <th className="py-2 pr-3">Confidence</th>
                  <th className="py-2 pr-3">Risk</th>
                  <th className="py-2 pr-3">Value Position</th>
                  <th className="py-2 pr-3">Approval Status</th>
                  <th className="py-2 pr-3">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {aiRecommendations.data.map((row) => (
                  <tr key={row.id} className="border-b border-slate-100">
                    <td className="py-2 pr-3 font-mono text-xs">{row.product_id.slice(0, 8)}</td>
                    <td className="py-2 pr-3">
                      {money(row.recommended_price_low)} - {money(row.recommended_price_high)}
                    </td>
                    <td className="py-2 pr-3">{(row.confidence * 100).toFixed(1)}%</td>
                    <td className="py-2 pr-3">{label(row.risk_level)}</td>
                    <td className="py-2 pr-3">{label(row.value_positioning_label)}</td>
                    <td className="py-2 pr-3">{label(row.approval_status)}</td>
                    <td className="py-2 pr-3">{new Date(row.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {status ? <div className="rounded-lg bg-slate-100 p-3 text-sm text-slate-700">{status}</div> : null}
    </div>
  );
}
