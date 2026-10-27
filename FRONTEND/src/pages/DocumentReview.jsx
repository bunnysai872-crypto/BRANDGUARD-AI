import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import api from '../services/api';
import {
  Upload,
  FileText,
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
  HelpCircle,
  History,
  RefreshCw,
  FileType,
  Accessibility,
  Eye,
  BarChart2,
} from 'lucide-react';

// ─── Severity badge ───────────────────────────────────────────────────────────
const SeverityBadge = ({ severity }) => {
  const map = {
    Critical: 'bg-purple-100 text-purple-800 border-purple-200',
    High: 'bg-red-100 text-red-800 border-red-200',
    Medium: 'bg-amber-100 text-amber-800 border-amber-200',
    Low: 'bg-sky-100 text-sky-800 border-sky-200',
    'Unable to Verify': 'bg-slate-100 text-slate-600 border-slate-200',
  };
  return (
    <span className={`inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full border ${map[severity] || map['Unable to Verify']}`}>
      {severity}
    </span>
  );
};

// ─── Review type badge ────────────────────────────────────────────────────────
const TypeBadge = ({ type }) => {
  const isA11y = type === 'Accessibility';
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
      isA11y ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-forest-50 text-forest-700 border-forest-200'
    }`}>
      {isA11y ? <Accessibility className="w-2.5 h-2.5" /> : <ShieldCheck className="w-2.5 h-2.5" />}
      {type}
    </span>
  );
};

// ─── Status badge ─────────────────────────────────────────────────────────────
const StatusBadge = ({ status }) => {
  const map = {
    Compliant: { cls: 'bg-emerald-50 text-emerald-800 border-emerald-200', Icon: CheckCircle2 },
    'Action Required': { cls: 'bg-amber-50 text-amber-800 border-amber-200', Icon: AlertTriangle },
    'Violations Detected': { cls: 'bg-red-50 text-red-800 border-red-200', Icon: XCircle },
  };
  const { cls, Icon } = map[status] || map['Action Required'];
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${cls}`}>
      <Icon className="w-3.5 h-3.5" />
      {status}
    </span>
  );
};

