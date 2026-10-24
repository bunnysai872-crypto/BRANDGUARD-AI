import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import api from '../services/api';
import {
  Sparkles,
  BookOpen,
  Save,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Info,
  ShieldCheck,
  ChevronRight,
  Layers,
  ArrowLeft
} from 'lucide-react';
import { Link } from 'react-router-dom';

const CreateContent = () => {
  const navigate = useNavigate();
  const [brands, setBrands] = useState([]);
  const [selectedBrandId, setSelectedBrandId] = useState('');
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [brandGuidelines, setBrandGuidelines] = useState([]);
  const [loadingBrands, setLoadingBrands] = useState(true);

  const [title, setTitle] = useState('');
  const [contentText, setContentText] = useState('');
  const [status, setStatus] = useState('Draft');
  const [reason, setReason] = useState('Initial draft creation');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Fetch accessible brands
  useEffect(() => {
    const fetchBrands = async () => {
      try {
        const res = await api.get('/brands');
        if (res.data.success && res.data.brands.length > 0) {
          setBrands(res.data.brands);
          setSelectedBrandId(res.data.brands[0].id.toString());
          setSelectedBrand(res.data.brands[0]);
        }
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch brands');
      } finally {
        setLoadingBrands(false);
      }
    };
    fetchBrands();
  }, []);

  // Fetch guidelines for selected brand
  useEffect(() => {
    if (!selectedBrandId) return;
    const fetchGuidelines = async () => {
      try {
        const res = await api.get(`/brands/${selectedBrandId}/guidelines`);
        if (res.data.success) {
          setBrandGuidelines(res.data.guidelines);
        }
      } catch (err) {
        console.error('Failed to fetch brand guidelines', err);
      }
    };
    const brand = brands.find((b) => b.id === parseInt(selectedBrandId));
    setSelectedBrand(brand || null);
    fetchGuidelines();
  }, [selectedBrandId, brands]);

  // Statistics calculation
  const wordCount = contentText.trim() ? contentText.trim().split(/\s+/).length : 0;
  const charCount = contentText.length;
  const readingTime = Math.ceil(wordCount / 200);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedBrandId) {
      setError('Please select an accessible brand.');
      return;
    }
    if (!title.trim()) {
      setError('Please provide a submission title.');
      return;
    }
    if (!contentText.trim()) {
      setError('Please provide content copy.');
      return;
    }

    setError('');
    setSubmitting(true);

    try {
      const res = await api.post('/submissions', {
        brand_id: parseInt(selectedBrandId),
        title: title.trim(),
        content_text: contentText.trim(),
        status,
        reason: reason.trim() || 'Initial draft',
      });

      if (res.data.success) {
        navigate(`/submissions/${res.data.submission.id}`);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save submission');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout title="Create Content Draft">
      {/* Top Breadcrumb / Action */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <Link
          to="/creator/submissions"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Submissions</span>
        </Link>
      </div>

      {error && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loadingBrands ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
          <p className="text-xs font-medium">Checking brand memberships...</p>
        </div>
      ) : brands.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
          <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">No Brand Access Assigned</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            You do not currently have membership in any brand. Please contact your Brand Manager or Admin to be assigned as a contributor.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Content Form Area (2 cols) */}
            <div className="lg:col-span-2 space-y-5">
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                {/* Brand Selector */}
                <div className="mb-4">
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Select Target Brand *
                  </label>
                  <select
                    value={selectedBrandId}
                    onChange={(e) => setSelectedBrandId(e.target.value)}
                    className="w-full px-3 py-2.5 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-800"
                  >
                    {brands.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Submission Title */}
                <div className="mb-4">
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Promotional Campaign / Content Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Q4 CloudFlow Enterprise Product Launch Email"
                    className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-forest-800"
                  />
                </div>

                {/* Content Copy */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                      Promotional Marketing Copy *
                    </label>
                    <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
                      <span>{wordCount} words</span>
                      <span>•</span>
                      <span>{charCount} chars</span>
                      <span>•</span>
                      <span>~{readingTime} min read</span>
                    </div>
                  </div>

                  <textarea
                    rows={12}
                    required
                    value={contentText}
                    onChange={(e) => setContentText(e.target.value)}
                    placeholder="Write or paste your marketing promotional copy here. In Phase 3, BrandGuard AI will inspect this text against approved brand rules..."
                    className="w-full p-3.5 border border-slate-300 rounded-lg text-sm font-sans leading-relaxed text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-forest-800"
                  />
                </div>
              </div>

              {/* Status and Action Buttons */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-slate-600">Save Status:</span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setStatus('Draft')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border ${
                        status === 'Draft'
                          ? 'bg-slate-900 text-white border-slate-900'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      Save as Draft
                    </button>
                    <button
                      type="button"
                      onClick={() => setStatus('Ready for AI Review')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border ${
                        status === 'Ready for AI Review'
                          ? 'bg-forest-900 text-white border-forest-900'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      Ready for AI Review
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 disabled:opacity-50 transition-colors shadow-sm"
                  >
                    {submitting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4 text-emerald-300" />
                    )}
                    <span>Save Content Submission</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Side-Panel: Live Brand Guidelines Helper (1 col) */}
            <div className="space-y-5">
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                  <BookOpen className="w-4 h-4 text-forest-700" />
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    {selectedBrand?.name} Guidelines
                  </h3>
                </div>

                {selectedBrand?.tone_style && (
                  <div className="mb-4 p-3 bg-purple-50/60 border border-purple-200 rounded-lg text-xs">
                    <span className="font-semibold text-purple-900 block mb-0.5">Approved Tone:</span>
                    <p className="text-purple-800 italic">"{selectedBrand.tone_style}"</p>
                  </div>
                )}

                {selectedBrand?.approved_terminology && (
                  <div className="mb-4 p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg text-xs">
                    <span className="font-semibold text-emerald-900 block mb-1">
                      Approved Terminology:
                    </span>
                    <p className="text-emerald-800 font-mono text-[11px] leading-relaxed">
                      {selectedBrand.approved_terminology}
                    </p>
                  </div>
                )}

                {selectedBrand?.restricted_words && (
                  <div className="mb-4 p-3 bg-red-50/60 border border-red-200 rounded-lg text-xs">
                    <span className="font-semibold text-red-900 block mb-1">
                      Restricted / Prohibited Words:
                    </span>
                    <p className="text-red-800 font-mono text-[11px] leading-relaxed">
                      {selectedBrand.restricted_words}
                    </p>
                  </div>
                )}

                {/* Specific Guidelines List */}
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      Active Rules ({brandGuidelines.length})
                    </span>
                    <Link
                      to={`/creator/guidelines?brandId=${selectedBrandId}`}
                      target="_blank"
                      className="text-[11px] font-semibold text-forest-700 hover:underline"
                    >
                      View all
                    </Link>
                  </div>

                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {brandGuidelines.length === 0 ? (
                      <p className="text-xs text-slate-400 py-3 text-center">
                        No specific rules registered.
                      </p>
                    ) : (
                      brandGuidelines.map((rule) => (
                        <div
                          key={rule.id}
                          className="p-2.5 rounded-lg border border-slate-100 bg-slate-50/60 text-xs"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-bold text-slate-800">{rule.title}</span>
                            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white text-slate-500 border border-slate-200">
                              {rule.category}
                            </span>
                          </div>
                          <p className="text-slate-600 text-[11px] line-clamp-2">
                            {rule.rule_content}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </form>
      )}
    </DashboardLayout>
  );
};

export default CreateContent;
