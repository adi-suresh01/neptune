// Try multiple ports for the backend
const POSSIBLE_PORTS = [8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009];

// Check if we're in production (Tauri) mode
function isProductionMode(): boolean {
  if (typeof window === 'undefined') return false;
  
  const isTauri = window.location.protocol === 'tauri:' || 
                  window.location.hostname === 'tauri.localhost' ||
                  // @ts-ignore
                  window.__TAURI__ !== undefined;
  
  console.log('🔍 Environment check:', {
    protocol: window.location.protocol,
    hostname: window.location.hostname,
    href: window.location.href,
    isTauri,
    // @ts-ignore
    hasTauriAPI: window.__TAURI__ !== undefined
  });
  
  return isTauri;
}

// Enhanced backend discovery with production support
async function findBackendUrl(): Promise<string> {
  console.log('🔍 Looking for Neptune backend...');
  console.log('🔍 Testing ports:', POSSIBLE_PORTS);
  
  const isProduction = isProductionMode();
  if (isProduction) {
    console.log('🖥️  Production mode detected - waiting for backend startup...');
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
  
  const results: Array<{port: number, status: string, error?: string, data?: any}> = [];
  
  for (const port of POSSIBLE_PORTS) {
    const url = `http://localhost:${port}`;
    try {
      console.log(`  🔍 Testing ${url}...`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      const response = await fetch(`${url}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      console.log(`  📊 ${url} response: ${response.status} ${response.statusText}`);
      
      if (response.ok) {
        try {
          const data = await response.json();
          console.log(`  📦 ${url} data:`, data);
          
          results.push({ port, status: 'success', data });
          
          // 👈 FIXED: Accept any healthy backend (more flexible)
          if (data.status === 'healthy') {
            console.log(`✅ Healthy backend found at ${url}`);
            return url;
          } else {
            console.log(`  ⚠️  ${url} returned non-healthy status:`, data);
          }
        } catch (jsonError) {
          console.log(`  ❌ ${url} returned invalid JSON:`, jsonError);
          results.push({ port, status: 'invalid_json', error: jsonError.message });
        }
      } else {
        console.log(`  ❌ ${url} returned ${response.status}: ${response.statusText}`);
        results.push({ port, status: `http_${response.status}` });
      }
    } catch (error) {
      console.log(`  ❌ ${url} failed:`, error.message);
      results.push({ port, status: 'error', error: error.message });
    }
  }
  
  console.log('🔍 Backend discovery results:', results);
  
  // If we found any responding servers (even if not healthy), show them
  const respondingServers = results.filter(r => r.status === 'success' || r.status.startsWith('http_'));
  if (respondingServers.length > 0) {
    console.log('📡 Found responding servers:', respondingServers);
  }
  
  throw new Error(`No healthy backend found. Tested ports: ${POSSIBLE_PORTS.join(', ')}`);
}

// Timeout wrapper for fetch
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
            console.log(`🔍 Attempt ${attempt + 1}: Discovering backend...`);
            currentBaseUrl = await findBackendUrl();
            API_BASE_URL = currentBaseUrl;
            hasTriedDiscovery = true;
            console.log(`🎯 Using ${currentBaseUrl}`);
          } catch (discoveryError) {
            console.log(`🔍 Discovery failed:`, discoveryError.message);
            if (attempt === 0) {
              console.log('⏳ Backend might still be starting...');
            }
          } finally {
            discoveryInProgress = false;
          }
        } else {
          console.log('⏳ Discovery already in progress, waiting...');
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      const url = `${currentBaseUrl}${endpoint}`;
      console.log(`📡 ${attempt + 1}/${maxRetries}: ${endpoint} → ${url}`);
      
      const response = await fetchWithTimeout(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Cache-Control': 'no-cache',
          ...options.headers,
        },
      }, isProduction ? 12000 : 6000);
      
      console.log(`📊 Response for ${endpoint}: ${response.status} ${response.statusText}`);
      
      if (response.ok) {
        console.log(`✅ Success: ${endpoint}`);
        return response;
      }
      
      if (response.status >= 400 && response.status < 500) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
    } catch (error) {
      const isLastAttempt = attempt === maxRetries - 1;
      
      console.log(`❌ ${attempt + 1}/${maxRetries} failed:`, error.message);
      
      // If it's a network error, reset discovery for next attempt
      if (error.name === 'AbortError' || error.message.includes('fetch') || error.message.includes('NetworkError')) {
        console.log('🔄 Network error detected, will rediscover backend on next attempt');
        hasTriedDiscovery = false;
      }
      
      if (isLastAttempt) {
        throw new Error(`Backend unavailable after ${maxRetries} attempts: ${error.message}`);
      }
      
      console.log(`⏳ Retrying in ${retryDelay}ms... (${maxRetries - attempt - 1} attempts left)`);
      await new Promise(resolve => setTimeout(resolve, retryDelay));
    }
  }
  
  throw new Error('Request failed');
};

export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    console.log('🩺 Health check starting...');
    const isProduction = isProductionMode();
    const response = await apiRequest('/health', {}, { 
      maxRetries: isProduction ? 15 : 6, 
      retryDelay: isProduction ? 2000 : 1500 
    });
    console.log('✅ Health check passed');
    return response.ok;
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    return false;
  }
};

// Force reset discovery (useful for debugging)
export const resetBackendDiscovery = () => {
  console.log('🔄 Resetting backend discovery...');
  API_BASE_URL = 'http://localhost:8000';
  discoveryInProgress = false;
};

// 👈 FIXED: Add trailing slashes and use correct endpoints
export const api = {
  health: () => apiRequest('/health'),
  
  filesystem: {
    list: () => apiRequest('/api/filesystem/'),  // 👈 Added trailing slash
    create: (data: any) => apiRequest('/api/filesystem/', { method: 'POST', body: JSON.stringify(data) }),  // 👈 Added trailing slash  
    get: (id: number) => apiRequest(`/api/filesystem/${id}`),
    update: (id: number, data: any) => apiRequest(`/api/filesystem/${id}/content`, { method: 'PUT', body: JSON.stringify(data) }),  // 👈 Use /content endpoint
    delete: (id: number) => apiRequest(`/api/filesystem/${id}`, { method: 'DELETE' }),
  },
  
  knowledgeGraph: {
    get: () => apiRequest('/api/knowledge-graph/'),  // 👈 Added trailing slash
    refresh: () => apiRequest('/api/knowledge-graph/refresh', { method: 'POST' }),
    status: () => apiRequest('/api/knowledge-graph/status'),
  },
};