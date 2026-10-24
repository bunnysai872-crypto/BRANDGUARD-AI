import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  Shield,
  Layers,
  Building2,
  Plus,
  Loader2
} from 'lucide-react';

const CreatorDashboard = () => {
  const { user } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [subsRes, brandsRes] = await Promise.all([
          api.get('/submissions'),
          api.get('/brands'),
        ]);
        if (subsRes.data.success) {
          setSubmissions(subsRes.data.submissions);
        }
        if (brandsRes.data.success) {
          setBrands(brandsRes.data.brands);
        }
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const draftsCount = submissions.filter((s) => s.status === 'Draft').length;
  const pendingCount = submissions.filter(
    (s) => s.status === 'Ready for AI Review' || s.status === 'Pending Manager Approval'
  ).length;
  const approvedCount = submissions.filter((s) => s.status === 'Approved' || s.status === 'Published').length;
  const changesCount = submissions.filter((s) => s.status === 'Changes Requested').length;

  const metrics = [
    {
      title: 'My Drafts',
      value: draftsCount.toString(),
      description: 'Drafts in progress',
      icon: FileText,
      color: 'text-slate-700',
      bg: 'bg-slate-100',
    },
    {
      title: 'Pending Reviews',
      value: pendingCount.toString(),
      description: 'Awaiting AI or manager review',
      icon: Clock,
      color: 'text-amber-700',
      bg: 'bg-amber-50',
    },
    {
      title: 'Approved Content',
      value: approvedCount.toString(),
      description: 'Signed off by manager',
      icon: CheckCircle2,
      color: 'text-emerald-700',
      bg: 'bg-emerald-50',
    },
    {
      title: 'Requiring Changes',
      value: changesCount.toString(),
      description: 'Revisions requested',
      icon: AlertTriangle,
      color: 'text-red-700',
      bg: 'bg-red-50',
    },
  ];

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

  return (
    <DashboardLayout title="Creator Dashboard">
      {/* Welcome Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-8 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                Phase 2 Active
              </span>
              <span className="text-xs text-slate-500 font-mono">Role: Content Creator</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">
              Welcome back, {user?.full_name || user?.username}!
            </h2>
            <p className="text-sm text-slate-600 mt-0.5">
              Draft promotional copy, track revisions, and align with approved brand guidelines.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/creator/submissions/new"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4 text-emerald-300" />
              <span>Create Content Draft</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {metrics.map((m) => {
          const Icon = m.icon;
          return (
            <div
              key={m.title}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:border-slate-300 transition-colors"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {m.title}
                </span>
                <div className={`w-8 h-8 rounded-lg ${m.bg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${m.color}`} />
                </div>
              </div>
              <p className="text-2xl font-bold text-slate-900">{m.value}</p>
              <p className="text-xs text-slate-500 mt-1">{m.description}</p>
            </div>
          );
        })}
      </div>

      {/* Content Pipeline & Session Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Submissions List */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Recent Content Submissions</h3>
              <p className="text-xs text-slate-500">Drafts stored in your database</p>
            </div>
            <Link
              to="/creator/submissions"
              className="text-xs font-semibold text-forest-700 hover:underline inline-flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="py-12 flex justify-center text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin text-forest-800" />
            </div>
          ) : submissions.length === 0 ? (
            <div className="py-12 text-center">
              <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center mb-3">
                <Layers className="w-6 h-6" />
              </div>
              <p className="text-sm font-semibold text-slate-800">No submissions created yet</p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                Draft marketing copy for assigned brands and manage versions.
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
            <div className="divide-y divide-slate-100">
              {submissions.slice(0, 5).map((sub) => (
                <div key={sub.id} className="py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-forest-50 text-forest-900 border border-forest-200">
                        {sub.brand_name}
                      </span>
                      <span
                        className={`text-[9px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${getStatusBadge(
                          sub.status
                        )}`}
                      >
                        {sub.status}
                      </span>
                    </div>
                    <p className="text-xs font-bold text-slate-900 truncate">{sub.title}</p>
                    <p className="text-[11px] text-slate-400">
                      Rev #{sub.revision_count || 1} •{' '}
                      {new Date(sub.updated_at || sub.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <Link
                    to={`/submissions/${sub.id}`}
                    className="p-1.5 text-slate-400 hover:text-forest-900 rounded-lg hover:bg-slate-50"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Assigned Brands & Security Info */}
        <div className="space-y-6">
          {/* Accessible Brands Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-forest-700" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Accessible Brands ({brands.length})
                </h3>
              </div>
              <Link
                to="/creator/guidelines"
                className="text-[11px] font-semibold text-forest-700 hover:underline"
              >
                Guidelines
              </Link>
            </div>

            {brands.length === 0 ? (
              <p className="text-xs text-slate-400 py-3 text-center">
                No assigned brands. Ask a Brand Manager to assign you.
              </p>
            ) : (
              <div className="space-y-2">
                {brands.map((b) => (
                  <div
                    key={b.id}
                    className="p-2.5 rounded-lg border border-slate-100 bg-slate-50 flex items-center justify-between"
                  >
                    <div>
                      <p className="text-xs font-bold text-slate-800">{b.name}</p>
                      <p className="text-[10px] text-slate-400">
                        {b.guidelines_count} guidelines active
                      </p>
                    </div>
                    <Link
                      to={`/creator/guidelines?brandId=${b.id}`}
                      className="text-[11px] font-semibold text-forest-700 hover:text-forest-900"
                    >
                      View Rules →
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* System & Session Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3 mb-3">
              <Shield className="w-4 h-4 text-forest-700" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Security & Session
              </h3>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Creator:</span>
                <span className="font-semibold text-slate-700">{user?.full_name || user?.username}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Role:</span>
                <span className="text-emerald-700 font-semibold uppercase">Content Creator</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Database:</span>
                <span className="text-slate-700 font-mono">SQLite (Local)</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Governance:</span>
                <span className="font-semibold text-forest-800">Phase 2 Active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default CreatorDashboard;
