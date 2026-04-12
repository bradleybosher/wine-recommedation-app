export const FILE_SIZE_LIMITS = {
  MAX_MB: 10,
  WARN_MB: 5,
  MAX_BYTES: 10 * 1024 * 1024,
  WARN_BYTES: 5 * 1024 * 1024
} as const;

export const MEAL_DESCRIPTION = {
  MAX_CHARS: 500
} as const;

export const ALLOWED_MIME_TYPES: string[] = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/gif',
  'application/pdf',
  'text/plain'
];

export const API_CONFIG = {
  TIMEOUT_MS: 30000,
  DEFAULT_URL: 'http://localhost:8000/recommend'
} as const;
