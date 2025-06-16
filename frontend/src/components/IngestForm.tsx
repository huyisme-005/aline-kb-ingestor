/**
 * @author Huy Le (huyisme-005)
 * 
 * frontend/src/components/IngestForm.tsx
 *
 * React component rendering the ingestion form.
 */

import { useState, ChangeEvent, FormEvent } from "react";
import { ingestUrl, ingestPdf } from "../lib/api";

export default function IngestForm() {
  /**
   * Local component state for form inputs and feedback.
   */
  const [teamId, setTeamId] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [link, setLink] = useState("");
  const [message, setMessage] = useState("");

  /**
   * Handles form submission by choosing URL vs PDF ingestion.
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMessage("Submitting…");
    let res;
    if (url) {
      res = await ingestUrl(teamId, url);
    } else {
      res = await ingestPdf(teamId, file || undefined, link);
    }
    setMessage(JSON.stringify(res, null, 2));
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 600, margin: "auto" }}>
      <h1>KB Ingestor</h1>
      <label>
        Team ID
        <input
          value={teamId}
          onChange={(e) => setTeamId(e.target.value)}
          required
        />
      </label>
      <hr />
      <label>
        Blog/Guide URL
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://interviewing.io/blog"
        />
      </label>
      <p>— OR —</p>
      <label>
        PDF File
        <input
          type="file"
          accept="application/pdf"
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setFile(e.target.files?.[0] ?? null)
          }
        />
      </label>
      <label>
        PDF Drive Link
        <input
          value={link}
          onChange={(e) => setLink(e.target.value)}
          placeholder="https://drive.google.com/…"
        />
      </label>
      <button type="submit">Ingest</button>
      {message && <pre>{message}</pre>}
    </form>
  );
}
