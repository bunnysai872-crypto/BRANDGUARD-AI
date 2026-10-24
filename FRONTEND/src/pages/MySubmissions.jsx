import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  FileText,
  Plus,
  Search,
  Filter,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ArrowRight,
  History,
  Building2,
  Loader2,
  AlertCircle
} from 'lucide-react';

const STATUS_FILTERS = [
  'All',
  'Draft',
  'Ready for AI Review',
  'AI Reviewed',
  'Changes Requested',
  'Pending Manager Approval',
  'Approved',
  'Published'
];

const MySubmissions = () => {
  const { user, isAdmin } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [selectedBrandId, setSelectedBrandId] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [brandsRes, subsRes] = await Promise.all([
        api.get('/brands'),
        api.get('/submissions'),
      ]);

      if (brandsRes.data.success) {
        setBrands(brandsRes.data.brands);
      }
      if (subsRes.data.success) {
        setSubmissions(subsRes.data.submissions);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch content submissions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Draft':
        return 'bg-slate-100 text-slate-700 border-slate-200';
      case 'Ready for AI Review':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'AI Reviewed':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'Changes Requested':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'Pending Manager Approval':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'Approved':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'Published':
        return 'bg-teal-50 text-teal-800 border-teal-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const filteredSubmissions = submissions.filter((sub) => {
    if (selectedBrandId && sub.brand_id !== parseInt(selectedBrandId)) return false;
    if (selectedStatus !== 'All' && sub.status !== selectedStatus) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        sub.title.toLowerCase().includes(q) ||
        sub.content_text.toLowerCase().includes(q) ||
        (sub.brand_name && sub.brand_name.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <DashboardLayout title={isAdmin ? 'Content Submissions Queue' : 'My Content Submissions'}>
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            {isAdmin ? 'Campaign Submissions' : 'Promotional Drafts & Submissions'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {isAdmin
              ? 'Review promotional drafts submitted across governed brand profiles.'
              : 'Track, edit, and inspect revision history for all your marketing drafts.'}
          </p>
        </div>

        <Link
          to="/creator/submissions/new"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4 text-emerald-300" />
          <span>New Content Draft</span>
        </Link>
      </div>

      {error && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Brand Filter */}
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-slate-400" />
            <select
              value={selectedBrandId}
              onChange={(e) => setSelectedBrandId(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-forest-800"
            >
              <option value="">All Brands</option>
              {brands.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-forest-800"
            >
              {STATUS_FILTERS.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Search */}
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search submissions..."
            className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-800"
          />
        </div>
      </div>

      {/* Submissions List */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
          <p className="text-xs font-medium">Loading submissions...</p>
        </div>
      ) : filteredSubmissions.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">No content submissions found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            {searchQuery || selectedBrandId || selectedStatus !== 'All'
              ? 'No drafts match the selected filter criteria.'
              : 'Create your first promotional content draft to start tracking brand governance.'}
          </p>
          <Link
            to="/creator/submissions/new"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create First Draft</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-3.5">
          {filteredSubmissions.map((sub) => (
            <div
              key={sub.id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:border-slate-300 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
            >
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-1.5">
                  <span className="text-xs font-bold text-forest-900 bg-forest-50 border border-forest-200 px-2.5 py-0.5 rounded-full">
                    {sub.brand_name || 'Brand'}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${getStatusBadge(
                      sub.status
                    )}`}
                  >
                    {sub.status}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    Rev #{sub.revision_count || 1}
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-900 truncate mb-1">
                  {sub.title}
                </h3>

                <p className="text-xs text-slate-500 line-clamp-1 mb-2">
                  {sub.content_text}
                </p>

                <div className="flex items-center gap-4 text-[11px] text-slate-400">
                  <span>Author: {sub.creator_name}</span>
                  <span>•</span>
                  <span>
                    Updated: {new Date(sub.updated_at || sub.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {/* Action Button */}
              <div className="flex items-center gap-2 w-full md:w-auto justify-end">
                <Link
                  to={`/submissions/${sub.id}`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-50 hover:bg-forest-900 hover:text-white text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold transition-all shadow-xs"
                >
                  <span>View Details</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
};

export default MySubmissions;
