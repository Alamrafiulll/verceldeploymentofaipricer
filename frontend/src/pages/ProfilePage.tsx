import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { User, Sun, Moon, ShieldAlert, Key } from 'lucide-react';

import api from '../lib/api';
import { getThemeForUser, setThemeForUser, type ThemeMode } from '../lib/theme';
import type { UserMe } from '../types/api';
import Spinner from '../components/Spinner';

export default function ProfilePage() {
  const me = useQuery({
    queryKey: ['profile', 'me'],
    queryFn: async () => (await api.get<UserMe>('/auth/me')).data,
  });

  const [theme, setTheme] = useState<ThemeMode>('light');

  useEffect(() => {
    if (!me.data?.id) return;
    setTheme(getThemeForUser(me.data.id));
  }, [me.data?.id]);

  const changeTheme = (next: ThemeMode) => {
    setTheme(next);
    if (me.data?.id) {
      setThemeForUser(me.data.id, next);
    }
  };

  const initials = me.data?.name
    ? me.data.name
        .split(' ')
        .map((part) => part[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : 'U';

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Profile Card */}
      <section className="glass-card rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2.5px] bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 opacity-80" />
        
        <h2 className="font-display text-lg font-bold tracking-tight text-slate-900 dark:text-white mb-6 flex items-center gap-2">
          <User className="h-5 w-5 text-indigo-500" />
          My Profile
        </h2>

        {me.isLoading ? (
          <div className="flex items-center justify-center py-6">
            <Spinner size="md" />
          </div>
        ) : me.data ? (
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-bold text-xl shadow-[0_0_15px_rgba(99,102,241,0.4)] border-2 border-white/20 dark:border-slate-800/60">
              {initials}
            </div>
            
            <div className="flex-1 grid gap-4 text-xs font-semibold md:grid-cols-2 w-full">
              <div className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 p-3.5">
                <span className="text-[10px] uppercase tracking-wider text-slate-400 dark:text-slate-500 block mb-1">Full Name</span>
                <span className="text-slate-800 dark:text-slate-200 text-sm font-bold">{me.data.name}</span>
              </div>
              <div className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 p-3.5">
                <span className="text-[10px] uppercase tracking-wider text-slate-400 dark:text-slate-500 block mb-1">Email Address</span>
                <span className="text-slate-800 dark:text-slate-200 text-sm font-bold">{me.data.email}</span>
              </div>
              <div className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 p-3.5">
                <span className="text-[10px] uppercase tracking-wider text-slate-400 dark:text-slate-500 block mb-1">Access Role</span>
                <span className="text-indigo-600 dark:text-indigo-400 text-sm font-bold capitalize">{me.data.role}</span>
              </div>
              <div className="rounded-xl border border-slate-200/50 dark:border-slate-800/40 bg-slate-500/5 p-3.5">
                <span className="text-[10px] uppercase tracking-wider text-slate-400 dark:text-slate-500 block mb-1">Account Status</span>
                <span className="text-emerald-600 dark:text-emerald-400 text-sm font-bold capitalize">{me.data.account_status}</span>
              </div>
            </div>
          </div>
        ) : null}
      </section>

      {/* Theme Card */}
      <section className="glass-card rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2.5px] bg-gradient-to-r from-purple-500 to-pink-500 opacity-80" />
        
        <h3 className="font-display text-lg font-bold tracking-tight text-slate-900 dark:text-white">Workspace Theme</h3>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 font-medium">
          Select your visual theme preference. The setting applies instantly and is saved to your profile session.
        </p>
        
        <div className="mt-5 grid grid-cols-2 gap-4 max-w-sm">
          {/* Light Theme Card Option */}
          <button
            type="button"
            onClick={() => changeTheme('light')}
            className={`flex flex-col items-center gap-3 rounded-xl border p-4 transition-all duration-300 ${
              theme === 'light'
                ? 'border-indigo-500/40 bg-indigo-500/5 text-indigo-600 ring-2 ring-indigo-500/20'
                : 'border-slate-200/50 bg-slate-500/5 text-slate-600 dark:border-slate-800/40 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-500/10'
            }`}
          >
            <div className={`p-2.5 rounded-lg transition-colors ${theme === 'light' ? 'bg-indigo-500/15 text-indigo-600' : 'bg-slate-500/10 text-slate-500'}`}>
              <Sun className="h-5 w-5" />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider">Light Theme</span>
          </button>

          {/* Dark Theme Card Option */}
          <button
            type="button"
            onClick={() => changeTheme('dark')}
            className={`flex flex-col items-center gap-3 rounded-xl border p-4 transition-all duration-300 ${
              theme === 'dark'
                ? 'border-indigo-500/40 bg-indigo-500/10 text-indigo-400 ring-2 ring-indigo-500/30'
                : 'border-slate-200/50 bg-slate-500/5 text-slate-600 dark:border-slate-800/40 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-500/10'
            }`}
          >
            <div className={`p-2.5 rounded-lg transition-colors ${theme === 'dark' ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-500/10 text-slate-500'}`}>
              <Moon className="h-5 w-5" />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider">Dark Theme</span>
          </button>
        </div>
      </section>

      {/* Security Alert Card */}
      <section className="glass-card rounded-2xl p-6 shadow-xl relative overflow-hidden flex items-start gap-4">
        <div className="absolute top-0 left-0 bottom-0 w-[4px] bg-amber-500" />
        <div className="p-2.5 rounded-xl bg-amber-500/10 dark:bg-amber-500/15 text-amber-500 shrink-0">
          <Key className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-display text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            Password & Security
          </h3>
          <p className="mt-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400 font-medium">
            Password policies and credentials are managed centrally by the governance administrator. 
            Contact your IT administration team or pricing officer if you require an account password reset or credential rotation.
          </p>
        </div>
      </section>
    </div>
  );
}
