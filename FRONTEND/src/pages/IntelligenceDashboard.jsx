import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  BarChart3, TrendingUp, AlertTriangle, AlertCircle, CheckCircle2,
  Globe, Clock, RotateCcw, ShieldAlert, ShieldCheck, FileText,
  Filter, Calendar, Loader2, Info, Building2, Sparkles, Eye,
  FileType, Accessibility, Lightbulb, Activity, Target, XCircle,
  HelpCircle, RefreshCw, Users, BookOpen, TrendingDown, Zap,
  ChevronDown, ChevronUp, Award, BarChart2,
} from 'lucide-react';

// ─── Mini helpers ─────────────────────────────────────────────────────────────
const pct = (n, total) => (total > 0 ? Math.round((n / total) * 100) : 0);

const SevBar = ({ label, count, total, colorCls }) => {
  const w = pct(count, total);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[11px] font-semibold">
        <span className="text-slate-700">{label}</span>
        <span className="font-mono text-slate-500">{count}</span>
      </div>
      <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${colorCls}`} style={{ width: `${w}%` }} />
      </div>
    </div>
  );
};

const MetricCard = ({ label, value, sub, icon: Icon, colorCls = 'border-slate-200', valueCls = 'text-slate-900' }) => (
  <div className={`bg-white border ${colorCls} rounded-xl p-4 shadow-sm`}>
    <div className="flex items-center justify-between mb-1">
      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
      {Icon && <Icon className="w-4 h-4 text-slate-300" />}
    </div>
    <p className={`text-2xl font-extrabold ${valueCls}`}>{value ?? '—'}</p>
    {sub && <p className="text-[10px] text-slate-400 mt-0.5">{sub}</p>}
  </div>
);

const InsightCard = ({ insight }) => {
  const cfg = {
    critical: { bg: 'bg-red-50 border-red-200', icon: XCircle, iconCls: 'text-red-500', badge: 'bg-red-100 text-red-800' },
    warning: { bg: 'bg-amber-50 border-amber-200', icon: AlertTriangle, iconCls: 'text-amber-500', badge: 'bg-amber-100 text-amber-800' },
    info: { bg: 'bg-sky-50 border-sky-200', icon: Lightbulb, iconCls: 'text-sky-500', badge: 'bg-sky-100 text-sky-800' },
  };
  const { bg, icon: Icon, iconCls, badge } = cfg[insight.type] || cfg.info;
  return (
    <div className={`rounded-xl border p-5 ${bg}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${iconCls}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <p className="text-sm font-bold text-slate-900">{insight.title}</p>
            {insight.metric != null && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${badge}`}>
                {insight.metric} {insight.metric_label}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-700 leading-relaxed mb-2">{insight.description}</p>
          <div className="flex items-start gap-2 p-2.5 bg-white/60 rounded-lg border border-white">
            <Target className="w-3.5 h-3.5 text-forest-700 shrink-0 mt-0.5" />
            <p className="text-[11px] text-slate-800 font-medium leading-relaxed">{insight.recommendation}</p>
          </div>
          <p className="text-[10px] text-slate-400 mt-1.5 italic">Evidence: {insight.evidence}</p>
        </div>
      </div>
    </div>
  );
};

const SourceBadge = ({ source }) => {
  const map = {
    'Text Compliance': 'bg-forest-50 text-forest-800 border-forest-200',
    'Visual Compliance': 'bg-indigo-50 text-indigo-700 border-indigo-200',
    'Document Review': 'bg-violet-50 text-violet-700 border-violet-200',
  };
  return (
    <span className={`inline-flex text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${map[source] || 'bg-slate-50 text-slate-600 border-slate-200'}`}>
      {source}
    </span>
  );
};

// ─── Mini bar chart ───────────────────────────────────────────────────────────
const TimelineChart = ({ data }) => {
  if (!data || data.length === 0) return null;
  const maxVal = Math.max(...data.map(d => d.total), 1);
  return (
    <div className="flex items-end gap-1 h-20">
      {data.map((d, i) => (
        <div key={i} className="flex-1 flex flex-col items-center justify-end h-full group relative" title={`${d.date}: ${d.total} reviews`}>
          <div className="w-full rounded-t overflow-hidden flex flex-col" style={{ height: `${Math.max(Math.round((d.total / maxVal) * 100), 8)}%` }}>
            <div className="flex-1 bg-forest-700 group-hover:bg-forest-600 transition-colors" />
          </div>
          <span className="text-[8px] text-slate-400 mt-1 font-mono truncate max-w-full hidden sm:block">{d.date?.slice(5)}</span>
        </div>
      ))}
    </div>
  );
};

// ─── Donut-style percent ring (pure CSS) ─────────────────────────────────────
const PctRing = ({ value, size = 64, stroke = 7, color = '#166534' }) => {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e2e8f0" strokeWidth={stroke} />
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={color} strokeWidth={stroke}
        strokeDasharray={c} strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.6s ease' }}
      />
    </svg>
  );
};

// ─── Signal badge for guideline effectiveness ─────────────────────────────────
const SignalBadge = ({ signal }) => {
  const cfg = {
    'High-Impact': 'bg-red-100 text-red-800 border-red-200',
    'Active': 'bg-emerald-100 text-emerald-800 border-emerald-200',
    'Low-Signal': 'bg-amber-100 text-amber-800 border-amber-200',
    'No-Signal': 'bg-slate-100 text-slate-600 border-slate-200',
  };
  return (
    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${cfg[signal] || cfg['No-Signal']}`}>
      {signal}
    </span>
  );
};

