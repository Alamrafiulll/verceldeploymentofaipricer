import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import api from '../lib/api';
import { defaultRouteByRole, setSession } from '../lib/auth';
import { applyTheme, getThemeForUser } from '../lib/theme';
import type { Role, UserMe } from '../types/api';
import ChinHinLogo from '../components/ChinHinLogo';

const BYPASS_USERS: Record<Role, UserMe> = {
  sales: {
    id: '00000000-0000-0000-0000-000000000001',
    name: 'Sales Manager',
    email: 'salesmanager@gmail.com',
    role: 'sales',
    approval_status: 'approved',
    account_status: 'active',
  },
  approver: {
    id: '00000000-0000-0000-0000-000000000002',
    name: 'Sales Director Approver',
    email: 'salesdirector@gmail.com',
    role: 'approver',
    approval_status: 'approved',
    account_status: 'active',
  },
  executive: {
    id: '00000000-0000-0000-0000-000000000003',
    name: 'Executive Viewer',
    email: 'executiveviewer@gmail.com',
    role: 'executive',
    approval_status: 'approved',
    account_status: 'active',
  },
  admin: {
    id: '00000000-0000-0000-0000-000000000004',
    name: 'Admin Governance',
    email: 'admin@gmail.com',
    role: 'admin',
    approval_status: 'approved',
    account_status: 'active',
  },
};

const ROLE_CARDS: { role: Role; label: string; desc: string; icon: string }[] = [
  { role: 'sales', label: 'Sales Manager', desc: 'Create deals & generate AI pricing', icon: '💼' },
  { role: 'approver', label: 'Sales Director', desc: 'Review & approve pricing requests', icon: '✅' },
  { role: 'executive', label: 'Executive Viewer', desc: 'View analytics & KPI dashboards', icon: '📊' },
  { role: 'admin', label: 'Admin Governance', desc: 'System admin & user management', icon: '⚙️' },
];

export default function LoginPage() {
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const authBypassEnabled = String(import.meta.env.VITE_AUTH_BYPASS ?? 'false') === 'true';

  const completeSignIn = async (accessToken: string) => {
    const meRes = await api.get<UserMe>('/auth/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    setSession({ token: accessToken, user: meRes.data });
    applyTheme(getThemeForUser(meRes.data.id));
    navigate(defaultRouteByRole(meRes.data.role));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const tokenRes = await api.post<{ access_token: string }>('/auth/login', {
        email: identifier,
        password,
      });
      await completeSignIn(tokenRes.data.access_token);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const status = err?.response?.status;
      if (!err?.response) {
        setError('Cannot reach backend API. Check if backend server is running.');
      } else if (status >= 500) {
        setError('Server/Database error. Check backend logs and migrations.');
      } else {
        setError(typeof detail === 'string' ? detail : 'Invalid credentials');
      }
    } finally {
      setLoading(false);
    }
  };

  const loginAsActor = async (role: Role) => {
    setError('');
    setLoading(true);
    try {
      const tokenRes = await api.post<{ access_token: string }>('/auth/dev-login', { role });
      await completeSignIn(tokenRes.data.access_token);
    } catch (err: any) {
      const fallbackUser = BYPASS_USERS[role];
      setSession({ token: `bypass-${role}`, user: fallbackUser });
      applyTheme(getThemeForUser(fallbackUser.id));
      navigate(defaultRouteByRole(role));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen" id="login-page">
      {/* Left panel — branding */}
      <div
        className="relative hidden w-[480px] flex-col justify-between overflow-hidden lg:flex"
        style={{ background: 'linear-gradient(160deg, #262261 0%, #1b1849 50%, #110f36 100%)' }}
      >
        {/* Decorative shapes */}
        <div className="absolute -left-20 -top-20 h-64 w-64 rounded-full bg-brand-red/10 blur-3xl" />
        <div className="absolute bottom-20 right-10 h-48 w-48 rounded-full bg-white/5 blur-2xl" />

        <div className="relative z-10 p-10">
          <ChinHinLogo />
          <div className="mt-12">
            <h2 className="font-display text-3xl font-bold leading-tight text-white">
              AI Pricing
              <br />
              Strategist
            </h2>
            <p className="mt-4 max-w-[320px] text-sm leading-relaxed text-white/60">
              Maximize profit with AI-driven pricing recommendations powered by Azure OpenAI. 
              Real-time win probability scoring, margin optimization, and negotiation guidance.
            </p>
          </div>

          <div className="mt-12 space-y-4">
            {[
              'AI-optimized price recommendations',
              'Real-time win probability scoring',
              'Automated policy enforcement',
              'Full audit trail & governance',
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-3 text-white/70">
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-red/80">
                  <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="text-[13px]">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 p-10">
          <p className="text-[11px] text-white/30">© 2026 Chin Hin Group Berhad. All rights reserved.</p>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex flex-1 items-center justify-center bg-gradient-to-br from-slate-50 via-white to-slate-100 p-6">
        <form
          onSubmit={onSubmit}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <div className="mb-8 lg:hidden">
            <div className="inline-flex items-center gap-2">
              <svg viewBox="0 0 48 48" fill="none" className="h-8 w-8">
                <polygon points="4,38 20,10 26,10 10,38" fill="#E41E2B" />
                <polygon points="12,38 28,10 34,10 18,38" fill="#1e3a7b" />
                <polygon points="20,38 36,10 42,10 26,38" fill="#262261" />
                <polygon points="10,38 26,10 28,10 12,38" fill="white" opacity="0.9" />
                <polygon points="18,38 34,10 36,10 20,38" fill="white" opacity="0.9" />
              </svg>
              <span className="font-display text-lg font-bold text-brand-navy">CHIN HIN</span>
            </div>
          </div>

          <h1 className="font-display text-3xl font-bold text-slate-900">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-500">Sign in to the Pricing Copilot platform</p>

          {authBypassEnabled ? (
            <div className="mt-8 space-y-3">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
                Select Actor Role
              </p>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                {ROLE_CARDS.map(({ role, label, desc, icon }) => (
                  <button
                    key={role}
                    type="button"
                    className="group flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-left transition-all hover:border-brand-navy/30 hover:shadow-md active:scale-[0.98]"
                    disabled={loading}
                    onClick={() => loginAsActor(role)}
                  >
                    <span className="text-xl">{icon}</span>
                    <div>
                      <p className="text-sm font-semibold text-slate-900 group-hover:text-brand-navy">
                        {label}
                      </p>
                      <p className="mt-0.5 text-[11px] text-slate-400">{desc}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              <label className="mt-8 block text-sm font-medium text-slate-700">
                Email
              </label>
              <input
                className="input mt-2"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                placeholder="admin@gmail.com"
                autoComplete="username"
                required
              />

              <label className="mt-5 block text-sm font-medium text-slate-700">
                Password
              </label>
              <input
                type="password"
                className="input mt-2"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                required
              />
            </>
          )}

          {error ? (
            <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          {!authBypassEnabled ? (
            <button
              type="submit"
              className="btn-primary mt-6 flex w-full items-center justify-center gap-2 py-3 text-base"
              disabled={loading}
            >
              {loading ? (
                <svg
                  className="h-4 w-4 animate-spin text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : null}
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          ) : null}

          <div className="mt-8 rounded-xl bg-slate-50 p-4 text-[12px] text-slate-500 leading-relaxed">
            {authBypassEnabled
              ? 'Bypass mode is enabled for actor workflow testing. Select a role above to enter the system directly.'
              : 'Registration is disabled. Admin creates all user accounts and controls activation.'}
          </div>
        </form>
      </div>
    </div>
  );
}
