import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  BookOpen,
  Plus,
  Search,
  Edit2,
  Trash2,
  AlertCircle,
  Check,
  X,
  Loader2,
  CheckCircle2,
  XCircle,
  FileCheck,
  ShieldCheck,
  Layers,
  FileText,
  UploadCloud,
  ToggleLeft,
  ToggleRight,
  ShieldAlert,
  Info
} from 'lucide-react';

const CATEGORIES = [
  'All',
  'Tone',
  'Terminology',
  'Messaging',
  'Approved Facts',
  'Prohibited Claims',
  'Restricted Claims',
  'Mandatory Disclaimer',
  'Visual Identity',
  'Accessibility',
  'Other'
];

const SEVERITIES = ['Low', 'Medium', 'High', 'Critical'];

const GuidelinesPage = () => {
  const { user, isAdmin } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const brandIdFromUrl = searchParams.get('brandId');
  const fileInputRef = useRef(null);

  const [brands, setBrands] = useState([]);
  const [selectedBrandId, setSelectedBrandId] = useState('');
  const [guidelines, setGuidelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [extractingDoc, setExtractingDoc] = useState(false);
  const [extractMsg, setExtractMsg] = useState('');

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingGuideline, setEditingGuideline] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    category: 'Tone',
    title: '',
    rule_content: '',
    reference_evidence: '',
    approved_wording: '',
    prohibited_wording: '',
    severity: 'Medium',
    is_active: true,
  });

  // Fetch accessible brands
  useEffect(() => {
    const fetchBrands = async () => {
      try {
        const res = await api.get('/brands');
        if (res.data.success && res.data.brands.length > 0) {
          setBrands(res.data.brands);
          if (brandIdFromUrl && res.data.brands.some((b) => b.id === parseInt(brandIdFromUrl))) {
            setSelectedBrandId(brandIdFromUrl);
          } else {
            setSelectedBrandId(res.data.brands[0].id.toString());
          }
        } else {
          setLoading(false);
        }
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch brands');
        setLoading(false);
      }
    };
    fetchBrands();
  }, [brandIdFromUrl]);

  // Fetch guidelines whenever selectedBrandId or activeCategory changes
  useEffect(() => {
    if (!selectedBrandId) return;

    const fetchGuidelines = async () => {
      setLoading(true);
      setError('');
      try {
        const url = activeCategory === 'All'
          ? `/brands/${selectedBrandId}/guidelines`
          : `/brands/${selectedBrandId}/guidelines?category=${encodeURIComponent(activeCategory)}`;
        const res = await api.get(url);
        if (res.data.success) {
          setGuidelines(res.data.guidelines);
        }
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load guidelines');
      } finally {
        setLoading(false);
      }
    };

    fetchGuidelines();
  }, [selectedBrandId, activeCategory]);

  const handleBrandChange = (e) => {
    const newId = e.target.value;
    setSelectedBrandId(newId);
    setSearchParams({ brandId: newId });
  };

  const handleOpenCreate = () => {
    setEditingGuideline(null);
    setFormData({
      category: activeCategory !== 'All' ? activeCategory : 'Tone',
      title: '',
      rule_content: '',
      reference_evidence: '',
      approved_wording: '',
      prohibited_wording: '',
      severity: 'Medium',
      is_active: true,
    });
    setExtractMsg('');
    setShowModal(true);
  };

  const handleOpenEdit = (guideline) => {
    setEditingGuideline(guideline);
    setFormData({
      category: guideline.category,
      title: guideline.title,
      rule_content: guideline.rule_content,
      reference_evidence: guideline.reference_evidence || '',
      approved_wording: guideline.approved_wording || '',
      prohibited_wording: guideline.prohibited_wording || '',
      severity: guideline.severity || 'Medium',
      is_active: guideline.is_active !== undefined ? guideline.is_active : true,
    });
    setExtractMsg('');
    setShowModal(true);
  };

  const handleSaveGuideline = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (editingGuideline) {
        const res = await api.put(`/guidelines/${editingGuideline.id}`, formData);
        if (res.data.success) {
          setSuccessMsg('Guideline updated successfully.');
          setShowModal(false);
          refreshGuidelines();
        }
      } else {
        const res = await api.post(`/brands/${selectedBrandId}/guidelines`, formData);
        if (res.data.success) {
          setSuccessMsg('Guideline rule created successfully.');
          setShowModal(false);
          refreshGuidelines();
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save guideline');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (guideline) => {
    try {
      const res = await api.post(`/guidelines/${guideline.id}/toggle-active`);
      if (res.data.success) {
        setSuccessMsg(`Guideline "${guideline.title}" is now ${res.data.guideline.is_active ? 'Active' : 'Inactive'}.`);
        refreshGuidelines();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to toggle status');
    }
  };

  const handleDeleteGuideline = async (id) => {
    if (!window.confirm('Are you sure you want to delete this guideline rule?')) return;
    try {
      const res = await api.delete(`/guidelines/${id}`);
      if (res.data.success) {
        setSuccessMsg('Guideline deleted.');
        refreshGuidelines();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete guideline');
    }
  };

  const handleDocumentUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const fileExt = file.name.split('.').pop()?.toLowerCase();
    if (!['txt', 'pdf'].includes(fileExt)) {
      setError('Only .txt and .pdf guideline documents are supported.');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('Document file size exceeds 5MB limit.');
      return;
    }

    const uploadData = new FormData();
    uploadData.append('file', file);

    setExtractingDoc(true);
    setExtractMsg('Extracting text securely from document...');
    setError('');

    try {
      const res = await api.post('/guidelines/extract-text', uploadData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (res.data.success) {
        const extracted = res.data.extracted_text;
        setFormData((prev) => ({
          ...prev,
          rule_content: prev.rule_content ? `${prev.rule_content}\n\n${extracted}` : extracted,
          title: prev.title || file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ')
        }));
        setExtractMsg(`Extracted ${res.data.length} characters from "${res.data.filename}". Review and edit before saving.`);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to extract text from document');
      setExtractMsg('');
    } finally {
      setExtractingDoc(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const refreshGuidelines = async () => {
    try {
      const url = activeCategory === 'All'
        ? `/brands/${selectedBrandId}/guidelines`
        : `/brands/${selectedBrandId}/guidelines?category=${encodeURIComponent(activeCategory)}`;
      const res = await api.get(url);
      if (res.data.success) {
        setGuidelines(res.data.guidelines);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const filteredGuidelines = guidelines.filter((g) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      g.title.toLowerCase().includes(q) ||
      g.rule_content.toLowerCase().includes(q) ||
      (g.approved_wording && g.approved_wording.toLowerCase().includes(q)) ||
      (g.prohibited_wording && g.prohibited_wording.toLowerCase().includes(q)) ||
      (g.reference_evidence && g.reference_evidence.toLowerCase().includes(q))
    );
  });

  const getCategoryBadgeClass = (category) => {
    switch (category) {
      case 'Tone':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'Terminology':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Messaging':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'Approved Facts':
        return 'bg-teal-50 text-teal-800 border-teal-200';
      case 'Prohibited Claims':
      case 'Restricted Claims':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      case 'Mandatory Disclaimer':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'Visual Identity':
        return 'bg-indigo-50 text-indigo-800 border-indigo-200';
      case 'Accessibility':
        return 'bg-cyan-50 text-cyan-800 border-cyan-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getSeverityBadgeClass = (sev) => {
    switch (sev) {
      case 'Critical':
        return 'bg-red-700 text-white border-red-800 font-bold';
      case 'High':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'Medium':
        return 'bg-amber-100 text-amber-900 border-amber-300';
      case 'Low':
      default:
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    }
  };

  const selectedBrand = brands.find((b) => b.id === parseInt(selectedBrandId));

  return (
    <DashboardLayout title="Brand Guidelines Management">
      {/* Top Banner & Brand Switcher */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-forest-900 text-white flex items-center justify-center font-bold">
              <BookOpen className="w-5 h-5 text-emerald-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Active Brand Context
                </span>
                {!isAdmin && (
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                    Read-Only Reference
                  </span>
                )}
              </div>
              {brands.length > 0 ? (
                <select
                  value={selectedBrandId}
                  onChange={handleBrandChange}
                  className="mt-0.5 text-base font-bold text-slate-900 bg-transparent border-0 border-b border-dashed border-slate-300 hover:border-forest-700 focus:outline-none cursor-pointer"
                >
                  {brands.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="text-sm font-semibold text-slate-600">No brands accessible.</p>
              )}
            </div>
          </div>

          {isAdmin && (
            <div className="flex items-center gap-2">
              <button
                onClick={handleOpenCreate}
                disabled={!selectedBrandId}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 transition-colors shadow-sm disabled:opacity-50"
              >
                <Plus className="w-4 h-4 text-emerald-300" />
                <span>Add Guideline Rule</span>
              </button>
            </div>
          )}
        </div>

        {/* Brand Tone Quick Snippet */}
        {selectedBrand?.tone_style && (
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-600">
            <span className="font-semibold text-forest-800">Approved Tone Style:</span>
            <span className="italic">"{selectedBrand.tone_style}"</span>
          </div>
        )}
      </div>

      {/* Notifications */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between text-xs text-red-700">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError('')}><X className="w-4 h-4" /></button>
        </div>
      )}

      {successMsg && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')}><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Category Pills & Search */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 mb-6">
        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 md:pb-0 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors border ${
                activeCategory === cat
                  ? 'bg-forest-900 text-white border-forest-900 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search rules, wording, or references..."
            className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-800"
          />
        </div>
      </div>

      {/* Guidelines Cards Grid */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
          <p className="text-xs font-medium">Loading guideline rules...</p>
        </div>
      ) : brands.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
          <Layers className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">No brand profiles found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            {isAdmin
              ? 'Please create a brand profile before establishing guidelines.'
              : 'You have not been assigned to any brands yet. Contact your Brand Manager.'}
          </p>
        </div>
      ) : filteredGuidelines.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
          <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">
            {searchQuery ? 'No matching guidelines' : 'No guidelines recorded in this category'}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            {isAdmin
              ? 'Add guidelines for tone, terminology, prohibited claims, approved wording, and mandatory disclaimers.'
              : 'The Brand Manager has not added guidelines to this category yet.'}
          </p>
          {isAdmin && (
            <button
              onClick={handleOpenCreate}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>Add Guideline</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredGuidelines.map((g) => (
            <div
              key={g.id}
              className={`bg-white border rounded-xl p-5 shadow-sm transition-all flex flex-col justify-between ${
                g.is_active === false ? 'border-dashed border-slate-300 bg-slate-50/50 opacity-75' : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${getCategoryBadgeClass(
                        g.category
                      )}`}
                    >
                      {g.category}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full border ${getSeverityBadgeClass(
                        g.severity || 'Medium'
                      )}`}
                    >
                      {g.severity || 'Medium'} Severity
                    </span>
                    {g.is_active === false && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-200 text-slate-600 font-semibold">
                        Inactive
                      </span>
                    )}
                  </div>

                  <span className="text-[10px] font-mono text-slate-400">#{g.id}</span>
                </div>

                <h3 className="text-sm font-bold text-slate-900 mb-2 leading-snug">{g.title}</h3>

                <p className="text-xs text-slate-600 leading-relaxed mb-4 whitespace-pre-line">
                  {g.rule_content}
                </p>

                {/* Approved Wording */}
                {g.approved_wording && (
                  <div className="p-2.5 rounded-lg bg-emerald-50/70 border border-emerald-100 text-[11px] text-emerald-900 mb-2">
                    <div className="flex items-center gap-1.5 font-semibold text-emerald-800 mb-0.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Approved Wording / Facts:</span>
                    </div>
                    <span className="italic">{g.approved_wording}</span>
                  </div>
                )}

                {/* Prohibited Wording */}
                {g.prohibited_wording && (
                  <div className="p-2.5 rounded-lg bg-rose-50/70 border border-rose-100 text-[11px] text-rose-900 mb-2">
                    <div className="flex items-center gap-1.5 font-semibold text-rose-800 mb-0.5">
                      <XCircle className="w-3.5 h-3.5 text-rose-600" />
                      <span>Prohibited Wording / Claims:</span>
                    </div>
                    <span className="italic">{g.prohibited_wording}</span>
                  </div>
                )}

                {g.reference_evidence && (
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-[11px] text-slate-600 mb-2">
                    <span className="font-semibold text-slate-700 block mb-0.5">
                      Approved Reference / Evidence:
                    </span>
                    <span>{g.reference_evidence}</span>
                  </div>
                )}
              </div>

              {/* Manager Actions */}
              {isAdmin && (
                <div className="flex items-center justify-between gap-2 pt-3 border-t border-slate-100 mt-2">
                  <button
                    onClick={() => handleToggleActive(g)}
                    title={g.is_active ? 'Click to deactivate rule' : 'Click to activate rule'}
                    className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded transition-colors ${
                      g.is_active !== false
                        ? 'text-emerald-700 hover:bg-emerald-50'
                        : 'text-slate-500 hover:bg-slate-200'
                    }`}
                  >
                    {g.is_active !== false ? (
                      <>
                        <ToggleRight className="w-4 h-4 text-emerald-600" />
                        <span>Active</span>
                      </>
                    ) : (
                      <>
                        <ToggleLeft className="w-4 h-4 text-slate-400" />
                        <span>Inactive</span>
                      </>
                    )}
                  </button>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleOpenEdit(g)}
                      title="Edit Guideline"
                      className="p-1.5 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteGuideline(g.id)}
                      title="Delete Guideline"
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* CREATE / EDIT GUIDELINE MODAL */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full p-6 my-8 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  {editingGuideline ? 'Edit Guideline Rule' : 'New Guideline Rule'}
                </h3>
                <p className="text-xs text-slate-500">
                  Guidelines are fed to Gemini to govern promotional compliance grounded in brand facts.
                </p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Document Import Helper */}
            {!editingGuideline && (
              <div className="mb-5 p-3.5 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <UploadCloud className="w-4 h-4 text-forest-800 shrink-0" />
                    <div>
                      <p className="text-xs font-semibold text-slate-800">
                        Import from Guideline Document (.txt or .pdf)
                      </p>
                      <p className="text-[11px] text-slate-500">
                        Securely extracts text directly into the rule description. Max 5MB.
                      </p>
                    </div>
                  </div>
                  <label className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-forest-900 bg-white border border-slate-300 hover:bg-slate-50 shadow-2xs">
                    {extractingDoc ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <FileText className="w-3.5 h-3.5 text-forest-700" />
                    )}
                    <span>{extractingDoc ? 'Extracting...' : 'Upload File'}</span>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".txt,.pdf"
                      onChange={handleDocumentUpload}
                      disabled={extractingDoc}
                      className="hidden"
                    />
                  </label>
                </div>
                {extractMsg && (
                  <p className="mt-2 text-[11px] text-emerald-800 font-medium flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    {extractMsg}
                  </p>
                )}
              </div>
            )}

            <form onSubmit={handleSaveGuideline} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Category *
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:outline-none focus:ring-2 focus:ring-forest-800"
                  >
                    {CATEGORIES.filter((c) => c !== 'All').map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Severity *
                  </label>
                  <select
                    value={formData.severity}
                    onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:outline-none focus:ring-2 focus:ring-forest-800"
                  >
                    {SEVERITIES.map((sev) => (
                      <option key={sev} value={sev}>
                        {sev}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Rule Title *
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g. Mandatory SOC2 Type II Certification Wording"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-forest-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Description / Rule Requirement *
                </label>
                <textarea
                  rows={4}
                  required
                  value={formData.rule_content}
                  onChange={(e) => setFormData({ ...formData, rule_content: e.target.value })}
                  placeholder="Explain the guideline rule, factual restrictions, or required positioning..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-forest-800"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Approved Wording / Facts (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={formData.approved_wording}
                    onChange={(e) => setFormData({ ...formData, approved_wording: e.target.value })}
                    placeholder="Exact phrasing or verified facts that can be quoted..."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-forest-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Prohibited Wording / Claims (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={formData.prohibited_wording}
                    onChange={(e) => setFormData({ ...formData, prohibited_wording: e.target.value })}
                    placeholder="Forbidden phrases, unverified guarantees, or misleading words..."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-forest-800"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Approved Reference / Evidence (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.reference_evidence}
                    onChange={(e) => setFormData({ ...formData, reference_evidence: e.target.value })}
                    placeholder="e.g. Brand Manual 2026 p.14, Audit Report #504"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-forest-800"
                  />
                </div>

                <div className="pt-4 flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-forest-800 border-slate-300 rounded focus:ring-forest-800 cursor-pointer"
                  />
                  <label htmlFor="is_active" className="text-xs font-semibold text-slate-800 cursor-pointer select-none">
                    Active Rule (Included in AI Compliance Analysis)
                  </label>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 disabled:opacity-50"
                >
                  {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{editingGuideline ? 'Save Changes' : 'Create Rule'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
};

export default GuidelinesPage;

