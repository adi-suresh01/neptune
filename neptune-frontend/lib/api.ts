const POSSIBLE_PORTS = [8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009];

function isProductionMode(): boolean {
  if (typeof window === 'undefined') return false;
  const isTauri =
    window.location.protocol === 'tauri:' ||
    window.location.hostname === 'tauri.localhost' ||
    // @ts-ignore
    window.__TAURI__ !== undefined;
  return isTauri;
}

async function findBackendUrl(): Promise<string> {
  const isProduction = isProductionMode();
  if (isProduction) {
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }

  for (const port of POSSIBLE_PORTS) {
    const url = `http://localhost:${port}`;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch(`${url}/health`, {
        method: 'GET',
        headers: {
          Accept: 'application/json',
          'Cache-Control': 'no-cache',
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          return url;
        }
      }
    } catch {
      continue;
    }
  }

  throw new Error(`No healthy backend found. Tested ports: ${POSSIBLE_PORTS.join(', ')}`);
}

async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs: number = 8000): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

let API_BASE_URL = 'http://localhost:8000';
let discoveryInProgress = false;

interface RequestOptions {
  maxRetries?: number;
  retryDelay?: number;
}

export const apiRequest = async (
  endpoint: string, 
  options: RequestInit = {}, 
  requestOptions: RequestOptions = {}
): Promise<Response> => {
  const isProduction = isProductionMode();
  const { maxRetries = isProduction ? 20 : 8, retryDelay = isProduction ? 2000 : 1500 } = requestOptions;
  
  let currentBaseUrl = API_BASE_URL;
  let hasTriedDiscovery = false;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      // Try backend discovery on first attempt and every 5th attempt
      if (!hasTriedDiscovery || (attempt > 0 && attempt % 5 === 0)) {
        if (!discoveryInProgress) {
          try {
            discoveryInProgress = true;
            currentBaseUrl = await findBackendUrl();
            API_BASE_URL = currentBaseUrl;
            hasTriedDiscovery = true;
          } catch (discoveryError) {
            if (attempt === 0) {
              // Initial discovery may fail while backend starts.
            }
          } finally {
            discoveryInProgress = false;
          }
        } else {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      const url = `${currentBaseUrl}${endpoint}`;
      
      const response = await fetchWithTimeout(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Cache-Control': 'no-cache',
          ...options.headers,
        },
      }, isProduction ? 12000 : 6000);
      
      if (response.ok) {
        return response;
      }
      
      if (response.status >= 400 && response.status < 500) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
    } catch (error) {
      const isLastAttempt = attempt === maxRetries - 1;
      
      // If it's a network error, reset discovery for next attempt
      if (error.name === 'AbortError' || error.message.includes('fetch') || error.message.includes('NetworkError')) {
        hasTriedDiscovery = false;
      }
      
      if (isLastAttempt) {
        throw new Error(`Backend unavailable after ${maxRetries} attempts: ${error.message}`);
      }
      
      await new Promise(resolve => setTimeout(resolve, retryDelay));
    }
  }
  
  throw new Error('Request failed');
};

export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const isProduction = isProductionMode();
    const response = await apiRequest('/health', {}, { 
      maxRetries: isProduction ? 15 : 6, 
      retryDelay: isProduction ? 2000 : 1500 
    });
    return response.ok;
  } catch (error) {
    return false;
  }
};

export const resetBackendDiscovery = () => {
  API_BASE_URL = 'http://localhost:8000';
  discoveryInProgress = false;
};

export const api = {
  health: () => apiRequest('/health'),
  
  filesystem: {
    list: (params?: { owner_id?: string; limit?: number; offset?: number }) => {
      const query = params
        ? `?${new URLSearchParams(
            Object.entries(params).filter(([, v]) => v !== undefined) as Array<[string, string]>
          ).toString()}`
        : '';
      return apiRequest(`/api/filesystem/${query}`);
    },
    create: (data: { name: string; type: string; parent_id?: number | null; owner_id?: string | null }) =>
      apiRequest('/api/filesystem/', { method: 'POST', body: JSON.stringify(data) }),
    get: (id: number) => apiRequest(`/api/filesystem/${id}`),
    update: (id: number, data: { content: string; content_checksum?: string | null }) =>
      apiRequest(`/api/filesystem/${id}/content`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => apiRequest(`/api/filesystem/${id}`, { method: 'DELETE' }),
    restore: (id: number) => apiRequest(`/api/filesystem/${id}/restore`, { method: 'POST' }),
  },
  
  knowledgeGraph: {
    get: () => apiRequest('/api/knowledge-graph/'),
    refresh: () => apiRequest('/api/knowledge-graph/refresh', { method: 'POST' }),
    status: () => apiRequest('/api/knowledge-graph/status'),
  },

  search: {
    query: (q: string, limit?: number) => {
      const params = new URLSearchParams({ q });
      if (limit) params.set('limit', String(limit));
      return apiRequest(`/api/search?${params.toString()}`);
    },
  },

  embeddings: {
    backfill: (limit?: number) => {
      const params = limit ? `?limit=${limit}` : '';
      return apiRequest(`/api/embeddings/backfill${params}`, { method: 'POST' });
    },
    related: (fileId: number, topK?: number) => {
      const params = topK ? `?top_k=${topK}` : '';
      return apiRequest(`/api/embeddings/related/${fileId}${params}`);
    },
  },
};
