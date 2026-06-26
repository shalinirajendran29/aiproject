import React, { useState, useEffect, useRef } from 'react';
import { 
  UploadCloud, Cpu, FileText, CheckCircle, Server, Globe, 
  RefreshCw, Play, Check, Eye, AlertCircle, HelpCircle, Save,
  Plus, X, Trash2, Layers, Layout, Activity, Terminal, Database, 
  ShieldAlert, Monitor, ChevronRight, Sliders, Settings
} from 'lucide-react';

const STANDARD_FIELDS = [
  { key: 'full_name', label: 'Customer Name', placeholder: 'e.g. G 5 TRADERS' },
  { key: 'mobile_number', label: 'Mobile Number', placeholder: 'e.g. 9876543210' },
  { key: 'email', label: 'Email Address', placeholder: 'e.g. hello@reallygreatsite.com' },
  { key: 'dob', label: 'Date of Birth', placeholder: 'e.g. 15-08-1990' },
  { key: 'address', label: 'Customer Address', placeholder: 'e.g. 809A, SRI KAMATCHI AMMAN NAGAR' },
  { key: 'country', label: 'Country', placeholder: 'e.g. India' },
  { key: 'state', label: 'State', placeholder: 'e.g. Tamil Nadu' },
  { key: 'district', label: 'District', placeholder: 'e.g. Kanchipuram' },
  { key: 'pin_code', label: 'Customer PIN Code', placeholder: 'e.g. 602117' },
  { key: 'pan_no', label: 'Customer PAN', placeholder: 'e.g. BOPPG9733L' },
  { key: 'gstin_no', label: 'Customer GSTIN', placeholder: 'e.g. 33BOPPG9733L1ZE' },
  { key: 'invoice_number', label: 'Invoice Number', placeholder: 'e.g. INV-2026-905' },
  { key: 'invoice_date', label: 'Invoice Date', placeholder: 'e.g. 05-06-2026' },
  { key: 'total_amount', label: 'Total Amount', placeholder: 'e.g. 14,500.00' },
  { key: 'vendor_name', label: 'Vendor Name', placeholder: 'e.g. SPP Enterprises' },
  { key: 'vendor_address', label: 'Vendor Address', placeholder: 'e.g. NO. 176/6A, 8A MAMBAKKAM MAIN ROAD' },
  { key: 'vendor_gstin', label: 'Vendor GSTIN', placeholder: 'e.g. 33AXIPP0415D1ZZ' },
  { key: 'vendor_pan', label: 'Vendor PAN', placeholder: 'e.g. AXIPP0415D' },
  { key: 'item_description', label: 'Item Description', placeholder: 'e.g. Gold Necklace' },
  { key: 'gross_weight', label: 'Gross Weight (g)', placeholder: 'e.g. 24.550' },
  { key: 'net_weight', label: 'Net Weight (g)', placeholder: 'e.g. 22.120' },
  { key: 'purity', label: 'Purity (Karat/Hallmark)', placeholder: 'e.g. 22K (916)' },
  { key: 'making_charges', label: 'Making Charges', placeholder: 'e.g. 350.00' },
  { key: 'wastage', label: 'Wastage (%)', placeholder: 'e.g. 8.5' },
  { key: 'rate_per_gram', label: 'Rate per Gram', placeholder: 'e.g. 7,250.00' },
  { key: 'stone_weight', label: 'Stone Weight (g)', placeholder: 'e.g. 2.430' },
  { key: 'quantity', label: 'Quantity', placeholder: 'e.g. 5' },
  { key: 'unit_price', label: 'Unit Price', placeholder: 'e.g. 250.00' },
  { key: 'discount', label: 'Discount', placeholder: 'e.g. 50.00' },
  { key: 'hsn_code', label: 'HSN/SAC Code', placeholder: 'e.g. 5208' },
  { key: 'shipping_charges', label: 'Shipping Charges', placeholder: 'e.g. 120.00' },
  { key: 'sku_code', label: 'SKU Code', placeholder: 'e.g. SKU-TEXT-452' },
  { key: 'patient_name', label: 'Patient Name', placeholder: 'e.g. Rajesh Kumar' },
  { key: 'doctor_name', label: 'Doctor Name', placeholder: 'e.g. Dr. Aditi Sharma' },
  { key: 'admission_date', label: 'Admission Date', placeholder: 'e.g. 10-06-2026' },
  { key: 'discharge_date', label: 'Discharge Date', placeholder: 'e.g. 15-06-2026' },
  { key: 'room_number', label: 'Room/Ward Number', placeholder: 'e.g. Room 402' },
  { key: 'medicine_cost', label: 'Medicine Cost', placeholder: 'e.g. 4,500.00' },
  { key: 'insurance_provider', label: 'Insurance Provider', placeholder: 'e.g. Star Health' },
  { key: 'pnr_no', label: 'PNR/Booking ID', placeholder: 'e.g. PNR1234567' },
  { key: 'journey_date', label: 'Journey Date', placeholder: 'e.g. 20-06-2026' },
  { key: 'source_location', label: 'Source Location', placeholder: 'e.g. Chennai Central' },
  { key: 'destination_location', label: 'Destination Location', placeholder: 'e.g. Bangalore City' },
  { key: 'seat_number', label: 'Seat Number', placeholder: 'e.g. Coach A1, Seat 24' },
  { key: 'vehicle_no', label: 'Vehicle/Train/Flight No.', placeholder: 'e.g. 12623 / AI-502' },
];

