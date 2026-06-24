import React, { useState, useEffect } from 'react';
import { 
  UploadCloud, Cpu, FileText, CheckCircle, Server, Globe, 
  RefreshCw, Play, Check, Eye, AlertCircle, HelpCircle, Save,
  Plus, X, Trash2
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
  const [slmInfo, setSlmInfo] = useState({ model: 'Offline', url: '' });
  const [loadingStats, setLoadingStats] = useState(true);

  // Ingestion settings
  const [ingestionMode, setIngestionMode] = useState('single'); // 'single', 'multiple', 'excel', 'pdf'
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

  // Reset active row selection on document change
  useEffect(() => {
    setActiveRecordIdx(0);
    setShowAddField(false);
  }, [documentId]);

  // Form Automation states
  const [targetUrl, setTargetUrl] = useState('http://erpretails.s3-website.ap-south-1.amazonaws.com/admin/customer/form?type=create'); // Default URL
  const [crawledFields, setCrawledFields] = useState([]);
  const [crawling, setCrawling] = useState(false);
  const [filling, setFilling] = useState(false);
  const [fillResult, setFillResult] = useState(null);
  const [showScreenshot, setShowScreenshot] = useState(false);
  const [bulkFilling, setBulkFilling] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);

  // Fetch all documents
  const fetchDocuments = async () => {
    try {
      const res = await fetch('/api/v1/documents');
      if (res.ok) {
        const data = await res.json();
        setDocumentsList(data);
        
        // Auto-select first document if none selected
        if (!selectedDocId && data.length > 0) {
          setSelectedDocId(data[0].id);
          setDocumentId(data[0].id);
          setDocumentData(data[0]);
        } else if (selectedDocId) {
          const updatedDoc = data.find(doc => doc.id === selectedDocId);
          if (updatedDoc) {
            setDocumentData(updatedDoc);
            
            // Sync status
            if (updatedDoc.status === 'completed') {
              setUploadProgress('completed');
            } else if (updatedDoc.status === 'failed') {
              setUploadProgress('failed');
            } else if (updatedDoc.status === 'processing') {
              if (updatedDoc.ocr_raw_text) {
                setUploadProgress('slm');
              } else {
                setUploadProgress('ocr');
              }
            } else if (updatedDoc.status === 'pending') {
              setUploadProgress('preprocessing');
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
  }, [selectedDocId]);

  // Load backend stats
  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const rootRes = await fetch('/api/v1/documents').catch(() => null);
      if (rootRes && rootRes.ok) {
        setBackendOnline(true);
      } else {
        setBackendOnline(false);
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

    // Concurrently upload all selected files
    await Promise.all(selectedFiles.map(async (file, index) => {
      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/v1/documents/upload', {
          method: 'POST',
          body: formData
        });
        if (res.ok) {
          const data = await res.json();
          // Auto-select the first uploaded file in this batch
          if (index === 0) {
            setSelectedDocId(data.id);
            setDocumentId(data.id);
            setDocumentData(data);
            setUploadProgress('preprocessing');
          }
        }
      } catch (err) {
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
    setBulkResult(null);
    
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

  // Trigger Bulk Fill
  const triggerBulkAutoFill = async () => {
    if (!documentId || !targetUrl) return;
    setBulkFilling(true);
    setBulkResult(null);
    setFillResult(null);

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
        
        // Map to fillResult so that screenshot displays the bulk execution report
        setFillResult({
          success: result.success,
          screenshot_url: result.screenshot_url,
          mappings: {} // Leave empty so we default to the tabular execution summary
        });
        setShowScreenshot(true);
      } else {
        const err = await res.json();
        alert(`Bulk Fill Failed: ${err.detail || 'Internal Error'}`);
      }
    } catch (e) {
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
      alert("No completed documents found in the workspace to fill. Please wait for processing to finish.");
      setBulkFilling(false);
      return;
    }

    const results = [];
    let lastScreenshotUrl = "";
    let globalSuccess = true;

    for (let i = 0; i < completedDocs.length; i++) {
      const doc = completedDocs[i];
      const docData = doc.corrected_json || doc.extracted_json || {};
      const customerName = docData.full_name || docData.name || doc.filename;

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

  return (
    <div className="min-h-screen p-6 text-slate-100">
      {/* Top Header */}
      <header className="glass-panel header-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap: '8px', padding: '20px' }}>
        <div className="flex flex-col items-center">
          <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-teal-300 bg-clip-text text-transparent" style={{ margin: 0 }}>
            SmartFill AI
          </h1>
          <p className="text-xs text-slate-400 font-medium" style={{ margin: '4px 0 0 0' }}>Intelligent Form Fill and Document Verification</p>
        </div>
      </header>

      {/* Main Two-Column Layout */}
      <main className="dashboard-split-layout">
        
        {/* Column 1: Document Workspace (Left - Width 38%) */}
        <section className="glass-panel p-6 flex flex-col gap-5 overflow-y-auto max-h-[85vh]">
          <h2 className="column-title">
            <UploadCloud className="w-5 h-5 text-indigo-400" />
            Document Workspace
          </h2>

          {/* Ingestion Mode Selector */}
          <div className="mode-selector-wrapper">
            <span className="queue-title">Select Upload Mode</span>
            <div className="mode-selector" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
              {[
                { id: 'single', label: 'Single Image' },
                { id: 'multiple', label: 'Multiple Images' },
                { id: 'excel', label: 'Spreadsheet' },
                { id: 'pdf', label: 'PDF Document' },
                { id: 'word', label: 'Word Document' }
              ].map((mode) => (
                <button
                  key={mode.id}
                  onClick={() => {
                    setIngestionMode(mode.id);
                    setFillResult(null);
                    setBulkResult(null);
                  }}
                  className={`mode-btn ${ingestionMode === mode.id ? 'active' : ''}`}
                  style={{ gridColumn: mode.id === 'word' ? 'span 2' : 'span 1', fontSize: '10px' }}
                >
                  {mode.label}
                </button>
              ))}
            </div>
          </div>

          {/* Upload Area */}
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
            <UploadCloud className="w-8 h-8 text-indigo-400 animate-bounce" />
            <div>
              <p className="text-xs font-semibold" style={{ margin: 0, color: '#f1f5f9' }}>
                {ingestionMode === 'single' && 'Upload Image'}
                {ingestionMode === 'multiple' && 'Upload Multiple Images'}
                {ingestionMode === 'excel' && 'Upload Spreadsheet'}
                {ingestionMode === 'pdf' && 'Upload PDF Document'}
                {ingestionMode === 'word' && 'Upload Word Document'}
              </p>
              <p className="text-[10px] text-slate-500 mt-1" style={{ margin: 0 }}>
                {ingestionMode === 'single' && 'Supports JPG, PNG'}
                {ingestionMode === 'multiple' && 'Supports JPG, PNG (Hold Ctrl)'}
                {ingestionMode === 'excel' && 'Supports XLSX, XLS, CSV, XSLV'}
                {ingestionMode === 'pdf' && 'Supports PDF Files'}
                {ingestionMode === 'word' && 'Supports DOCX, DOC'}
              </p>
            </div>
          </div>

          {/* Document Sidebar/Queue */}
          {documentsList.length > 0 ? (
            <div className="queue-wrapper">
              <h3 className="queue-title">Active Documents ({documentsList.length})</h3>
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
                      <div className="flex items-center gap-3 min-width-0 flex-1">
                        {getFileIcon(doc.filename)}
                        <div className="queue-item-info">
                          <span className="queue-item-name">
                            {doc.filename}
                          </span>
                          <span className="queue-item-time">
                            {new Date(doc.created_at).toLocaleDateString()} {new Date(doc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                      
                      <div className="queue-item-actions">
                        <span className={badgeClass}>
                          {doc.status}
                        </span>
                        
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            if (confirm(`Delete document "${doc.filename}"?`)) {
                              try {
                                const res = await fetch(`/api/v1/documents/${doc.id}`, { method: 'DELETE' });
                                if (res.ok) {
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
                          title="Delete Document"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-6 text-slate-500 bg-slate-950/20 border border-slate-900 rounded-xl mt-4">
              <FileText className="w-8 h-8 stroke-[1.5] mb-2 text-slate-600" />
              <p className="text-[11px]">No processed documents in workspace.</p>
            </div>
          )}

          {/* Progress Tracker */}
          {uploadProgress && uploadProgress !== 'completed' && uploadProgress !== 'failed' && (
            <div className="progress-tracker flex items-center gap-3">
              <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
              <span className="text-xs text-slate-300 font-medium">
                {uploadProgress === 'uploading' && 'Ingesting file package...'}
                {uploadProgress === 'preprocessing' && 'Analyzing document geometry...'}
                {uploadProgress === 'ocr' && 'Extracting text layout...'}
                {uploadProgress === 'slm' && 'Resolving fields with ExtractFlow AI...'}
              </span>
            </div>
          )}

          {uploadProgress === 'failed' && (
            <div className="progress-tracker flex items-center gap-2.5" style={{ borderColor: 'rgba(244, 63, 94, 0.2)', background: 'rgba(244, 63, 94, 0.05)' }}>
              <AlertCircle className="w-4 h-4 text-rose-400" />
              <span className="text-xs text-rose-400 font-medium">Failed to ingest file. Verify format.</span>
            </div>
          )}


        </section>

        {/* Column 2: Workspace & Fill Console (Right - Width 62%) */}
        <section className="glass-panel p-6 flex flex-col gap-6 max-h-[85vh] overflow-y-auto">
          <h2 className="column-title">
            <Server className="w-5 h-5 text-indigo-400" />
            Verification & Execution Workspace
          </h2>

          {!documentData ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-12 text-slate-500">
              <FileText className="w-16 h-16 stroke-[1] mb-3 text-slate-600" />
              <p className="text-sm max-w-sm">Select or upload a source document from the left workspace panel to review and automate data injection.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-5 flex-1">
              
              {/* Row Selector and Match Badge */}
              <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Confidence Metric:</span>
                  <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                    documentData.confidence_score > 0.8 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/10' : 'bg-amber-500/10 text-amber-400 border border-amber-500/10'
                  }`}>
                    {Math.round(documentData.confidence_score * 100)}% Confidence Match
                  </span>
                </div>
              </div>

              {/* Advanced spreadsheet rows selector card */}
              {(() => {
                const data = documentData.corrected_json || documentData.extracted_json || {};
                if (data.records && Array.isArray(data.records) && data.records.length > 0) {
                  return (
                    <div className="row-nav-card flex flex-row items-center justify-between gap-4">
                      <button
                        onClick={() => {
                          setActiveRecordIdx(prev => Math.max(0, prev - 1));
                          setFillResult(null);
                          setBulkResult(null);
                        }}
                        disabled={activeRecordIdx === 0}
                        className="px-2 py-1 bg-slate-900 border border-slate-800 hover:bg-slate-850 text-[10px] font-semibold rounded transition-colors text-slate-400 disabled:opacity-30"
                      >
                        &larr; Prev
                      </button>
                      
                      <div className="flex-1 flex flex-col items-center">
                        <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">Active Spreadsheet Record</span>
                        <select
                          value={activeRecordIdx}
                          onChange={(e) => {
                            setActiveRecordIdx(parseInt(e.target.value, 10));
                            setFillResult(null);
                            setBulkResult(null);
                          }}
                          className="bg-slate-900 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-1.5 font-medium cursor-pointer w-full max-w-[280px] text-center mt-1 focus:outline-none focus:border-indigo-500"
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
                        }}
                        disabled={activeRecordIdx === data.records.length - 1}
                        className="px-2 py-1 bg-slate-900 border border-slate-800 hover:bg-slate-850 text-[10px] font-semibold rounded transition-colors text-slate-400 disabled:opacity-30"
                      >
                        Next &rarr;
                      </button>
                    </div>
                  );
                }
                return null;
              })()}

              {/* Editable Fields in an attractive Grid */}
              <div className="verification-scroll-container">
                {(() => {
                  const activeFields = getActiveFields();
                  const keysToExclude = ['id', 'created_at', 'updated_at', 'status', 'filename', 'storage_path', 'mime_type', 'confidence_score', 'ocr_raw_text', 'records'];
                  const editableFields = Object.entries(activeFields).filter(([key]) => !keysToExclude.includes(key));
                  
                  if (editableFields.length === 0) {
                    return <p className="text-xs text-slate-400 italic p-4 text-center">No fields extracted. Toggle Add Field below to verify records.</p>;
                  }
                  
                  return (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {editableFields.map(([key, val]) => {
                        const std = STANDARD_FIELDS.find(f => f.key === key);
                        return (
                          <div key={key} className="field-input-card">
                            <div className="field-label-wrapper">
                              <span className="field-label-text">{getFieldLabel(key)}</span>
                              <button
                                onClick={() => handleRemoveField(key)}
                                className="text-[10px] text-rose-400 hover:text-rose-300 font-semibold transition-colors"
                                title="Remove Field"
                              >
                                Remove
                              </button>
                            </div>
                            <input 
                              type="text" 
                              value={val || ''}
                              onChange={(e) => handleFieldChange(key, e.target.value)}
                              className="input-glass w-full"
                              placeholder={std ? std.placeholder : `Enter ${key.replace(/_/g, ' ')}`}
                            />
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}

                {/* Styled Inline Add Field Widget */}
                <div className="mt-4 pt-4 border-t border-slate-900">
                  {!showAddField ? (
                    <div className="flex justify-end">
                      <button 
                        onClick={() => setShowAddField(true)}
                        className="custom-adder-button flex items-center gap-1.5"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        Add Record Field
                      </button>
                    </div>
                  ) : (
                    <div className="p-4 rounded-xl bg-slate-950/45 border border-slate-900 flex flex-col gap-3">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Choose or Create Field</span>
                        <button 
                          onClick={() => {
                            setShowAddField(false);
                            setCustomFieldName('');
                          }} 
                          className="text-slate-400 hover:text-slate-200"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      {/* Tag list for remaining standard fields */}
                      <div className="flex flex-wrap gap-1.5">
                        {STANDARD_FIELDS.filter(f => !Object.keys(getActiveFields()).includes(f.key)).map((f) => (
                          <button
                            key={f.key}
                            onClick={() => {
                              handleFieldChange(f.key, "");
                              setShowAddField(false);
                            }}
                            className="px-2.5 py-1 bg-slate-900 border border-slate-800 hover:bg-slate-850 hover:border-slate-700 text-[10px] font-medium rounded-md transition-colors"
                          >
                            + {f.label}
                          </button>
                        ))}
                      </div>

                      {/* Custom key name input */}
                      <div className="flex gap-2 items-center mt-2 border-t border-slate-900/60 pt-2">
                        <input 
                          type="text" 
                          placeholder="Or type custom (e.g. Spouse Name)"
                          value={customFieldName}
                          onChange={(e) => setCustomFieldName(e.target.value)}
                          className="input-glass flex-1 py-1 px-3 text-xs"
                        />
                        <button
                          onClick={() => {
                            if (customFieldName.trim()) {
                              addCustomField(customFieldName);
                              setCustomFieldName('');
                              setShowAddField(false);
                            }
                          }}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded text-xs font-semibold transition-colors"
                        >
                          Add Custom
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Target Portal Config & Autofill Actions */}
              <div className="mt-auto border-t border-slate-900 pt-5 flex flex-col gap-4">
                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
                  <div className="flex-1 flex flex-col gap-1.5 w-full">
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Target Automation URL</label>
                    <div className="flex gap-2">
                      <input 
                        type="text" 
                        value={targetUrl}
                        onChange={(e) => {
                          setTargetUrl(e.target.value);
                          setCrawledFields([]); // Reset scan status
                        }}
                        className="input-glass flex-1 text-xs"
                        placeholder="http://example.com/register"
                      />
                      <button 
                        onClick={crawlTarget}
                        disabled={crawling || !targetUrl}
                        className="px-2.5 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-850 rounded-lg text-[10px] font-bold transition-colors disabled:opacity-40"
                      >
                        {crawling ? 'Analyzing Portal...' : 'Verify Form fields'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Alignment status check */}
                {crawling ? (
                  <div className="flex items-center gap-2 text-slate-400 p-2 text-xs">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                    <span>Mapping inputs to portal DOM nodes...</span>
                  </div>
                ) : crawledFields.length > 0 ? (
                  <div className="px-3 py-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10 flex items-center gap-2 text-xs text-emerald-400">
                    <Check className="w-4 h-4 text-emerald-400" />
                    <span>Aligned with {crawledFields.length} target fields. Ready to run autofill.</span>
                  </div>
                ) : null}

                {/* Run Autofill Buttons */}
                <div className="flex flex-col gap-3 pt-2">
                  {(() => {
                    const docData = documentData?.corrected_json || documentData?.extracted_json || {};
                    const isSpreadsheet = docData.records && Array.isArray(docData.records) && docData.records.length > 0;
                    
                    return (
                      <div className="flex flex-col gap-3">
                        <div className="flex justify-center" style={{ marginTop: '16px', marginBottom: '8px' }}>
                          <button 
                            onClick={saveCorrections}
                            className="px-2.5 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-850 text-slate-300 rounded-lg text-[10px] font-bold transition-colors flex items-center gap-1.5"
                          >
                            <Save className="w-3 h-3 text-slate-400" />
                            Confirm & Save
                          </button>
                        </div>

                        {isSpreadsheet ? (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <button 
                              onClick={triggerBulkAutoFill}
                              disabled={bulkFilling || filling || !documentId}
                              className="btn-premium flex items-center justify-center gap-2"
                            >
                              <Play className="w-4 h-4 fill-current text-white" />
                              {bulkFilling ? 'Running Bulk Autofill...' : 'Execute Bulk Autofill (All Rows)'}
                            </button>
                            <button 
                              onClick={triggerAutoFill}
                              disabled={bulkFilling || filling || !documentId}
                              className="px-4 py-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-850 text-slate-200 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2"
                            >
                              <Play className="w-4 h-4 text-indigo-400" />
                              {filling ? 'Injecting Selected...' : 'Autofill Selected Row Only'}
                            </button>
                          </div>
                        ) : ingestionMode === 'multiple' && documentsList.filter(d => d.status === 'completed').length > 1 ? (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <button 
                              onClick={triggerBatchImageAutofill}
                              disabled={bulkFilling || filling}
                              className="btn-premium flex items-center justify-center gap-2"
                            >
                              <Play className="w-4 h-4 fill-current text-white" />
                              {bulkFilling ? 'Running Batch Fill...' : 'Execute Batch Autofill (All Images)'}
                            </button>
                            <button 
                              onClick={triggerAutoFill}
                              disabled={bulkFilling || filling || !documentId}
                              className="px-4 py-2.5 bg-slate-900 border border-slate-800 hover:bg-slate-850 text-slate-200 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2"
                            >
                              <Play className="w-4 h-4 text-indigo-400" />
                              {filling ? 'Injecting Selected...' : 'Autofill Active Image Only'}
                            </button>
                          </div>
                        ) : (
                          <button 
                            onClick={triggerAutoFill}
                            disabled={filling || !documentId}
                            className="btn-premium w-full flex items-center justify-center gap-2"
                          >
                            <Play className="w-4 h-4 fill-current text-white" />
                            {filling ? 'Injecting form values...' : 'Execute Form Fill'}
                          </button>
                        )}
                      </div>
                    );
                  })()}
                </div>

              </div>
            </div>
          )}
        </section>

      </main>

      {/* Corporate Verification Summary Modal */}
      {showScreenshot && fillResult && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-panel max-w-4xl w-full flex flex-col overflow-hidden max-h-[90vh]">
            <div className="p-4 border-b border-slate-900 flex justify-between items-center bg-slate-950/40">
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
                <span className="font-bold text-sm">Execution Summary Report</span>
              </div>
              <button 
                onClick={() => {
                  setShowScreenshot(false);
                  setBulkResult(null);
                }}
                className="px-3.5 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg text-xs font-semibold text-slate-300 transition-colors"
              >
                Close Report
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto bg-slate-950/20 flex flex-col gap-6">
              
              {/* Tabular summary list if bulkResult is present */}
              {bulkResult ? (
                <div className="flex flex-col gap-4">
                  <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 flex justify-between items-center">
                    <div>
                      <h4 className="text-sm font-bold text-slate-200">Bulk Form Automation Completed</h4>
                      <p className="text-xs text-slate-400 mt-1">Processed all entries in the uploaded spreadsheet using cloud worker containers.</p>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-black text-indigo-400">
                        {bulkResult.results?.filter(r => r.success).length} / {bulkResult.results?.length}
                      </span>
                      <p className="text-[9px] uppercase tracking-wider text-slate-500 font-bold mt-1">Records Succeeded</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto border border-slate-900 rounded-xl bg-black/35">
                    <table className="summary-table-wrapper">
                      <thead>
                        <tr>
                          <th className="summary-table-header">Row</th>
                          <th className="summary-table-header">Customer Identity</th>
                          <th className="summary-table-header">Validation State</th>
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
                                <td className="summary-table-cell text-slate-400">#{res.record_index + 1}</td>
                                <td className="summary-table-cell font-medium text-slate-200">{recName}</td>
                                <td className="summary-table-cell">
                                  <span className={`badge ${res.success ? 'badge-completed' : 'badge-failed'}`}>
                                    {res.success ? 'Success' : 'Error'}
                                  </span>
                                </td>
                                <td className="summary-table-cell text-slate-400">
                                  {res.success ? 'Injected successfully and validation satisfied' : res.errors?.join('; ') || 'Record validation failed'}
                                </td>
                                <td className="summary-table-cell text-right">
                                  <a 
                                    href={screenshotUrl} 
                                    target="_blank" 
                                    rel="noreferrer"
                                    className="text-indigo-400 hover:text-indigo-300 font-semibold underline"
                                  >
                                    View Frame
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
                <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10 flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <div>
                    <h4 className="text-xs font-bold text-emerald-400">Single Automation Submission Complete</h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">Verified record has been correctly mapped and injected. Target page validation satisfied.</p>
                  </div>
                </div>
              )}
              
              {/* Form Render Viewport */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Final State Capture:</span>
                <div className="border border-slate-900 rounded-xl overflow-hidden shadow-2xl bg-black/45 flex justify-center p-2">
                  <img 
                    src={fillResult.screenshot_url} 
                    alt="Automation Frame"
                    className="max-h-[50vh] object-contain rounded-lg"
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
