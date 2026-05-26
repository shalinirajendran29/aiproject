import React, { useState, useEffect } from 'react';
import { 
  UploadCloud, Cpu, FileText, CheckCircle, Server, Globe, 
  RefreshCw, Play, Check, Eye, AlertCircle, HelpCircle, Save 
} from 'lucide-react';

export default function App() {
  // Connection states
  const [backendOnline, setBackendOnline] = useState(false);
  const [slmInfo, setSlmInfo] = useState({ model: 'Offline', url: '' });
  const [loadingStats, setLoadingStats] = useState(true);

  // Document states
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null); // 'uploading', 'preprocessing', 'ocr', 'slm', 'completed', 'failed'
  const [documentId, setDocumentId] = useState(null);
  const [documentData, setDocumentData] = useState(null);

  // Form Automation states
  const [targetUrl, setTargetUrl] = useState('http://localhost:8000/static/portal_form.html'); // Fallback URL
  const [crawledFields, setCrawledFields] = useState([]);
  const [crawling, setCrawling] = useState(false);
  const [filling, setFilling] = useState(false);
  const [fillResult, setFillResult] = useState(null);
  const [showScreenshot, setShowScreenshot] = useState(false);

  // Poll for document status
  useEffect(() => {
    let interval;
    if (documentId && (uploadProgress !== 'completed' && uploadProgress !== 'failed')) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/v1/documents/${documentId}`);
          if (res.ok) {
            const data = await res.json();
            setDocumentData(data);
            if (data.status === 'completed') {
              setUploadProgress('completed');
              clearInterval(interval);
            } else if (data.status === 'failed') {
              setUploadProgress('failed');
              clearInterval(interval);
            } else if (data.status === 'processing') {
              if (data.ocr_raw_text) {
                setUploadProgress('slm');
              } else {
                setUploadProgress('ocr');
              }
            }
          }
        } catch (e) {
          console.error(e);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [documentId, uploadProgress]);

  // Load backend stats
  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const res = await fetch('/api/v1/documents/upload', { method: 'OPTIONS' }).catch(() => null);
      const rootRes = await fetch('/').catch(() => null);
      
      if (rootRes && rootRes.ok) {
        const rootData = await rootRes.json();
        setBackendOnline(true);
        setSlmInfo({ model: rootData.slm_model, url: rootData.ollama_url });
      } else {
        setBackendOnline(false);
        setSlmInfo({ model: 'Offline', url: '' });
      }
    } catch (e) {
      setBackendOnline(false);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Setup target URL standard based on current origin if applicable
    const base = window.location.origin;
    setTargetUrl(`${base}/static/portal_form.html`);
  }, []);

  // Upload file handler
  const handleUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setUploadProgress('uploading');
    setFillResult(null);
    setCrawledFields([]);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('/api/v1/documents/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setDocumentId(data.id);
        setDocumentData(data);
        setUploadProgress('preprocessing');
      } else {
        setUploadProgress('failed');
      }
    } catch (err) {
      setUploadProgress('failed');
    }
  };

  // Update field value locally
  const handleFieldChange = (key, value) => {
    if (!documentData) return;
    const targetKey = documentData.corrected_json ? 'corrected_json' : 'extracted_json';
    const updatedFields = { 
      ...(documentData[targetKey] || documentData.extracted_json || {}), 
      [key]: value 
    };

    setDocumentData({
      ...documentData,
      corrected_json: updatedFields
    });
  };

  // Save changes to DB
  const saveCorrections = async () => {
    if (!documentId || !documentData) return;
    const dataToSend = documentData.corrected_json || documentData.extracted_json || {};
    try {
      const res = await fetch(`/api/v1/documents/${documentId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ corrected_json: dataToSend })
      });
      if (res.ok) {
        const updatedDoc = await res.json();
        setDocumentData(updatedDoc);
        alert('Corrections saved and mapping memory updated!');
      }
    } catch (e) {
      alert('Failed to save corrections.');
    }
  };

  // Crawl target page
  const crawlTarget = async () => {
    if (!targetUrl) return;
    setCrawling(true);
    try {
      const res = await fetch('/api/v1/automation/crawl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl })
      });
      if (res.ok) {
        const fields = await res.json();
        setCrawledFields(fields);
      } else {
        alert('Crawl failed. Check target URL.');
      }
    } catch (e) {
      alert('Crawl crashed.');
    } finally {
      setCrawling(false);
    }
  };

  // Trigger Fill
  const triggerAutoFill = async () => {
    if (!documentId || !targetUrl) return;
    setFilling(true);
    setFillResult(null);
    try {
      const res = await fetch('/api/v1/automation/fill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: documentId,
          target_url: targetUrl
        })
      });
      if (res.ok) {
        const result = await res.json();
        setFillResult(result);
        if (result.success) {
          setShowScreenshot(true);
        }
      } else {
        const err = await res.json();
        alert(`Fill Failed: ${err.detail || 'Internal Error'}`);
      }
    } catch (e) {
      alert('Autofill request crashed.');
    } finally {
      setFilling(false);
    }
  };

  // Get active form state keys
  const getActiveFields = () => {
    if (!documentData) return {};
    return documentData.corrected_json || documentData.extracted_json || {};
  };

  return (
    <div className="min-h-screen p-6 text-slate-100">
      {/* Top Header */}
      <header className="glass-panel p-4 mb-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-500/10 rounded-xl text-indigo-400">
            <Cpu className="w-8 h-8 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-teal-300 bg-clip-text text-transparent">
              Intelligent Form Automation Console
            </h1>
            <p className="text-xs text-slate-400">Small Language Model (SLM) Parsing & Form Autofilling</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/40 rounded-lg border border-slate-700/50">
            <Server className="w-4 h-4 text-indigo-400" />
            <span className="text-slate-400">Backend:</span>
            {backendOnline ? (
              <span className="text-teal-400 font-medium flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping"></span>
                Online
              </span>
            ) : (
              <span className="text-rose-400 font-medium">Offline</span>
            )}
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/40 rounded-lg border border-slate-700/50">
            <Cpu className="w-4 h-4 text-teal-400" />
            <span className="text-slate-400">Local SLM:</span>
            <span className="text-slate-200 font-semibold">{slmInfo.model || 'Offline'}</span>
          </div>

          <button 
            onClick={fetchStats}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors border border-slate-700/50"
            title="Refresh System Stats"
          >
            <RefreshCw className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <main className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Column 1: Upload & Document Viewer */}
        <section className="glass-panel p-6 flex flex-col gap-6">
          <h2 className="text-lg font-semibold flex items-center gap-2 border-b border-slate-800 pb-3 text-slate-300">
            <UploadCloud className="w-5 h-5 text-indigo-400" />
            1. Document Ingestion
          </h2>

          {/* Upload Area */}
          <div className="relative border-2 border-dashed border-slate-700/80 hover:border-indigo-400 rounded-xl p-8 flex flex-col items-center justify-center gap-3 transition-colors cursor-pointer bg-slate-900/20">
            <input 
              type="file" 
              accept="image/*,application/pdf"
              onChange={handleUpload}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />
            <UploadCloud className="w-10 h-10 text-slate-400" />
            <div className="text-center">
              <p className="text-sm font-semibold">Upload document</p>
              <p className="text-xs text-slate-500 mt-1">Supports JPG, PNG, Scanned PDFs</p>
            </div>
          </div>

          {/* Progress Tracker */}
          {uploadProgress && (
            <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Pipeline Status</h3>
              <div className="flex flex-col gap-3">
                {[
                  { key: 'uploading', label: 'Uploading Document' },
                  { key: 'preprocessing', label: 'OpenCV Denoise & Deskew' },
                  { key: 'ocr', label: 'EasyOCR Text Segmentation' },
                  { key: 'slm', label: 'SLM Semantic Field Parsing' },
                ].map((step, idx) => {
                  let statusColor = 'text-slate-500';
                  let icon = <div className="w-4 h-4 rounded-full border border-slate-600 flex items-center justify-center text-[10px]">{idx+1}</div>;

                  const stepIndex = ['uploading', 'preprocessing', 'ocr', 'slm'].indexOf(uploadProgress);
                  const currentIndex = ['uploading', 'preprocessing', 'ocr', 'slm'].indexOf(step.key);

                  if (uploadProgress === 'completed' || currentIndex < stepIndex) {
                    statusColor = 'text-teal-400';
                    icon = <Check className="w-4 h-4 text-teal-400" />;
                  } else if (uploadProgress === step.key) {
                    statusColor = 'text-indigo-400 font-medium';
                    icon = <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />;
                  } else if (uploadProgress === 'failed' && currentIndex >= stepIndex) {
                    statusColor = 'text-rose-400';
                    icon = <AlertCircle className="w-4 h-4 text-rose-400" />;
                  }

                  return (
                    <div key={step.key} className="flex items-center gap-3 text-sm">
                      {icon}
                      <span className={statusColor}>{step.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Document Preview */}
          {documentData && (
            <div className="flex-1 flex flex-col min-h-[220px]">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Source Document Preview</h3>
              <div className="flex-1 rounded-lg border border-slate-800 overflow-hidden bg-black/40 flex items-center justify-center relative p-2">
                <img 
                  src={`/static/${documentData.filename}`} 
                  alt="Original Document" 
                  className="max-h-[280px] max-w-full object-contain rounded"
                  onError={(e) => {
                    // Fallback representation if static is inaccessible
                    e.target.style.display = 'none';
                  }}
                />
                <div className="absolute bottom-2 left-2 bg-slate-900/80 px-2 py-1 rounded text-[10px] text-slate-400 border border-slate-800">
                  {documentData.filename}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Column 2: SLM Review Panel */}
        <section className="glass-panel p-6 flex flex-col gap-6">
          <h2 className="text-lg font-semibold flex items-center gap-2 border-b border-slate-800 pb-3 text-slate-300">
            <FileText className="w-5 h-5 text-indigo-400" />
            2. SLM Output & Human Verification
          </h2>

          {!documentData ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-500">
              <FileText className="w-12 h-12 stroke-[1.5] mb-2" />
              <p>Upload a document to extract data using local SLM models.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-5 flex-1">
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Confidence Score</span>
                <span className={`text-sm font-semibold px-2 py-0.5 rounded-full ${
                  documentData.confidence_score > 0.8 ? 'bg-teal-500/10 text-teal-400' : 'bg-amber-500/10 text-amber-400'
                }`}>
                  {Math.round(documentData.confidence_score * 100)}% Match
                </span>
              </div>

              {/* Editable Fields */}
              <div className="flex-1 flex flex-col gap-4 overflow-y-auto max-h-[420px] pr-1">
                {Object.entries(getActiveFields()).map(([key, val]) => (
                  <div key={key} className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-slate-400 capitalize">
                      {key.replace('_', ' ')}
                    </label>
                    <input 
                      type="text" 
                      value={val || ''}
                      onChange={(e) => handleFieldChange(key, e.target.value)}
                      className="input-glass w-full"
                      placeholder={`No ${key.replace('_', ' ')} identified`}
                    />
                  </div>
                ))}
              </div>

              {/* Save Corrections */}
              <button 
                onClick={saveCorrections}
                className="btn-premium w-full flex items-center justify-center gap-2 mt-auto"
              >
                <Save className="w-4 h-4" />
                Confirm & Learn Corrections
              </button>
            </div>
          )}
        </section>

        {/* Column 3: Playwright Automation */}
        <section className="glass-panel p-6 flex flex-col gap-6">
          <h2 className="text-lg font-semibold flex items-center gap-2 border-b border-slate-800 pb-3 text-slate-300">
            <Globe className="w-5 h-5 text-indigo-400" />
            3. Web Form Auto-Filling
          </h2>

          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-400">Target Website Portal</label>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  className="input-glass flex-1 text-xs"
                  placeholder="http://example.com/register"
                />
                <button 
                  onClick={crawlTarget}
                  disabled={crawling || !targetUrl}
                  className="px-3 py-2 bg-slate-800 border border-slate-700 hover:bg-slate-700 rounded-lg text-xs font-medium transition-colors disabled:opacity-40"
                >
                  {crawling ? 'Crawling...' : 'Scan Form'}
                </button>
              </div>
            </div>
          </div>

          {/* Form Match Mapper */}
          <div className="flex-1 flex flex-col min-h-[220px]">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Semantic Field Mapping Alignment</span>
            
            {crawledFields.length === 0 ? (
              <div className="flex-1 rounded-lg border border-slate-800/80 bg-slate-900/10 flex flex-col items-center justify-center text-center p-6 text-slate-500">
                <Globe className="w-10 h-10 stroke-[1.5] mb-2" />
                <p className="text-xs">Scan the target webpage to align and preview semantic matches.</p>
              </div>
            ) : (
              <div className="flex-1 border border-slate-800 rounded-lg overflow-y-auto max-h-[280px] p-3 flex flex-col gap-2.5 bg-black/20">
                {crawledFields.map((field) => {
                  // Figure out best guess mapping
                  // For demo, standard keywords
                  let matchedKey = null;
                  const labelLower = field.label.toLowerCase() || field.name.toLowerCase() || field.id.toLowerCase();
                  
                  if (labelLower.includes('name')) matchedKey = 'full_name';
                  else if (labelLower.includes('mail') || labelLower.includes('email')) matchedKey = 'email';
                  else if (labelLower.includes('phone') || labelLower.includes('tel') || labelLower.includes('contact')) matchedKey = 'phone';
                  else if (labelLower.includes('birth') || labelLower.includes('dob')) matchedKey = 'dob';
                  else if (labelLower.includes('address') || labelLower.includes('street')) matchedKey = 'address';
                  else if (labelLower.includes('card') || labelLower.includes('id') || labelLower.includes('passport')) matchedKey = 'id_number';

                  const extractedVal = getActiveFields()[matchedKey];

                  return (
                    <div key={field.selector} className="p-2.5 rounded bg-slate-900/60 border border-slate-800/80 flex flex-col gap-1.5 text-xs">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="text-slate-400 font-semibold">Web Selector: <code className="text-slate-300 bg-slate-800 px-1 rounded">{field.selector}</code></span>
                        {extractedVal ? (
                          <span className="text-teal-400 font-semibold bg-teal-400/10 px-1.5 py-0.5 rounded">Matched</span>
                        ) : (
                          <span className="text-slate-500">No Match</span>
                        )}
                      </div>
                      
                      <div className="flex items-center justify-between gap-1 text-[11px]">
                        <span className="text-slate-300 font-medium">🏷️ Label: "{field.label || field.name}"</span>
                        {extractedVal && (
                          <span className="text-slate-400 truncate max-w-[150px]">
                            ➡️ Value: "{extractedVal}"
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Trigger Playwright Filling */}
          <button 
            onClick={triggerAutoFill}
            disabled={filling || !documentId || crawledFields.length === 0}
            className="btn-premium w-full flex items-center justify-center gap-2 mt-auto"
          >
            <Play className="w-4 h-4 fill-current" />
            {filling ? 'Auto-filling form in Playwright...' : 'Execute Browser Autofill'}
          </button>
        </section>

      </main>

      {/* Screen Mockup / Modal for screenshot verification */}
      {showScreenshot && fillResult && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-panel max-w-4xl w-full flex flex-col overflow-hidden max-h-[90vh]">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center">
              <div className="flex items-center gap-2 text-teal-400">
                <CheckCircle className="w-5 h-5" />
                <span className="font-semibold text-sm">Browser Autofill Successful</span>
              </div>
              <button 
                onClick={() => setShowScreenshot(false)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-xs font-semibold"
              >
                Close View
              </button>
            </div>
            
            <div className="p-4 overflow-y-auto bg-slate-950 flex flex-col items-center gap-4">
              <p className="text-xs text-slate-400 text-center">
                Playwright has populated the page using semantic mappings. Below is the confirmation render captured from the browser context:
              </p>
              
              <div className="border border-slate-800 rounded-lg overflow-hidden shadow-2xl max-w-full">
                <img 
                  src={fillResult.screenshot_url} 
                  alt="Playwright Form Filling Result"
                  className="max-h-[60vh] object-contain"
                  onError={(e) => {
                    // Fallback demo indicator if image URL route fails
                    e.target.src = 'https://raw.githubusercontent.com/microsoft/playwright/main/packages/playwright-core/src/server/chromium/video.png';
                  }}
                />
              </div>

              <div className="w-full max-w-lg p-3 rounded bg-slate-900 border border-slate-800 text-[11px] text-left">
                <h4 className="font-semibold text-slate-300 mb-1">Populated SELECTORS:</h4>
                <ul className="list-disc list-inside text-slate-400">
                  {Object.entries(fillResult.mappings || {}).map(([sel, val]) => (
                    <li key={sel} className="truncate">
                      <code className="text-indigo-400 bg-black/40 px-1 rounded">{sel}</code> &larr; <span className="text-teal-400">"{val}"</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