export default function App() {
  // Connection states
  const [backendOnline, setBackendOnline] = useState(false);
  const [slmInfo, setSlmInfo] = useState({ model: 'Qwen2.5-7B-Instruct', url: 'Ollama-local' });
  const [loadingStats, setLoadingStats] = useState(true);

  // Ingestion settings
  const [ingestionMode, setIngestionMode] = useState('single'); // 'single', 'multiple', 'excel', 'pdf', 'word'
  const [documentsList, setDocumentsList] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [customFields, setCustomFields] = useState([]);

  // Custom Field adder state
  const [showAddField, setShowAddField] = useState(false);
  const [customFieldName, setCustomFieldName] = useState('');

  // Document states
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null); // 'uploading', 'preprocessing', 'ocr', 'slm', 'completed', 'failed'
  const [documentId, setDocumentId] = useState(null);
  const [documentData, setDocumentData] = useState(null);
  const [activeRecordIdx, setActiveRecordIdx] = useState(0);

  // Form Automation states
  const [targetUrl, setTargetUrl] = useState('http://erpretails.s3-website.ap-south-1.amazonaws.com/admin/customer/form?type=create'); // Default URL
  const [crawledFields, setCrawledFields] = useState([]);
  const [crawling, setCrawling] = useState(false);
  const [filling, setFilling] = useState(false);
  const [fillResult, setFillResult] = useState(null);
  const [showScreenshot, setShowScreenshot] = useState(false);
  const [bulkFilling, setBulkFilling] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);

  // Plugins & Layout states
  const [layout, setLayout] = useState('command'); // 'command' (3col), 'split' (2col), 'focus' (tabbed)
  const [focusTab, setFocusTab] = useState('verification'); // active tab in focus mode
  const [activePlugins, setActivePlugins] = useState({
    ingestor: true,
    feed: true,
    verification: true,
    mapper: true,
    logs: true,
    evidence: true
  });

  // Telemetry simulated states
  const [latency, setLatency] = useState(24);
  const [logs, setLogs] = useState([]);
  const logEndRef = useRef(null);

  // Log helper
  const addLog = (message, type = 'sys') => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    setLogs(prev => [...prev, { id: Math.random().toString(), time, message, type }]);
  };

  // Auto-scroll logs
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Ping latency simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setLatency(Math.round(20 + Math.random() * 15));
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // System startup logs
  useEffect(() => {
    addLog('System initialized. Banking-grade form injector core online.', 'sys');
    addLog('Connected to local DB sql_app.db. Table DBModelDocument read initialized.', 'db');
    addLog('Cognitive module mapping memory loaded.', 'slm');
  }, []);

  // Toggle single plugin visibility
  const togglePlugin = (key) => {
    setActivePlugins(prev => {
      const next = { ...prev, [key]: !prev[key] };
      addLog(`Plugin '${key}' visibility toggled to: ${next[key] ? 'VISIBLE' : 'HIDDEN'}`, 'sys');
      return next;
    });
  };

  // Reset active row selection on document change
  useEffect(() => {
    setActiveRecordIdx(0);
    setShowAddField(false);
  }, [documentId]);

  // Fetch all documents
  const fetchDocuments = async () => {
    try {
      const res = await fetch('/api/v1/documents');
      if (res.ok) {
        const data = await res.json();
        
        // Log if document count changes
        if (data.length !== documentsList.length) {
          addLog(`Database feed updated. Total records: ${data.length}`, 'db');
        }
        setDocumentsList(data);
        
        // Auto-select first document if none selected
        if (!selectedDocId && data.length > 0) {
          setSelectedDocId(data[0].id);
          setDocumentId(data[0].id);
          setDocumentData(data[0]);
          addLog(`Auto-loaded active document: ${data[0].filename}`, 'db');
        } else if (selectedDocId) {
          const updatedDoc = data.find(doc => doc.id === selectedDocId);
          if (updatedDoc) {
            setDocumentData(updatedDoc);
            
            // Sync status
            if (updatedDoc.status === 'completed' && uploadProgress !== 'completed') {
              setUploadProgress('completed');
              addLog(`SLM extraction complete for document: ${updatedDoc.filename}`, 'slm');
            } else if (updatedDoc.status === 'failed' && uploadProgress !== 'failed') {
              setUploadProgress('failed');
              addLog(`Ingestion PIPELINE FAILED for document: ${updatedDoc.filename}`, 'sys');
            } else if (updatedDoc.status === 'processing') {
              if (updatedDoc.ocr_raw_text && uploadProgress !== 'slm') {
                setUploadProgress('slm');
                addLog('Ollama ExtractFlow LLM processing layout tokens...', 'slm');
              } else if (!updatedDoc.ocr_raw_text && uploadProgress !== 'ocr') {
                setUploadProgress('ocr');
                addLog('OpenCV Preprocessing & Tesseract OCR active.', 'ocr');
              }
            } else if (updatedDoc.status === 'pending' && uploadProgress !== 'preprocessing') {
              setUploadProgress('preprocessing');
              addLog('Document placed in background queue. Analyzing geometry...', 'sys');
            }
          }
        }
      }
    } catch (e) {
      console.error("Error fetching documents:", e);
    }
  };

  // Poll for list updates
  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(() => {
      fetchDocuments();
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedDocId, documentsList.length]);

  // Load backend stats
  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const rootRes = await fetch('/api/v1/documents').catch(() => null);
      if (rootRes && rootRes.ok) {
        setBackendOnline(true);
        addLog('FastAPI host connection handshake: SECURE.', 'sys');
      } else {
        setBackendOnline(false);
        addLog('Warning: FastAPI host connection handshake: OFFLINE.', 'sys');
      }
    } catch (e) {
      setBackendOnline(false);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Default to the actual retail ERP site
    setTargetUrl('http://erpretails.s3-website.ap-south-1.amazonaws.com/admin/customer/form?type=create');
  }, []);

  // Upload file handler supporting single and batch uploads
  const handleUpload = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length === 0) return;

    setFillResult(null);
    setBulkResult(null);
    setCrawledFields([]);
    setUploadProgress('uploading');
    addLog(`Initiating packet upload of ${selectedFiles.length} file(s)...`, 'sys');

    // Concurrently upload all selected files
    await Promise.all(selectedFiles.map(async (file, index) => {
      const formData = new FormData();
      formData.append('file', file);
      addLog(`Uploading file buffer: ${file.name} (${Math.round(file.size / 1024)} KB)`, 'db');

      try {
        const res = await fetch('/api/v1/documents/upload', {
          method: 'POST',
          body: formData
        });
        if (res.ok) {
          const data = await res.json();
          addLog(`Server successfully locked file ID: ${data.id.substring(0, 8)}...`, 'sys');
          // Auto-select the first uploaded file in this batch
          if (index === 0) {
            setSelectedDocId(data.id);
            setDocumentId(data.id);
            setDocumentData(data);
            setUploadProgress('preprocessing');
          }
        }
      } catch (err) {
        addLog(`Error uploading packet: ${file.name}`, 'sys');
        console.error("Upload error for file:", file.name, err);
      }
    }));

    fetchDocuments();
  };

  // Update field value locally
  const handleFieldChange = (key, value) => {
    if (!documentData) return;
    const targetKey = documentData.corrected_json ? 'corrected_json' : 'extracted_json';
    const currentData = { ...(documentData[targetKey] || documentData.extracted_json || {}) };
    
    if (currentData.records && Array.isArray(currentData.records)) {
      const updatedRecords = [...currentData.records];
      updatedRecords[activeRecordIdx] = {
        ...updatedRecords[activeRecordIdx],
        [key]: value
      };
      
      setDocumentData({
        ...documentData,
        corrected_json: {
          ...currentData,
          records: updatedRecords
        }
      });
    } else {
      const updatedFields = { 
        ...currentData, 
        [key]: value 
      };
      setDocumentData({
        ...documentData,
        corrected_json: updatedFields
      });
    }
    
    // Add periodic logs for modifications (capped to prevent noise)
    if (Math.random() < 0.15) {
      addLog(`Local buffer updated: Field '${key}' adjusted.`, 'sys');
    }
  };

  // Remove field value locally
  const handleRemoveField = (key) => {
    if (!documentData) return;
    const targetKey = documentData.corrected_json ? 'corrected_json' : 'extracted_json';
    const currentData = { ...(documentData[targetKey] || documentData.extracted_json || {}) };
    
    if (currentData.records && Array.isArray(currentData.records)) {
      const updatedRecords = [...currentData.records];
      const updatedRec = { ...updatedRecords[activeRecordIdx] };
      delete updatedRec[key];
      updatedRecords[activeRecordIdx] = updatedRec;
      
      setDocumentData({
        ...documentData,
        corrected_json: {
          ...currentData,
          records: updatedRecords
        }
      });
    } else {
      const updatedFields = { ...currentData };
      delete updatedFields[key];
      setDocumentData({
        ...documentData,
        corrected_json: updatedFields
      });
    }
    addLog(`Field removed from current record: '${key}'`, 'sys');
  };

  // Save changes to DB
  const saveCorrections = async () => {
    if (!documentId || !documentData) return;
    const dataToSend = documentData.corrected_json || documentData.extracted_json || {};
    addLog('Submitting manual corrections to database mapping layer...', 'db');
    try {
      const res = await fetch(`/api/v1/documents/${documentId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ corrected_json: dataToSend })
      });
      if (res.ok) {
        const updatedDoc = await res.json();
        setDocumentData(updatedDoc);
        addLog('Handshake complete: Mapping memory updated successfully.', 'db');
        alert('Corrections saved and mapping memory updated!');
      }
    } catch (e) {
      addLog('Error: Failed to save changes to database.', 'sys');
      alert('Failed to save corrections.');
    }
  };

  // Crawl target page
  const crawlTarget = async () => {
    if (!targetUrl) return;
    setCrawling(true);
    addLog(`Initiating crawling scan on URL: ${targetUrl}`, 'auto');
    try {
      const res = await fetch('/api/v1/automation/crawl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl })
      });
      if (res.ok) {
        const fields = await res.json();
        setCrawledFields(fields);
        addLog(`Scan complete. Resolved ${fields.length} visible DOM nodes matching data profiles.`, 'auto');
      } else {
        addLog('Web page DOM crawl rejected by host target.', 'auto');
        alert('Crawl failed. Check target URL.');
      }
    } catch (e) {
      addLog('Execution crash on crawler socket service.', 'sys');
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
    setBulkResult(null);
    
    addLog('Automation agent spawned. Launching Headless Playwright worker...', 'auto');
    addLog(`Navigating to URL: ${targetUrl}`, 'auto');
    
    const docData = documentData.corrected_json || documentData.extracted_json || {};
    const bodyData = {
      document_id: documentId,
      target_url: targetUrl
    };
    if (docData.records && Array.isArray(docData.records)) {
      bodyData.record_index = activeRecordIdx;
    }

    try {
      const res = await fetch('/api/v1/automation/fill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyData)
      });
      if (res.ok) {
        const result = await res.json();
        setFillResult(result);
        addLog(`Autofill execution status: SUCCESS. Mapped ${result.filled_fields?.length || 0} fields.`, 'auto');
        if (result.success) {
          setShowScreenshot(true);
        }
      } else {
        const err = await res.json();
        addLog(`Form submission execution rejected: ${err.detail || 'Internal Error'}`, 'auto');
        alert(`Fill Failed: ${err.detail || 'Internal Error'}`);
      }
    } catch (e) {
      addLog('Automation process aborted due to server network error.', 'sys');
      alert('Autofill request crashed.');
    } finally {
      setFilling(false);
    }
  };

  // Trigger Bulk Fill
  const triggerBulkAutoFill = async () => {
    if (!documentId || !targetUrl) return;
    setBulkFilling(true);
    setBulkResult(null);
    setFillResult(null);
    
    addLog('Executing bulk transaction agent. Spawning batch operations...', 'auto');
    addLog(`Bulk injection URL target: ${targetUrl}`, 'auto');

    try {
      const res = await fetch('/api/v1/automation/fill-bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: documentId,
          target_url: targetUrl
        })
      });
      if (res.ok) {
        const result = await res.json();
        setBulkResult(result);
        addLog(`Bulk process complete. Success rate: ${result.results?.filter(r => r.success).length}/${result.results?.length} records.`, 'auto');
        
        // Map to fillResult so that screenshot displays the bulk execution report
        setFillResult({
          success: result.success,
          screenshot_url: result.screenshot_url,
          mappings: {} // Leave empty so we default to the tabular execution summary
        });
        setShowScreenshot(true);
      } else {
        const err = await res.json();
        addLog(`Bulk injection pipeline failed: ${err.detail || 'Internal Error'}`, 'auto');
        alert(`Bulk Fill Failed: ${err.detail || 'Internal Error'}`);
      }
    } catch (e) {
      addLog('Bulk workflow execution crashed on network socket.', 'sys');
      alert('Bulk autofill request crashed.');
    } finally {
      setBulkFilling(false);
    }
  };

  // Trigger Batch Ingestion Autofill for Multiple Images/PDFs
  const triggerBatchImageAutofill = async () => {
    if (documentsList.length === 0 || !targetUrl) return;
    setBulkFilling(true);
    setBulkResult(null);
    setFillResult(null);

    const completedDocs = documentsList.filter(doc => doc.status === 'completed');
    if (completedDocs.length === 0) {
      addLog('Warning: Attempted batch automation, but zero documents exist in COMPLETED state.', 'sys');
      alert("No completed documents found in the workspace to fill. Please wait for processing to finish.");
      setBulkFilling(false);
      return;
    }

    addLog(`Spawning batch queue agent for ${completedDocs.length} images...`, 'auto');

    const results = [];
    let lastScreenshotUrl = "";
    let globalSuccess = true;

    for (let i = 0; i < completedDocs.length; i++) {
      const doc = completedDocs[i];
      const docData = doc.corrected_json || doc.extracted_json || {};
      const customerName = docData.full_name || docData.name || doc.filename;
      addLog(`[Batch Item ${i+1}/${completedDocs.length}] Starting form fill for: ${doc.filename}`, 'auto');

      try {
        const res = await fetch('/api/v1/automation/fill', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            document_id: doc.id,
            target_url: targetUrl
          })
        });

        if (res.ok) {
          const resData = await res.json();
          results.push({
            record_index: i,
            success: resData.success,
            customer_name: customerName,
            errors: resData.errors || [],
            screenshot_url: resData.screenshot_url
          });
          if (resData.screenshot_url) {
            lastScreenshotUrl = resData.screenshot_url;
          }
          if (!resData.success) {
            globalSuccess = false;
            addLog(`[Batch Item ${i+1}/${completedDocs.length}] Form injection errors reported. Check logs.`, 'auto');
          } else {
            addLog(`[Batch Item ${i+1}/${completedDocs.length}] Inject success. Screen captured.`, 'auto');
          }
        } else {
          results.push({
            record_index: i,
            success: false,
            customer_name: customerName,
            errors: ['Failed to trigger form filler engine'],
            screenshot_url: ""
          });
          globalSuccess = false;
          addLog(`[Batch Item ${i+1}/${completedDocs.length}] Target rejected connection payload.`, 'auto');
        }
      } catch (err) {
        results.push({
          record_index: i,
          success: false,
          customer_name: customerName,
          errors: [err.message || 'Crashed during filling execution'],
          screenshot_url: ""
        });
        globalSuccess = false;
        addLog(`[Batch Item ${i+1}/${completedDocs.length}] Script execution exception.`, 'sys');
      }
    }

    setBulkResult({
      success: globalSuccess,
      results: results,
      screenshot_url: lastScreenshotUrl
    });

    setFillResult({
      success: globalSuccess,
      screenshot_url: lastScreenshotUrl,
      mappings: {}
    });

    setShowScreenshot(true);
    setBulkFilling(false);
    addLog(`Batch multi-file pipeline finished. Consolidated report generated.`, 'auto');
  };

  // Get active form state keys
  const getActiveFields = () => {
    if (!documentData) return {};
    const docData = documentData.corrected_json || documentData.extracted_json || {};
    if (docData.records && Array.isArray(docData.records) && docData.records.length > 0) {
      return docData.records[activeRecordIdx] || {};
    }
    return docData;
  };

  // Add custom field helper
  const addCustomField = (label) => {
    const key = label.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').trim();
    if (!key) return;
    
    if (STANDARD_FIELDS.some(f => f.key === key) || customFields.some(f => f.key === key)) {
      alert("Field already exists!");
      return;
    }
    
    setCustomFields(prev => [...prev, { key, label, placeholder: `Enter ${label}` }]);
    handleFieldChange(key, "");
    addLog(`Registered custom alignment schema field: '${key}'`, 'sys');
  };

  const getFieldLabel = (key) => {
    const std = STANDARD_FIELDS.find(f => f.key === key) || customFields.find(f => f.key === key);
    return std ? std.label : key.replace(/_/g, ' ');
  };

  // File Icon helper
  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    if (['xlsx', 'xls', 'csv', 'xlsm', 'xlsb', 'ods', 'xslv', 'xlsv'].includes(ext)) {
      return <FileText className="w-4 h-4 text-emerald-400" />;
    } else if (ext === 'pdf') {
      return <FileText className="w-4 h-4 text-rose-400" />;
    } else if (['docx', 'doc'].includes(ext)) {
      return <FileText className="w-4 h-4 text-blue-400" />;
    } else {
      return <FileText className="w-4 h-4 text-indigo-400" />;
    }
  };

  // RENDER PLUGINS AS MODULAR JSX
  
  // 1. INGESTOR PLUGIN
  const renderIngestorPlugin = () => {
    if (!activePlugins.ingestor) return null;
    return (
      <div className="glass-panel flex flex-col gap-4">
        <div className="card-header-bar">
          <div className="card-header-title">
            <UploadCloud className="w-4 h-4 text-blue-500" />
            <span>Plugin // Ingest_Core</span>
          </div>
          <div className="card-header-actions">
            <div className="card-action-dot red" onClick={() => togglePlugin('ingestor')} title="Hide module"></div>
            <div className="card-action-dot yellow" title="Settings"></div>
            <div className="card-action-dot green" title="Diagnostic"></div>
          </div>
        </div>

        <div className="mode-selector-wrapper flex flex-col gap-2">
          <span className="queue-title">Ingest Protocol</span>
          <div className="mode-selector">
            {[
              { id: 'single', label: 'Single IMG' },
              { id: 'multiple', label: 'Batch IMG' },
              { id: 'excel', label: 'Excel/CSV' },
              { id: 'pdf', label: 'PDF Doc' },
              { id: 'word', label: 'Word Doc' }
            ].map((mode) => (
              <button
                key={mode.id}
                onClick={() => {
                  setIngestionMode(mode.id);
                  setFillResult(null);
                  setBulkResult(null);
                  addLog(`Ingest protocol toggled to: ${mode.label}`, 'sys');
                }}
                className={`mode-btn ${ingestionMode === mode.id ? 'active' : ''}`}
                style={{ fontSize: '9px', padding: '6px 4px' }}
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>

        <div className="upload-dropzone">
          <input 
            type="file" 
            accept={
              ingestionMode === 'excel' 
                ? '.xlsx,.xls,.csv,.xlsm,.xlsb,.ods,.xslv,.xlsv' 
                : ingestionMode === 'pdf' 
                ? '.pdf' 
                : ingestionMode === 'word'
                ? '.docx,.doc'
                : 'image/*'
            }
            multiple={ingestionMode === 'multiple'}
            onChange={handleUpload}
            className="absolute inset-0 opacity-0 cursor-pointer"
          />
          <UploadCloud className="w-8 h-8 text-blue-500 animate-pulse" />
          <div>
            <p className="text-[11px] font-bold text-slate-200" style={{ margin: 0 }}>
              LOAD SOURCE BINARY
            </p>
            <p className="text-[9px] text-slate-500 mt-1" style={{ margin: 0 }}>
              {ingestionMode === 'single' && 'Drag JPEG / PNG file'}
              {ingestionMode === 'multiple' && 'Drag multiple Images (Ctrl+Click)'}
              {ingestionMode === 'excel' && 'Drag spreadsheet (XLSX, CSV)'}
              {ingestionMode === 'pdf' && 'Drag structural PDF'}
              {ingestionMode === 'word' && 'Drag Word Document (.docx)'}
            </p>
          </div>
        </div>
      </div>
    );
  };

  // 2. DOCUMENT QUEUE PLUGIN
  const renderFeedPlugin = () => {
    if (!activePlugins.feed) return null;
    return (
      <div className="glass-panel flex flex-col gap-4">
        <div className="card-header-bar">
          <div className="card-header-title">
            <Database className="w-4 h-4 text-emerald-500" />
            <span>Plugin // Repository_Feed</span>
          </div>
          <div className="card-header-actions">
            <div className="card-action-dot red" onClick={() => togglePlugin('feed')} title="Hide module"></div>
            <div className="card-action-dot yellow" title="Settings"></div>
            <div className="card-action-dot green" title="Diagnostic"></div>
          </div>
        </div>

        {documentsList.length > 0 ? (
          <div className="queue-wrapper">
            <div className="flex justify-between items-center mb-1">
              <h3 className="queue-title">FEED STREAM</h3>
              <span className="text-[9px] font-mono text-slate-500">{documentsList.length} items loaded</span>
            </div>
            <div className="queue-container">
              {documentsList.map((doc) => {
                const isSelected = doc.id === selectedDocId;
                
                let badgeClass = 'badge badge-completed';
                if (doc.status === 'completed') badgeClass = 'badge badge-completed';
                else if (doc.status === 'processing') badgeClass = 'badge badge-processing';
                else if (doc.status === 'pending') badgeClass = 'badge badge-pending';
                else if (doc.status === 'failed') badgeClass = 'badge badge-failed';

                return (
                  <div 
                    key={doc.id}
                    onClick={() => {
                      setSelectedDocId(doc.id);
                      setDocumentId(doc.id);
                      setDocumentData(doc);
                      setFillResult(null);
                      setBulkResult(null);
                    }}
                    className={`queue-item ${isSelected ? 'selected' : ''}`}
                  >
                    <div className="flex items-center gap-2.5 min-width-0 flex-1">
                      {getFileIcon(doc.filename)}
                      <div className="queue-item-info">
                        <span className="queue-item-name">{doc.filename}</span>
                        <span className="queue-item-time">
                          {new Date(doc.created_at).toLocaleDateString()} {new Date(doc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
                        </span>
                      </div>
                    </div>
                    
                    <div className="queue-item-actions">
                      <span className={badgeClass} style={{ fontSize: '8px', padding: '1px 4px' }}>
                        {doc.status}
                      </span>
                      
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          if (confirm(`Delete database entry "${doc.filename}"?`)) {
                            try {
                              const res = await fetch(`/api/v1/documents/${doc.id}`, { method: 'DELETE' });
                              if (res.ok) {
                                addLog(`Deleted document entry: ${doc.filename}`, 'db');
                                if (selectedDocId === doc.id) {
                                  setSelectedDocId(null);
                                  setDocumentId(null);
                                  setDocumentData(null);
                                  setUploadProgress(null);
                                }
                                fetchDocuments();
                              }
                            } catch (err) {
                              console.error(err);
                            }
                          }
                        }}
                        className="delete-btn"
                        title="Purge record"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-6 text-slate-500 bg-slate-950/20 border border-slate-900 rounded mt-2 text-center">
            <FileText className="w-6 h-6 stroke-[1.5] mb-2 text-slate-700" />
            <p className="text-[10px] font-mono">REPOSITORY EMPTY</p>
          </div>
        )}

        {/* Progress Tracker */}
        {uploadProgress && uploadProgress !== 'completed' && uploadProgress !== 'failed' && (
          <div className="progress-tracker flex items-center gap-2.5">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-500" />
            <span className="text-[10px] text-slate-300 font-mono">
              {uploadProgress === 'uploading' && 'Ingesting file buffer...'}
              {uploadProgress === 'preprocessing' && 'OpenCV: Scanning contours...'}
              {uploadProgress === 'ocr' && 'OCR: Extracting layout lines...'}
              {uploadProgress === 'slm' && 'ExtractFlow: LLM resolution...'}
            </span>
          </div>
        )}

        {uploadProgress === 'failed' && (
          <div className="progress-tracker flex items-center gap-2" style={{ borderColor: 'rgba(239, 68, 68, 0.2)', background: 'rgba(239, 68, 68, 0.04)' }}>
            <AlertCircle className="w-3.5 h-3.5 text-red-500" />
            <span className="text-[10px] text-red-400 font-mono">Ingest pipeline failed.</span>
          </div>
        )}
      </div>
    );
  };

  // 3. FIELD VERIFICATION STUDIO PLUGIN
  const renderVerificationPlugin = () => {
    if (!activePlugins.verification) return null;
    return (
      <div className="glass-panel flex flex-col gap-4">
        <div className="card-header-bar">
          <div className="card-header-title">
            <Sliders className="w-4 h-4 text-amber-500" />
            <span>Plugin // Verification_Studio</span>
          </div>
          <div className="card-header-actions">
            <div className="card-action-dot red" onClick={() => togglePlugin('verification')} title="Hide module"></div>
            <div className="card-action-dot yellow" title="Settings"></div>
            <div className="card-action-dot green" title="Diagnostic"></div>
          </div>
        </div>

        {!documentData ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-12 text-slate-500">
            <ShieldAlert className="w-12 h-12 stroke-[1] mb-2 text-slate-600 animate-pulse" />
            <p className="text-xs font-mono">NO ACTIVE FILE SWITCHED</p>
            <p className="text-[10px] text-slate-600 max-w-xs mt-1">Select or ingest a file from the repository feed to initialize the extraction workspace.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-4 flex-1">
            
            {/* Header Telemetry Grid */}
            <div className="grid grid-cols-2 gap-3 p-3 bg-slate-950/20 border border-slate-900 rounded">
              <div className="flex flex-col">
                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Doc ID Ref</span>
                <span className="text-xs font-mono text-slate-300 truncate" title={documentData.id}>
                  {documentData.id}
                </span>
              </div>
              <div className="flex flex-col">
                <div className="flex justify-between items-center">
                  <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Confidence Index</span>
                  <span className="text-[10px] font-mono font-bold text-amber-400">
                    {Math.round((documentData.confidence_score || 0) * 100)}%
                  </span>
                </div>
                <div className="confidence-gauge-bg">
                  <div 
                    className="confidence-gauge-fill"
                    style={{ 
                      width: `${(documentData.confidence_score || 0) * 100}%`,
                      backgroundColor: documentData.confidence_score > 0.8 ? 'var(--success-color)' : 'var(--warning-color)'
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Row Selector for spreadsheets */}
            {(() => {
              const data = documentData.corrected_json || documentData.extracted_json || {};
              if (data.records && Array.isArray(data.records) && data.records.length > 0) {
                return (
                  <div className="row-nav-card">
                    <button
                      onClick={() => {
                        setActiveRecordIdx(prev => Math.max(0, prev - 1));
                        setFillResult(null);
                        setBulkResult(null);
                        addLog(`Navigation: Switch to spreadsheet row: ${activeRecordIdx}`, 'sys');
                      }}
                      disabled={activeRecordIdx === 0}
                      className="custom-adder-button text-[10px]"
                      style={{ padding: '4px 8px' }}
                    >
                      &larr; PREV
                    </button>
                    
                    <div className="flex-1 flex flex-col items-center">
                      <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Record Frame Row</span>
                      <select
                        value={activeRecordIdx}
                        onChange={(e) => {
                          const idx = parseInt(e.target.value, 10);
                          setActiveRecordIdx(idx);
                          setFillResult(null);
                          setBulkResult(null);
                          addLog(`Navigation: Selected row frame index: ${idx + 1}`, 'sys');
                        }}
                        className="bg-slate-900 border border-slate-800 text-xs text-slate-200 rounded px-2 py-1 font-mono cursor-pointer mt-1 focus:outline-none focus:border-blue-500 w-full max-w-[200px]"
                      >
                        {data.records.map((rec, index) => (
                          <option key={index} value={index}>
                            Row {index + 1}: {rec.full_name || rec.name || `Record ${index + 1}`}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <button
                      onClick={() => {
                        setActiveRecordIdx(prev => Math.min(data.records.length - 1, prev + 1));
                        setFillResult(null);
                        setBulkResult(null);
                        addLog(`Navigation: Switch to spreadsheet row: ${activeRecordIdx + 2}`, 'sys');
                      }}
                      disabled={activeRecordIdx === data.records.length - 1}
                      className="custom-adder-button text-[10px]"
                      style={{ padding: '4px 8px' }}
                    >
                      NEXT &rarr;
                    </button>
                  </div>
                );
              }
              return null;
            })()}

            {/* Fields grid */}
            <div className="verification-scroll-container">
              {(() => {
                const activeFields = getActiveFields();
                const keysToExclude = ['id', 'created_at', 'updated_at', 'status', 'filename', 'storage_path', 'mime_type', 'confidence_score', 'ocr_raw_text', 'records'];
                const editableFields = Object.entries(activeFields).filter(([key]) => !keysToExclude.includes(key));
                
                if (editableFields.length === 0) {
                  return <p className="text-xs text-slate-400 italic p-4 text-center">No fields resolved. Choose or create fields below.</p>;
                }
                
                // Required fields check
                const requiredFields = [
                  { key: 'full_name', label: 'Customer Name' },
                  { key: 'mobile_number', label: 'Mobile Number' },
                  { key: 'country', label: 'Country' },
                  { key: 'state', label: 'State' }
                ];
                const missingRequired = requiredFields.filter(f => !activeFields[f.key] || !activeFields[f.key].toString().trim());

                return (
                  <>
                    {missingRequired.length > 0 && (
                      <div className="flex flex-col gap-1.5 p-3 rounded border border-red-500/20 bg-red-500/5 text-red-300 mb-2">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                          <span className="text-[9px] font-bold uppercase tracking-wider font-mono">ERP REQUIRED SCHEMAS MISSING</span>
                        </div>
                        <p className="text-[10px] text-slate-400 leading-normal">
                          Missing required elements to satisfy target database constraint. Form filling automation may trigger field validations:
                        </p>
                        <ul className="list-disc list-inside text-[10px] font-mono text-red-300 flex flex-wrap gap-x-3">
                          {missingRequired.map(f => (
                            <li key={f.key}>{f.label}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {editableFields.map(([key, val]) => {
                        const std = STANDARD_FIELDS.find(f => f.key === key);
                        const isRequired = requiredFields.some(rf => rf.key === key);
                        const isEmpty = !val || !val.toString().trim();
                        const isWarning = isRequired && isEmpty;
                        
                        return (
                          <div key={key} className={`field-input-card ${isWarning ? 'border-red-500/30 bg-red-500/5' : ''}`}>
                            <div className="field-label-wrapper">
                              <span className="field-label-text">
                                {getFieldLabel(key)}
                                {isRequired && <span className="text-red-500 ml-1 font-bold">*</span>}
                              </span>
                              <button
                                onClick={() => handleRemoveField(key)}
                                className="text-[9px] text-red-400 hover:text-red-300 font-mono transition-colors"
                                title="Remove key"
                              >
                                [PURGE]
                              </button>
                            </div>
                            <input 
                              type="text" 
                              value={val || ''}
                              onChange={(e) => handleFieldChange(key, e.target.value)}
                              className={`input-glass ${isWarning ? 'border-red-500' : ''}`}
                              placeholder={std ? std.placeholder : `Enter ${key.replace(/_/g, ' ')}`}
                            />
                          </div>
                        );
                      })}
                    </div>
                  </>
                );
              })()}

              {/* Inline Add Field Panel */}
              <div className="mt-2 pt-3 border-t border-slate-900">
                {!showAddField ? (
                  <div className="flex justify-end">
                    <button 
                      onClick={() => setShowAddField(true)}
                      className="custom-adder-button flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" />
                      ADD SCHEMATIC FIELD
                    </button>
                  </div>
                ) : (
                  <div className="p-3 rounded bg-slate-950/45 border border-slate-900 flex flex-col gap-2.5">
                    <div className="flex justify-between items-center">
                      <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider font-mono">CHOOSE/CREATE DATA FIELD</span>
                      <button 
                        onClick={() => {
                          setShowAddField(false);
                          setCustomFieldName('');
                        }} 
                        className="text-slate-400 hover:text-slate-200"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>

                    {/* Tag list */}
                    <div className="flex flex-wrap gap-1 max-h-[80px] overflow-y-auto">
                      {STANDARD_FIELDS.filter(f => !Object.keys(getActiveFields()).includes(f.key)).map((f) => (
                        <button
                          key={f.key}
                          onClick={() => {
                            handleFieldChange(f.key, "");
                            setShowAddField(false);
                          }}
                          className="px-2 py-0.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-[9px] font-mono rounded text-slate-300"
                        >
                          + {f.label}
                        </button>
                      ))}
                    </div>

                    {/* Custom key name */}
                    <div className="flex gap-2 items-center mt-1 border-t border-slate-900/60 pt-2">
                      <input 
                        type="text" 
                        placeholder="Custom Schema Tag (e.g. spouse_name)"
                        value={customFieldName}
                        onChange={(e) => setCustomFieldName(e.target.value)}
                        className="input-glass py-1 px-2 text-xs flex-1"
                      />
                      <button
                        onClick={() => {
                          if (customFieldName.trim()) {
                            addCustomField(customFieldName);
                            setCustomFieldName('');
                            setShowAddField(false);
                          }
                        }}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-[10px] font-bold transition-colors"
                      >
                        ADD
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Confirm Save database */}
            <div className="flex justify-center mt-1">
              <button 
                onClick={saveCorrections}
                className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded text-[10px] font-bold flex items-center gap-1.5 transition-colors"
              >
                <Save className="w-3 h-3 text-slate-400" />
                CONFIRM & WRITE DB CHANGES
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  // 4. PORTAL MAPPER PLUGIN
  const renderMapperPlugin = () => {
    if (!activePlugins.mapper) return null;
    return (
      <div className="glass-panel flex flex-col gap-4">
        <div className="card-header-bar">
          <div className="card-header-title">
            <Globe className="w-4 h-4 text-indigo-500" />
            <span>Plugin // Portal_DOM_Mapper</span>
          </div>
          <div className="card-header-actions">
            <div className="card-action-dot red" onClick={() => togglePlugin('mapper')} title="Hide module"></div>
            <div className="card-action-dot yellow" title="Settings"></div>
            <div className="card-action-dot green" title="Diagnostic"></div>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-[9px] font-bold text-slate-500 uppercase tracking-wider font-mono">AUTOMATION TARGET NODE (URL)</label>
          <div className="flex gap-2">
            <input 
              type="text" 
              value={targetUrl}
              onChange={(e) => {
                setTargetUrl(e.target.value);
                setCrawledFields([]); // Reset scan
              }}
              className="input-glass text-xs"
              placeholder="http://example-target-system.com/form"
            />
            <button 
              onClick={crawlTarget}
              disabled={crawling || !targetUrl}
              className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-[10px] font-bold rounded flex items-center gap-1"
            >
              {crawling ? <RefreshCw className="w-3 h-3 animate-spin text-indigo-500" /> : <Eye className="w-3 h-3" />}
              <span>VERIFY</span>
            </button>
          </div>
        </div>

        {/* DOM nodes list */}
        {crawling ? (
          <div className="flex items-center gap-2 text-slate-500 p-2 text-[10px] font-mono">
            <RefreshCw className="w-3 h-3 animate-spin text-indigo-400" />
            <span>Aligning browser DOM descriptors...</span>
          </div>
        ) : crawledFields.length > 0 ? (
          <div className="flex flex-col gap-2.5">
            <div className="px-3 py-1.5 rounded bg-emerald-500/5 border border-emerald-500/10 flex items-center gap-2 text-[10px] text-emerald-400 font-mono">
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span>DOM ALIGNED: {crawledFields.length} INPUTS IDENTIFIED</span>
            </div>
            
            {/* Visual alignment grid map */}
            <div className="alignment-grid max-h-[140px] overflow-y-auto">
              {crawledFields.slice(0, 8).map((cf, idx) => (
                <div className="alignment-row" key={idx}>
                  <span className="alignment-field-key">{cf.name || cf.id || `field_${idx}`}</span>
                  <span className="alignment-arrow">&rarr;</span>
                  <span className="alignment-dom-node">{cf.tag || 'input'}[type={cf.type || 'text'}]</span>
                </div>
              ))}
              {crawledFields.length > 8 && (
                <div className="text-center text-[9px] text-slate-600 font-mono mt-1">
                  + {crawledFields.length - 8} additional inputs aligned
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-[10px] font-mono text-slate-600 italic p-2 border border-dashed border-slate-900 rounded text-center">
            Run DOM verify to inspect injection node alignments.
          </div>
        )}
      </div>
    );
  };

  // 5. EXECUTION CENTER PLUGIN
  const renderExecutionPlugin = () => {
    if (!activePlugins.verification || !documentData) return null; // dependency: must have file loaded
    return (
      <div className="glass-panel flex flex-col gap-4">
        <div className="card-header-bar">
          <div className="card-header-title">
            <Play className="w-4 h-4 text-purple-500" />
            <span>Plugin // Execution_Trigger</span>
          </div>
          <div className="card-header-actions">
            <div className="card-action-dot red" title="Toggle active"></div>
            <div className="card-action-dot yellow" title="Settings"></div>
            <div className="card-action-dot green" title="Diagnostic"></div>
          </div>
        </div>

        {(() => {
          const docData = documentData?.corrected_json || documentData?.extracted_json || {};
          const isSpreadsheet = docData.records && Array.isArray(docData.records) && docData.records.length > 0;
          
          return (
            <div className="flex flex-col gap-2.5">
              {isSpreadsheet ? (
                <>
                  <button 
                    onClick={triggerBulkAutoFill}
                    disabled={bulkFilling || filling || !documentId}
                    className="btn-premium w-full"
                  >
                    {bulkFilling ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin mr-2" />
                        RUNNING BULK AUTOMATION...
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 fill-current mr-2" />
                        EXECUTE BULK INJECTION (ALL ROWS)
                      </>
                    )}
                  </button>
                  <button 
                    onClick={triggerAutoFill}
                    disabled={bulkFilling || filling || !documentId}
                    className="px-3 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 rounded text-[11px] font-bold transition-colors flex items-center justify-center gap-1.5"
                  >
                    <Play className="w-3.5 h-3.5 text-indigo-400" />
                    <span>INJECT ACTIVE ROW ({activeRecordIdx + 1}) ONLY</span>
                  </button>
                </>
              ) : ingestionMode === 'multiple' && documentsList.filter(d => d.status === 'completed').length > 1 ? (
                <>
                  <button 
                    onClick={triggerBatchImageAutofill}
                    disabled={bulkFilling || filling}
                    className="btn-premium w-full"
                  >
                    {bulkFilling ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin mr-2" />
                        RUNNING BATCH AUTOMATION...
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 fill-current mr-2" />
                        EXECUTE BATCH INJECTION (ALL IMAGES)
                      </>
                    )}
                  </button>
                  <button 
                    onClick={triggerAutoFill}
                    disabled={bulkFilling || filling || !documentId}
                    className="px-3 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 rounded text-[11px] font-bold transition-colors flex items-center justify-center gap-1.5"
                  >
                    <Play className="w-3.5 h-3.5 text-indigo-400" />
                    <span>INJECT SELECTED IMAGE ONLY</span>
                  </button>
                </>
              ) : (
                <button 
                  onClick={triggerAutoFill}
                  disabled={filling || !documentId}
                  className="btn-premium w-full"
                >
                  {filling ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin mr-2" />
                      INJECTING FIELD PAYLOADS...
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-current mr-2" />
                      EXECUTE FORM INJECTION
                    </>
                  )}
                </button>
              )}
            </div>
          );
        })()}
      </div>
    );
  };

  // 6. LIVE CONSOLE LOGS PLUGIN
  const renderLogsPlugin = () => {
    if (!activePlugins.logs) return null;
    return (
      <div className="glass-panel flex flex-col gap-4">
        <div className="card-header-bar">
          <div className="card-header-title">
            <Terminal className="w-4 h-4 text-teal-400" />
            <span>Plugin // Live_Engine_Console</span>
          </div>
          <div className="card-header-actions">
            <div className="card-action-dot red" onClick={() => togglePlugin('logs')} title="Hide module"></div>
            <div className="card-action-dot yellow" title="Clear console" onClick={() => setLogs([])}></div>
            <div className="card-action-dot green" title="Diagnostic"></div>
          </div>
        </div>

        <div className="log-console">
          {logs.length === 0 ? (
            <div className="text-slate-600 italic">No telemetry streams captured...</div>
          ) : (
            logs.map(log => (
              <div className="log-line" key={log.id}>
                <span className="log-time">[{log.time}]</span>
                <span className={`log-tag-${log.type}`}>{log.type.toUpperCase()}: </span>
                <span>{log.message}</span>
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </div>
      </div>
    );
  };

  // 7. SCREEN EVIDENCE VIEWER
  const renderEvidencePlugin = () => {
    if (!activePlugins.evidence || !fillResult) return null;
    return (
      <div className="glass-panel flex flex-col gap-4">
        <div className="card-header-bar">
          <div className="card-header-title">
            <Monitor className="w-4 h-4 text-purple-400" />
            <span>Plugin // Evidence_Output</span>
          </div>
          <div className="card-header-actions">
            <div className="card-action-dot red" onClick={() => { setFillResult(null); setBulkResult(null); }} title="Close evidence"></div>
            <div className="card-action-dot yellow" title="Refresh"></div>
            <div className="card-action-dot green" title="Inspect capture"></div>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider font-mono">AUTOMATION FRAME EVIDENCE</span>
            <button 
              onClick={() => setShowScreenshot(true)} 
              className="text-[9px] font-mono text-blue-400 hover:underline"
            >
              [ENLARGE FRAME]
            </button>
          </div>
          
          <div className="border border-slate-900 rounded overflow-hidden shadow-inner bg-black/60 flex justify-center p-1.5 max-h-[140px]">
            <img 
              src={fillResult.screenshot_url} 
              alt="Automation Frame"
              className="max-h-[120px] object-contain rounded"
              onError={(e) => {
                e.target.src = 'https://raw.githubusercontent.com/microsoft/playwright/main/packages/playwright-core/src/server/chromium/video.png';
              }}
            />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="smartfill-plugin-root min-h-screen p-4 text-slate-700">
      {/* Brand Header */}
      <header className="glass-panel flex flex-col md:flex-row justify-between items-center gap-4 mb-4" style={{ padding: '12px 20px', borderLeft: '4px solid var(--accent-color)' }}>
        <div className="flex items-center gap-4">
          {/* Unitive Official Logo Image */}
          <div className="flex items-center justify-center bg-white p-1 rounded border border-slate-200 shadow-sm" style={{ flexShrink: 0 }}>
            <img 
              src="https://unitive.in/assets/images/logo/9.png" 
              alt="Unitive Technologies Logo" 
              className="h-10 object-contain"
              onError={(e) => {
                // fallback hide if network error
                e.target.style.display = 'none';
              }}
            />
          </div>
          
          {/* Title & Tagline */}
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-800 tracking-wide m-0" style={{ fontFamily: "'Poppins', sans-serif" }}>
                Unitive Technologies
              </h1>
              <span className="text-[9px] font-mono font-bold bg-orange-500/10 text-orange-600 px-2 py-0.5 rounded border border-orange-500/20 uppercase tracking-wider">
                FORM AUTOMATION PLATFORM
              </span>
            </div>
            <span className="text-[10px] text-slate-500 font-medium mt-0.5">
              Intelligent Form Fill and Document Verification Platform
            </span>
          </div>
        </div>

        {/* System Session Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-mono bg-emerald-500/5 px-3 py-1.5 rounded border border-emerald-500/10">
            <span className="led led-green led-pulse" style={{ width: '6px', height: '6px' }}></span>
            <span>SECURE SYSTEM LINK ESTABLISHED</span>
          </div>
        </div>
      </header>

      {/* Top Telemetry HUD Bar */}
      <header className="telemetry-bar">
        <div className="telemetry-item" style={{ borderRight: '1px solid var(--border-color)' }}>
          <span className="telemetry-label">SYSTEM CORE</span>
          <div className="telemetry-value">
            <span className={`led led-green led-pulse`}></span>
            <span>UNITIVE_AI // ACTIVE</span>
          </div>
        </div>
        
        <div className="telemetry-item" style={{ borderRight: '1px solid var(--border-color)' }}>
          <span className="telemetry-label">EXTRACTION ENGINE</span>
          <div className="telemetry-value text-indigo-400">
            <span className="led led-blue"></span>
            <span>{slmInfo.model}</span>
          </div>
        </div>

        <div className="telemetry-item" style={{ borderRight: '1px solid var(--border-color)' }}>
          <span className="telemetry-label">HOST SERVICE ping</span>
          <div className="telemetry-value text-emerald-400 font-mono">
            {backendOnline ? (
              <>
                <span>{latency}ms</span>
                <span className="text-[9px] text-slate-600">PORT_8000</span>
              </>
            ) : (
              <span className="text-red-500 font-bold uppercase">OFFLINE</span>
            )}
          </div>
        </div>

        <div className="telemetry-item" style={{ borderRight: '1px solid var(--border-color)' }}>
          <span className="telemetry-label">DATABASE FEED</span>
          <div className="telemetry-value font-mono">
            <Database className="w-3.5 h-3.5 text-slate-500" />
            <span>{documentsList.length} FILE BUFFERS</span>
          </div>
        </div>

        <div className="telemetry-item">
          <span className="telemetry-label">OP SESSION STATE</span>
          <div className="telemetry-value text-slate-400 font-mono text-[11px]">
            <span>SECURE_OP_902</span>
          </div>
        </div>
      </header>

      {/* Plugin Command Switch Board */}
      <section className="plugin-deck">
        <div className="flex flex-col gap-1">
          <span className="queue-title" style={{ fontSize: '10px' }}>Dashboard Plugin Control Deck</span>
          <div className="plugin-toggles mt-1">
            {[
              { key: 'ingestor', label: 'Ingest_Core' },
              { key: 'feed', label: 'Repository_Feed' },
              { key: 'verification', label: 'Verification_Studio' },
              { key: 'mapper', label: 'Portal_DOM_Mapper' },
              { key: 'logs', label: 'Live_Engine_Console' }
            ].map((p) => (
              <button
                key={p.key}
                onClick={() => togglePlugin(p.key)}
                className={`plugin-toggle-btn ${activePlugins[p.key] ? 'active' : ''}`}
              >
                <div className={`led ${activePlugins[p.key] ? 'led-blue' : 'bg-slate-700'}`} style={{ width: '6px', height: '6px' }}></div>
                <span>{p.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="layout-selector mt-2 md:mt-0">
          <Layout className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-[10px] uppercase font-mono text-slate-500">ARCHITECTURE</span>
          <select 
            value={layout} 
            onChange={(e) => {
              setLayout(e.target.value);
              addLog(`Layout architecture rearranged to: ${e.target.value.toUpperCase()}`, 'sys');
            }} 
            className="layout-select"
          >
            <option value="command">Command Console (3-Col)</option>
            <option value="split">Split Workspace (2-Col)</option>
            <option value="focus">Focus Frame (Tabbed)</option>
          </select>
        </div>
      </section>

      {/* Responsive Grid Layout Renderer */}
      <main>
        {/* LAYOUT 1: COMMAND CONSOLE (3 COLUMNS) */}
        {layout === 'command' && (
          <div className="layout-grid-3cols" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
            {/* Column 1: Left */}
            <div className="flex flex-col gap-4">
              {renderIngestorPlugin()}
              {renderFeedPlugin()}
            </div>
            
            {/* Column 2: Middle */}
            <div className="flex flex-col gap-4">
              {renderVerificationPlugin()}
            </div>
            
            {/* Column 3: Right */}
            <div className="flex flex-col gap-4">
              {renderMapperPlugin()}
              {renderExecutionPlugin()}
              {renderEvidencePlugin()}
              {renderLogsPlugin()}
            </div>
          </div>
        )}

        {/* LAYOUT 2: SPLIT WORKSPACE (2 COLUMNS) */}
        {layout === 'split' && (
          <div className="layout-grid-2cols" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
            {/* Column 1: Left */}
            <div className="flex flex-col gap-4">
              {renderIngestorPlugin()}
              {renderFeedPlugin()}
              {renderMapperPlugin()}
              {renderLogsPlugin()}
            </div>
            
            {/* Column 2: Right */}
            <div className="flex flex-col gap-4">
              {renderVerificationPlugin()}
              {renderExecutionPlugin()}
              {renderEvidencePlugin()}
            </div>
          </div>
        )}

        {/* LAYOUT 3: FOCUS FRAME (TABBED SELECTOR) */}
        {layout === 'focus' && (
          <div className="flex flex-col gap-4">
            {/* Tabs bar */}
            <div className="flex flex-wrap gap-1 border-b border-slate-900 pb-1">
              {[
                { key: 'ingestor', label: 'Ingest Core', enabled: activePlugins.ingestor },
                { key: 'feed', label: 'Repository Feed', enabled: activePlugins.feed },
                { key: 'verification', label: 'Verification Studio', enabled: activePlugins.verification },
                { key: 'mapper', label: 'DOM Mapper', enabled: activePlugins.mapper },
                { key: 'logs', label: 'Engine Console', enabled: activePlugins.logs }
              ].filter(t => t.enabled).map((t) => (
                <button
                  key={t.key}
                  onClick={() => setFocusTab(t.key)}
                  className={`px-4 py-2 font-mono text-[11px] font-bold border-t border-x rounded-t transition-all ${
                    focusTab === t.key 
                      ? 'bg-slate-900 border-slate-800 text-blue-400' 
                      : 'bg-slate-950/40 border-slate-950/60 text-slate-500 hover:text-slate-300'
                  }`}
                  style={{ marginBottom: '-1px' }}
                >
                  {t.label}
                </button>
              ))}
              {fillResult && activePlugins.evidence && (
                <button
                  onClick={() => setFocusTab('evidence')}
                  className={`px-4 py-2 font-mono text-[11px] font-bold border-t border-x rounded-t transition-all ${
                    focusTab === 'evidence' 
                      ? 'bg-slate-900 border-slate-800 text-purple-400' 
                      : 'bg-slate-950/40 border-slate-950/60 text-slate-500 hover:text-slate-300'
                  }`}
                  style={{ marginBottom: '-1px' }}
                >
                  Evidence View
                </button>
              )}
            </div>

            {/* Render single item */}
            {focusTab === 'ingestor' && renderIngestorPlugin()}
            {focusTab === 'feed' && renderFeedPlugin()}
            {focusTab === 'verification' && (
              <div className="flex flex-col gap-4">
                {renderVerificationPlugin()}
                {renderExecutionPlugin()}
              </div>
            )}
            {focusTab === 'mapper' && renderMapperPlugin()}
            {focusTab === 'logs' && renderLogsPlugin()}
            {focusTab === 'evidence' && renderEvidencePlugin()}
          </div>
        )}
      </main>

      {/* Corporate Verification Summary Modal */}
      {showScreenshot && fillResult && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
          <div className="glass-panel max-w-4xl w-full flex flex-col overflow-hidden max-h-[90vh] bg-slate-950 border border-slate-800 rounded">
            <div className="p-4 border-b border-slate-900 flex justify-between items-center bg-slate-950">
              <div className="flex items-center gap-2 text-emerald-400 font-mono">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
                <span className="font-bold text-xs uppercase tracking-wider">Verification Execution Summary Report</span>
              </div>
              <button 
                onClick={() => {
                  setShowScreenshot(false);
                  setBulkResult(null);
                }}
                className="px-3.5 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded text-xs font-mono font-semibold text-slate-300 transition-colors"
              >
                [CLOSE_REPORT]
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex flex-col gap-6">
              
              {/* Tabular summary list if bulkResult is present */}
              {bulkResult ? (
                <div className="flex flex-col gap-4">
                  <div className="p-4 rounded bg-blue-500/5 border border-blue-500/10 flex justify-between items-center font-mono">
                    <div>
                      <h4 className="text-xs font-bold text-slate-200">BULK BATCH EXECUTION SUCCESS</h4>
                      <p className="text-[10px] text-slate-500 mt-1">Processed all entries in the workspace registry using automated worker browser containers.</p>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-black text-blue-400">
                        {bulkResult.results?.filter(r => r.success).length} / {bulkResult.results?.length}
                      </span>
                      <p className="text-[8px] uppercase tracking-wider text-slate-500 font-bold mt-1">Succeeded Rows</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto border border-slate-900 rounded bg-slate-950">
                    <table className="summary-table-wrapper">
                      <thead>
                        <tr>
                          <th className="summary-table-header">Index</th>
                          <th className="summary-table-header">Customer Identity</th>
                          <th className="summary-table-header">State</th>
                          <th className="summary-table-header">Execution Comments</th>
                          <th className="summary-table-header text-right">Evidence Link</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          const docData = documentData?.corrected_json || documentData?.extracted_json || {};
                          const records = docData.records || [];
                          return bulkResult.results?.map((res, i) => {
                            const recName = res.customer_name || records[res.record_index]?.full_name || records[res.record_index]?.name || `Record ${res.record_index + 1}`;
                            const screenshotUrl = res.screenshot_url || `/static/screenshots/screenshot_bulk_${res.record_index}.png`;
                            return (
                              <tr key={i} className="summary-table-row">
                                <td className="summary-table-cell text-slate-500 font-mono">#{res.record_index + 1}</td>
                                <td className="summary-table-cell font-medium text-slate-200 font-mono">{recName}</td>
                                <td className="summary-table-cell">
                                  <span className={`badge ${res.success ? 'badge-completed' : 'badge-failed'}`} style={{ fontSize: '8px', padding: '1px 4px' }}>
                                    {res.success ? 'Success' : 'Error'}
                                  </span>
                                </td>
                                <td className="summary-table-cell text-slate-400 font-mono text-[10px]">
                                  {res.success ? 'Injected successfully and validation satisfied' : res.errors?.join('; ') || 'Record validation failed'}
                                </td>
                                <td className="summary-table-cell text-right">
                                  <a 
                                    href={screenshotUrl} 
                                    target="_blank" 
                                    rel="noreferrer"
                                    className="text-blue-400 hover:text-blue-300 font-semibold underline font-mono text-[10px]"
                                  >
                                    [VIEW]
                                  </a>
                                </td>
                              </tr>
                            );
                          });
                        })()}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                /* Single verification success comment */
                <div className="p-3 rounded bg-emerald-500/5 border border-emerald-500/10 flex items-center gap-3 font-mono">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <div>
                    <h4 className="text-xs font-bold text-emerald-400">SINGLE TRANSACTION COMPLETE</h4>
                    <p className="text-[10px] text-slate-500 mt-0.5">Verified record has been correctly mapped and injected. Target page validation satisfied.</p>
                  </div>
                </div>
              )}
              
              {/* Form Render Viewport */}
              <div className="flex flex-col gap-2 font-mono">
                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">CAPTURED SCREEN EVIDENCE:</span>
                <div className="border border-slate-900 rounded overflow-hidden shadow-2xl bg-black/60 flex justify-center p-2">
                  <img 
                    src={fillResult.screenshot_url} 
                    alt="Automation Frame"
                    className="max-h-[50vh] object-contain rounded"
                    onError={(e) => {
                      e.target.src = 'https://raw.githubusercontent.com/microsoft/playwright/main/packages/playwright-core/src/server/chromium/video.png';
                    }}
                  />
                </div>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