// ─── Creator row ──────────────────────────────────────────────────────────────
const CreatorRow = ({ creator, idx }) => {
  const rate = creator.compliance_rate;
  const rateColor = rate == null ? 'text-slate-400' : rate >= 75 ? 'text-emerald-700' : rate >= 50 ? 'text-amber-700' : 'text-red-700';
  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border ${creator.sufficient_data ? 'bg-white border-slate-100' : 'bg-slate-50/50 border-slate-100'}`}>
      <span className="text-[10px] font-mono text-slate-400 w-5 shrink-0">{idx + 1}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <p className="text-xs font-bold text-slate-900 truncate">{creator.creator_name}</p>
          {!creator.sufficient_data && (
            <span className="text-[9px] font-medium text-amber-600 bg-amber-50 border border-amber-200 rounded px-1">Low data</span>
          )}
        </div>
        <div className="flex items-center gap-2.5 mt-0.5">
          <span className="text-[10px] text-slate-500">{creator.total_submissions} submissions</span>
          {creator.top_violation_category && (
            <span className="text-[9px] font-mono text-slate-400 bg-slate-100 px-1 rounded">
              Top: {creator.top_violation_category}
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <div className="text-right">
          <p className={`text-sm font-extrabold ${rateColor}`}>
            {rate != null ? `${rate}%` : '—'}
          </p>
          <p className="text-[9px] text-slate-400">approval</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-bold text-slate-700">
            {creator.total_text_findings}
          </p>
          <p className="text-[9px] text-slate-400">findings</p>
        </div>
      </div>
    </div>
  );
};

// ─── Tab component ────────────────────────────────────────────────────────────
const Tab = ({ id, label, icon: Icon, active, onClick }) => (
  <button
    id={id}
    onClick={onClick}
    className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg transition-colors ${
      active
        ? 'bg-forest-900 text-white shadow-sm'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
    }`}
  >
    <Icon className="w-3.5 h-3.5" />
    {label}
  </button>
);