// ─── Finding card ─────────────────────────────────────────────────────────────
const FindingCard = ({ finding }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className={`rounded-xl border transition-all ${
      finding.severity === 'Critical' ? 'border-purple-200 bg-purple-50/30' :
      finding.severity === 'High' ? 'border-red-200 bg-red-50/30' :
      finding.severity === 'Medium' ? 'border-amber-200 bg-amber-50/20' :
      finding.severity === 'Low' ? 'border-sky-200 bg-sky-50/20' :
      'border-slate-200 bg-slate-50/40'
    }`}>
      <button
        onClick={() => setOpen(p => !p)}
        className="w-full flex items-start gap-3 p-4 text-left"
        aria-expanded={open}
      >
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-1.5 mb-1">
            <SeverityBadge severity={finding.severity} />
            <TypeBadge type={finding.review_type} />
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-500">
              {finding.category}
            </span>
            {finding.human_verification_required && (
              <span className="text-[10px] font-semibold text-purple-700 bg-purple-50 border border-purple-200 px-1.5 py-0.5 rounded-full">
                Human review
              </span>
            )}
          </div>
          <p className="text-xs font-semibold text-slate-800 line-clamp-2">{finding.problematic_text}</p>
        </div>
        <span className="shrink-0 text-slate-400 mt-1">
          {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </span>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-white/60 pt-3">
          {/* Guideline reference */}
          {finding.guideline_title && (
            <div className="flex items-start gap-2 p-2.5 bg-white/70 rounded-lg border border-slate-100">
              <BookOpen className="w-3.5 h-3.5 text-forest-700 shrink-0 mt-0.5" />
              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-0.5">Brand Guideline Referenced</p>
                <p className="text-xs font-semibold text-slate-800">{finding.guideline_title}</p>
                {finding.guideline_rule && (
                  <p className="text-[11px] text-slate-600 mt-0.5 italic">"{finding.guideline_rule}"</p>
                )}
              </div>
            </div>
          )}

          {/* Explanation */}
          <div>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Finding</p>
            <p className="text-xs text-slate-700 leading-relaxed">{finding.explanation}</p>
          </div>

          {/* Correction */}
          {finding.suggested_correction && (
            <div className="p-2.5 bg-emerald-50/60 border border-emerald-100 rounded-lg">
              <p className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider mb-1">Suggested Correction</p>
              <p className="text-xs text-emerald-800 leading-relaxed">{finding.suggested_correction}</p>
            </div>
          )}

          {/* Unable to verify */}
          {finding.severity === 'Unable to Verify' && (
            <div className="flex items-start gap-2 p-2.5 bg-slate-100 rounded-lg border border-slate-200">
              <HelpCircle className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
              <p className="text-[11px] text-slate-600">
                This check cannot be confirmed from text alone and requires human review.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── History item ─────────────────────────────────────────────────────────────
const HistoryItem = ({ item, onSelect }) => {
  const fmtIcon = { txt: '📄', pdf: '📕', docx: '📘' };
  return (
    <button
      onClick={() => onSelect(item.id)}
      className="w-full text-left flex items-center gap-3 p-3 rounded-lg border border-slate-100 bg-white hover:border-forest-300 hover:bg-forest-50/30 transition-colors"
    >
      <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0 text-base">
        {fmtIcon[item.detected_format] || '📄'}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-slate-800 truncate">{item.original_filename}</p>
        <p className="text-[11px] text-slate-500">
          {new Date(item.created_at).toLocaleString()} •{' '}
          <span className={item.review_status === 'Compliant' ? 'text-emerald-600' : item.review_status === 'Violations Detected' ? 'text-red-600' : 'text-amber-600'}>
            {item.review_status}
          </span>
        </p>
      </div>
      <span className="text-[11px] font-bold text-slate-500 shrink-0 uppercase">{item.detected_format}</span>
    </button>
  );
};

// ─── Main component ───────────────────────────────────────────────────────────
const DocumentReview = () => {
  const [brands, setBrands] = useState([]);
  const [selectedBrandId, setSelectedBrandId] = useState('');
  const [loadingBrands, setLoadingBrands] = useState(true);

  const [docFile, setDocFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const [reviewing, setReviewing] = useState(false);
  const [review, setReview] = useState(null);
  const [error, setError] = useState('');

  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // Active filter tab: 'all' | 'Brand Compliance' | 'Accessibility'
  const [activeTab, setActiveTab] = useState('all');

  const MAX_MB = 20;
  const ALLOWED = ['text/plain', 'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  const ALLOWED_EXT = ['txt', 'pdf', 'docx'];

  // ── Fetch brands ────────────────────────────────────────────────────────────
  useEffect(() => {
    api.get('/brands').then(res => {
      if (res.data.success && res.data.brands.length > 0) {
        setBrands(res.data.brands);
        setSelectedBrandId(res.data.brands[0].id.toString());
      }
    }).catch(err => setError(err.response?.data?.error || 'Failed to load brands.')).finally(() => setLoadingBrands(false));
  }, []);

  // ── Fetch history when brand changes ────────────────────────────────────────
  useEffect(() => {
    if (!selectedBrandId) return;
    setReview(null);
    fetchHistory();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBrandId]);

  const fetchHistory = async () => {
    if (!selectedBrandId) return;
    setHistoryLoading(true);
    try {
      const res = await api.get(`/document-review/brands/${selectedBrandId}/history`);
      if (res.data.success) setHistory(res.data.history || []);
    } catch { setHistory([]); } finally { setHistoryLoading(false); }
  };

  // ── File handling ───────────────────────────────────────────────────────────
  const processFile = useCallback((file) => {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXT.includes(ext)) {
      setError('Only TXT, PDF, and DOCX files are supported.');
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`Document must be smaller than ${MAX_MB} MB.`);
      return;
    }
    setError('');
    setReview(null);
    setDocFile(file);
  }, []);

  const handleFilePick = e => processFile(e.target.files?.[0]);
  const handleDrop = e => { e.preventDefault(); setDragOver(false); processFile(e.dataTransfer.files?.[0]); };
  const clearFile = () => { setDocFile(null); setReview(null); setError(''); if (fileInputRef.current) fileInputRef.current.value = ''; };

  // ── Load historical review ──────────────────────────────────────────────────
  const loadHistoricalReview = async (reviewId) => {
    try {
      const res = await api.get(`/document-review/${reviewId}`);
      if (res.data.success) {
        setReview(res.data.review);
        setDocFile(null);
        setShowHistory(false);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } catch (err) { setError(err.response?.data?.error || 'Failed to load review.'); }
  };

  // ── Submit ──────────────────────────────────────────────────────────────────
  const handleAnalyze = async e => {
    e.preventDefault();
    if (!selectedBrandId) { setError('Please select a brand.'); return; }
    if (!docFile) { setError('Please upload a document to review.'); return; }
    setError(''); setReviewing(true); setReview(null);
    const formData = new FormData();
    formData.append('brand_id', selectedBrandId);
    formData.append('document', docFile);
    try {
      const res = await api.post('/document-review/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data.success) { setReview(res.data.review); fetchHistory(); }
    } catch (err) {
      setError(err.response?.data?.error || 'Document review failed. Please try again.');
    } finally { setReviewing(false); }
  };

  // ── Derived state ────────────────────────────────────────────────────────────
  const filteredFindings = review?.findings?.filter(f =>
    activeTab === 'all' || f.review_type === activeTab
  ) ?? [];

  const brandFindings = review?.findings?.filter(f => f.review_type === 'Brand Compliance').length ?? 0;
  const a11yFindings = review?.findings?.filter(f => f.review_type === 'Accessibility').length ?? 0;

  const fmtIcon = { txt: '📄', pdf: '📕', docx: '📘' };
  const ext = docFile?.name?.split('.').pop().toLowerCase();

  return (
    <DashboardLayout title="Document Review">
      {/* Breadcrumb */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <Link to="/creator-dashboard" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
        <button
          onClick={() => { setShowHistory(p => !p); if (!showHistory) fetchHistory(); }}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 border border-slate-200 rounded-lg px-3 py-1.5 bg-white hover:bg-slate-50 transition-colors"
        >
          <History className="w-3.5 h-3.5" />
          {showHistory ? 'Hide History' : 'Past Reviews'}
        </button>
      </div>

      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-700 to-forest-800 flex items-center justify-center shadow-sm">
            <FileType className="w-5 h-5 text-indigo-200" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Multi-Format & Accessibility Review</h1>
            <p className="text-xs text-slate-500">Upload TXT, PDF, or DOCX documents for brand compliance and accessibility analysis.</p>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-xs text-red-700">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {loadingBrands ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-forest-700 mb-2" />
          <p className="text-xs font-medium">Loading brands…</p>
        </div>
      ) : brands.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
          <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">No Brand Access</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">Contact your Brand Manager to get access to a brand.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* ── Left: Upload + Results ─────────────────────────────────────── */}
          <div className="lg:col-span-2 space-y-5">

            {/* History panel */}
            {showHistory && (
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <History className="w-4 h-4 text-forest-700" />
                    <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Past Document Reviews</h3>
                  </div>
                  <button onClick={fetchHistory} disabled={historyLoading} className="text-[11px] font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1">
                    <RefreshCw className={`w-3 h-3 ${historyLoading ? 'animate-spin' : ''}`} /> Refresh
                  </button>
                </div>
                {historyLoading ? (
                  <div className="py-6 flex items-center justify-center"><Loader2 className="w-5 h-5 animate-spin text-slate-400" /></div>
                ) : history.length === 0 ? (
                  <p className="text-xs text-slate-400 py-4 text-center">No reviews yet for this brand.</p>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {history.map(item => <HistoryItem key={item.id} item={item} onSelect={loadHistoricalReview} />)}
                  </div>
                )}
              </div>
            )}

            {/* Upload card */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-5">
                <Upload className="w-4 h-4 text-forest-700" />
                <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Upload Document</h2>
              </div>

              {/* Brand selector */}
              <div className="mb-5">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">Select Brand *</label>
                <select
                  value={selectedBrandId}
                  onChange={e => { setSelectedBrandId(e.target.value); clearFile(); }}
                  className="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-800"
                  id="doc-brand-select"
                >
                  {brands.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </div>

              {/* Drag-and-drop zone */}
              <div
                onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => !docFile && fileInputRef.current?.click()}
                className={`relative rounded-xl border-2 border-dashed transition-colors cursor-pointer ${
                  dragOver ? 'border-indigo-500 bg-indigo-50/40' :
                  docFile ? 'border-forest-400 bg-white cursor-default' :
                  'border-slate-300 bg-slate-50/50 hover:border-forest-400 hover:bg-forest-50/20'
                }`}
                style={{ minHeight: '160px' }}
                role="region"
                aria-label="Document drop zone"
              >
                {docFile ? (
                  <div className="p-6 flex flex-col items-center gap-3">
                    <div className="text-4xl">{fmtIcon[ext] || '📄'}</div>
                    <div className="text-center">
                      <p className="text-sm font-semibold text-slate-800">{docFile.name}</p>
                      <p className="text-xs text-slate-400 font-mono">{(docFile.size / 1024).toFixed(0)} KB • {ext?.toUpperCase()}</p>
                    </div>
                    <button
                      type="button"
                      onClick={e => { e.stopPropagation(); clearFile(); }}
                      className="text-[11px] font-semibold text-red-600 hover:text-red-800 border border-red-200 rounded px-2 py-0.5 bg-red-50 transition-colors"
                      id="remove-doc-btn"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6">
                    <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
                      <FileText className="w-7 h-7 text-slate-400" />
                    </div>
                    <div className="text-center">
                      <p className="text-sm font-semibold text-slate-700">
                        Drop document here, or <span className="text-forest-700 underline underline-offset-2">browse</span>
                      </p>
                      <p className="text-[11px] text-slate-400 mt-1">TXT, PDF, DOCX — max {MAX_MB} MB</p>
                    </div>
                  </div>
                )}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.pdf,.docx,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={handleFilePick}
                className="hidden"
                id="doc-file-input"
                aria-label="Document file upload"
              />

              <div className="mt-5 flex justify-end">
                <button
                  id="analyze-doc-btn"
                  onClick={handleAnalyze}
                  disabled={reviewing || !docFile || !selectedBrandId}
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg text-xs font-bold text-white bg-indigo-700 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                >
                  {reviewing ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Analysing…</>
                  ) : (
                    <><Eye className="w-4 h-4" /> Run Document Review</>
                  )}
                </button>
              </div>
            </div>

            {/* Analysing state */}
            {reviewing && (
              <div className="bg-white border border-slate-200 rounded-xl p-10 shadow-sm flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-indigo-50 border-2 border-indigo-200 flex items-center justify-center">
                  <FileType className="w-8 h-8 text-indigo-600 animate-pulse" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-bold text-slate-800 mb-1">Reviewing document…</p>
                  <p className="text-xs text-slate-500 max-w-xs">Extracting text, checking brand guidelines, and analysing accessibility. This may take a few seconds.</p>
                </div>
                <div className="flex gap-1.5">
                  {[0,1,2].map(i => (
                    <div key={i} className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            )}

            {/* Results */}
            {review && !reviewing && (
              <div className="space-y-5" id="review-results">
                {/* Summary card */}
                <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <BarChart2 className="w-4 h-4 text-forest-700" />
                        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Review Summary</h3>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{review.summary}</p>
                    </div>
                    <div className="shrink-0">
                      <StatusBadge status={review.review_status} />
                    </div>
                  </div>

                  {/* Counts grid */}
                  <div className="grid grid-cols-3 sm:grid-cols-5 gap-2.5 mt-4">
                    {[
                      { label: 'Critical', count: review.critical_severity_count, cls: 'border-purple-200 bg-purple-50 text-purple-700' },
                      { label: 'High', count: review.high_severity_count, cls: 'border-red-200 bg-red-50 text-red-700' },
                      { label: 'Medium', count: review.medium_severity_count, cls: 'border-amber-200 bg-amber-50 text-amber-700' },
                      { label: 'Low', count: review.low_severity_count, cls: 'border-sky-200 bg-sky-50 text-sky-700' },
                      { label: 'Unverifiable', count: review.unable_to_verify_count, cls: 'border-slate-200 bg-slate-50 text-slate-600' },
                    ].map(({ label, count, cls }) => (
                      <div key={label} className={`rounded-lg border px-2 py-2.5 flex flex-col items-center ${cls}`}>
                        <span className="text-lg font-extrabold">{count}</span>
                        <span className="text-[10px] font-semibold opacity-80">{label}</span>
                      </div>
                    ))}
                  </div>

                  {/* Metadata */}
                  <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap gap-x-4 gap-y-1">
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <FileText className="w-3 h-3" /> {review.original_filename}
                    </span>
                    <span className="text-[11px] text-slate-400 uppercase font-mono">{review.detected_format}</span>
                    <span className="text-[11px] text-slate-400">{review.extracted_char_count.toLocaleString()} chars extracted</span>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {new Date(review.created_at).toLocaleString()}
                    </span>
                  </div>

                  {/* Limitations */}
                  {review.has_limitations && (
                    <div className="mt-3 p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-start gap-2">
                      <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                      <p className="text-[11px] text-slate-600">
                        <strong>Limitation notice:</strong> {review.unable_to_verify_count} check{review.unable_to_verify_count !== 1 ? 's' : ''} could not be verified from text content alone and {review.unable_to_verify_count !== 1 ? 'are' : 'is'} marked "Unable to Verify". Human review is recommended for those items. Text extraction cannot assess visual layout, colour contrast, or image content.
                      </p>
                    </div>
                  )}

                  {/* No auto-approve warning */}
                  <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                    <p className="text-[11px] text-amber-800">
                      This review does <strong>not</strong> constitute approval. Brand Manager sign-off is always required before publishing.
                    </p>
                  </div>
                </div>

                {/* Findings */}
                {review.findings && review.findings.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                    {/* Tabs */}
                    <div className="flex items-center gap-2 mb-4 flex-wrap">
                      {[
                        { key: 'all', label: `All (${review.findings.length})` },
                        { key: 'Brand Compliance', label: `Brand (${brandFindings})` },
                        { key: 'Accessibility', label: `Accessibility (${a11yFindings})` },
                      ].map(tab => (
                        <button
                          key={tab.key}
                          onClick={() => setActiveTab(tab.key)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border ${
                            activeTab === tab.key
                              ? 'bg-slate-900 text-white border-slate-900'
                              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                          }`}
                        >
                          {tab.label}
                        </button>
                      ))}
                    </div>

                    <div className="space-y-3">
                      {filteredFindings.length === 0 ? (
                        <p className="text-xs text-slate-400 py-4 text-center">No {activeTab === 'all' ? '' : activeTab.toLowerCase()} findings.</p>
                      ) : (
                        filteredFindings.map((f, i) => <FindingCard key={f.id || i} finding={f} />)
                      )}
                    </div>
                  </div>
                )}

                {/* Fully compliant */}
                {review.review_status === 'Compliant' && (!review.findings || review.findings.length === 0) && (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-8 text-center shadow-sm">
                    <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                    <h3 className="text-sm font-bold text-emerald-900 mb-1">No Issues Detected</h3>
                    <p className="text-xs text-emerald-700 max-w-sm mx-auto">
                      The document appears to comply with all evaluated brand guidelines. Note that text-only analysis has inherent limitations. Manager review is still required.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Right: Info sidebar ─────────────────────────────────────────── */}
          <div className="space-y-5">
            {/* What is checked */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                <Info className="w-4 h-4 text-forest-700" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">What is Reviewed</h3>
              </div>
              <div className="space-y-4 text-xs">
                <div>
                  <p className="font-bold text-forest-800 flex items-center gap-1 mb-1.5">
                    <ShieldCheck className="w-3.5 h-3.5" /> Brand Compliance
                  </p>
                  <ul className="space-y-1 text-slate-600 list-disc list-inside text-[11px]">
                    <li>Prohibited / restricted words</li>
                    <li>Tone and voice alignment</li>
                    <li>Unsupported or false claims</li>
                    <li>Missing required disclaimers</li>
                    <li>Terminology violations</li>
                  </ul>
                </div>
                <div>
                  <p className="font-bold text-indigo-700 flex items-center gap-1 mb-1.5">
                    <Accessibility className="w-3.5 h-3.5" /> Accessibility (Text-Based)
                  </p>
                  <ul className="space-y-1 text-slate-600 list-disc list-inside text-[11px]">
                    <li>Language complexity & jargon</li>
                    <li>Heading / structure (where detectable)</li>
                    <li>Vague link text ("click here")</li>
                    <li>Run-on prose vs list structure</li>
                    <li>Plain language issues</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Supported formats */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                <FileType className="w-4 h-4 text-forest-700" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Supported Formats</h3>
              </div>
              <div className="space-y-2">
                {[
                  { icon: '📄', fmt: 'TXT', desc: 'Plain text, UTF-8 / Latin-1', limit: '20 MB' },
                  { icon: '📕', fmt: 'PDF', desc: 'Text-based PDFs only (not image-scanned)', limit: '20 MB' },
                  { icon: '📘', fmt: 'DOCX', desc: 'Word documents (text + tables)', limit: '20 MB' },
                ].map(item => (
                  <div key={item.fmt} className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-lg">{item.icon}</span>
                    <div>
                      <p className="text-xs font-bold text-slate-800">{item.fmt}</p>
                      <p className="text-[11px] text-slate-500">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Limitations notice */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Known Limitations</p>
              <ul className="text-[11px] text-slate-500 space-y-1.5 list-disc list-inside">
                <li>Image-scanned PDFs yield no extractable text.</li>
                <li>Visual accessibility (contrast, layout) cannot be checked from text.</li>
                <li>Embedded images and alt-text are not always extractable.</li>
                <li>Results are AI-assisted — always confirm with a human reviewer.</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
};

export default DocumentReview;
