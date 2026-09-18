/**
 * The single place in the frontend that talks HTTP.
 *
 * Every other module calls apiGet/apiPost/apiDelete - no component ever calls
 * fetch() directly (BRD section 28). That gives us one place to add the auth
 * header in Milestone 3, one place to normalise errors, and one place to look
 * when a request misbehaves.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8010';

/** An error that carries the HTTP status, so callers can react to 401 vs 500. */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch {
    // fetch() only rejects on network-level failures: server down, DNS failure,
    // CORS rejection. An HTTP 500 does NOT land here - it resolves normally.
    throw new ApiError('Cannot reach the server. Is the backend running?', 0);
  }

  if (!response.ok) {
    // FastAPI puts its error text in a "detail" field.
    const body = await response.json().catch(() => null);
    const detail =
      body && typeof body.detail === 'string' ? body.detail : response.statusText;
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export const apiGet = <T>(path: string) => request<T>(path, { method: 'GET' });

export const apiPost = <T>(path: string, body?: unknown) =>
  request<T>(path, {
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body),
  });

export const apiDelete = <T>(path: string) => request<T>(path, { method: 'DELETE' });
