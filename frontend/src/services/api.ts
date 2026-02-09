export function getBaseUrl(): string {
    if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
    if (typeof window !== 'undefined') {
        const host = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
        return `${window.location.protocol}//${host}:8000/api/v1`;
    }
    return 'http://127.0.0.1:8000/api/v1';
}
const BASE_URL = getBaseUrl();
const backendBase = BASE_URL.replace(/\/api\/v1\/?$/, '') || 'http://localhost:8000';

function getAuthHeaders(): Record<string, string> {
    if (typeof window === 'undefined') return {};
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function wrapNetworkError(err: unknown, isTimeout?: boolean): Error {
    if (isTimeout || (err instanceof Error && err.name === 'AbortError'))
        return new Error('Tarama çok uzun sürdü, bağlantı zaman aşımına uğradı (5 dk). Daha küçük hedef deneyin veya backend loglarına bakın.');
    if (err instanceof Error) {
        if (err.message.toLowerCase().includes('fetch') || err.message === 'Failed to fetch')
            return new Error(`Backend'e bağlanılamadı. Backend çalışıyor mu? (${backendBase})`);
        return err;
    }
    return new Error('Network error');
}

async function fetchWithTimeout(
    url: string,
    options: RequestInit,
    timeoutMs: number
): Promise<Response> {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const res = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(id);
        return res;
    } catch (e) {
        clearTimeout(id);
        throw e;
    }
}

const api = {
    get: async (url: string) => {
        try {
            const res = await fetch(`${BASE_URL}${url}`, {
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() }
            });
            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                const msg = (body as { detail?: string }).detail ?? (body as { message?: string }).message ?? res.statusText;
                throw new Error(msg);
            }
            return { data: await res.json() };
        } catch (e) {
            throw wrapNetworkError(e);
        }
    },
    post: async (url: string, body: any, options?: { timeoutMs?: number }) => {
        const timeoutMs = options?.timeoutMs ?? 30000;
        try {
            const res = await fetchWithTimeout(
                `${BASE_URL}${url}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                    body: JSON.stringify(body)
                },
                timeoutMs
            );
            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                const msg = (body as { detail?: string }).detail ?? (body as { message?: string }).message ?? res.statusText;
                throw new Error(msg);
            }
            return { data: await res.json() };
        } catch (e) {
            const isTimeout = e instanceof Error && e.name === 'AbortError';
            throw wrapNetworkError(e, isTimeout);
        }
    }
};

export default api;
