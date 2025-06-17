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
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${API_URL}/health`, { 
      method: 'GET',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
};

/**
 * Validate URL against supported domains
 */
const validateUrl = (url: string): { valid: boolean; message?: string } => {
  try {
    new URL(url);
  } catch {
    return { valid: false, message: 'Invalid URL format' };
  }

  const supportedPatterns = [
    'interviewing.io/blog',
    'interviewing.io/topics', 
    'interviewing.io/learn',
    'interviewing.io/guides', // Add this line to support /guides/ URLs
    'nilmamano.com/blog/category/dsa',
    'drive.google.com/drive/folders',
    '.substack.com' // Updated to match any Substack publication
  ];

  const isSupported = supportedPatterns.some(pattern => {
    if (pattern === '.substack.com') {
      // Special handling for Substack URLs
      try {
        const urlObj = new URL(url);
        return urlObj.hostname.endsWith('.substack.com');
      } catch {
        return false;
      }
    }
    return url.includes(pattern);
  });
  
  if (!isSupported) {
    return {
      valid: false,
      message: `Unsupported URL. Supported patterns: ${supportedPatterns.join(', ')}`
    };
  }

  // Additional validation for Google Drive URLs
  if (url.includes('drive.google.com')) {
    if (!url.includes('/drive/folders/')) {
      return {
        valid: false,
        message: 'Google Drive URLs must be folder links (e.g., https://drive.google.com/drive/folders/FOLDER_ID)'
      };
    }
  }

  // Additional validation for Substack URLs
  if (url.includes('substack.com')) {
    try {
      const urlObj = new URL(url);
      if (!urlObj.hostname.endsWith('.substack.com')) {
        return {
          valid: false,
          message: 'Substack URLs must be in format: https://publication.substack.com/'
        };
      }
      // Check if it's the base URL (not a specific post)
      if (urlObj.pathname.startsWith('/p/')) {
        return {
          valid: false,
          message: 'Please use the main Substack URL (e.g., https://publication.substack.com/) not a specific post URL'
        };
      }
    } catch {
      return {
        valid: false,
        message: 'Invalid Substack URL format'
      };
    }
  }

  return { valid: true };
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

    // Skip validation for localhost development to allow testing any URL
    const isLocalhost = typeof window !== 'undefined' && 
      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
    
    if (!isLocalhost) {
      // Only validate URLs in production
      const validation = validateUrl(url);
      if (!validation.valid) {
        return { error: validation.message };
      }
    }

    // Check backend health first
    const isHealthy = await checkBackendHealth();
    if (!isHealthy) {
      return {
        error: `Backend server is not responding at ${API_URL}. Please ensure:
1. Backend server is running (cd backend && python -m uvicorn api.main:app --reload)
2. Backend is accessible at ${API_URL}
3. No firewall blocking the connection`
      };
    }

    const form = new FormData();
    form.append("team_id", teamId);
    form.append("source_url", url);
    
    const fetchUrl = `${API_URL}/ingest/url`;
    console.log('Fetching URL:', fetchUrl);
    
    const controller = new AbortController();
    // Longer timeout for Google Drive and Substack as they might take more time
    const timeout = url.includes('drive.google.com') || url.includes('substack.com') ? 180000 : 60000;
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const res = await fetch(fetchUrl, {
      method: "POST",
      body: form,
      signal: controller.signal,
      mode: 'cors'
    });
    
    clearTimeout(timeoutId);
    
    console.log('Response status:', res.status);
    console.log('Response ok:', res.ok);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error response:', errorText);
      
      // Try to parse JSON error for better error messages
      try {
        const errorJson = JSON.parse(errorText);
        if (errorJson.detail) {
          throw new Error(errorJson.detail);
        }
      } catch (parseError) {
        // If not JSON, use the raw text
      }
      
      throw new Error(`HTTP ${res.status}: ${errorText || res.statusText}`);
    }
    
    const result = await res.json();
    console.log('Success response:', result);
    return result;
    
  } catch (error) {
    console.error('Error in ingestUrl:', error);
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return { error: 'Request timed out. Please check if the backend server is running and the URL is accessible. Substack ingestion may take longer than usual.' };
      }
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        return { 
          error: `Cannot connect to backend server at ${API_URL}. Please ensure:
1. Backend server is running (cd backend && python -m uvicorn api.main:app --reload)
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

    // Check backend health first
    const isHealthy = await checkBackendHealth();
    if (!isHealthy) {
      return {
        error: `Backend server is not responding at ${API_URL}. Please ensure the backend server is running.`
      };
    }

    const form = new FormData();
    form.append("team_id", teamId);
    
    if (file) {
      console.log('Adding file:', file.name, 'Size:', file.size);
      form.append("file", file); // Note: backend expects "file", not "pdf_file"
    }
    
    // Note: Your backend doesn't currently support PDF links, only file uploads
    if (link && !file) {
      return { error: 'PDF links are not currently supported. Please upload a PDF file directly.' };
    }
    
    const fetchUrl = `${API_URL}/ingest/pdf`;
    console.log('Fetching URL:', fetchUrl);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout for file uploads
    
    const res = await fetch(fetchUrl, {
      method: "POST",
      body: form,
      signal: controller.signal,
      mode: 'cors'
    });
    
    clearTimeout(timeoutId);
    
    console.log('Response status:', res.status);
    console.log('Response ok:', res.ok);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error('Error response:', errorText);
      
      // Try to parse JSON error for better error messages
      try {
        const errorJson = JSON.parse(errorText);
        if (errorJson.detail) {
          throw new Error(errorJson.detail);
        }
      } catch (parseError) {
        // If not JSON, use the raw text
      }
      
      throw new Error(`HTTP ${res.status}: ${errorText || res.statusText}`);
    }
    
    const result = await res.json();
    console.log('Success response:', result);
    return result;
    
  } catch (error) {
    console.error('Error in ingestPdf:', error);
  }
}