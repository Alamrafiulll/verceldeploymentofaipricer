import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  Boxes,
  BriefcaseBusiness,
  ClipboardList,
  FileUp,
  Gauge,
  LogOut,
  ShieldCheck,
  Sparkles,
  UserRound,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import RevenueMindLogo from './RevenueMindLogo';
import { clearSession, getSession } from '../lib/auth';

interface NavItem {
  to: string;
  label: string;
  description: string;
  icon: LucideIcon;
  exact?: boolean;
}

const navByRole: Record<string, NavItem[]> = {
  sales: [
    { to: '/sales', label: 'Workspace', description: 'Sales cockpit', icon: BriefcaseBusiness, exact: true },
    { to: '/sales/quotes/new', label: 'New Quote', description: 'Quote builder', icon: ClipboardList },
    { to: '/dashboard', label: 'Dashboard', description: 'Pricing overview', icon: Gauge },
    { to: '/products', label: 'Products', description: 'Catalog and import', icon: Boxes },
    { to: '/pricing', label: 'Pricing Lab', description: 'AI recommendation', icon: Sparkles },
    { to: '/upload-center', label: 'Upload Center', description: 'Files and review', icon: FileUp },
    { to: '/profile', label: 'Profile', description: 'Account details', icon: UserRound },
  ],
  approver: [
    { to: '/dashboard', label: 'Dashboard', description: 'Pricing overview', icon: Gauge },
    { to: '/products', label: 'Products', description: 'Catalog', icon: Boxes },
    { to: '/pricing', label: 'Pricing Lab', description: 'AI recommendation', icon: Sparkles },
    { to: '/upload-center', label: 'Upload Center', description: 'File review', icon: FileUp },
    { to: '/approvals', label: 'Approvals', description: 'Deal governance', icon: ShieldCheck },
    { to: '/profile', label: 'Profile', description: 'Account details', icon: UserRound },
  ],
  executive: [
    { to: '/dashboard', label: 'Dashboard', description: 'Pricing overview', icon: Gauge },
    { to: '/products', label: 'Products', description: 'Catalog', icon: Boxes },
    { to: '/analytics', label: 'Analytics', description: 'Performance', icon: BarChart3 },
    { to: '/upload-center', label: 'Upload Center', description: 'Market files', icon: FileUp },
    { to: '/profile', label: 'Profile', description: 'Account details', icon: UserRound },
  ],
  admin: [
    { to: '/admin', label: 'Admin', description: 'Governance setup', icon: ShieldCheck },
    { to: '/dashboard', label: 'Dashboard', description: 'Pricing overview', icon: Gauge },
    { to: '/products', label: 'Products', description: 'Catalog and import', icon: Boxes },
    { to: '/pricing', label: 'Pricing Lab', description: 'AI recommendation', icon: Sparkles },
    { to: '/upload-center', label: 'Upload Center', description: 'Files and review', icon: FileUp },
    { to: '/analytics', label: 'Analytics', description: 'Performance', icon: BarChart3 },
    { to: '/profile', label: 'Profile', description: 'Account details', icon: UserRound },
  ],
};

function isActivePath(pathname: string, link: NavItem) {
  if (link.exact) return pathname === link.to;
  return pathname === link.to || pathname.startsWith(`${link.to}/`);
}

export default function Layout() {
  const session = getSession();
  const navigate = useNavigate();
  const location = useLocation();

  if (!session) {
    return <Outlet />;
  }

  const links = navByRole[session.user.role] ?? [];
  const userInitial = session.user.name?.slice(0, 1).toUpperCase() || session.user.email.slice(0, 1).toUpperCase();

  return (
    <div className="min-h-screen font-body transition-all duration-300">
      {/* Sleek Glassmorphic Header */}
      <header className="sticky top-0 z-50 border-b border-slate-200/50 bg-white/75 backdrop-blur-md dark:border-slate-800/40 dark:bg-slate-950/75 transition-all duration-300">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-5 py-3.5 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <RevenueMindLogo
              collapsed
              className="shrink-0 border border-slate-100 p-1 shadow-sm dark:border-slate-800/40"
              imageClassName="h-9 w-36"
            />
            <div className="hidden min-w-0 sm:block">
              <p className="truncate font-display text-base font-bold tracking-tight text-slate-900 dark:text-white">
                Pricing Copilot
              </p>
              <p className="truncate text-[10px] font-medium text-slate-400 dark:text-slate-500">
                Commercial pricing, margin governance, and file intelligence
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Elegant profile capsule */}
            <div className="flex items-center gap-2 rounded-xl border border-slate-200/60 bg-white/50 px-3 py-1.5 dark:border-slate-800/60 dark:bg-slate-900/40 transition-all duration-300">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500 text-xs font-bold text-white shadow-md shadow-indigo-500/10">
                {userInitial}
              </span>
              <div className="leading-tight text-left">
                <p className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-500 dark:text-indigo-400">
                  {session.user.role}
                </p>
                <p className="max-w-[140px] truncate text-[10px] font-bold text-slate-500 dark:text-slate-400">
                  {session.user.email}
                </p>
              </div>
            </div>
            
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-600 transition-all duration-200 hover:border-red-500/30 hover:bg-red-50 dark:hover:bg-red-950/10 hover:text-red-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400 dark:hover:text-red-400"
              onClick={() => {
                clearSession();
                navigate('/login');
              }}
            >
              <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Page Layout */}
      <main className="mx-auto grid max-w-[1600px] grid-cols-1 gap-6 px-5 py-6 lg:grid-cols-[260px,minmax(0,1fr)] lg:px-8">
        {/* Floating Sidebar card */}
        <aside className="lg:sticky lg:top-24 h-fit glass-card rounded-2xl p-4 shadow-sm border border-slate-200/40 dark:border-slate-800/40">
          <div className="mb-4 border-b border-slate-100 dark:border-slate-800/50 px-2 pb-3.5">
            <p className="text-[10px] font-extrabold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">
              System Console
            </p>
            <p className="mt-1 text-xs font-bold text-slate-500 dark:text-slate-400">
              Pricing Action Suite
            </p>
          </div>
          <nav className="space-y-1.5 sidebar-scroll overflow-y-auto max-h-[calc(100vh-200px)]">
            {links.map((link) => {
              const Icon = link.icon;
              const active = isActivePath(location.pathname, link);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`group flex items-center gap-3.5 rounded-xl px-3.5 py-3 text-xs transition-all duration-300 ${
                    active
                      ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-600/10 dark:shadow-indigo-500/15'
                      : 'text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-slate-50 dark:hover:bg-slate-900/40 hover:-translate-x-0.5'
                  }`}
                >
                  <Icon className={`h-4.5 w-4.5 shrink-0 transition-transform duration-300 group-hover:scale-110 ${active ? 'text-white' : 'text-slate-400 group-hover:text-indigo-500'}`} aria-hidden="true" />
                  <span className="min-w-0 text-left">
                    <span className="block truncate font-bold text-[13px]">{link.label}</span>
                    <span className={`block truncate text-[10px] mt-0.5 font-semibold transition-colors duration-300 ${active ? 'text-indigo-100' : 'text-slate-400 dark:text-slate-500'}`}>
                      {link.description}
                    </span>
                  </span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Content Area */}
        <section className="min-w-0">
          <div className="transition-all duration-300">
            <Outlet />
          </div>
        </section>
      </main>
    </div>
  );
}
