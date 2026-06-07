import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import api from '../lib/api';
import { defaultRouteByRole, setSession } from '../lib/auth';
import { applyTheme, getThemeForUser } from '../lib/theme';
import type { Role, UserMe } from '../types/api';
import RevenueMindLogo from '../components/RevenueMindLogo';

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
  { role: 'sales', label: 'Sales Manager', desc: 'Create deals & run pricing simulations', icon: 'SM' },
  { role: 'approver', label: 'Sales Director', desc: 'Review & approve pricing overrides', icon: 'SD' },
  { role: 'executive', label: 'Executive Viewer', desc: 'View global analytics & leakage stats', icon: 'EV' },
  { role: 'admin', label: 'Admin Governance', desc: 'Ingest policy rules & manage users', icon: 'AG' },
];

export default function LoginPage() {
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState('admin@gmail.com');
  const [password, setPassword] = useState('123456');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const authBypassEnabled = String(import.meta.env.VITE_AUTH_BYPASS ?? 'true') === 'true';

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
    <div className="flex min-h-screen bg-slate-950 text-slate-100" id="login-page">
      {/* Left panel — premium corporate branding */}
      <div
        className="relative hidden w-[490px] flex-col justify-between overflow-hidden lg:flex border-r border-slate-900 shadow-2xl"
        style={{ background: 'linear-gradient(160deg, #090b16 0%, #11142e 50%, #060812 100%)' }}
      >
        {/* Glow effects */}
        <div className="absolute -left-20 -top-20 h-80 w-80 rounded-full bg-indigo-500/10 blur-[100px]" />
        <div className="absolute bottom-40 right-0 h-64 w-64 rounded-full bg-violet-500/10 blur-[120px]" />

        <div className="relative z-10 p-10">
          <RevenueMindLogo className="p-3 shadow-lg" imageClassName="h-16 w-56" />
          
          <div className="mt-16">
            <span className="rounded-full bg-indigo-500/10 px-3 py-1 text-xs font-semibold tracking-wider text-indigo-400 border border-indigo-500/20 uppercase">
              AI Command Suite
            </span>
            <h2 className="mt-4 font-display text-4xl font-extrabold leading-tight tracking-tight text-white">
              RevenueMind <br />
              <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-indigo-400 bg-clip-text text-transparent">
                Pricing Copilot
              </span>
            </h2>
            <p className="mt-5 max-w-[340px] text-[13px] leading-relaxed text-slate-400">
              Transform deal workflows with state-of-the-art AI recommendations, real-time margin simulators, smart document extraction, and seamless approval governance.
            </p>
          </div>

          <div className="mt-16 space-y-4">
            {[
              { title: 'AI Recommendation Engine', desc: 'Optimized margin floors based on parameters' },
              { title: 'Governance & Integrity', desc: 'Secure approval workflow for margin exceptions' },
              { title: 'True Margin Simulations', desc: 'Accurate MDF and rebate deduction snapshots' },
              { title: 'Document Intelligence', desc: 'Extract trading terms from PDFs automatically' },
            ].map((feature, idx) => (
              <div key={idx} className="flex items-start gap-4">
                <div className="mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-500/20 border border-indigo-500/30">
                  <div className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                </div>
                <div className="leading-tight">
                  <p className="text-[13px] font-bold text-white">{feature.title}</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 p-10 border-t border-slate-900/60 bg-slate-950/20">
          <p className="text-[11px] text-slate-600">
            (c) 2026 RevenueMind. Enterprise control tower suite.
          </p>
        </div>
      </div>

      {/* Right panel — login interface */}
      <div className="flex flex-1 items-center justify-center p-6 bg-radial-gradient">
        {/* Glow ambient background */}
        <div className="absolute right-10 top-10 h-72 w-72 rounded-full bg-indigo-600/5 blur-[120px] pointer-events-none" />
        <div className="absolute left-1/3 bottom-10 h-96 w-96 rounded-full bg-violet-600/5 blur-[140px] pointer-events-none" />

        <div className="w-full max-w-lg glass-card rounded-3xl p-8 border border-slate-800/80 bg-slate-900/40 shadow-2xl relative z-10">
          {/* Mobile logo */}
          <div className="mb-8 lg:hidden">
            <RevenueMindLogo className="border border-slate-800 p-2 shadow-sm" imageClassName="h-10 w-40" />
          </div>

          <h1 className="font-display text-3xl font-extrabold text-white tracking-tight">System Control Tower</h1>
          <p className="mt-2 text-sm text-slate-400">Authenticating user node for RevenueMind</p>

          {authBypassEnabled ? (
            <div className="mt-8 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  Select System Node Role
                </span>
                <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">
                  Dev Bypass Active
                </span>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {ROLE_CARDS.map(({ role, label, desc, icon }) => (
                  <button
                    key={role}
                    type="button"
                    className="group flex flex-col justify-between items-start rounded-2xl border border-slate-800 bg-slate-950/40 p-4 text-left transition-all duration-300 hover:-translate-y-0.5 hover:border-indigo-500/40 hover:bg-slate-900/40 hover:shadow-lg hover:shadow-indigo-500/5 active:scale-[0.98]"
                    disabled={loading}
                    onClick={() => loginAsActor(role)}
                  >
                    <div className="flex items-center gap-2">
                      <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-700 bg-slate-900 text-[11px] font-extrabold tracking-wider text-indigo-300">
                        {icon}
                      </span>
                      <p className="text-sm font-bold text-white group-hover:text-indigo-400 transition-colors">
                        {label}
                      </p>
                    </div>
                    <p className="mt-2 text-[10px] text-slate-500 leading-normal">{desc}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="mt-8 space-y-5">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                  Corporate Email
                </label>
                <input
                  type="email"
                  className="input mt-2 bg-slate-950/40 border-slate-800 text-slate-100"
                  value={identifier}
                  onChange={(event) => setIdentifier(event.target.value)}
                  placeholder="admin@gmail.com"
                  autoComplete="username"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                  Security Password
                </label>
                <input
                  type="password"
                  className="input mt-2 bg-slate-950/40 border-slate-800 text-slate-100"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>

              {error ? (
                <div className="rounded-xl border border-red-950/50 bg-red-950/20 px-4 py-3 text-xs text-red-400 border-l-4 border-l-red-500">
                  {error}
                </div>
              ) : null}

              <button
                type="submit"
                className="btn-primary mt-6 flex w-full items-center justify-center gap-2.5 py-3 text-sm font-bold shadow-lg shadow-indigo-600/20"
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
                {loading ? 'Validating Nodes...' : 'Establish Secure Connection'}
              </button>
            </form>
          )}

          <div className="mt-8 rounded-2xl bg-slate-950/50 p-4 border border-slate-900 text-[11px] text-slate-500 leading-relaxed text-center">
            {authBypassEnabled
              ? 'Dev bypass active. Select any system node above to directly load mock data simulations.'
              : 'Public registrations are strictly prohibited. Node accounts managed by Admin Governance.'}
          </div>
        </div>
      </div>
    </div>
  );
}
