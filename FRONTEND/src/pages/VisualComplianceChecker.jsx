import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import api from '../services/api';
import {
  Upload,
  ImageIcon,
  ShieldCheck,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ArrowLeft,
  BookOpen,
  XCircle,
  Info,
  Clock,
  ChevronDown,
  ChevronUp,
  Eye,
  FileImage,
  Gauge,
  HelpCircle,
  History,
  RefreshCw,
} from 'lucide-react';

// ─── Severity badge ──────────────────────────────────────────────────────────
const SeverityBadge = ({ severity }) => {
  const map = {
    High: 'bg-red-100 text-red-800 border-red-200',
    Medium: 'bg-amber-100 text-amber-800 border-amber-200',
    Low: 'bg-sky-100 text-sky-800 border-sky-200',
    'Unable to Verify': 'bg-slate-100 text-slate-600 border-slate-200',
  };
  return (
    <span
      className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full border ${
        map[severity] || map['Unable to Verify']
      }`}
    >
      {severity}
    </span>
  );
};

// ─── Review status badge ─────────────────────────────────────────────────────
const StatusBadge = ({ status }) => {
  const map = {
    Compliant: {
      cls: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      Icon: CheckCircle2,
    },
    'Action Required': {
      cls: 'bg-amber-50 text-amber-800 border-amber-200',
      Icon: AlertTriangle,
    },
    'Violations Detected': {
      cls: 'bg-red-50 text-red-800 border-red-200',
      Icon: XCircle,
    },
  };
  const { cls, Icon } = map[status] || map['Action Required'];
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${cls}`}
    >
      <Icon className="w-3.5 h-3.5" />
      {status}
    </span>
  );
};

// ─── Compliance score ring ───────────────────────────────────────────────────
const ScoreRing = ({ score }) => {
  if (score === null || score === undefined) return null;
  const pct = Math.max(0, Math.min(100, score));
  const r = 28;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  const color = pct >= 75 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';

  return (
    <div className="flex flex-col items-center">
      <svg width="80" height="80" viewBox="0 0 80 80" className="-rotate-90">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#e2e8f0" strokeWidth="7" />
        <circle
          cx="40"
          cy="40"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="7"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.8s ease' }}
        />
      </svg>
      <div className="-mt-[68px] flex flex-col items-center">
        <span className="text-xl font-extrabold text-slate-900">{pct}</span>
        <span className="text-[10px] font-semibold text-slate-500 mt-0.5">/ 100</span>
      </div>
      <span className="text-[11px] font-medium text-slate-500 mt-1 mb-1">Compliance Score</span>
    </div>
  );
};

