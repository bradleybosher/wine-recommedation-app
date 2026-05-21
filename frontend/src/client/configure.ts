import { client } from './client.gen';

export const TOKEN_STORAGE_KEY = 'vinotheque.token';
export const ACTIVE_PROFILE_STORAGE_KEY = 'vinotheque.activeProfileId';

export function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function readActiveProfileId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_PROFILE_STORAGE_KEY);
  } catch {
    return null;
  }
}

let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

export function installAuthInterceptors(): void {
  client.interceptors.request.use((request) => {
    const token = readToken();
    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`);
    }
    const profileId = readActiveProfileId();
    if (profileId) {
      request.headers.set('X-Profile-Id', profileId);
    }
    return request;
  });

  client.interceptors.response.use((response) => {
    if (response.status === 401 && unauthorizedHandler) {
      unauthorizedHandler();
    }
    return response;
  });
}
