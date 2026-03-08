import type { Role, UserMe } from '../types/api';
import { queryClient } from './queryClient';

export interface Session {
  token: string;
  user: UserMe;
}

export const getSession = (): Session | null => {
  const raw = localStorage.getItem('pricing_session');
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
};

export const setSession = (session: Session): void => {
  queryClient.clear();
  localStorage.setItem('pricing_session', JSON.stringify(session));
  localStorage.setItem('auth_token', session.token);
};

export const clearSession = (): void => {
  queryClient.clear();
  localStorage.removeItem('pricing_session');
  localStorage.removeItem('auth_token');
};

export const hasRole = (role: Role, allowed: Role[]): boolean => allowed.includes(role);

export const defaultRouteByRole = (role: Role): string => {
  if (role === 'sales') return '/sales';
  if (role === 'approver') return '/approvals';
  if (role === 'executive') return '/analytics';
  return '/admin';
};
