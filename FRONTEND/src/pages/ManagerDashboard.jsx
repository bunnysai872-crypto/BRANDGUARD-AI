import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  BookOpen,
  CheckSquare,
  History,
  FileCheck2,
  Shield,
  Layers,
  Sparkles,
  Building2,
  Plus,
  ArrowRight,
  Users,
  Loader2
} from 'lucide-react';

const ManagerDashboard = () => {
  const { user } = useAuth();
  const [brands, setBrands] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
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
        console.error('Failed to load manager dashboard data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalGuidelines = brands.reduce((acc, b) => acc + (b.guidelines_count || 0), 0);
  const pendingApprovals = submissions.filter(
    (s) => s.status === 'Pending Manager Approval'
  ).length;

  const metrics = [
    {
      title: 'Governed Brands',
      value: brands.length.toString(),
      description: 'Active brand profiles',
      icon: Building2,
      color: 'text-forest-700',
      bg: 'bg-forest-50',
    },
    {
      title: 'Brand Guidelines',
      value: totalGuidelines.toString(),
      description: 'Total compliance rules',
      icon: BookOpen,
      color: 'text-blue-700',
      bg: 'bg-blue-50',
    },
    {
      title: 'Pending Approvals',
      value: pendingApprovals.toString(),
      description: 'Awaiting your sign-off',
      icon: CheckSquare,
      color: 'text-amber-700',
      bg: 'bg-amber-50',
      to: '/manager/approvals',
    },
    {
      title: 'Total Submissions',
      value: submissions.length.toString(),
      description: 'Recorded campaigns',
      icon: FileCheck2,
      color: 'text-slate-700',
      bg: 'bg-slate-100',
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
    <DashboardLayout title="Brand Governance Dashboard">
      {/* Welcome Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-8 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-900">
                Phase 2 Active
              </span>
              <span className="text-xs text-slate-500 font-mono">Role: Brand Manager / Admin</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">
              Welcome, {user?.full_name || user?.username}!
            </h2>
            <p className="text-sm text-slate-600 mt-0.5">
              Establish brand profiles, define tone and restricted claims, assign creators, and monitor submissions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/manager/approvals"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 transition-colors shadow-sm"
            >
              <CheckSquare className="w-4 h-4 text-amber-200" />
              <span>Review Approvals ({pendingApprovals})</span>
            </Link>

            <Link
              to="/manager/brands"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 transition-colors shadow-sm"
            >
              <Building2 className="w-4 h-4 text-emerald-300" />
              <span>Manage Brands</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {metrics.map((m) => {
          const Icon = m.icon;
          const CardContent = (
            <div
              className={`bg-white border rounded-xl p-5 shadow-sm transition-all h-full ${
                m.to ? 'hover:border-forest-400 hover:shadow-md cursor-pointer border-slate-200' : 'border-slate-200'
              }`}
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

          return m.to ? (
            <Link key={m.title} to={m.to}>
              {CardContent}
            </Link>
          ) : (
            <div key={m.title}>{CardContent}</div>
          );
        })}
      </div>

      {/* Main Grid: Governed Brands & Submissions Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Governed Brands List (2 cols) */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Governed Brand Profiles</h3>
              <p className="text-xs text-slate-500">Established brand rulebooks and assigned teams</p>
            </div>
            <Link
              to="/manager/brands"
              className="text-xs font-semibold text-forest-700 hover:underline inline-flex items-center gap-1"
            >
              <span>Manage all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="py-12 flex justify-center text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin text-forest-800" />
            </div>
          ) : brands.length === 0 ? (
            <div className="py-12 text-center">
              <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center mb-3">
                <Building2 className="w-6 h-6" />
              </div>
              <p className="text-sm font-semibold text-slate-800">No brand profiles established</p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                Create brand profiles to establish tone, approved terminology, and compliance rules.
              </p>
              <Link
                to="/manager/brands"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 shadow-sm"
              >
                <Plus className="w-4 h-4" />
                <span>Create Brand Profile</span>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {brands.map((b) => (
                <div
                  key={b.id}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
                >
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{b.name}</h4>
                    <p className="text-xs text-slate-500 line-clamp-1">
                      {b.description || 'No description entered'}
                    </p>
                    <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono mt-1.5">
                      <span>{b.guidelines_count} guidelines</span>
                      <span>•</span>
                      <span>{b.members_count} creators</span>
                      <span>•</span>
                      <span>{b.submissions_count} submissions</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Link
                      to={`/manager/guidelines?brandId=${b.id}`}
                      className="px-3 py-1.5 bg-white border border-slate-200 hover:border-forest-700 text-slate-700 text-xs font-semibold rounded-lg shadow-xs transition-colors"
                    >
                      Guidelines
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar: Recent Submissions & Governance Privileges */}
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Recent Submissions ({submissions.length})
              </h3>
              <Link
                to="/creator/submissions"
                className="text-[11px] font-semibold text-forest-700 hover:underline"
              >
                View all
              </Link>
            </div>

            {submissions.length === 0 ? (
              <p className="text-xs text-slate-400 py-3 text-center">
                No submissions received yet.
              </p>
            ) : (
              <div className="space-y-2.5">
                {submissions.slice(0, 4).map((sub) => (
                  <Link
                    key={sub.id}
                    to={`/submissions/${sub.id}`}
                    className="p-2.5 rounded-lg border border-slate-100 bg-slate-50/70 hover:border-slate-300 block transition-colors"
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-[10px] font-bold text-forest-900 truncate">
                        {sub.brand_name}
                      </span>
                      <span
                        className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border uppercase ${getStatusBadge(
                          sub.status
                        )}`}
                      >
                        {sub.status}
                      </span>
                    </div>
                    <p className="text-xs font-bold text-slate-800 truncate">{sub.title}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">By {sub.creator_name}</p>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Admin Governance Status */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3 mb-3">
              <Shield className="w-4 h-4 text-forest-700" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Governance Access
              </h3>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Manager:</span>
                <span className="font-semibold text-slate-800">{user?.full_name || user?.username}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Privileges:</span>
                <span className="text-amber-700 font-semibold uppercase">Admin / Manager</span>
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

export default ManagerDashboard;