// ─── Individual finding card ──────────────────────────────────────────────────
const FindingCard = ({ finding, index }) => {
  const [open, setOpen] = useState(false);
  const categoryIcons = {
    'Logo Usage': '🏷️',
    'Brand Colors': '🎨',
    Typography: '🔤',
    'Layout & Spacing': '📐',
    'Contrast & Readability': '👁️',
    'Visual Hierarchy': '🗂️',
    'Other Visual Guideline': '📋',
  };

  return (
    <div
      className={`rounded-xl border transition-all ${
        finding.severity === 'High'
          ? 'border-red-200 bg-red-50/40'
          : finding.severity === 'Medium'
          ? 'border-amber-200 bg-amber-50/30'
          : finding.severity === 'Low'
          ? 'border-sky-200 bg-sky-50/30'
          : 'border-slate-200 bg-slate-50/60'
      }`}
    >
      {/* Header row */}
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-start gap-3 p-4 text-left"
        aria-expanded={open}
      >
        <span className="text-lg shrink-0 mt-0.5">
          {categoryIcons[finding.category] || '📋'}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <SeverityBadge severity={finding.severity} />
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-500">
              {finding.category}
            </span>
            {finding.human_verification_required && (
              <span className="text-[10px] font-semibold text-purple-700 bg-purple-50 border border-purple-200 px-1.5 py-0.5 rounded-full">
                Human review needed
              </span>
            )}
          </div>
          <p className="text-xs font-semibold text-slate-800 line-clamp-2">
            {finding.visual_element}
          </p>
        </div>
        <span className="shrink-0 text-slate-400 mt-1">
          {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </span>
      </button>

      {/* Expanded body */}
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-white/60 pt-3">
          {/* Guideline reference */}
          {finding.guideline_title && (
            <div className="flex items-start gap-2 p-2.5 bg-white/70 rounded-lg border border-slate-100">
              <BookOpen className="w-3.5 h-3.5 text-forest-700 shrink-0 mt-0.5" />
              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">
                  Brand Guideline Referenced
                </p>
                <p className="text-xs font-semibold text-slate-800">{finding.guideline_title}</p>
                {finding.guideline_rule && (
                  <p className="text-[11px] text-slate-600 mt-0.5 italic">
                    "{finding.guideline_rule}"
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Explanation */}
          <div>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Finding
            </p>
            <p className="text-xs text-slate-700 leading-relaxed">{finding.explanation}</p>
          </div>

          {/* Suggested correction */}
          {finding.suggested_correction && (
            <div className="p-2.5 bg-emerald-50/60 border border-emerald-100 rounded-lg">
              <p className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider mb-1">
                Suggested Correction
              </p>
              <p className="text-xs text-emerald-800 leading-relaxed">
                {finding.suggested_correction}
              </p>
            </div>
          )}

          {/* Unable to verify note */}
          {finding.severity === 'Unable to Verify' && (
            <div className="flex items-start gap-2 p-2.5 bg-slate-100 rounded-lg border border-slate-200">
              <HelpCircle className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
              <p className="text-[11px] text-slate-600">
                This rule could not be verified from the image alone and requires human review.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── History list item ────────────────────────────────────────────────────────
const HistoryItem = ({ item, onSelect }) => (
  <button
    onClick={() => onSelect(item.id)}
    className="w-full text-left flex items-center gap-3 p-3 rounded-lg border border-slate-100 bg-white hover:border-forest-300 hover:bg-forest-50/30 transition-colors"
  >
    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
      <FileImage className="w-4 h-4 text-slate-400" />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-xs font-semibold text-slate-800 truncate">{item.original_filename}</p>
      <p className="text-[11px] text-slate-500">
        {new Date(item.created_at).toLocaleString()} •{' '}
        <span
          className={
            item.review_status === 'Compliant'
              ? 'text-emerald-600'
              : item.review_status === 'Violations Detected'
              ? 'text-red-600'
              : 'text-amber-600'
          }
        >
          {item.review_status}
        </span>
      </p>
    </div>
    {item.compliance_score !== null && item.compliance_score !== undefined && (
      <span className="text-xs font-bold text-slate-700 shrink-0">{item.compliance_score}%</span>
    )}
  </button>
);

// ─── Main page component ─────────────────────────────────────────────────────
const VisualComplianceChecker = () => {
  // Brands
  const [brands, setBrands] = useState([]);
  const [selectedBrandId, setSelectedBrandId] = useState('');
  const [loadingBrands, setLoadingBrands] = useState(true);

  // File upload
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  // Analysis state
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');

  // History
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // ── Fetch accessible brands ───────────────────────────────────────────────
  useEffect(() => {
    const fetchBrands = async () => {
      try {
        const res = await api.get('/brands');
        if (res.data.success && res.data.brands.length > 0) {
          setBrands(res.data.brands);
          setSelectedBrandId(res.data.brands[0].id.toString());
        }
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch brands.');
      } finally {
        setLoadingBrands(false);
      }
    };
    fetchBrands();
  }, []);

  // ── Fetch history when brand changes ─────────────────────────────────────
  useEffect(() => {
    if (!selectedBrandId) return;
    setAnalysis(null);
    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBrandId]);

  const fetchHistory = async () => {
    if (!selectedBrandId) return;
    setHistoryLoading(true);
    try {
      const res = await api.get(`/visual-compliance/brands/${selectedBrandId}/history`);
      if (res.data.success) setHistory(res.data.history || []);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  // ── File helpers ──────────────────────────────────────────────────────────
  const MAX_MB = 10;
  const ALLOWED_TYPES = ['image/png', 'image/jpeg'];

  const processFile = useCallback((file) => {
    if (!file) return;
    if (!ALLOWED_TYPES.includes(file.type)) {
      setError('Only PNG and JPEG/JPG images are supported.');
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`Image must be smaller than ${MAX_MB} MB.`);
      return;
    }
    setError('');
    setAnalysis(null);
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setImagePreview(e.target.result);
    reader.readAsDataURL(file);
  }, []);

  const handleFilePick = (e) => processFile(e.target.files?.[0]);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    processFile(e.dataTransfer.files?.[0]);
  };

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    setAnalysis(null);
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ── Load historical analysis ──────────────────────────────────────────────
  const loadHistoricalAnalysis = async (analysisId) => {
    try {
      const res = await api.get(`/visual-compliance/${analysisId}`);
      if (res.data.success) {
        setAnalysis(res.data.analysis);
        setImageFile(null);
        setImagePreview(null);
        setShowHistory(false);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load analysis.');
    }
  };

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleAnalyze = async (e) => {
    e.preventDefault();
    const brandIdToSubmit = selectedBrandId ? String(selectedBrandId).trim() : '';
    if (!brandIdToSubmit || brandIdToSubmit === 'undefined' || brandIdToSubmit === 'null') {
      setError('Please select a brand.');
      return;
    }
    if (!imageFile) {
      setError('Please upload an image to analyze.');
      return;
    }

    setError('');
    setAnalyzing(true);
    setAnalysis(null);

    const formData = new FormData();
    formData.append('brand_id', brandIdToSubmit);
    formData.append('image', imageFile);

    try {
      const res = await api.post('/visual-compliance/analyze', formData);
      if (res.data.success) {
        setAnalysis(res.data.analysis);
        fetchHistory(); // refresh history list
      }
    } catch (err) {
      setError(
        err.response?.data?.error ||
          'Visual compliance analysis failed. Please try again.'
      );
    } finally {
      setAnalyzing(false);
    }
  };

  // ── Derived counts ────────────────────────────────────────────────────────
  const highCount = analysis?.high_severity_count ?? 0;
  const medCount = analysis?.medium_severity_count ?? 0;
  const lowCount = analysis?.low_severity_count ?? 0;
  const utv = analysis?.unable_to_verify_count ?? 0;

  return (
    <DashboardLayout title="Visual Brand Compliance">
      {/* Breadcrumb */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <Link
          to="/creator-dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
        <button
          onClick={() => {
            setShowHistory((p) => !p);
            if (!showHistory) fetchHistory();
          }}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded-lg px-3 py-1.5 bg-white hover:bg-slate-50 transition-colors"
        >
          <History className="w-3.5 h-3.5" />
          {showHistory ? 'Hide History' : 'Past Analyses'}
        </button>
      </div>

      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-forest-900 to-forest-700 flex items-center justify-center shadow-sm">
            <Eye className="w-5 h-5 text-emerald-300" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Visual Brand Compliance Checker</h1>
            <p className="text-xs text-slate-500">
              Upload a marketing image or poster and check it against brand guidelines using AI.
            </p>
          </div>
        </div>
      </div>

      {/* Global error */}
      {error && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-xs text-red-700">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Brand loading / no access */}
      {loadingBrands ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-forest-700 mb-2" />
          <p className="text-xs font-medium">Loading brands…</p>
        </div>
      ) : brands.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
          <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">No Brand Access</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            You are not a member of any brand. Contact your Brand Manager to get access.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ── Left: Upload form ─────────────────────────────────────────── */}
          <div className="lg:col-span-2 space-y-5">
            {/* History panel */}
            {showHistory && (
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <History className="w-4 h-4 text-forest-700" />
                    <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Past Visual Analyses
                    </h3>
                  </div>
                  <button
                    onClick={fetchHistory}
                    disabled={historyLoading}
                    className="text-[11px] font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1 transition-colors"
                  >
                    <RefreshCw className={`w-3 h-3 ${historyLoading ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                </div>
                {historyLoading ? (
                  <div className="py-6 flex items-center justify-center">
                    <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
                  </div>
                ) : history.length === 0 ? (
                  <p className="text-xs text-slate-400 py-4 text-center">
                    No analyses yet for this brand.
                  </p>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {history.map((item) => (
                      <HistoryItem key={item.id} item={item} onSelect={loadHistoricalAnalysis} />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Upload card */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-5">
                <Upload className="w-4 h-4 text-forest-700" />
                <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Upload Marketing Image
                </h2>
              </div>

              {/* Brand selector */}
              <div className="mb-5">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Select Brand *
                </label>
                <select
                  value={selectedBrandId}
                  onChange={(e) => {
                    setSelectedBrandId(e.target.value);
                    clearImage();
                  }}
                  className="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-800"
                  id="brand-select"
                >
                  {brands.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Drag-and-drop zone */}
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => !imageFile && fileInputRef.current?.click()}
                className={`relative rounded-xl border-2 border-dashed transition-colors cursor-pointer ${
                  dragOver
                    ? 'border-forest-600 bg-forest-50/50'
                    : imageFile
                    ? 'border-forest-400 bg-white cursor-default'
                    : 'border-slate-300 bg-slate-50/50 hover:border-forest-400 hover:bg-forest-50/30'
                }`}
                style={{ minHeight: '240px' }}
                role="region"
                aria-label="Image drop zone"
              >
                {imagePreview ? (
                  /* Image preview */
                  <div className="p-4 flex flex-col items-center gap-3">
                    <img
                      src={imagePreview}
                      alt="Uploaded preview"
                      className="max-h-64 max-w-full rounded-lg object-contain shadow-sm border border-slate-200"
                    />
                    <div className="flex items-center gap-3">
                      <p className="text-xs text-slate-600 font-medium">
                        {imageFile?.name}{' '}
                        <span className="text-slate-400 font-mono">
                          ({(imageFile?.size / 1024).toFixed(0)} KB)
                        </span>
                      </p>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          clearImage();
                        }}
                        className="text-[11px] font-semibold text-red-600 hover:text-red-800 border border-red-200 rounded px-2 py-0.5 bg-red-50 transition-colors"
                        id="remove-image-btn"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Empty state */
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6">
                    <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
                      <ImageIcon className="w-7 h-7 text-slate-400" />
                    </div>
                    <div className="text-center">
                      <p className="text-sm font-semibold text-slate-700">
                        Drop your image here, or{' '}
                        <span className="text-forest-700 underline underline-offset-2">browse</span>
                      </p>
                      <p className="text-[11px] text-slate-400 mt-1">
                        PNG, JPG, JPEG — max {MAX_MB} MB
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept=".png,.jpg,.jpeg,image/png,image/jpeg"
                onChange={handleFilePick}
                className="hidden"
                id="image-file-input"
                aria-label="Image file upload"
              />

              {/* Analyze button */}
              <div className="mt-5 flex justify-end">
                <button
                  id="analyze-image-btn"
                  onClick={handleAnalyze}
                  disabled={analyzing || !imageFile || !selectedBrandId}
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg text-xs font-bold text-white bg-forest-900 hover:bg-forest-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Analyzing with AI…
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4 text-emerald-300" />
                      Run Visual Compliance Check
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* ── Analysis results ──────────────────────────────────────── */}
            {analyzing && (
              <div className="bg-white border border-slate-200 rounded-xl p-10 shadow-sm flex flex-col items-center justify-center gap-4">
                <div className="relative">
                  <div className="w-16 h-16 rounded-full bg-forest-50 border-2 border-forest-200 flex items-center justify-center">
                    <ShieldCheck className="w-8 h-8 text-forest-700 animate-pulse" />
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-sm font-bold text-slate-800 mb-1">
                    Analysing visual compliance…
                  </p>
                  <p className="text-xs text-slate-500 max-w-xs">
                    BrandGuard AI is inspecting your image against brand guidelines. This may take
                    a few seconds.
                  </p>
                </div>
                <div className="flex gap-1.5">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-2 h-2 rounded-full bg-forest-400 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </div>
            )}

            {analysis && !analyzing && (
              <div className="space-y-5" id="analysis-results">
                {/* Summary card */}
                <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Gauge className="w-4 h-4 text-forest-700" />
                        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                          Visual Compliance Summary
                        </h3>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed max-w-xl">
                        {analysis.summary}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-2 shrink-0">
                      <StatusBadge status={analysis.review_status} />
                      {analysis.compliance_score !== null && analysis.compliance_score !== undefined && (
                        <ScoreRing score={analysis.compliance_score} />
                      )}
                    </div>
                  </div>

                  {/* Severity summary grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                    {[
                      { label: 'High', count: highCount, cls: 'border-red-200 bg-red-50 text-red-700' },
                      { label: 'Medium', count: medCount, cls: 'border-amber-200 bg-amber-50 text-amber-700' },
                      { label: 'Low', count: lowCount, cls: 'border-sky-200 bg-sky-50 text-sky-700' },
                      { label: 'Unable to Verify', count: utv, cls: 'border-slate-200 bg-slate-50 text-slate-600' },
                    ].map(({ label, count, cls }) => (
                      <div
                        key={label}
                        className={`rounded-lg border px-3 py-2.5 flex flex-col items-center ${cls}`}
                      >
                        <span className="text-xl font-extrabold">{count}</span>
                        <span className="text-[10px] font-semibold opacity-80">{label}</span>
                      </div>
                    ))}
                  </div>

                  {/* Metadata */}
                  <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap gap-x-4 gap-y-1">
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <FileImage className="w-3 h-3" />
                      {analysis.original_filename}
                    </span>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(analysis.created_at).toLocaleString()}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Model: {analysis.model_identifier}
                    </span>
                  </div>

                  {/* Limitations warning */}
                  {analysis.has_limitations && (
                    <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-start gap-2">
                      <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                      <p className="text-[11px] text-slate-600">
                        <strong>Limitation notice:</strong> {utv} guideline
                        {utv !== 1 ? 's' : ''} could not be verified from the image alone and{' '}
                        {utv !== 1 ? 'are' : 'is'} marked "Unable to Verify". Human review is
                        recommended for those items.
                      </p>
                    </div>
                  )}

                  {/* Manager approval notice */}
                  <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                    <p className="text-[11px] text-amber-800">
                      This AI analysis does <strong>not</strong> constitute approval. Brand Manager
                      sign-off is always required before publishing.
                    </p>
                  </div>
                </div>

                {/* Findings */}
                {analysis.findings && analysis.findings.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-4">
                      Detailed Findings ({analysis.findings.length})
                    </h3>
                    <div className="space-y-3">
                      {analysis.findings.map((f, i) => (
                        <FindingCard key={f.id || i} finding={f} index={i} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Compliant with no findings */}
                {analysis.review_status === 'Compliant' &&
                  (!analysis.findings || analysis.findings.length === 0) && (
                    <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-8 text-center shadow-sm">
                      <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                      <h3 className="text-sm font-bold text-emerald-900 mb-1">
                        No Violations Detected
                      </h3>
                      <p className="text-xs text-emerald-700 max-w-sm mx-auto">
                        The uploaded image appears to comply with all evaluated brand guidelines.
                        Manager review is still required before publishing.
                      </p>
                    </div>
                  )}
              </div>
            )}
          </div>

          {/* ── Right: Guidelines sidebar ───────────────────────────────── */}
          <div className="space-y-5">
            {/* Info card */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                <Info className="w-4 h-4 text-forest-700" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  What is Checked
                </h3>
              </div>
              <ul className="space-y-2.5 text-xs text-slate-600">
                {[
                  { icon: '🏷️', label: 'Logo Usage', desc: 'Placement, distortion, clear space' },
                  { icon: '🎨', label: 'Brand Colors', desc: 'Palette consistency' },
                  { icon: '🔤', label: 'Typography', desc: 'Font style and hierarchy' },
                  { icon: '📐', label: 'Layout & Spacing', desc: 'Alignment, white space' },
                  { icon: '👁️', label: 'Contrast & Readability', desc: 'Legibility concerns' },
                  { icon: '🗂️', label: 'Visual Hierarchy', desc: 'Information structure' },
                ].map((item) => (
                  <li key={item.label} className="flex items-start gap-2">
                    <span className="text-base shrink-0">{item.icon}</span>
                    <div>
                      <p className="font-semibold text-slate-700">{item.label}</p>
                      <p className="text-[11px] text-slate-400">{item.desc}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Selected brand guidelines summary */}
            {selectedBrandId && brands.find((b) => b.id === parseInt(selectedBrandId)) && (
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                  <BookOpen className="w-4 h-4 text-forest-700" />
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    {brands.find((b) => b.id === parseInt(selectedBrandId))?.name} Profile
                  </h3>
                </div>
                {(() => {
                  const brand = brands.find((b) => b.id === parseInt(selectedBrandId));
                  return (
                    <div className="space-y-3 text-xs">
                      {brand?.tone_style && (
                        <div className="p-2.5 bg-purple-50 border border-purple-100 rounded-lg">
                          <p className="font-semibold text-purple-800 mb-0.5">Tone & Style</p>
                          <p className="text-purple-700 italic text-[11px]">"{brand.tone_style}"</p>
                        </div>
                      )}
                      {brand?.restricted_words && (
                        <div className="p-2.5 bg-red-50 border border-red-100 rounded-lg">
                          <p className="font-semibold text-red-800 mb-0.5">Restricted Words</p>
                          <p className="text-red-700 font-mono text-[11px]">
                            {brand.restricted_words}
                          </p>
                        </div>
                      )}
                      {brand?.approved_terminology && (
                        <div className="p-2.5 bg-emerald-50 border border-emerald-100 rounded-lg">
                          <p className="font-semibold text-emerald-800 mb-0.5">
                            Approved Terminology
                          </p>
                          <p className="text-emerald-700 font-mono text-[11px]">
                            {brand.approved_terminology}
                          </p>
                        </div>
                      )}
                      {!brand?.tone_style && !brand?.restricted_words && !brand?.approved_terminology && (
                        <p className="text-slate-400 text-[11px] text-center py-2">
                          No brand profile fields configured.
                        </p>
                      )}
                      <Link
                        to={`/creator/guidelines?brandId=${selectedBrandId}`}
                        target="_blank"
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-forest-700 hover:underline"
                      >
                        <BookOpen className="w-3 h-3" />
                        View all brand guidelines →
                      </Link>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* Tips */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                Tips for best results
              </p>
              <ul className="text-[11px] text-slate-500 space-y-1.5 list-disc list-inside">
                <li>Use the final, print-ready version of the image.</li>
                <li>Ensure the image is clear and not heavily compressed.</li>
                <li>Add brand guidelines to your brand profile for better checking.</li>
                <li>Results are AI-assisted — always confirm with a human reviewer.</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
};

export default VisualComplianceChecker;
