/**
 * @author Huy Le (huyisme-005)
 * frontend/src/lib/api.ts
 *
 * Provides wrappers around backend ingestion endpoints.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Ensure API_URL is properly defined
if (!API_URL) {
  console.error('API_URL is not defined');
}

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
    console.log('Full URL:', `${API_URL}/ingest/url`);
    
    const form = new FormData();
    form.append("team_id", teamId);
    form.append("source_url", url);
    
    const fetchUrl = `${API_URL}/ingest/url`;
    console.log('Fetching:', fetchUrl);
    
    const res = await fetch(fetchUrl, {
      method: "POST",
      body: form
    });
    
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    
    return await res.json();
  } catch (error) {
    console.error('Error in ingestUrl:', error);
    return { error: error instanceof Error ? error.message : 'Unknown error occurred' };
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
    
    const form = new FormData();
    form.append("team_id", teamId);
    if (file) form.append("pdf_file", file);
    if (link) form.append("pdf_link", link);
    
    const fetchUrl = `${API_URL}/ingest/pdf`;
    console.log('Fetching:', fetchUrl);
    
    const res = await fetch(fetchUrl, {
      method: "POST",
      body: form
    });
    
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    
    return await res.json();
  } catch (error) {
    console.error('Error in ingestPdf:', error);
    return { error: error instanceof Error ? error.message : 'Unknown error occurred' };
  }
}