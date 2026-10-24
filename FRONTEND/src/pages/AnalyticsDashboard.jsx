import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Globe,
  Clock,
  RotateCcw,
  Layers,
  ShieldAlert,
  ShieldCheck,
  FileText,
  Filter,
  Calendar,
  Loader2,
  Info,
  Building2,
  Sparkles,
  ArrowUpRight
} from 'lucide-react';

const AnalyticsDashboard = () => {
  const { user, isAdmin } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  // Filters
  const [selectedBrand, setSelectedBrand] = useState(searchParams.get('brandId') || '');
  const [selectedDays, setSelectedDays] = useState(searchParams.get('days') || '');

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError('');
      const params = {};
      if (selectedBrand) params.brand_id = selectedBrand;
      if (selectedDays) params.days = selectedDays;

      const res = await api.get('/analytics', { params });
      if (res.data.success) {
        setData(res.data);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load governance analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [selectedBrand, selectedDays]);

  const handleBrandChange = (e) => {
    const val = e.target.value;
    setSelectedBrand(val);
    const newParams = new URLSearchParams(searchParams);
    if (val) newParams.set('brandId', val);
    else newParams.delete('brandId');
    setSearchParams(newParams);
  };

  const handleDaysChange = (val) => {
    setSelectedDays(val);
    const newParams = new URLSearchParams(searchParams);
    if (val) newParams.set('days', val);
    else newParams.delete('days');
    setSearchParams(newParams);
  };

  const metrics = data?.metrics || {
    total_submissions: 0,
    drafts_count: 0,
    pending_review_count: 0,
    changes_requested_count: 0,
    approved_count: 0,
    published_count: 0,
    avg_revisions_per_submission: 0.0,
    total_guidelines: 0,
    active_guidelines: 0,
    total_findings: 0
  };

  const severityDist = data?.severity_distribution || { Critical: 0, High: 0, Medium: 0, Low: 0 };
  const totalFindings = metrics.total_findings || 1;

  const maxCategoryCount = Math.max(
    ...(data?.category_distribution?.map((c) => c.count) || [1]),
    1
  );

  return (
    <DashboardLayout title="Governance Analytics">
      {/* Top Banner / Filter Toolbar */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6 shadow-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-forest-900 text-white flex items-center justify-center font-bold">
              <BarChart3 className="w-5 h-5 text-emerald-300" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Brand Governance & Compliance Analytics
              </h2>
              <p className="text-xs text-slate-500">
                Calculated strictly from live database records and audit logs.
              </p>
            </div>
          </div>

          {/* Filters: Brand & Timeframe */}
          <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
            {/* Brand Dropdown */}
            {data?.brands && data.brands.length > 0 && (
              <div className="relative">
                <select
                  value={selectedBrand}
                  onChange={handleBrandChange}
                  className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-forest-800"
                >
                  <option value="">All Accessible Brands</option>
                  {data.brands.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Timeframe Pills */}
            <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs font-medium">
              {[
                { label: 'All Time', val: '' },
                { label: '7 Days', val: '7' },
                { label: '30 Days', val: '30' },
                { label: '90 Days', val: '90' }
              ].map((pill) => (
                <button
                  key={pill.val}
                  type="button"
                  onClick={() => handleDaysChange(pill.val)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors ${
                    selectedDays === pill.val
                      ? 'bg-white text-forest-900 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {pill.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="py-24 flex flex-col items-center justify-center text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
          <p className="text-xs font-medium">Aggregating governance metrics from database...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Key Metric Highlights Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
            {/* Total Submissions */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Submissions</span>
                <FileText className="w-4 h-4 text-slate-400" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{metrics.total_submissions}</p>
              <p className="text-[10px] text-slate-400 mt-0.5">Recorded campaigns</p>
            </div>

            {/* Published */}
            <div className="bg-white border border-teal-200/80 rounded-xl p-4 shadow-2xs">
              <div className="flex items-center justify-between text-teal-600 mb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-teal-800">Published</span>
                <Globe className="w-4 h-4 text-teal-600" />
              </div>
              <p className="text-2xl font-bold text-teal-950">{metrics.published_count}</p>
              <p className="text-[10px] text-teal-700 mt-0.5">Live in-app archive</p>
            </div>

            {/* Approved */}
            <div className="bg-white border border-emerald-200/80 rounded-xl p-4 shadow-2xs">
              <div className="flex items-center justify-between text-emerald-600 mb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-800">Approved</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              </div>
              <p className="text-2xl font-bold text-emerald-950">{metrics.approved_count}</p>
              <p className="text-[10px] text-emerald-700 mt-0.5">Manager authorized</p>
            </div>

            {/* Pending Manager Approval */}
            <div className="bg-white border border-amber-200/80 rounded-xl p-4 shadow-2xs">
              <div className="flex items-center justify-between text-amber-600 mb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-800">Pending</span>
                <Clock className="w-4 h-4 text-amber-600" />
              </div>
              <p className="text-2xl font-bold text-amber-950">{metrics.pending_review_count}</p>
              <p className="text-[10px] text-amber-700 mt-0.5">Awaiting decision</p>
            </div>

            {/* Changes Requested */}
            <div className="bg-white border border-orange-200/80 rounded-xl p-4 shadow-2xs">
              <div className="flex items-center justify-between text-orange-600 mb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-orange-800">Revisions Req.</span>
                <RotateCcw className="w-4 h-4 text-orange-600" />
              </div>
              <p className="text-2xl font-bold text-orange-950">{metrics.changes_requested_count}</p>
              <p className="text-[10px] text-orange-700 mt-0.5">Returned to creator</p>
            </div>

            {/* Average Revisions / Submission */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">Avg. Revisions</span>
                <TrendingUp className="w-4 h-4 text-slate-400" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{metrics.avg_revisions_per_submission}</p>
              <p className="text-[10px] text-slate-400 mt-0.5">Per submission</p>
            </div>
          </div>

          {/* Active Guidelines & Rule Health Overview */}
          <div className="bg-forest-900 text-white rounded-xl p-5 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-emerald-300" />
              </div>
              <div>
                <h3 className="text-sm font-bold">Brand Guideline Coverage</h3>
                <p className="text-xs text-emerald-100/80">
                  {metrics.active_guidelines} active rules currently grounding Gemini compliance reviews.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="text-right">
                <span className="text-xs text-emerald-200 font-medium">Active Rules</span>
                <p className="text-lg font-bold">{metrics.active_guidelines} / {metrics.total_guidelines}</p>
              </div>
              <div className="text-right">
                <span className="text-xs text-emerald-200 font-medium">Flagged Issues</span>
                <p className="text-lg font-bold">{metrics.total_findings}</p>
              </div>
            </div>
          </div>

          {/* Middle Two-Column Grid: Flagged Categories & Severity Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Most Frequently Flagged Guideline Categories */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-forest-800" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Most Frequently Flagged Categories
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">By Issue Frequency</span>
              </div>

              {(!data?.category_distribution || data.category_distribution.length === 0) ? (
                <div className="py-12 text-center text-slate-400 text-xs">
                  No guideline violations recorded in the selected period.
                </div>
              ) : (
                <div className="space-y-3.5">
                  {data.category_distribution.map((cat, idx) => {
                    const percent = Math.round((cat.count / maxCategoryCount) * 100);
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between text-xs font-semibold">
                          <span className="text-slate-800">{cat.category}</span>
                          <span className="text-slate-500 font-mono">{cat.count} flags</span>
                        </div>
                        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-forest-800 h-full rounded-full transition-all duration-500"
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Severity Distribution */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-red-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Finding Severity Breakdown
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">Total: {metrics.total_findings}</span>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-5">
                <div className="p-3 bg-red-100/70 border border-red-200 rounded-xl">
                  <span className="text-[11px] font-bold text-red-900 uppercase tracking-wider block">
                    Critical Severity
                  </span>
                  <span className="text-2xl font-bold text-red-950 mt-1 block">
                    {severityDist.Critical || 0}
                  </span>
                  <span className="text-[10px] text-red-800">Severe policy breach</span>
                </div>

                <div className="p-3 bg-rose-50 border border-rose-100 rounded-xl">
                  <span className="text-[11px] font-bold text-rose-800 uppercase tracking-wider block">
                    High Severity
                  </span>
                  <span className="text-2xl font-bold text-rose-950 mt-1 block">
                    {severityDist.High || 0}
                  </span>
                  <span className="text-[10px] text-rose-700">Requires review exception</span>
                </div>

                <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl">
                  <span className="text-[11px] font-bold text-amber-800 uppercase tracking-wider block">
                    Medium Severity
                  </span>
                  <span className="text-2xl font-bold text-amber-950 mt-1 block">
                    {severityDist.Medium || 0}
                  </span>
                  <span className="text-[10px] text-amber-700">Tone & terminology issues</span>
                </div>

                <div className="p-3 bg-blue-50 border border-blue-100 rounded-xl">
                  <span className="text-[11px] font-bold text-blue-800 uppercase tracking-wider block">
                    Low Severity
                  </span>
                  <span className="text-2xl font-bold text-blue-950 mt-1 block">
                    {severityDist.Low || 0}
                  </span>
                  <span className="text-[10px] text-blue-700">Stylistic suggestions</span>
                </div>
              </div>

              {/* Severity Proportional Bar */}
              {metrics.total_findings > 0 && (
                <div>
                  <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden flex">
                    <div
                      style={{ width: `${((severityDist.Critical || 0) / totalFindings) * 100}%` }}
                      className="bg-red-800 h-full"
                      title={`Critical: ${severityDist.Critical || 0}`}
                    />
                    <div
                      style={{ width: `${((severityDist.High || 0) / totalFindings) * 100}%` }}
                      className="bg-rose-500 h-full"
                      title={`High: ${severityDist.High || 0}`}
                    />
                    <div
                      style={{ width: `${((severityDist.Medium || 0) / totalFindings) * 100}%` }}
                      className="bg-amber-500 h-full"
                      title={`Medium: ${severityDist.Medium || 0}`}
                    />
                    <div
                      style={{ width: `${((severityDist.Low || 0) / totalFindings) * 100}%` }}
                      className="bg-blue-400 h-full"
                      title={`Low: ${severityDist.Low || 0}`}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 font-mono">
                    <span>Critical / High</span>
                    <span>Medium / Low</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Lower Grid: Most Common Compliance Phrases & Review Outcomes */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Most Common Problematic Phrases Flagged */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Common Problematic Phrases Flagged
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">By Recurrence</span>
              </div>

              {(!data?.common_issues || data.common_issues.length === 0) ? (
                <div className="py-12 text-center text-slate-400 text-xs">
                  No recurring flagged phrases recorded.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {data.common_issues.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-50 border border-slate-100 rounded-lg flex items-center justify-between gap-3 text-xs"
                    >
                      <div className="space-y-0.5 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-200 text-slate-700">
                            {item.category}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {item.severity}
                          </span>
                        </div>
                        <p className="font-mono text-slate-800 text-[11px] truncate">
                          "{item.phrase}"
                        </p>
                      </div>
                      <span className="text-xs font-bold text-forest-900 bg-white px-2.5 py-1 rounded border border-slate-200 shrink-0">
                        {item.frequency}x
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Manager Review Outcomes & Submission Status Breakdown */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Manager Review Decisions
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">Recorded Outcomes</span>
              </div>

              {(!data?.review_outcomes || data.review_outcomes.length === 0) ? (
                <div className="py-12 text-center text-slate-400 text-xs">
                  No manager review decisions recorded yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {data.review_outcomes.map((ro, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-50 border border-slate-100 rounded-lg flex items-center justify-between"
                    >
                      <span className="text-xs font-bold text-slate-800">{ro.decision}</span>
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-white border border-slate-200 text-forest-900">
                        {ro.count} decision{ro.count !== 1 ? 's' : ''}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Submission Timeline Trends */}
              {data?.timeline_trends && data.timeline_trends.length > 0 && (
                <div className="mt-6 pt-4 border-t border-slate-100">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Recent Submission Activity
                  </h4>
                  <div className="flex items-end gap-1.5 h-16 pt-2">
                    {data.timeline_trends.map((t, idx) => {
                      const maxDaily = Math.max(...data.timeline_trends.map((x) => x.submissions), 1);
                      const heightPercent = Math.round((t.submissions / maxDaily) * 100);
                      return (
                        <div
                          key={idx}
                          className="flex-1 flex flex-col items-center justify-end h-full group relative"
                        >
                          <div
                            className="w-full bg-forest-800 hover:bg-forest-700 rounded-t transition-all"
                            style={{ height: `${Math.max(heightPercent, 12)}%` }}
                          />
                          <span className="text-[9px] text-slate-400 mt-1 font-mono truncate max-w-full">
                            {t.date.slice(5)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Governance Analytics Disclaimer Alert Box */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-3">
            <Info className="w-5 h-5 text-slate-500 shrink-0 mt-0.5" />
            <div className="space-y-1 leading-relaxed">
              <p className="font-semibold text-slate-800">
                Governance Analytical Integrity & Methodology Note
              </p>
              <p className="text-[11px]">
                {data?.governance_note ||
                  'All governance metrics, severity distributions, and category counts are dynamically computed from active database records. Historical trends and violation frequencies represent recorded compliance events and do not necessarily prove causation.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
};

export default AnalyticsDashboard;
