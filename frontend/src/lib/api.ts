/**
 * @author Huy Le (huyisme-005)
 * frontend/src/lib/api.ts
 *
 * Provides wrappers around backend ingestion endpoints.
 */

// Get API URL from environment or default to localhost
const getApiUrl = (): string => {
  if (typeof window !== 'undefined') {
    // Client-side
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }
  // Server-side
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_URL = getApiUrl();

/**
 * Check if backend is reachable
 */
const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_URL}/health`, { 
      method: 'GET',
      timeout: 5000 
    });
    return response.ok;
  } catch {
    return false;
  }
};

/**
 * POST /ingest/url to queue a URL scrape.
 *
 * @param teamId - Unique team identifier
 * @param url - Source URL to ingest
 * @returns JSON response from backend
 */
export async function ingestUrl(teamId: string, url: string) {
  try {
    console.log('API_URL:', API_URL);
    
    if (!teamId || !url) {
      throw new Error('Team ID and URL are required');
    }

    const form = new FormData();
    form.append("team_id", teamId);
    form.append("source_url", url);
    
    const fetchUrl = `${API_URL}/ingest/url`;
    console.log('Fetching URL:', fetchUrl);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
    const res = await fetch(fetchUrl, {
      method: "POST",
      body: form,
      signal: controller.signal,
      headers: {
        // Don't set Content-Type for FormData, let browser set it
      },
      // Add mode for CORS if needed
      mode: 'cors'
    });
    
    clearTimeout(timeoutId);
    
    console.log('Response status:', res.status);
    console.log('Response ok:', res.ok);
    
    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`HTTP ${res.status}: ${errorText || res.statusText}`);
    }
    
    const result = await res.json();
    console.log('Success response:', result);
    return result;
    
  } catch (error) {
    console.error('Error in ingestUrl:', error);
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return { error: 'Request timed out. Please check if the backend server is running.' };
      }
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        return { 
          error: `Cannot connect to backend server at ${API_URL}. Please ensure:
1. Backend server is running
2. Backend is accessible at ${API_URL}
3. No firewall blocking the connection
4. CORS is properly configured on backend`,
          details: error.message 
        };
      }
      return { error: error.message };
    }
    
    return { error: 'An unknown error occurred' };
  }
}

/**
 * POST /ingest/pdf to queue a PDF ingestion.
 *
 * @param teamId - Unique team identifier
 * @param file - Optional PDF File object
 * @param link - Optional Google Drive link
 * @returns JSON response from backend
 */
export async function ingestPdf(
  teamId: string,
  file?: File,
  link?: string
) {
  try {
    console.log('API_URL:', API_URL);
    
    if (!teamId) {
      throw new Error('Team ID is required');
    }
    
    if (!file && !link) {
      throw new Error('Either a PDF file or Google Drive link is required');
    }

    const form = new FormData();
    form.append("team_id", teamId);
    if (file) {
      console.log('Adding file:', file.name, 'Size:', file.size);
      form.append("pdf_file", file);
    }
    if (link) {
      console.log('Adding link:', link);
      form.append("pdf_link", link);
    }
    
    const fetchUrl = `${API_URL}/ingest/pdf`;
    console.log('Fetching URL:', fetchUrl);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout for file uploads
    
    const res = await fetch(fetchUrl, {
      method: "POST",
      body: form,
      signal: controller.signal,
      headers: {
        // Don't set Content-Type for FormData, let browser set it
      },
      // Add mode for CORS if needed
      mode: 'cors'
    });
    
    clearTimeout(timeoutId);
    
    console.log('Response status:', res.status);
    console.log('Response ok:', res.ok);
    
    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`HTTP ${res.status}: ${errorText || res.statusText}`);
    }
    
    const result = await res.json();
    console.log('Success response:', result);
    return result;
    
  } catch (error) {
    console.error('Error in ingestPdf:', error);
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return { error: 'Request timed out. Please check if the backend server is running.' };
      }
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        return { 
          error: `Cannot connect to backend server at ${API_URL}. Please ensure:
1. Backend server is running  
2. Backend is accessible at ${API_URL}
3. No firewall blocking the connection
4. CORS is properly configured on backend`,
          details: error.message 
        };
      }
      return { error: error.message };
    }
    
    return { error: 'An unknown error occurred' };
  }
}