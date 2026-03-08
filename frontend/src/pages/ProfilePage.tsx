import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import api from '../lib/api';
import { getThemeForUser, setThemeForUser, type ThemeMode } from '../lib/theme';
import type { UserMe } from '../types/api';

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

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-white/70 bg-white p-5 shadow-card">
        <h2 className="font-display text-2xl font-semibold">My Profile</h2>
        {me.isLoading ? (
          <p className="mt-2 text-sm text-slate-600">Loading profile...</p>
        ) : me.data ? (
          <div className="mt-3 grid gap-2 text-sm text-slate-700 md:grid-cols-2">
            <p><span className="font-semibold">Name:</span> {me.data.name}</p>
            <p><span className="font-semibold">Email:</span> {me.data.email}</p>
            <p><span className="font-semibold">Role:</span> {me.data.role}</p>
            <p><span className="font-semibold">Account:</span> {me.data.account_status}</p>
          </div>
        ) : null}
      </section>

      <section className="space-y-2 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
        <h3 className="font-display text-lg font-semibold">Theme</h3>
        <p className="text-sm text-slate-600">Select Light or Dark mode. Preference is saved to your profile session.</p>
        <div className="max-w-xs">
          <select
            className="input"
            value={theme}
            onChange={(event) => {
              const next = event.target.value as ThemeMode;
              setTheme(next);
              if (me.data?.id) {
                setThemeForUser(me.data.id, next);
              }
            }}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </section>

      <section className="space-y-2 rounded-2xl border border-white/70 bg-white p-5 shadow-card">
        <h3 className="font-display text-lg font-semibold">Password Management</h3>
        <p className="text-sm text-slate-600">
          Password changes are managed by admin only. Contact your admin to reset your account password.
        </p>
      </section>
    </div>
  );
}
