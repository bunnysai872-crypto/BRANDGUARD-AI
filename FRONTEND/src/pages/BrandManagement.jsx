import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import api from '../services/api';
import {
  Building2,
  Plus,
  Users,
  BookOpen,
  FileText,
  Search,
  Edit2,
  Trash2,
  Check,
  X,
  Loader2,
  AlertCircle,
  Sparkles,
  UserPlus,
  ShieldAlert
} from 'lucide-react';
import { Link } from 'react-router-dom';

const BrandManagement = () => {
  const [brands, setBrands] = useState([]);
  const [creators, setCreators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingBrand, setEditingBrand] = useState(null);
  const [activeMemberBrand, setActiveMemberBrand] = useState(null);
  const [brandMembers, setBrandMembers] = useState([]);
  const [selectedCreatorId, setSelectedCreatorId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    tone_style: '',
    approved_terminology: '',
    restricted_words: '',
    approved_facts: '',
    prohibited_claims: '',
  });

  const fetchBrands = async () => {
    try {
      setLoading(true);
      const res = await api.get('/brands');
      if (res.data.success) {
        setBrands(res.data.brands);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load brands');
    } finally {
      setLoading(false);
    }
  };

  const fetchCreators = async () => {
    try {
      const res = await api.get('/brands/creators-list');
      if (res.data.success) {
        setCreators(res.data.creators);
      }
    } catch (err) {
      console.error('Failed to load creators list', err);
    }
  };

  useEffect(() => {
    fetchBrands();
    fetchCreators();
  }, []);

  const handleOpenCreate = () => {
    setEditingBrand(null);
    setFormData({
      name: '',
      description: '',
      tone_style: '',
      approved_terminology: '',
      restricted_words: '',
      approved_facts: '',
      prohibited_claims: '',
    });
    setShowCreateModal(true);
  };

  const handleOpenEdit = (brand) => {
    setEditingBrand(brand);
    setFormData({
      name: brand.name,
      description: brand.description || '',
      tone_style: brand.tone_style || '',
      approved_terminology: brand.approved_terminology || '',
      restricted_words: brand.restricted_words || '',
      approved_facts: brand.approved_facts || '',
      prohibited_claims: brand.prohibited_claims || '',
    });
    setShowCreateModal(true);
  };

  const handleSaveBrand = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (editingBrand) {
        const res = await api.put(`/brands/${editingBrand.id}`, formData);
        if (res.data.success) {
          setSuccessMsg(`Brand '${res.data.brand.name}' updated successfully.`);
          setShowCreateModal(false);
          fetchBrands();
        }
      } else {
        const res = await api.post('/brands', formData);
        if (res.data.success) {
          setSuccessMsg(`Brand '${res.data.brand.name}' created successfully.`);
          setShowCreateModal(false);
          fetchBrands();
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save brand profile');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenMembers = async (brand) => {
    setActiveMemberBrand(brand);
    setSelectedCreatorId('');
    try {
      const res = await api.get(`/brands/${brand.id}/members`);
      if (res.data.success) {
        setBrandMembers(res.data.members);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load brand members');
    }
  };

  const handleAddMember = async () => {
    if (!selectedCreatorId) return;
    try {
      const res = await api.post(`/brands/${activeMemberBrand.id}/members`, {
        user_id: selectedCreatorId,
        role: 'contributor',
      });
      if (res.data.success) {
        setSuccessMsg('Creator assigned to brand successfully.');
        setSelectedCreatorId('');
        handleOpenMembers(activeMemberBrand);
        fetchBrands();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to assign creator');
    }
  };

  const handleRemoveMember = async (memberUserId) => {
    try {
      const res = await api.delete(`/brands/${activeMemberBrand.id}/members/${memberUserId}`);
      if (res.data.success) {
        handleOpenMembers(activeMemberBrand);
        fetchBrands();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to remove member');
    }
  };

  return (
    <DashboardLayout title="Brand Management">
      {/* Top Header Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Brand Profiles & Governance</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Define communication tone, approved terminology, facts, and assign creators.
          </p>
        </div>

        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4 text-emerald-300" />
          <span>New Brand Profile</span>
        </button>
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

      {/* Brand Cards Grid */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
          <p className="text-xs font-medium">Loading brand profiles...</p>
        </div>
      ) : brands.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
          <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">No brand profiles established</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
            Create your first brand profile to set approved tone, terminology, facts, and rules.
          </p>
          <button
            onClick={handleOpenCreate}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create First Brand</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {brands.map((brand) => (
            <div
              key={brand.id}
              className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:border-slate-300 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2.5">
                    <div className="w-10 h-10 rounded-lg bg-forest-50 border border-forest-200 flex items-center justify-center text-forest-900 font-bold">
                      {brand.name[0].toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">{brand.name}</h3>
                      <p className="text-[11px] text-slate-400">Created by {brand.created_by}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleOpenEdit(brand)}
                    title="Edit Brand Profile"
                    className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                </div>

                <p className="text-xs text-slate-600 line-clamp-2 my-3">
                  {brand.description || 'No description provided.'}
                </p>

                {brand.tone_style && (
                  <div className="mb-4 p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                    <span className="font-semibold text-slate-700 block text-[11px] uppercase tracking-wider mb-0.5">
                      Tone & Style
                    </span>
                    <p className="text-slate-600 italic">"{brand.tone_style}"</p>
                  </div>
                )}

                {/* Counts Summary */}
                <div className="grid grid-cols-3 gap-2 py-3 border-y border-slate-100 text-center mb-4">
                  <div>
                    <span className="block text-sm font-bold text-slate-900">{brand.guidelines_count}</span>
                    <span className="text-[10px] text-slate-400 font-medium">Guidelines</span>
                  </div>
                  <div>
                    <span className="block text-sm font-bold text-slate-900">{brand.members_count}</span>
                    <span className="text-[10px] text-slate-400 font-medium">Creators</span>
                  </div>
                  <div>
                    <span className="block text-sm font-bold text-slate-900">{brand.submissions_count}</span>
                    <span className="text-[10px] text-slate-400 font-medium">Drafts</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-2">
                <Link
                  to={`/manager/guidelines?brandId=${brand.id}`}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold text-forest-900 bg-forest-50 hover:bg-forest-100 border border-forest-200 transition-colors"
                >
                  <BookOpen className="w-3.5 h-3.5 text-forest-700" />
                  <span>Guidelines</span>
                </Link>

                <button
                  onClick={() => handleOpenMembers(brand)}
                  className="inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-colors"
                >
                  <Users className="w-3.5 h-3.5 text-slate-600" />
                  <span>Members</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CREATE / EDIT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
              <h3 className="text-base font-bold text-slate-900">
                {editingBrand ? 'Edit Brand Profile' : 'Create Brand Profile'}
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveBrand} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Brand Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Acme Cloud Corp"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forest-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Summary of brand identity and market positioning"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forest-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Brand Tone & Communication Style
                </label>
                <input
                  type="text"
                  value={formData.tone_style}
                  onChange={(e) => setFormData({ ...formData, tone_style: e.target.value })}
                  placeholder="e.g. Authoritative, transparent, approachable, and evidence-driven"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forest-800"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-emerald-800 uppercase tracking-wider mb-1">
                    Approved Terminology
                  </label>
                  <textarea
                    rows={3}
                    value={formData.approved_terminology}
                    onChange={(e) => setFormData({ ...formData, approved_terminology: e.target.value })}
                    placeholder="Comma/newline separated: CloudFlow, Enterprise Grade, NextGen AI"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-forest-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-red-800 uppercase tracking-wider mb-1">
                    Restricted Words
                  </label>
                  <textarea
                    rows={3}
                    value={formData.restricted_words}
                    onChange={(e) => setFormData({ ...formData, restricted_words: e.target.value })}
                    placeholder="Comma/newline separated: Cheap, Guaranteed, Bulletproof, Zero-defect"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-forest-800"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Approved Facts & Data Points
                  </label>
                  <textarea
                    rows={3}
                    value={formData.approved_facts}
                    onChange={(e) => setFormData({ ...formData, approved_facts: e.target.value })}
                    placeholder="e.g. Founded in 2020. Over 100k active developers. 99.99% uptime."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-forest-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Prohibited Promotional Claims
                  </label>
                  <textarea
                    rows={3}
                    value={formData.prohibited_claims}
                    onChange={(e) => setFormData({ ...formData, prohibited_claims: e.target.value })}
                    placeholder="e.g. Never claim our system is immune to all attacks without human oversight."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-forest-800"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
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
                  <span>{editingBrand ? 'Save Changes' : 'Create Brand'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MANAGE MEMBERS MODAL */}
      {activeMemberBrand && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Brand Members</h3>
                <p className="text-xs text-slate-500">
                  Assign Creators who can draft content and access guidelines for <strong>{activeMemberBrand.name}</strong>.
                </p>
              </div>
              <button
                onClick={() => setActiveMemberBrand(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Add Creator Section */}
            <div className="flex items-center gap-2 mb-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
              <select
                value={selectedCreatorId}
                onChange={(e) => setSelectedCreatorId(e.target.value)}
                className="flex-1 px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-forest-800"
              >
                <option value="">Select a registered creator...</option>
                {creators.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.full_name || c.username} ({c.email})
                  </option>
                ))}
              </select>

              <button
                onClick={handleAddMember}
                disabled={!selectedCreatorId}
                className="inline-flex items-center gap-1.5 px-3 py-2 bg-forest-900 text-white rounded-lg text-xs font-semibold hover:bg-forest-800 disabled:opacity-40"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Assign</span>
              </button>
            </div>

            {/* Current Members List */}
            <div className="max-h-60 overflow-y-auto divide-y divide-slate-100">
              {brandMembers.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">No assigned creators yet.</p>
              ) : (
                brandMembers.map((m) => (
                  <div key={m.id} className="py-2.5 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-bold text-slate-800">{m.user_full_name || m.username}</p>
                      <p className="text-[11px] text-slate-400">{m.user_email}</p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 uppercase">
                        {m.membership_role}
                      </span>
                      {m.membership_role !== 'manager' && (
                        <button
                          onClick={() => handleRemoveMember(m.user_id)}
                          title="Remove from brand"
                          className="p-1 text-slate-400 hover:text-red-600 rounded transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="pt-4 border-t border-slate-100 mt-4 text-right">
              <button
                onClick={() => setActiveMemberBrand(null)}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
};

export default BrandManagement;
