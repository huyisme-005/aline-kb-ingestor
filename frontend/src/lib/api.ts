/**
 * @author Huy Le (huyisme-005)
 * frontend/src/lib/api.ts
 *
 * Provides wrappers around backend ingestion endpoints.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL;

/**
 * POST /ingest/url to queue a URL scrape.
 *
 * @param teamId - Unique team identifier
 * @param url - Source URL to ingest
 * @returns JSON response from backend
 */
export async function ingestUrl(teamId: string, url: string) {
  const form = new FormData();
  form.append("team_id", teamId);
  form.append("source_url", url);
  const res = await fetch(`${API_URL}/ingest/url`, {
    method: "POST",
    body: form
  });
  return res.json();
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
  const form = new FormData();
  form.append("team_id", teamId);
  if (file) form.append("pdf_file", file);
  if (link) form.append("pdf_link", link);
  const res = await fetch(`${API_URL}/ingest/pdf`, {
    method: "POST",
    body: form
  });
  return res.json();
}

