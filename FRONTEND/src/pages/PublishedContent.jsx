import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Globe,
  Search,
  Building2,
  Calendar,
  User,
  Copy,
  Check,
  ArrowRight,
  ShieldCheck,
  FileCheck2,
  Loader2,
  ExternalLink,
  Info,
  Filter
} from 'lucide-react';

const PublishedContent = () => {
  const { user, isAdmin } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  const fetchPublishedData = async () => {
    try {
      setLoading(true);
      setError('');
      const [subsRes, brandsRes] = await Promise.all([
        api.get('/submissions', { params: { status: 'Published' } }),
        api.get('/brands')
      ]);

      if (subsRes.data.success) {
        setSubmissions(subsRes.data.submissions);
      }
      if (brandsRes.data.success) {
        setBrands(brandsRes.data.brands);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load published content.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPublishedData();
  }, []);

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredSubmissions = submissions.filter((item) => {
    if (selectedBrand !== 'all' && item.brand_id !== parseInt(selectedBrand)) {
      return false;
    }
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const titleMatch = item.title?.toLowerCase().includes(q);
      const textMatch = item.content_text?.toLowerCase().includes(q);
      const brandMatch = item.brand_name?.toLowerCase().includes(q);
      const publisherMatch = item.published_by?.toLowerCase().includes(q);
      return titleMatch || textMatch || brandMatch || publisherMatch;
    }
    return true;
  });

  return (
    <DashboardLayout title="Published Content Directory">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-teal-50 text-teal-800 border border-teal-200 flex items-center gap-1.5">
                <Globe className="w-3 h-3 text-teal-600" />
                Live In-App Governance
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">
              Published Content Archive
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Inspect formally approved and published promotional campaigns. Content is archived under enterprise brand governance and permanently locked against edits.
            </p>
          </div>

          <div className="p-3 bg-teal-50/60 border border-teal-100 rounded-lg text-xs text-teal-900 max-w-sm">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
              <p className="text-[11px] leading-relaxed">
                <strong>In-App Publication:</strong> Status changes represent verified governance sign-off in this application. This is not connected to external social platforms.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by title, copy, or publisher..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-forest-800"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Building2 className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedBrand}
            onChange={(e) => setSelectedBrand(e.target.value)}
            className="w-full sm:w-auto px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-medium focus:outline-none focus:ring-2 focus:ring-forest-800 bg-white"
          >
            <option value="all">All Governed Brands</option>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Content */}
      {loading ? (
        <div className="py-20 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-forest-800 mx-auto mb-2" />
          <p className="text-xs text-slate-500 font-medium">Loading published promotional content...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 mb-6">
          {error}
        </div>
      ) : filteredSubmissions.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-16 text-center">
          <div className="w-12 h-12 rounded-full bg-teal-50 text-teal-700 mx-auto flex items-center justify-center mb-3">
            <Globe className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">No Published Content Found</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
            {searchTerm || selectedBrand !== 'all'
              ? 'No published campaigns match the selected filters.'
              : 'Once Brand Managers review and approve promotional content, approved campaigns can be officially published in-app.'}
          </p>
          <Link
            to="/creator/submissions"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-forest-900 text-white rounded-lg text-xs font-semibold hover:bg-forest-800 transition-colors"
          >
            <span>View Submissions Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredSubmissions.map((sub) => {
            const formattedDate = sub.published_at
              ? new Date(sub.published_at).toLocaleString()
              : sub.updated_at
                ? new Date(sub.updated_at).toLocaleString()
                : 'Recently Published';

            return (
              <div
                key={sub.id}
                className="bg-white border border-slate-200 hover:border-slate-300 rounded-xl p-5 shadow-xs flex flex-col justify-between transition-all"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <span className="text-[11px] font-bold text-forest-900 bg-forest-50 border border-forest-200 px-2.5 py-0.5 rounded-full truncate">
                      {sub.brand_name}
                    </span>
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 text-teal-800 border border-teal-200">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
                      Published
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 mb-2 leading-snug">
                    {sub.title}
                  </h3>

                  <div className="p-3 bg-slate-50/80 rounded-lg border border-slate-200/80 text-xs text-slate-800 leading-relaxed font-sans mb-3 line-clamp-4 whitespace-pre-line">
                    {sub.content_text}
                  </div>
                </div>

                <div>
                  {/* Metadata Strip */}
                  <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500 mb-3">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{formattedDate}</span>
                    </div>

                    <div className="flex items-center gap-1 font-medium">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span>Published by: <strong className="text-slate-800">{sub.published_by || sub.creator_name || 'Brand Manager'}</strong></span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-100">
                    <button
                      onClick={() => handleCopy(sub.id, sub.content_text)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
                    >
                      {copiedId === sub.id ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span className="text-emerald-700">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-slate-500" />
                          <span>Copy Text</span>
                        </>
                      )}
                    </button>

                    <Link
                      to={`/submissions/${sub.id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-forest-800 hover:text-forest-900 transition-colors"
                    >
                      <span>Compliance History</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </DashboardLayout>
  );
};

export default PublishedContent;
