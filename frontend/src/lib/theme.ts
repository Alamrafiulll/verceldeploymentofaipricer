import { getSession } from './auth';

export type ThemeMode = 'light' | 'dark';

const FALLBACK_THEME: ThemeMode = 'light';

function storageKey(userId: string) {
  return `pricing_theme_${userId}`;
}

export function getThemeForUser(userId: string | null | undefined): ThemeMode {
  if (!userId) {
    return FALLBACK_THEME;
  }
  const raw = localStorage.getItem(storageKey(userId));
  if (raw === 'dark' || raw === 'light') {
    return raw;
  }
  return FALLBACK_THEME;
}

export function applyTheme(theme: ThemeMode): void {
  document.documentElement.setAttribute('data-theme', theme);
}

export function setThemeForUser(userId: string, theme: ThemeMode): void {
  localStorage.setItem(storageKey(userId), theme);
  applyTheme(theme);
}

export function initThemeFromSession(): void {
  const session = getSession();
  const theme = getThemeForUser(session?.user.id);
  applyTheme(theme);
}
