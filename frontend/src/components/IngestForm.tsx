/**
 * @author Huy Le (huyisme-005)
 * 
 * frontend/src/components/IngestForm.tsx
 *
 * React component rendering the ingestion form.
 */

import { useState, ChangeEvent, FormEvent, useEffect } from "react";
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
  const [isLocalhost, setIsLocalhost] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Supported URL patterns for easy reference
   */
  const supportedUrls = [
    "https://interviewing.io/blog",
    "https://interviewing.io/topics", 
    "https://interviewing.io/learn",
    "https://interviewing.io/guides",
    "https://nilmamano.com/blog/category/dsa",
    "https://drive.google.com/drive/folders/1AdUu4jh6DGwmCxfgnDQEMWWyo6_whPHJ",
    "https://drive.google.com/file/d/1khqaQ5NvkefQmG9pAEPlopT9Vi6cJk_4/view",
    "https://shreycation.substack.com/"
  ];

  /**
   * Check if running on localhost
   */
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      setIsLocalhost(hostname === 'localhost' || hostname === '127.0.0.1');
      
      // Set a default team ID for localhost
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        setTeamId('aline123');
      }
    }
  }, []);

  /**
   * Handles form submission by choosing URL vs PDF ingestion.
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage("Processing...");
    
    try {
      let res;
      if (url.trim()) {
        console.log('Submitting URL:', url);
        res = await ingestUrl(teamId, url.trim());
      } else if (file) {
        console.log('Submitting PDF file:', file.name);
        res = await ingestPdf(teamId, file, link.trim() || undefined);
      } else {
        setMessage("Please provide either a URL or upload a PDF file.");
        setIsLoading(false);
        return;
      }
      
      // Format the response for better readability
      if (res.error) {
        setMessage(`❌ Error: ${res.error}${res.details ? `\n\nDetails: ${res.details}` : ''}`);
      } else if (res.items && Array.isArray(res.items)) {
        setMessage(`✅ Success! Ingested ${res.items.length} items for team: ${res.team_id}\n\n${JSON.stringify(res, null, 2)}`);
      } else {
        setMessage(`✅ Response:\n${JSON.stringify(res, null, 2)}`);
      }
    } catch (error) {
      console.error('Form submission error:', error);
      setMessage(`❌ Unexpected error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle URL input changes and provide feedback
   */
  const handleUrlChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newUrl = e.target.value;
    setUrl(newUrl);
    
    // Clear file when URL is entered
    if (newUrl.trim() && file) {
      setFile(null);
    }
  };

  /**
   * Handle file input changes
   */
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] ?? null;
    setFile(selectedFile);
    
    // Clear URL when file is selected
    if (selectedFile && url.trim()) {
      setUrl("");
    }
  };

  /**
   * Set example URL
   */
  const setExampleUrl = (exampleUrl: string) => {
    setUrl(exampleUrl);
    setFile(null);
    setLink("");
  };

  /**
   * Get display name for URL
   */
  const getUrlDisplayName = (url: string) => {
    if (url.includes('interviewing.io/blog')) return 'Interviewing.io Blog';
    if (url.includes('interviewing.io/topics')) return 'Interviewing.io Topics';
    if (url.includes('interviewing.io/learn')) return 'Interviewing.io Learn';
    if(url.includes('interviewing.io/guides')) return 'Interviewing.io Guide';
    if (url.includes('nilmamano.com')) return 'Nil Mamano DSA Blog';
    if (url.includes('drive.google.com/drive/folders')) return 'Google Drive Folder';
    if (url.includes('drive.google.com/file/d/')) return 'Google Drive File';
    if (url.includes('shreycation.substack.com')) return 'Shreycation Substack';
    return url;
  };

  return (
    <div style={{ maxWidth: 800, margin: "auto", padding: "20px" }}>
      <h1>KB Ingestor</h1>
      <p>Ingest content from supported websites, Google Drive folders, Substack publications, or PDF files into your knowledge base.</p>
      
      <form onSubmit={handleSubmit}>
        {/* Only show Team ID input when NOT on localhost */}
        {!isLocalhost && (
          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
              Team ID *
            </label>
            <input
              value={teamId}
              onChange={(e) => setTeamId(e.target.value)}
              required
              style={{ width: "100%", padding: "8px", border: "1px solid #ccc", borderRadius: "4px" }}
              placeholder="Enter your team identifier"
            />
          </div>
        )}
        
        <div style={{ marginBottom: "20px" }}>
          <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
            Website URL / Google Drive / Substack
          </label>
          <input
            value={url}
            onChange={handleUrlChange}
            placeholder="Enter a supported URL"
            style={{ 
              width: "100%", 
              padding: "8px", 
              border: "1px solid #ccc", 
              borderRadius: "4px",
              marginBottom: "10px"
            }}
          />
          <div style={{ fontSize: "14px", color: "#666" }}>
            <strong>Suggested Sources:</strong>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
              {supportedUrls.map((supportedUrl, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => setExampleUrl(supportedUrl)}
                  className="example-url-btn"
                >
                  <span style={{ fontWeight: "500" }}>{getUrlDisplayName(supportedUrl)}</span>
                  <span style={{ fontSize: "11px", color: "#6c757d", fontFamily: "monospace" }}>
                    {supportedUrl.length > 50 ? `${supportedUrl.substring(0, 50)}...` : supportedUrl}
                  </span>
                </button>
              ))}
            </div>
            <div style={{ marginTop: "10px", fontSize: "12px", color: "#6c757d" }}>
              <strong>New Sources:</strong> Google Drive folders and Substack publications are now supported!
            </div>
          </div>
        </div>
        
        <div style={{ textAlign: "center", margin: "20px 0", fontSize: "16px", fontWeight: "bold" }}>
          — OR —
        </div>
        
        <div style={{ marginBottom: "20px" }}>
          <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
            PDF File
          </label>
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            style={{ 
              width: "100%", 
              padding: "8px", 
              border: "1px solid #ccc", 
              borderRadius: "4px",
              marginBottom: "5px"
            }}
          />
          <div style={{ fontSize: "12px", color: "#666" }}>
            Upload a PDF file to extract content chapters
          </div>
        </div>
        
        <button 
          type="submit" 
          disabled={isLoading || (!url.trim() && !file)}
          style={{
            width: "100%",
            padding: "12px",
            backgroundColor: isLoading || (!url.trim() && !file) ? "#ccc" : "#007bff",
            color: "white",
            border: "none",
            borderRadius: "4px",
            fontSize: "16px",
            cursor: isLoading || (!url.trim() && !file) ? "not-allowed" : "pointer",
            marginBottom: "20px"
          }}
        >
          {isLoading ? "Processing..." : "Ingest Content"}
        </button>
      </form>
      
      {message && (
        <div style={{
          marginTop: "20px",
          padding: "15px",
          backgroundColor: message.startsWith("❌") ? "#ffebee" : "#e8f5e8",
          border: `1px solid ${message.startsWith("❌") ? "#ffcdd2" : "#c8e6c8"}`,
          borderRadius: "4px",
          whiteSpace: "pre-wrap",
          fontFamily: "monospace",
          fontSize: "14px",
          maxHeight: "400px",
          overflow: "auto"
        }}>
          {message}
        </div>
      )}
      
      <div style={{ marginTop: "30px", fontSize: "12px", color: "#666" }}>
        <h3>Instructions:</h3>
        <ul>
          <li>For <strong>URL ingestion</strong>: Use one of the supported URL patterns above</li>
          <li>For <strong>Google Drive</strong>: Use the full folder URL (must be publicly accessible)</li>
          <li>For <strong>Substack</strong>: Use the publication's main URL</li>
          <li>For <strong>PDF ingestion</strong>: Upload a PDF file directly (max recommended: 10MB)</li>
          <li>Make sure your backend server is running: <code>cd backend && python -m uvicorn api.main:app --reload</code></li>
        </ul>
      </div>
    </div>
  );
}