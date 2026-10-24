import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  CheckSquare,
  Clock,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Building2,
  User,
  Search,
  Filter,
  ArrowRight,
  Loader2,
  FileText,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  RefreshCw
} from 'lucide-react';

const ApprovalQueue = () => {
  const { user } = useAuth();
  const [queue, setQueue] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('Pending Manager Approval');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchQueue = async () => {
    try {
      setLoading(true);
      setError('');

      const params = {};
      if (selectedBrand !== 'all') params.brand_id = selectedBrand;
      if (selectedStatus !== 'all') params.status = selectedStatus;

      const [queueRes, brandsRes] = await Promise.all([
        api.get('/submissions/queue', { params }),
        api.get('/brands')
      ]);

      if (queueRes.data.success) {
        setQueue(queueRes.data.queue);
      }
      if (brandsRes.data.success) {
        setBrands(brandsRes.data.brands);
      }
    } catch (err) {
      console.error('Failed to load approval queue:', err);
      setError(err.response?.data?.error || 'Failed to load manager approval queue.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [selectedBrand, selectedStatus]);

  // Client-side search filtering
  const filteredQueue = queue.filter((item) => {
    const term = searchTerm.toLowerCase();
    const titleMatch = item.title?.toLowerCase().includes(term);
    const brandMatch = item.brand_name?.toLowerCase().includes(term);
    const creatorMatch = item.creator_name?.toLowerCase().includes(term);
    return titleMatch || brandMatch || creatorMatch;
  });

  const pendingCount = queue.filter(
    (q) => q.status === 'Pending Manager Approval'
  ).length;
  const approvedCount = queue.filter((q) => q.status === 'Approved').length;
  const publishedCount = queue.filter((q) => q.status === 'Published').length;
  const changesCount = queue.filter((q) => q.status === 'Changes Requested').length;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Pending Manager Approval':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
            Pending Approval
          </span>
        );
      case 'Approved':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Approved
          </span>
        );
      case 'Published':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-50 text-teal-800 border border-teal-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
            Published
          </span>
        );
      case 'Changes Requested':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-orange-50 text-orange-800 border border-orange-200">
            <AlertTriangle className="w-3.5 h-3.5 text-orange-600" />
            Changes Requested
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  const getAiBadge = (item) => {
    if (!item.latest_analysis) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-600">
          No AI Audit
        </span>
      );
    }

    const { review_status, high_severity_count, issues_count, is_outdated } = item.latest_analysis;

    if (is_outdated) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-100 text-amber-900 border border-amber-200">
          <Clock className="w-3 h-3 text-amber-600" />
          Outdated Report
        </span>
      );
    }

    if (review_status === 'Compliant') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          AI Compliant
        </span>
      );
    }

    if (high_severity_count > 0) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-red-50 text-red-700 border border-red-200">
          <ShieldAlert className="w-3 h-3 text-red-600" />
          {high_severity_count} High Risk Flag{high_severity_count > 1 ? 's' : ''}
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
        <AlertCircle className="w-3 h-3 text-amber-600" />
        {issues_count} AI Warning{issues_count > 1 ? 's' : ''}
      </span>
    );
  };

  return (
    <DashboardLayout title="Manager Approval Queue & Review Governance">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-forest-50 text-forest-800 border border-forest-200">
                Phase 4 Workflow
              </span>
              <span className="text-xs text-slate-400">Brand Governance & Final Sign-Off</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">
              Content Review & Decision Queue
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Review creator submissions with AI evidence reports, sign off approvals, or return copies with actionable revision directives.
            </p>
          </div>

          <button
            onClick={fetchQueue}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold transition-colors self-start md:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
            <span>Refresh Queue</span>
          </button>
        </div>

        {/* Status Counters Strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-5 pt-5 border-t border-slate-100">
          <div
            onClick={() => setSelectedStatus('Pending Manager Approval')}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedStatus === 'Pending Manager Approval'
                ? 'bg-amber-50/70 border-amber-300 ring-1 ring-amber-300'
                : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <span className="text-[11px] font-semibold text-amber-800 uppercase tracking-wider block">
              Pending Sign-Off
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-xl font-bold text-amber-950">{pendingCount}</span>
              <span className="text-xs text-amber-700">Awaiting manager decision</span>
            </div>
          </div>

          <div
            onClick={() => setSelectedStatus('Approved')}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedStatus === 'Approved'
                ? 'bg-emerald-50/70 border-emerald-300 ring-1 ring-emerald-300'
                : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <span className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider block">
              Approved
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-xl font-bold text-emerald-950">{approvedCount}</span>
              <span className="text-xs text-emerald-700">Signed off for publishing</span>
            </div>
          </div>

          <div
            onClick={() => setSelectedStatus('Published')}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedStatus === 'Published'
                ? 'bg-teal-50/70 border-teal-300 ring-1 ring-teal-300'
                : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <span className="text-[11px] font-semibold text-teal-800 uppercase tracking-wider block">
              Published
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-xl font-bold text-teal-950">{publishedCount}</span>
              <span className="text-xs text-teal-700">Live in-app</span>
            </div>
          </div>

          <div
            onClick={() => setSelectedStatus('Changes Requested')}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedStatus === 'Changes Requested'
                ? 'bg-orange-50/70 border-orange-300 ring-1 ring-orange-300'
                : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <span className="text-[11px] font-semibold text-orange-800 uppercase tracking-wider block">
              Changes Requested
            </span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-xl font-bold text-orange-950">{changesCount}</span>
              <span className="text-xs text-orange-700">Returned to creator</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by title, brand, or creator..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-forest-800"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {/* Brand Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-600 w-1/2 sm:w-auto">
            <Building2 className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs font-medium focus:outline-none focus:ring-2 focus:ring-forest-800 bg-white"
            >
              <option value="all">All Governed Brands</option>
              {brands.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-600 w-1/2 sm:w-auto">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs font-medium focus:outline-none focus:ring-2 focus:ring-forest-800 bg-white"
            >
              <option value="all">All Review Statuses</option>
              <option value="Pending Manager Approval">Pending Manager Approval</option>
              <option value="Approved">Approved</option>
              <option value="Published">Published</option>
              <option value="Changes Requested">Changes Requested</option>
            </select>
          </div>
        </div>
      </div>

      {/* Queue Content */}
      {loading ? (
        <div className="p-16 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-forest-800 mx-auto mb-3" />
          <p className="text-xs font-medium text-slate-500">Loading manager approval queue...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      ) : filteredQueue.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
          <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center mx-auto mb-3">
            <CheckSquare className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">
            {selectedStatus === 'Pending Manager Approval'
              ? 'No Submissions Pending Manager Approval'
              : 'No Submissions Found'}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            {selectedStatus === 'Pending Manager Approval'
              ? 'All creator content has been reviewed, or creators have not yet submitted drafts for sign-off.'
              : 'No content submissions match your current brand and status filter criteria.'}
          </p>
          {selectedStatus !== 'all' && (
            <button
              onClick={() => setSelectedStatus('all')}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
            >
              View All Submissions
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredQueue.map((item) => (
            <div
              key={item.id}
              className="bg-white border border-slate-200 hover:border-forest-300 rounded-xl p-5 shadow-xs hover:shadow-sm transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              {/* Left Column: Info */}
              <div className="space-y-2 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  {getStatusBadge(item.status)}
                  {getAiBadge(item)}
                  <span className="text-[11px] px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-700">
                    Rev #{item.current_revision || 1}
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded font-semibold bg-forest-50 text-forest-800 border border-forest-100 flex items-center gap-1">
                    <Building2 className="w-3 h-3" />
                    {item.brand_name}
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-900 hover:text-forest-900 transition-colors">
                  <Link to={`/submissions/${item.id}`}>{item.title}</Link>
                </h3>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <User className="w-3.5 h-3.5 text-slate-400" />
                    Author: <strong className="text-slate-700">{item.creator_name}</strong>
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    Submitted: {new Date(item.updated_at || item.created_at).toLocaleDateString()}
                  </span>
                  {item.latest_analysis?.summary && (
                    <span className="text-slate-500 truncate max-w-md italic">
                      "{item.latest_analysis.summary}"
                    </span>
                  )}
                </div>
              </div>

              {/* Right Column: Review Action Button */}
              <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                <Link
                  to={`/submissions/${item.id}`}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 transition-colors shadow-xs"
                >
                  <span>Review & Decide</span>
                  <ArrowRight className="w-3.5 h-3.5 text-emerald-300" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
};

export default ApprovalQueue;