// ─── Main component ───────────────────────────────────────────────────────────
const IntelligenceDashboard = () => {
  const { isAdmin } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  // Creator insights state (admin only)
  const [creatorData, setCreatorData] = useState(null);
  const [creatorLoading, setCreatorLoading] = useState(false);
  const [creatorError, setCreatorError] = useState('');

  // Guideline effectiveness state (admin only)
  const [guidelineData, setGuidelineData] = useState(null);
  const [guidelineLoading, setGuidelineLoading] = useState(false);
  const [guidelineError, setGuidelineError] = useState('');

  const [selectedBrand, setSelectedBrand] = useState(searchParams.get('brandId') || '');
  const [selectedDays, setSelectedDays] = useState(searchParams.get('days') || '');

  const fetchIntelligence = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const params = {};
      if (selectedBrand) params.brand_id = selectedBrand;
      if (selectedDays) params.days = selectedDays;
      const res = await api.get('/analytics/intelligence', { params });
      if (res.data.success) setData(res.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to load intelligence dashboard.');
    } finally { setLoading(false); }
  }, [selectedBrand, selectedDays]);

  const fetchCreatorInsights = useCallback(async () => {
    if (!isAdmin) return;
    setCreatorLoading(true); setCreatorError('');
    try {
      const params = {};
      if (selectedBrand) params.brand_id = selectedBrand;
      if (selectedDays) params.days = selectedDays;
      const res = await api.get('/analytics/creator-insights', { params });
      if (res.data.success) setCreatorData(res.data);
    } catch (e) {
      setCreatorError(e.response?.data?.error || 'Failed to load creator insights.');
    } finally { setCreatorLoading(false); }
  }, [selectedBrand, selectedDays, isAdmin]);

  const fetchGuidelineEffectiveness = useCallback(async () => {
    if (!isAdmin) return;
    setGuidelineLoading(true); setGuidelineError('');
    try {
      const params = {};
      if (selectedBrand) params.brand_id = selectedBrand;
      if (selectedDays) params.days = selectedDays;
      const res = await api.get('/analytics/guideline-effectiveness', { params });
      if (res.data.success) setGuidelineData(res.data);
    } catch (e) {
      setGuidelineError(e.response?.data?.error || 'Failed to load guideline effectiveness.');
    } finally { setGuidelineLoading(false); }
  }, [selectedBrand, selectedDays, isAdmin]);

  useEffect(() => { fetchIntelligence(); }, [fetchIntelligence]);
  useEffect(() => {
    if (activeTab === 'creators') fetchCreatorInsights();
    if (activeTab === 'guidelines') fetchGuidelineEffectiveness();
  }, [activeTab, fetchCreatorInsights, fetchGuidelineEffectiveness]);

  const handleRefresh = () => {
    fetchIntelligence();
    if (activeTab === 'creators') fetchCreatorInsights();
    if (activeTab === 'guidelines') fetchGuidelineEffectiveness();
  };

  const handleBrandChange = e => {
    const v = e.target.value; setSelectedBrand(v);
    const p = new URLSearchParams(searchParams);
    v ? p.set('brandId', v) : p.delete('brandId');
    setSearchParams(p);
  };
  const handleDaysChange = v => {
    setSelectedDays(v);
    const p = new URLSearchParams(searchParams);
    v ? p.set('days', v) : p.delete('days');
    setSearchParams(p);
  };

  // Derived
  const rc = data?.review_counts || {};
  const sm = data?.submission_metrics || {};
  const vm = data?.visual_metrics || {};
  const dm = data?.document_metrics || {};
  const cs = data?.combined_severity || {};
  const gh = data?.guideline_health || {};
  const totalFindings = data?.total_findings || 0;
  const insights = data?.insights || [];
  const recurring = data?.recurring_issues || [];
  const timeline = data?.timeline_trends || [];
  const decisions = data?.decision_distribution || [];
  const brands = data?.brands || [];

  const visCompliantPct = vm.total > 0 ? pct(vm.compliant, vm.total) : null;

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'insights', label: 'Insights', icon: Sparkles },
    ...(isAdmin ? [
      { id: 'creators', label: 'Creator Breakdown', icon: Users },
      { id: 'guidelines', label: 'Guideline Health', icon: BookOpen },
    ] : []),
  ];

  return (
    <DashboardLayout title="Governance Intelligence">
      {/* Header toolbar */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-5 shadow-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-forest-900 to-indigo-800 flex items-center justify-center shadow-sm">
              <Sparkles className="w-5 h-5 text-emerald-300" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900">Brand Governance Intelligence</h1>
              <p className="text-xs text-slate-500">All metrics computed from live database records across all review types.</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {brands.length > 0 && (
              <select
                id="intel-brand-filter"
                value={selectedBrand}
                onChange={handleBrandChange}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-forest-800"
              >
                <option value="">All Accessible Brands</option>
                {brands.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            )}
            <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs font-medium">
              {[{ label: 'All Time', val: '' }, { label: '7d', val: '7' }, { label: '30d', val: '30' }, { label: '90d', val: '90' }].map(pill => (
                <button
                  key={pill.val}
                  id={`intel-days-${pill.val || 'all'}`}
                  onClick={() => handleDaysChange(pill.val)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors ${selectedDays === pill.val ? 'bg-white text-forest-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
                >
                  {pill.label}
                </button>
              ))}
            </div>
            <button onClick={handleRefresh} disabled={loading} className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-slate-800 transition-colors">
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex items-center gap-1 mb-5 p-1 bg-slate-100 rounded-xl border border-slate-200 w-fit">
        {tabs.map(t => (
          <Tab key={t.id} id={`intel-tab-${t.id}`} label={t.label} icon={t.icon} active={activeTab === t.id} onClick={() => setActiveTab(t.id)} />
        ))}
      </div>

      {error && (
        <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* ─── OVERVIEW TAB ────────────────────────────────────────────────────── */}
      {activeTab === 'overview' && (
        loading ? (
          <div className="py-24 flex flex-col items-center justify-center text-slate-500">
            <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
            <p className="text-xs font-medium">Aggregating intelligence from database…</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Row 1: Review-type totals */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
              <MetricCard label="Total Reviews" value={rc.total_reviews} sub="Across all review types" icon={Activity} />
              <MetricCard label="Text Analyses" value={rc.text_compliance_analyses} sub="Submission compliance" icon={FileText} colorCls="border-forest-200" valueCls="text-forest-900" />
              <MetricCard label="Visual Analyses" value={rc.visual_compliance_analyses} sub="Image compliance" icon={Eye} colorCls="border-indigo-200" valueCls="text-indigo-900" />
              <MetricCard label="Document Reviews" value={rc.document_reviews} sub="TXT / PDF / DOCX" icon={FileType} colorCls="border-violet-200" valueCls="text-violet-900" />
            </div>

            {/* Row 2: Submission workflow metrics */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
              <MetricCard label="Submissions" value={sm.total} sub="Total recorded" icon={FileText} />
              <MetricCard label="Approved" value={sm.approved} sub="Manager authorized" icon={CheckCircle2} colorCls="border-emerald-200" valueCls="text-emerald-900" />
              <MetricCard label="Published" value={sm.published} sub="Live content" icon={Globe} colorCls="border-teal-200" valueCls="text-teal-900" />
              <MetricCard label="Pending" value={sm.pending_approval} sub="Awaiting decision" icon={Clock} colorCls="border-amber-200" valueCls="text-amber-900" />
              <MetricCard label="Revisions Req." value={sm.changes_requested} sub="Returned to creator" icon={RotateCcw} colorCls="border-orange-200" valueCls="text-orange-900" />
              <MetricCard
                label="Avg Turnaround"
                value={sm.avg_turnaround_days != null ? `${sm.avg_turnaround_days}d` : '—'}
                sub="Submission to decision"
                icon={TrendingUp}
              />
            </div>

            {/* Row 3: Three-panel review health */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Text compliance */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                  <ShieldCheck className="w-4 h-4 text-forest-700" />
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Text Compliance</h3>
                </div>
                {rc.text_compliance_analyses === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">No text analyses in this period.</p>
                ) : (
                  <div className="space-y-3">
                    <SevBar label="Critical" count={cs.Critical || 0} total={totalFindings} colorCls="bg-purple-700" />
                    <SevBar label="High" count={(data?.combined_severity?.High || 0)} total={totalFindings} colorCls="bg-red-600" />
                    <SevBar label="Medium" count={cs.Medium || 0} total={totalFindings} colorCls="bg-amber-500" />
                    <SevBar label="Low" count={cs.Low || 0} total={totalFindings} colorCls="bg-sky-500" />
                    <p className="text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                      {rc.text_compliance_analyses} analyses · avg {sm.avg_revisions} revisions/submission
                    </p>
                  </div>
                )}
              </div>

              {/* Visual compliance */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                  <Eye className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Visual Compliance</h3>
                </div>
                {vm.total === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">No visual analyses in this period.</p>
                ) : (
                  <div className="space-y-3">
                    {visCompliantPct != null && (
                      <div className="flex items-center gap-4 mb-2">
                        <div className="relative shrink-0">
                          <PctRing value={visCompliantPct} color="#16a34a" />
                          <span className="absolute inset-0 flex items-center justify-center text-xs font-extrabold text-slate-800">
                            {visCompliantPct}%
                          </span>
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-800">Compliant Rate</p>
                          <p className="text-[11px] text-slate-500">{vm.compliant} of {vm.total} analyses</p>
                          {vm.avg_compliance_score != null && (
                            <p className="text-[11px] text-slate-500">Avg score: {vm.avg_compliance_score}/100</p>
                          )}
                        </div>
                      </div>
                    )}
                    {vm.category_distribution.slice(0, 4).map((c, i) => {
                      const maxV = Math.max(...vm.category_distribution.map(x => x.count), 1);
                      return (
                        <div key={i} className="space-y-0.5">
                          <div className="flex justify-between text-[11px]">
                            <span className="text-slate-700 font-medium">{c.category}</span>
                            <span className="font-mono text-slate-400">{c.count}</span>
                          </div>
                          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-600 rounded-full" style={{ width: `${pct(c.count, maxV)}%` }} />
                          </div>
                        </div>
                      );
                    })}
                    <p className="text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                      {vm.violations} violations · {vm.action_required} action required
                    </p>
                  </div>
                )}
              </div>

              {/* Document review */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                  <FileType className="w-4 h-4 text-violet-600" />
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Document Review</h3>
                </div>
                {dm.total === 0 ? (
                  <p className="text-xs text-slate-400 py-6 text-center">No document reviews in this period.</p>
                ) : (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 mb-2">
                      <div className="p-2.5 rounded-lg bg-forest-50 border border-forest-200 text-center">
                        <p className="text-lg font-extrabold text-forest-900">{dm.brand_compliance_findings}</p>
                        <p className="text-[10px] text-forest-700 font-semibold">Brand findings</p>
                      </div>
                      <div className="p-2.5 rounded-lg bg-indigo-50 border border-indigo-200 text-center">
                        <p className="text-lg font-extrabold text-indigo-900">{dm.accessibility_findings}</p>
                        <p className="text-[10px] text-indigo-700 font-semibold">Accessibility</p>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      {dm.format_distribution.map(f => (
                        <div key={f.format} className="flex items-center justify-between text-xs">
                          <span className="font-mono uppercase font-bold text-slate-600">{f.format}</span>
                          <span className="font-bold text-slate-800">{f.count} docs</span>
                        </div>
                      ))}
                    </div>
                    <p className="text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                      {dm.violations} violations · {dm.action_required} action required
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Row 4: Combined severity + guideline health */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Unified severity breakdown */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-5">
                  <ShieldAlert className="w-4 h-4 text-red-600" />
                  <h3 className="text-sm font-bold text-slate-900">Combined Finding Severity</h3>
                  <span className="ml-auto text-[11px] text-slate-400">All review types · no double-count</span>
                </div>
                {totalFindings === 0 ? (
                  <div className="py-10 text-center text-slate-400 text-xs">No findings in the selected period.</div>
                ) : (
                  <div className="space-y-4">
                    {[
                      { label: 'Critical', key: 'Critical', cls: 'bg-purple-700', tag: 'bg-purple-100 text-purple-800' },
                      { label: 'High', key: 'High', cls: 'bg-red-600', tag: 'bg-red-100 text-red-800' },
                      { label: 'Medium', key: 'Medium', cls: 'bg-amber-500', tag: 'bg-amber-100 text-amber-800' },
                      { label: 'Low', key: 'Low', cls: 'bg-sky-500', tag: 'bg-sky-100 text-sky-800' },
                      { label: 'Unable to Verify', key: 'Unable to Verify', cls: 'bg-slate-400', tag: 'bg-slate-100 text-slate-600' },
                    ].map(({ label, key, cls, tag }) => {
                      const count = cs[key] || 0;
                      return (
                        <div key={key} className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${tag}`}>{label}</span>
                            <span className="text-xs font-bold text-slate-800">{count} <span className="font-normal text-slate-400">({pct(count, totalFindings)}%)</span></span>
                          </div>
                          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${cls}`} style={{ width: `${pct(count, totalFindings)}%`, transition: 'width 0.5s ease' }} />
                          </div>
                        </div>
                      );
                    })}
                    <p className="text-[11px] text-slate-400 pt-1 border-t border-slate-100">
                      Total: {totalFindings} findings across text, visual, and document reviews.
                    </p>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                {/* Guideline health */}
                <div className="bg-forest-900 text-white rounded-xl p-5 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center">
                      <ShieldCheck className="w-5 h-5 text-emerald-300" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold">Brand Guideline Coverage</h3>
                      <p className="text-[11px] text-emerald-100/70">{gh.active} active rules grounding AI reviews</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: 'Total Rules', value: gh.total },
                      { label: 'Active', value: gh.active },
                      { label: 'Inactive', value: gh.inactive },
                    ].map(({ label, value }) => (
                      <div key={label} className="bg-white/10 rounded-lg p-2.5 text-center">
                        <p className="text-lg font-extrabold">{value}</p>
                        <p className="text-[10px] text-emerald-200">{label}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Manager decisions */}
                <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex-1">
                  <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Manager Decisions</h3>
                  </div>
                  {decisions.length === 0 ? (
                    <p className="text-xs text-slate-400 py-4 text-center">No manager decisions recorded.</p>
                  ) : (
                    <div className="space-y-2">
                      {decisions.map((d, i) => (
                        <div key={i} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                          <span className="text-xs font-semibold text-slate-800">{d.decision}</span>
                          <span className="text-xs font-bold font-mono text-forest-900 bg-white border border-slate-200 px-2 py-0.5 rounded">{d.count}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Row 5: Timeline + Recurring issues */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Unified timeline */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                  <Activity className="w-4 h-4 text-forest-700" />
                  <h3 className="text-sm font-bold text-slate-900">Review Activity Timeline</h3>
                  <span className="ml-auto text-[11px] text-slate-400">All review types combined</span>
                </div>
                {timeline.length === 0 ? (
                  <div className="py-10 text-center text-slate-400 text-xs">No activity in the selected period.</div>
                ) : (
                  <>
                    <TimelineChart data={timeline} />
                    <div className="flex gap-4 mt-3 pt-3 border-t border-slate-100">
                      <div className="flex items-center gap-1 text-[10px] text-slate-500"><span className="w-2.5 h-2.5 rounded-sm bg-forest-700 inline-block" /> Text</div>
                      <div className="flex items-center gap-1 text-[10px] text-slate-500"><span className="w-2.5 h-2.5 rounded-sm bg-indigo-600 inline-block" /> Visual</div>
                      <div className="flex items-center gap-1 text-[10px] text-slate-500"><span className="w-2.5 h-2.5 rounded-sm bg-violet-600 inline-block" /> Document</div>
                    </div>
                  </>
                )}
              </div>

              {/* Recurring issues */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  <h3 className="text-sm font-bold text-slate-900">Recurring Issues</h3>
                  <span className="ml-auto text-[11px] text-slate-400">Top across all sources</span>
                </div>
                {recurring.length === 0 ? (
                  <div className="py-10 text-center text-slate-400 text-xs">No recurring issues detected.</div>
                ) : (
                  <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                    {recurring.map((item, i) => (
                      <div key={i} className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
                        <div className="flex items-center gap-1.5 flex-wrap mb-1">
                          <SourceBadge source={item.source} />
                          <span className="text-[10px] font-mono text-slate-500 bg-white border border-slate-200 rounded px-1">{item.category}</span>
                          <span className={`text-[9px] font-bold rounded-full px-1.5 py-0.5 ${
                            item.severity === 'Critical' ? 'bg-purple-100 text-purple-800' :
                            item.severity === 'High' ? 'bg-red-100 text-red-800' :
                            item.severity === 'Medium' ? 'bg-amber-100 text-amber-800' :
                            'bg-sky-100 text-sky-700'
                          }`}>{item.severity}</span>
                          <span className="ml-auto text-xs font-bold text-forest-900 bg-white border border-slate-200 px-2 py-0.5 rounded">{item.frequency}×</span>
                        </div>
                        <p className="text-[11px] text-slate-700 font-mono truncate">"{item.text}"</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Methodology note */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-3">
              <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-slate-800 mb-0.5">Analytical Integrity & Methodology</p>
                <p className="text-[11px] leading-relaxed">{data?.methodology_note}</p>
              </div>
            </div>
          </div>
        )
      )}

      {/* ─── INSIGHTS TAB ────────────────────────────────────────────────────── */}
      {activeTab === 'insights' && (
        loading ? (
          <div className="py-24 flex flex-col items-center justify-center text-slate-500">
            <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
            <p className="text-xs font-medium">Computing insights…</p>
          </div>
        ) : (
          <div className="space-y-5">
            {insights.length > 0 ? (
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-5">
                  <Sparkles className="w-4 h-4 text-forest-700" />
                  <h3 className="text-sm font-bold text-slate-900">Actionable Insights</h3>
                  <span className="ml-auto text-[11px] text-slate-400">Based on observed patterns · no invented statistics</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {insights.map((ins, i) => <InsightCard key={i} insight={ins} />)}
                </div>
              </div>
            ) : (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-8 text-center">
                <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                <p className="text-sm font-bold text-emerald-900">No Actionable Insights at This Time</p>
                <p className="text-xs text-emerald-700 max-w-sm mx-auto mt-1">
                  Insufficient data to derive patterns. Continue submitting content and running compliance reviews to generate evidence-backed insights.
                </p>
              </div>
            )}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-3">
              <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-slate-800 mb-0.5">About These Insights</p>
                <p className="text-[11px] leading-relaxed">{data?.methodology_note}</p>
              </div>
            </div>
          </div>
        )
      )}

      {/* ─── CREATOR BREAKDOWN TAB ─────────────────────────────────────────── */}
      {activeTab === 'creators' && isAdmin && (
        <div className="space-y-5">
          {creatorError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" /> {creatorError}
            </div>
          )}
          {creatorLoading ? (
            <div className="py-24 flex flex-col items-center justify-center text-slate-500">
              <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
              <p className="text-xs font-medium">Loading creator insights…</p>
            </div>
          ) : (
            <>
              {/* Summary header */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-forest-900 to-indigo-800 flex items-center justify-center">
                    <Users className="w-4 h-4 text-emerald-300" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-900">Creator Compliance Breakdown</h2>
                    <p className="text-xs text-slate-500">
                      {creatorData?.total_creators ?? 0} creator{creatorData?.total_creators !== 1 ? 's' : ''} with submissions in scope
                    </p>
                  </div>
                  <button
                    onClick={fetchCreatorInsights}
                    disabled={creatorLoading}
                    className="ml-auto p-1.5 rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-slate-800 transition-colors"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${creatorLoading ? 'animate-spin' : ''}`} />
                  </button>
                </div>

                {(!creatorData || creatorData.creator_insights.length === 0) ? (
                  <div className="py-12 text-center text-slate-400">
                    <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-xs font-medium">No creator data in the selected period.</p>
                    <p className="text-[11px] mt-1">Try removing the date filter or brand filter to expand the scope.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {creatorData.creator_insights.map((creator, idx) => (
                      <CreatorRow key={creator.creator_id} creator={creator} idx={idx} />
                    ))}
                  </div>
                )}
              </div>

              {/* Methodology */}
              {creatorData?.methodology_note && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-3">
                  <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-slate-800 mb-0.5">Methodology & Limitations</p>
                    <p className="text-[11px] leading-relaxed">{creatorData.methodology_note}</p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ─── GUIDELINE HEALTH TAB ─────────────────────────────────────────── */}
      {activeTab === 'guidelines' && isAdmin && (
        <div className="space-y-5">
          {guidelineError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" /> {guidelineError}
            </div>
          )}
          {guidelineLoading ? (
            <div className="py-24 flex flex-col items-center justify-center text-slate-500">
              <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
              <p className="text-xs font-medium">Analysing guideline effectiveness…</p>
            </div>
          ) : (
            <>
              {/* Summary cards */}
              {guidelineData && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
                  <MetricCard
                    label="Active Guidelines"
                    value={guidelineData.summary.total}
                    sub="In scope"
                    icon={BookOpen}
                    colorCls="border-slate-200"
                  />
                  <MetricCard
                    label="High-Impact"
                    value={guidelineData.summary.high_impact}
                    sub="Cited in ≥50% of analyses"
                    icon={Zap}
                    colorCls="border-red-200"
                    valueCls="text-red-800"
                  />
                  <MetricCard
                    label="Low-Signal"
                    value={guidelineData.summary.low_signal}
                    sub="Rarely generates findings"
                    icon={TrendingDown}
                    colorCls="border-amber-200"
                    valueCls="text-amber-800"
                  />
                  <MetricCard
                    label="No-Signal"
                    value={guidelineData.summary.no_signal}
                    sub="Zero findings recorded"
                    icon={HelpCircle}
                    colorCls="border-slate-200"
                    valueCls="text-slate-500"
                  />
                </div>
              )}

              {/* Guideline table */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                  <BookOpen className="w-4 h-4 text-forest-700" />
                  <h2 className="text-sm font-bold text-slate-900">Guideline Effectiveness Table</h2>
                  <span className="ml-auto text-[11px] text-slate-400">
                    {guidelineData?.total_analyses_in_scope ?? 0} text analyses in scope
                  </span>
                  <button
                    onClick={fetchGuidelineEffectiveness}
                    disabled={guidelineLoading}
                    className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-500 hover:text-slate-800 transition-colors"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${guidelineLoading ? 'animate-spin' : ''}`} />
                  </button>
                </div>

                {(!guidelineData || guidelineData.guidelines.length === 0) ? (
                  <div className="py-12 text-center text-slate-400">
                    <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-xs font-medium">No active guidelines found in the selected scope.</p>
                    <p className="text-[11px] mt-1">Create brand guidelines to see effectiveness metrics here.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {guidelineData.guidelines.map((g, i) => {
                      const rateColor = g.violation_rate_pct == null ? '' :
                        g.violation_rate_pct >= 50 ? 'text-red-700' :
                        g.violation_rate_pct >= 20 ? 'text-amber-700' : 'text-emerald-700';
                      return (
                        <div key={g.guideline_id} className="p-3 bg-slate-50 border border-slate-100 rounded-xl hover:border-slate-200 transition-colors">
                          <div className="flex items-start gap-3">
                            <span className="text-[10px] font-mono text-slate-400 w-5 shrink-0 mt-0.5">{i + 1}</span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 flex-wrap mb-1">
                                <p className="text-xs font-bold text-slate-900">{g.title}</p>
                                <SignalBadge signal={g.signal} />
                                <span className={`text-[9px] font-bold rounded-full px-1.5 py-0.5 ${
                                  g.severity === 'Critical' ? 'bg-purple-100 text-purple-800' :
                                  g.severity === 'High' ? 'bg-red-100 text-red-800' :
                                  g.severity === 'Medium' ? 'bg-amber-100 text-amber-800' :
                                  'bg-sky-100 text-sky-700'
                                }`}>{g.severity}</span>
                              </div>
                              <p className="text-[10px] text-slate-500 font-mono mb-1.5">{g.category}</p>
                              <p className="text-[10px] text-slate-600 leading-relaxed line-clamp-2">{g.rule_content}</p>
                              {/* Violation rate bar */}
                              {g.violation_rate_pct != null && (
                                <div className="mt-2 space-y-0.5">
                                  <div className="flex justify-between text-[9px] text-slate-400">
                                    <span>Violation rate</span>
                                    <span className={`font-bold ${rateColor}`}>{g.violation_rate_pct}%</span>
                                  </div>
                                  <div className="h-1 bg-slate-200 rounded-full overflow-hidden">
                                    <div
                                      className={`h-full rounded-full ${g.violation_rate_pct >= 50 ? 'bg-red-500' : g.violation_rate_pct >= 20 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                                      style={{ width: `${g.violation_rate_pct}%` }}
                                    />
                                  </div>
                                </div>
                              )}
                            </div>
                            <div className="shrink-0 text-right">
                              <p className="text-sm font-extrabold text-slate-800">{g.total_findings}</p>
                              <p className="text-[9px] text-slate-400">findings</p>
                              <p className="text-xs font-bold text-slate-600 mt-0.5">{g.analyses_referencing}</p>
                              <p className="text-[9px] text-slate-400">analyses</p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Methodology */}
              {guidelineData?.methodology_note && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-3">
                  <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-slate-800 mb-0.5">Methodology & Limitations</p>
                    <p className="text-[11px] leading-relaxed">{guidelineData.methodology_note}</p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </DashboardLayout>
  );
};

export default IntelligenceDashboard;
