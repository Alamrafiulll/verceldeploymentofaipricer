import { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { clearSession, getSession } from '../lib/auth';
import ChinHinLogo from './ChinHinLogo';

/* ── Icon components ─────────────────────────────── */
function IconSales() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5V6a3.75 3.75 0 1 0-7.5 0v4.5m11.356-1.993 1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 0 1-1.12-1.243l1.264-12A1.125 1.125 0 0 1 5.513 7.5h12.974c.576 0 1.059.435 1.119 1.007Z" />
    </svg>
  );
}
function IconNewQuote() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}
function IconDashboard() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6Zm0 9.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6Zm0 9.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25Z" />
    </svg>
  );
}
function IconProducts() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25" />
    </svg>
  );
}
function IconPricing() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}
function IconApprovals() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}
function IconAnalytics() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  );
}
function IconAdmin() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}
function IconProfile() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
    </svg>
  );
}
function IconLogout() {
  return (
    <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" />
    </svg>
  );
}

/* ── Icon map ─────────────────────────────────────── */
const ICONS: Record<string, () => JSX.Element> = {
  Sales: IconSales,
  'New Quote': IconNewQuote,
  Dashboard: IconDashboard,
  Products: IconProducts,
  Pricing: IconPricing,
  Approvals: IconApprovals,
  Analytics: IconAnalytics,
  Admin: IconAdmin,
  Profile: IconProfile,
  'Upload Center': IconProducts,
};

/* ── Navigation by role ───────────────────────────── */
const navByRole = {
  sales: [
    { to: '/sales', label: 'Sales' },
    { to: '/sales/quotes/new', label: 'New Quote' },
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/products', label: 'Products' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/upload-center', label: 'Upload Center' },
    { to: '/profile', label: 'Profile' },
  ],
  approver: [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/products', label: 'Products' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/approvals', label: 'Approvals' },
    { to: '/upload-center', label: 'Upload Center' },
    { to: '/profile', label: 'Profile' },
  ],
  executive: [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/products', label: 'Products' },
    { to: '/analytics', label: 'Analytics' },
    { to: '/upload-center', label: 'Upload Center' },
    { to: '/profile', label: 'Profile' },
  ],
  admin: [
    { to: '/admin', label: 'Admin' },
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/products', label: 'Products' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/analytics', label: 'Analytics' },
    { to: '/upload-center', label: 'Upload Center' },
    { to: '/profile', label: 'Profile' },
  ],
} as const;

const ROLE_LABELS: Record<string, string> = {
  sales: 'Sales Manager',
  approver: 'Sales Director',
  executive: 'Executive',
  admin: 'Administrator',
};

/* ── Layout component ─────────────────────────────── */
export default function Layout() {
  const session = getSession();
  const navigate = useNavigate();
  const location = useLocation();

  if (!session) {
    return <Outlet />;
  }

  const links = navByRole[session.user.role] ?? [];

  return (
    <div className="flex min-h-screen font-body">
      {/* ── Navy Sidebar ───────────────────────────── */}
      <aside
        className="group fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col shadow-sidebar"
        style={{ background: 'var(--sidebar-bg)' }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 border-b border-white/10 px-5 py-5">
          <ChinHinLogo />
        </div>

        {/* User badge */}
        <div className="mx-4 mt-4 rounded-xl bg-white/8 px-4 py-3">
          <p className="text-[13px] font-semibold text-white/90 truncate">
            {session.user.name}
          </p>
          <p className="mt-0.5 text-[11px] text-white/50">
            {ROLE_LABELS[session.user.role] ?? session.user.role}
          </p>
        </div>

        {/* Navigation */}
        <nav className="sidebar-scroll mt-4 flex-1 space-y-1 overflow-y-auto px-3">
          {links.map((link) => {
            const path = link.to as string;
            const isActive = location.pathname === path || (path !== '/' && location.pathname.startsWith(path));
            const Icon = ICONS[link.label];

            return (
              <Link
                key={link.to}
                to={link.to}
                className={`flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13px] font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-white/15 text-white shadow-sm shadow-white/5'
                    : 'text-white/60 hover:bg-white/8 hover:text-white/90'
                }`}
              >
                {Icon ? <Icon /> : null}
                {link.label}
                {isActive && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-brand-red" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="border-t border-white/10 p-3">
          <button
            type="button"
            className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-[13px] font-medium text-white/50 transition hover:bg-white/8 hover:text-white/80"
            onClick={() => {
              clearSession();
              navigate('/login');
            }}
          >
            <IconLogout />
            Sign Out
          </button>
        </div>

        {/* Subtle branding */}
        <div className="px-5 pb-4">
          <p className="text-[10px] text-white/25">AI Pricing Strategist v1.0</p>
        </div>
      </aside>

      {/* ── Main Content ───────────────────────────── */}
      <main className="ml-[260px] flex-1">
        {/* Top bar */}
        <header className="sticky top-0 z-40 border-b border-slate-200/60 bg-white/80 backdrop-blur-md">
          <div className="flex items-center justify-between px-8 py-4">
            <div>
              <h1 className="font-display text-lg font-semibold text-slate-900">
                {links.find((l) => location.pathname.startsWith(l.to))?.label ?? 'Dashboard'}
              </h1>
              <p className="text-xs text-slate-500">Chin Hin AI Pricing Strategist</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="rounded-full bg-brand-navy px-3 py-1 text-[11px] font-semibold text-white tracking-wide">
                {session.user.role.toUpperCase()}
              </span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <section className="px-8 py-6">
          <Outlet />
        </section>
      </main>
    </div>
  );
}
