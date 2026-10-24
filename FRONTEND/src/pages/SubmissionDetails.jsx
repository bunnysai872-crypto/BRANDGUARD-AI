import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  ArrowLeft,
  Edit3,
  Clock,
  History,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Loader2,
  FileText,
  Building2,
  User,
  Sparkles,
  Save,
  X,
  Check,
  Eye,
  RefreshCw,
  Copy,
  ShieldCheck,
  ShieldAlert,
  Info,
  ExternalLink,
  Send,
  Lock,
  MessageSquare,
  ThumbsUp,
  RotateCcw,
  CheckCheck,
  Globe
} from 'lucide-react';

const SubmissionDetails = () => {
  const { id } = useParams();
  const { user, isAdmin } = useAuth();

  const [submission, setSubmission] = useState(null);
  const [revisions, setRevisions] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // AI Compliance Analysis State
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Edit Draft Modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editReason, setEditReason] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Historical Revision Preview Modal
  const [previewRevision, setPreviewRevision] = useState(null);

  // Phase 4: Creator Approval Submission State & Modal
  const [submittingApproval, setSubmittingApproval] = useState(false);
  const [showCreatorAckModal, setShowCreatorAckModal] = useState(false);
  const [creatorAckChecked, setCreatorAckChecked] = useState(false);

  // Phase 4: Manager Review Action State
  const [reviewComments, setReviewComments] = useState('');
  const [managerAckChecked, setManagerAckChecked] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewActionError, setReviewActionError] = useState('');

  // Publishing Workflow State & Modal
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [publishError, setPublishError] = useState('');

  const fetchSubmissionDetails = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/submissions/${id}`);
      if (res.data.success) {
        setSubmission(res.data.submission);
        setRevisions(res.data.submission.revisions || []);
        setDecisions(res.data.submission.decisions || []);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load submission details');
    } finally {
      setLoading(false);
    }
  };

  const fetchLatestAnalysis = async () => {
    try {
      const res = await api.get(`/submissions/${id}/analysis`);
      if (res.data.success) {
        setAnalysis(res.data.analysis);
      }
    } catch (err) {
      if (err.response?.status !== 404) {
        console.error('Error fetching analysis:', err);
      }
    }
  };

  useEffect(() => {
    fetchSubmissionDetails();
    fetchLatestAnalysis();
  }, [id]);

  const handleRunAICompliance = async () => {
    setAnalyzing(true);
    setAnalysisError('');
    setError('');
    try {
      const res = await api.post(`/submissions/${id}/analyze`);
      if (res.data.success) {
        setAnalysis(res.data.analysis);
        setSuccessMsg('AI Compliance analysis completed successfully.');
        setSubmission((prev) => ({ ...prev, status: 'AI Reviewed' }));
      }
    } catch (err) {
      const msg = err.response?.data?.error || err.message || 'AI compliance check failed.';
      setAnalysisError(msg);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleOpenEdit = () => {
    if (!submission) return;
    if (
      submission.status === 'Pending Manager Approval' ||
      submission.status === 'Approved' ||
      submission.status === 'Published'
    ) {
      return;
    }
    setEditTitle(submission.title);
    setEditContent(submission.content_text);
    setEditReason('');
    setEditStatus(submission.status);
    setShowEditModal(true);
  };

  const handlePublish = async () => {
    try {
      setPublishing(true);
      setPublishError('');
      setError('');

      const res = await api.post(`/submissions/${id}/publish`);
      if (res.data.success) {
        setSuccessMsg('Submission published successfully! Content is now live in-app.');
        setShowPublishModal(false);
        await fetchSubmissionDetails();
      }
    } catch (err) {
      setPublishError(err.response?.data?.error || 'Failed to publish submission.');
    } finally {
      setPublishing(false);
    }
  };


  const handleSaveEdit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setSubmitting(true);

    try {
      const res = await api.put(`/submissions/${id}`, {
        title: editTitle.trim(),
        content_text: editContent.trim(),
        reason: editReason.trim() || 'Content updated',
      });

      if (res.data.success) {
        setSuccessMsg(
          'Submission updated and new revision recorded. Prior AI reports marked outdated.'
        );
        setShowEditModal(false);

        await fetchSubmissionDetails();
        await fetchLatestAnalysis();
      }
    } catch (err) {
      setError(
        err.response?.data?.error || 'Failed to update submission'
      );
    } finally {
      setSubmitting(false);
    }
  };


  // Phase 4: Creator Submit for Manager Approval
  const handleSubmitApprovalClick = () => {
    if (!analysis || analysis.is_outdated) {
      setError('Please run an up-to-date AI Compliance Check before submitting for manager approval.');
      return;
    }

    const hasHighIssues =
      (analysis.critical_severity_count || 0) > 0 ||
      (analysis.high_severity_count || 0) > 0;
    const hasHumanVerification = analysis.findings?.some((f) => f.human_verification_required);

    if (hasHighIssues || hasHumanVerification) {
      setCreatorAckChecked(false);
      setShowCreatorAckModal(true);
      return;
    }

    executeSubmitApproval(false);
  };

  const executeSubmitApproval = async (acknowledged) => {
    try {
      setSubmittingApproval(true);
      setError('');
      setShowCreatorAckModal(false);

      const res = await api.post(`/submissions/${id}/submit-approval`, {
        acknowledgement: acknowledged,
      });

      if (res.data.success) {
        setSuccessMsg('Submission successfully submitted for Manager Approval!');
        await fetchSubmissionDetails();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit for manager approval.');
    } finally {
      setSubmittingApproval(false);
    }
  };

  // Phase 4: Manager Decision Review
  const handleManagerDecision = async (decision) => {
    setReviewActionError('');
    if (!reviewComments.trim()) {
      setReviewActionError('Review comments are required to record your decision rationale.');
      return;
    }

    const hasHighFlags =
      (analysis?.critical_severity_count || 0) > 0 ||
      (analysis?.high_severity_count || 0) > 0;
    const hasUnverified = analysis?.findings?.some((f) => f.human_verification_required);

    if (decision === 'Approved' && (hasHighFlags || hasUnverified) && !managerAckChecked) {
      setReviewActionError(
        'You must acknowledge the high or critical severity AI compliance flags before approving this content.'
      );
      return;
    }

    try {
      setSubmittingReview(true);
      const res = await api.post(`/submissions/${id}/review`, {
        decision,
        review_comments: reviewComments.trim(),
        acknowledgement: managerAckChecked,
      });

      if (res.data.success) {
        setSuccessMsg(`Content successfully marked as "${decision}". Decision recorded in governance timeline.`);
        setReviewComments('');
        setManagerAckChecked(false);
        await fetchSubmissionDetails();
      }
    } catch (err) {
      setReviewActionError(err.response?.data?.error || 'Failed to record review decision.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleCopySuggestion = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleApplyCorrection = async (finding) => {
    if (!submission || isLocked) return;
    if (!finding.suggested_correction) return;

    let updatedContent = submission.content_text;
    if (finding.problematic_text && updatedContent.includes(finding.problematic_text)) {
      updatedContent = updatedContent.replace(finding.problematic_text, finding.suggested_correction);
    } else {
      updatedContent = `${updatedContent}\n\n${finding.suggested_correction}`;
    }

    try {
      setSubmitting(true);
      const res = await api.put(`/submissions/${id}`, {
        title: submission.title,
        content_text: updatedContent,
        revision_reason: `Applied AI suggested correction for rule: ${finding.guideline_title || finding.category}`,
        status: submission.status === 'Changes Requested' ? 'Draft' : submission.status
      });

      if (res.data.success) {
        setSuccessMsg('Suggested correction applied to draft successfully! Re-run AI Compliance to verify.');
        await fetchSubmissionDetails();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to apply suggested correction.');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Draft':
        return 'bg-slate-100 text-slate-700 border-slate-200';
      case 'Ready for AI Review':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'AI Reviewed':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'Changes Requested':
        return 'bg-orange-50 text-orange-800 border-orange-200';
      case 'Pending Manager Approval':
        return 'bg-amber-50 text-amber-800 border-amber-300';
      case 'Approved':
        return 'bg-emerald-50 text-emerald-800 border-emerald-300';
      case 'Published':
        return 'bg-teal-50 text-teal-800 border-teal-300';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'Critical':
        return 'bg-red-700 text-white border-red-800 font-bold';
      case 'High':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'Medium':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'Low':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  if (loading) {
    return (
      <DashboardLayout title="Content Submission">
        <div className="py-24 flex flex-col items-center justify-center text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-forest-800 mb-2" />
          <p className="text-xs font-medium">Loading submission details...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (!submission) {
    return (
      <DashboardLayout title="Content Submission">
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center max-w-lg mx-auto">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">Submission Not Found</h3>
          <p className="text-xs text-slate-500 my-3">
            {error || 'This submission could not be retrieved or access was denied.'}
          </p>
          <Link
            to="/creator/submissions"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold hover:bg-slate-200"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Submissions</span>
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  const wordCount = submission.content_text.trim()
    ? submission.content_text.trim().split(/\s+/).length
    : 0;

  const isLocked =
    submission.status === 'Pending Manager Approval' ||
    submission.status === 'Approved' ||
    submission.status === 'Published';
  const isCreator = !isAdmin || submission.creator_id === user?.id;
  const isApprovalEligible =
    isCreator &&
    !isLocked &&
    analysis &&
    !analysis.is_outdated &&
    (revisions.length <= (analysis.revision_number || 1));

  return (
    <DashboardLayout title="Content Submission & Compliance Audit">
      {/* Top Breadcrumb & Action Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <Link
          to={isAdmin ? '/manager/approvals' : '/creator/submissions'}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{isAdmin ? 'Back to Approval Queue' : 'Back to Submissions'}</span>
        </Link>

        <div className="flex flex-wrap items-center gap-3">
          {/* AI Check Button (Disabled if locked) */}
          <button
            onClick={handleRunAICompliance}
            disabled={analyzing || isLocked}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 disabled:opacity-50 transition-colors shadow-sm"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-300" />
                <span>Auditing with Gemini AI...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-emerald-300" />
                <span>Run AI Compliance Check</span>
              </>
            )}
          </button>

          {/* Submit for Manager Approval Button (Creator) */}
          {isCreator && !isLocked && (
            <button
              onClick={handleSubmitApprovalClick}
              disabled={submittingApproval || !isApprovalEligible}
              title={
                !analysis
                  ? 'Run an AI Compliance Check first'
                  : analysis.is_outdated
                    ? 'AI report is outdated. Rerun audit before submitting'
                    : 'Submit draft to Brand Manager for sign-off'
              }
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 disabled:bg-slate-300 disabled:text-slate-600 transition-colors shadow-xs"
            >
              {submittingApproval ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5 text-emerald-200" />
              )}
              <span>Submit for Manager Approval</span>
            </button>
          )}

          {/* Publish Content Button (Brand Manager only, Approved status only) */}
          {isAdmin && submission.status === 'Approved' && (
            <button
              onClick={() => {
                setPublishError('');
                setShowPublishModal(true);
              }}
              disabled={publishing}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-teal-700 hover:bg-teal-800 disabled:opacity-50 transition-colors shadow-xs"
            >
              {publishing ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-200" />
              ) : (
                <Globe className="w-3.5 h-3.5 text-teal-200" />
              )}
              <span>Publish Content</span>
            </button>
          )}

          {/* Edit Copy Button */}
          <button
            onClick={handleOpenEdit}
            disabled={isLocked}
            title={
              isLocked
                ? `Content locked in ${submission.status} state`
                : 'Revise copy & generate new revision'
            }
            className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold border transition-colors shadow-xs ${isLocked
              ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed'
              : 'text-slate-700 bg-white hover:bg-slate-50 border-slate-300'
              }`}
          >
            {isLocked ? <Lock className="w-3.5 h-3.5 text-slate-400" /> : <Edit3 className="w-3.5 h-3.5 text-slate-500" />}
            <span>Edit Copy</span>
          </button>
        </div>
      </div>

      {/* Status Alert Banners */}
      {submission.status === 'Pending Manager Approval' && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between gap-3 text-xs text-amber-900 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
              <Clock className="w-4 h-4 text-amber-700 animate-pulse" />
            </div>
            <div>
              <p className="font-bold text-amber-950">Pending Manager Approval</p>
              <p className="text-amber-800 mt-0.5">
                This promotional copy is currently awaiting review and sign-off by a Brand Manager. Content editing is locked.
              </p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-200/70 text-amber-900 border border-amber-300 shrink-0">
            Locked for Review
          </span>
        </div>
      )}

      {submission.status === 'Approved' && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-emerald-900 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
            </div>
            <div>
              <p className="font-bold text-emerald-950">Approved for Publication</p>
              <p className="text-emerald-800 mt-0.5">
                This content has been formally approved by brand management. It is permanently locked against further edits.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2.5 shrink-0">
            <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-200/70 text-emerald-900 border border-emerald-300 shrink-0">
              Publish-Ready
            </span>
            {isAdmin && (
              <button
                onClick={() => {
                  setPublishError('');
                  setShowPublishModal(true);
                }}
                disabled={publishing}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-teal-700 hover:bg-teal-800 transition-colors shadow-xs"
              >
                {publishing ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Globe className="w-3.5 h-3.5 text-teal-200" />
                )}
                <span>Publish Content</span>
              </button>
            )}
          </div>
        </div>
      )}

      {submission.status === 'Published' && (
        <div className="mb-6 p-4 bg-teal-50 border border-teal-200 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-teal-900 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center shrink-0">
              <CheckCheck className="w-4 h-4 text-teal-700" />
            </div>
            <div>
              <p className="font-bold text-teal-950">Published Successfully</p>
              <p className="text-teal-800 mt-0.5">
                This content has been officially published in-app. It is permanently locked and archived under brand governance.
              </p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-teal-200/70 text-teal-900 border border-teal-300 shrink-0 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-teal-600 animate-pulse" />
            Published In-App
          </span>
        </div>
      )}

      {submission.status === 'Changes Requested' && (
        <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-xl flex items-center justify-between gap-3 text-xs text-orange-900 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center shrink-0">
              <AlertTriangle className="w-4 h-4 text-orange-700" />
            </div>
            <div>
              <p className="font-bold text-orange-950">Changes Requested by Brand Manager</p>
              <p className="text-orange-800 mt-0.5">
                The manager has returned this copy with required revisions. Check the review comments below, edit copy, and re-audit before resubmitting.
              </p>
            </div>
          </div>
          <button
            onClick={handleOpenEdit}
            className="px-3.5 py-1.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-xs font-semibold shrink-0"
          >
            Edit & Revise Copy
          </button>
        </div>
      )}

      {/* Notifications */}
      {error && (
        <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between text-xs text-red-700">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError('')}><X className="w-4 h-4" /></button>
        </div>
      )}

      {successMsg && (
        <div className="mb-5 p-3.5 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')}><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* AI Error Alert */}
      {analysisError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-red-800">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">AI Compliance Audit Failed</p>
              <p className="text-red-700 mt-0.5 leading-relaxed">{analysisError}</p>
            </div>
          </div>
          <button
            onClick={handleRunAICompliance}
            className="px-3.5 py-1.5 bg-red-600 text-white rounded-lg text-xs font-semibold hover:bg-red-700 shrink-0"
          >
            Retry Check
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Content Viewer + Manager Review Panel + AI Compliance Report */}
        <div className="lg:col-span-2 space-y-6">

          {/* PHASE 4: MANAGER REVIEW & SIGN-OFF ACTION PANEL */}
          {isAdmin && submission.status === 'Pending Manager Approval' && (
            <div className="bg-white border-2 border-forest-800/40 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100 mb-4">
                <div className="w-8 h-8 rounded-lg bg-forest-900 text-white flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4 text-emerald-300" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-900">
                    Brand Manager Review Decision
                  </h2>
                  <p className="text-[11px] text-slate-500">
                    Review AI findings and provide mandatory rationale to Approve or Request Changes.
                  </p>
                </div>
              </div>

              {reviewActionError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{reviewActionError}</span>
                </div>
              )}

              {/* Review Comments Textarea */}
              <div className="mb-4">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Reviewer Notes & Revision Directives *
                </label>
                <textarea
                  rows={3}
                  value={reviewComments}
                  onChange={(e) => setReviewComments(e.target.value)}
                  placeholder="e.g. Approved. Copy accurately reflects our CloudNova SLA guarantees and tone."
                  className="w-full p-3 border border-slate-300 rounded-lg text-xs font-sans focus:outline-none focus:ring-2 focus:ring-forest-800"
                />
              </div>

              {/* High Severity Exception Acknowledgement */}
              {((analysis?.high_severity_count || 0) > 0 ||
                analysis?.findings?.some((f) => f.human_verification_required)) && (
                  <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <label className="flex items-start gap-2.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={managerAckChecked}
                        onChange={(e) => setManagerAckChecked(e.target.checked)}
                        className="mt-0.5 rounded text-forest-800 focus:ring-forest-800 border-slate-300"
                      />
                      <span className="text-xs text-amber-900 leading-snug">
                        <strong>Policy Exception Acknowledgement:</strong> I acknowledge that AI detected{' '}
                        {analysis.high_severity_count} high-severity issue(s) or claims requiring verification, and I approve this content under brand exception.
                      </span>
                    </label>
                  </div>
                )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => handleManagerDecision('Changes Requested')}
                  disabled={submittingReview}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-white hover:bg-orange-50 text-orange-700 border border-orange-300 rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Request Changes</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleManagerDecision('Approved')}
                  disabled={submittingReview}
                  className="inline-flex items-center gap-1.5 px-5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 shadow-xs"
                >
                  {submittingReview ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-200" />
                  )}
                  <span>Approve Content</span>
                </button>
              </div>
            </div>
          )}

          {/* Active Content Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex flex-wrap items-center gap-2.5 mb-3">
              <span className="text-xs font-bold text-forest-900 bg-forest-50 border border-forest-200 px-3 py-0.5 rounded-full">
                {submission.brand_name}
              </span>
              <span
                className={`text-xs font-bold px-3 py-0.5 rounded-full border uppercase tracking-wider ${getStatusBadge(
                  submission.status
                )}`}
              >
                {submission.status}
              </span>
              <span className="text-xs font-mono text-slate-400">
                Latest: Revision #{submission.revision_count || 1}
              </span>
            </div>

            <h1 className="text-xl font-bold text-slate-900 mb-4">{submission.title}</h1>

            <div className="p-5 rounded-xl bg-slate-50 border border-slate-200/80 mb-2">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200/60 text-xs text-slate-400 font-mono">
                <span>Active Promotional Copy</span>
                <span>{wordCount} words • {submission.content_text.length} chars</span>
              </div>
              <p className="text-sm font-sans text-slate-800 leading-relaxed whitespace-pre-line">
                {submission.content_text}
              </p>
            </div>
          </div>

          {/* AI COMPLIANCE REPORT SECTION */}
          {analyzing ? (
            <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
              <Loader2 className="w-10 h-10 animate-spin text-forest-800 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-900">
                Auditing Content with Gemini AI...
              </h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                Comparing promotional copy against stored brand guidelines, approved facts, terminology, and restricted claims.
              </p>
            </div>
          ) : analysis ? (
            <div className="space-y-4">
              {/* Stale Report Alert */}
              {analysis.is_outdated && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between gap-3 text-xs text-amber-900">
                  <div className="flex items-center gap-2.5">
                    <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
                    <div>
                      <p className="font-bold">Report Outdated</p>
                      <p className="text-amber-800 text-[11px] mt-0.5">
                        This report audited Revision #{analysis.revision_number}, but content has since been updated to Revision #{submission.revision_count || 1}.
                      </p>
                    </div>
                  </div>
                  {!isLocked && (
                    <button
                      onClick={handleRunAICompliance}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-700 text-white rounded-lg text-xs font-semibold hover:bg-amber-800 shrink-0"
                    >
                      <RefreshCw className="w-3 h-3" />
                      <span>Rerun Audit</span>
                    </button>
                  )}
                </div>
              )}

              {/* Analysis Header Card */}
              <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 mb-4">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-forest-900 text-white flex items-center justify-center">
                      <Sparkles className="w-5 h-5 text-emerald-300" />
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-slate-900">
                        AI Brand Compliance Report
                      </h2>
                      <p className="text-xs text-slate-400">
                        Model: {analysis.model_identifier} • Audited:{' '}
                        {new Date(analysis.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <span
                    className={`text-xs font-bold px-3 py-1 rounded-full border uppercase tracking-wider ${analysis.review_status === 'Compliant'
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : analysis.review_status === 'Violations Detected'
                        ? 'bg-red-50 text-red-800 border-red-200'
                        : 'bg-amber-50 text-amber-800 border-amber-200'
                      }`}
                  >
                    {analysis.review_status}
                  </span>
                </div>

                {/* Executive Summary */}
                <p className="text-xs text-slate-700 leading-relaxed mb-5">
                  {analysis.summary}
                </p>

                {/* Severity Counters */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-3 border-t border-slate-100 text-center">
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="block text-lg font-bold text-slate-900">
                      {analysis.issues_count}
                    </span>
                    <span className="text-[10px] text-slate-400 font-semibold uppercase">
                      Total Issues
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-red-100/70 border border-red-200">
                    <span className="block text-lg font-bold text-red-900">
                      {analysis.critical_severity_count || 0}
                    </span>
                    <span className="text-[10px] text-red-800 font-semibold uppercase">
                      Critical
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-rose-50/70 border border-rose-100">
                    <span className="block text-lg font-bold text-red-700">
                      {analysis.high_severity_count}
                    </span>
                    <span className="text-[10px] text-red-600 font-semibold uppercase">
                      High Severity
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-amber-50/60 border border-amber-100">
                    <span className="block text-lg font-bold text-amber-800">
                      {analysis.medium_severity_count}
                    </span>
                    <span className="text-[10px] text-amber-700 font-semibold uppercase">
                      Medium
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-blue-50/60 border border-blue-100">
                    <span className="block text-lg font-bold text-blue-700">
                      {analysis.low_severity_count}
                    </span>
                    <span className="text-[10px] text-blue-600 font-semibold uppercase">
                      Low
                    </span>
                  </div>
                </div>
              </div>

              {/* Mandatory Governance & Source-Grounded AI Disclaimer */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 flex items-start gap-2.5">
                <ShieldCheck className="w-4 h-4 text-forest-700 shrink-0 mt-0.5" />
                <div className="text-[11px] leading-relaxed">
                  <strong className="text-slate-800">AI Brand Governance Safeguard:</strong> Compliance findings are verified against active brand guidelines and verified factual references. Absence of detected issues does not guarantee factual accuracy or waive human oversight. Human Brand Manager approval remains strictly mandatory prior to publication.
                </div>
              </div>

              {/* Findings Breakdown */}
              <div className="space-y-4">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider px-1">
                  Compliance Findings & Suggested Corrections ({analysis.findings?.length || 0})
                </h3>

                {(!analysis.findings || analysis.findings.length === 0) ? (
                  <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-sm">
                    <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto mb-2" />
                    <h4 className="text-sm font-bold text-slate-900">Full Guidelines Compliance</h4>
                    <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                      Gemini found no tone discrepancies, prohibited terms, or unsupported claims in this copy.
                    </p>
                  </div>
                ) : (
                  analysis.findings.map((f, idx) => (
                    <div
                      key={idx}
                      className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span
                            className={`text-[11px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${getSeverityBadge(
                              f.severity
                            )}`}
                          >
                            {f.severity}
                          </span>
                          <span className="text-xs font-semibold text-slate-800">
                            {f.category}
                          </span>
                          {f.confidence_level && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium border border-slate-200">
                              Confidence: {f.confidence_level}
                            </span>
                          )}
                        </div>

                        {f.human_verification_required && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 text-purple-700 border border-purple-200">
                            <Info className="w-3 h-3" />
                            Human Verification Required
                          </span>
                        )}
                      </div>

                      {f.problematic_text && (
                        <div className="p-2.5 rounded-lg bg-red-50/50 border border-red-100 text-xs">
                          <span className="font-semibold text-red-900">Flagged Passage: </span>
                          <span className="text-red-700 font-mono">"{f.problematic_text}"</span>
                        </div>
                      )}

                      <p className="text-xs text-slate-600 leading-relaxed">
                        {f.explanation}
                      </p>

                      {f.guideline_title && (
                        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/70 text-xs text-slate-700 flex items-start gap-2">
                          <Building2 className="w-3.5 h-3.5 text-forest-700 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-bold text-slate-900">Violated Guideline: </span>
                            <span className="font-medium text-forest-900">{f.guideline_title}</span>
                            {f.guideline_rule && (
                              <p className="text-slate-500 text-[11px] mt-0.5">{f.guideline_rule}</p>
                            )}
                          </div>
                        </div>
                      )}

                      {f.suggested_correction && (
                        <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg text-xs">
                          <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                            <span className="font-bold text-emerald-950 flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                              AI Recommended Replacement
                            </span>
                            <div className="flex items-center gap-2">
                              {isCreator && !isLocked && (
                                <button
                                  type="button"
                                  onClick={() => handleApplyCorrection(f)}
                                  disabled={submitting}
                                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-white bg-forest-900 hover:bg-forest-800 px-2.5 py-1 rounded transition-colors shadow-2xs disabled:opacity-50"
                                >
                                  <Check className="w-3 h-3 text-emerald-300" />
                                  <span>Apply to Draft</span>
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => handleCopySuggestion(f.suggested_correction, idx)}
                                className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-800 hover:text-emerald-900 transition-colors"
                              >
                                {copiedIndex === idx ? (
                                  <>
                                    <Check className="w-3 h-3 text-emerald-600" />
                                    <span>Copied!</span>
                                  </>
                                ) : (
                                  <>
                                    <Copy className="w-3 h-3" />
                                    <span>Copy</span>
                                  </>
                                )}
                              </button>
                            </div>
                          </div>
                          <p className="text-emerald-900 font-mono text-[11px] bg-white/70 p-2 rounded border border-emerald-100 whitespace-pre-wrap">
                            {f.suggested_correction}
                          </p>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-sm">
              <div className="w-12 h-12 rounded-2xl bg-forest-50 text-forest-800 border border-forest-200 flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6 text-forest-800" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">AI Brand Compliance Audit</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-5 leading-relaxed">
                Run Google Gemini to audit this promotional text against <strong>{submission.brand_name}</strong>'s active brand rules, approved facts, communication tone, and restricted words.
              </p>
              <button
                onClick={handleRunAICompliance}
                disabled={analyzing}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold text-white bg-forest-900 hover:bg-forest-800 shadow-sm"
              >
                <Sparkles className="w-4 h-4 text-emerald-300" />
                <span>Run AI Compliance Check</span>
              </button>
            </div>
          )}
        </div>

        {/* Right Column (1 col): Metadata, Decision Timeline & Revision History */}
        <div className="space-y-6">
          {/* Metadata Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider pb-3 border-b border-slate-100 mb-3">
              Submission Metadata
            </h3>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Creator:</span>
                <span className="font-semibold text-slate-800">{submission.creator_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Target Brand:</span>
                <span className="font-semibold text-forest-900">{submission.brand_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Status:</span>
                <span className="font-semibold text-slate-800">{submission.status}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Created:</span>
                <span className="text-slate-700">
                  {new Date(submission.created_at).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Last Modified:</span>
                <span className="text-slate-700">
                  {new Date(submission.updated_at || submission.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* PHASE 4: IMMUTABLE DECISION HISTORY TIMELINE */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <ShieldCheck className="w-4 h-4 text-emerald-700" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Manager Decision History ({decisions.length})
              </h3>
            </div>

            {decisions.length === 0 ? (
              <div className="p-4 bg-slate-50 rounded-lg text-center text-xs text-slate-500">
                No manager review decisions recorded yet.
              </div>
            ) : (
              <div className="space-y-3">
                {decisions.map((dec) => (
                  <div
                    key={dec.id}
                    className="p-3 rounded-lg border border-slate-200 bg-slate-50/70 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-[11px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${dec.decision === 'Approved'
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                          : 'bg-orange-50 text-orange-800 border-orange-200'
                          }`}
                      >
                        {dec.decision}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        Rev #{dec.revision_number}
                      </span>
                    </div>

                    <p className="text-xs text-slate-800 font-medium whitespace-pre-wrap leading-relaxed">
                      "{dec.review_comments}"
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-200/50">
                      <span>Reviewed by {dec.reviewer_name}</span>
                      <span>{new Date(dec.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Revision History Timeline */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <History className="w-4 h-4 text-forest-700" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Revision History ({revisions.length})
              </h3>
            </div>

            <div className="space-y-3">
              {revisions.map((rev) => (
                <div
                  key={rev.id}
                  className="p-3 rounded-lg border border-slate-200 bg-slate-50/70 text-xs hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-slate-900">
                      Revision #{rev.revision_number}
                    </span>
                    <button
                      onClick={() => setPreviewRevision(rev)}
                      title="Inspect copy for this revision"
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-forest-700 hover:text-forest-900"
                    >
                      <Eye className="w-3 h-3" />
                      <span>View</span>
                    </button>
                  </div>

                  <p className="text-[11px] text-slate-600 mb-1.5 font-medium">
                    {rev.reason || 'No description entered'}
                  </p>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                    <span>{rev.created_by}</span>
                    <span>{new Date(rev.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* PHASE 4: CREATOR WARNING ACKNOWLEDGEMENT MODAL */}
      {showCreatorAckModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 pb-3 border-b border-slate-100 mb-4">
              <div className="w-9 h-9 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  High-Risk Compliance Findings Detected
                </h3>
                <p className="text-[11px] text-slate-500">
                  Acknowledgement required before submitting for manager sign-off.
                </p>
              </div>
            </div>

            <div className="space-y-3 mb-5 text-xs text-slate-600">
              <p>
                The AI Compliance check identified{' '}
                <strong className="text-red-700">
                  {analysis?.high_severity_count || 0} high-severity issue(s)
                </strong>{' '}
                or claims requiring explicit verification.
              </p>
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 text-xs">
                Submitting this draft will lock your copy and escalate it directly to the Brand Manager with compliance flags highlighted.
              </div>

              <label className="flex items-start gap-2.5 pt-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={creatorAckChecked}
                  onChange={(e) => setCreatorAckChecked(e.target.checked)}
                  className="mt-0.5 rounded text-forest-800 focus:ring-forest-800 border-slate-300"
                />
                <span className="text-xs text-slate-800 leading-snug">
                  I acknowledge these compliance warnings and request manager review under exception.
                </span>
              </label>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowCreatorAckModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!creatorAckChecked || submittingApproval}
                onClick={() => executeSubmitApproval(true)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50"
              >
                {submittingApproval && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Confirm & Submit for Review</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EDIT DRAFT MODAL */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">Edit Submission & Revise</h3>
                <p className="text-xs text-slate-500">
                  Modifying content will automatically append a new snapshot to Revision History and mark prior AI reports as outdated.
                </p>
              </div>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  required
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forest-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Promotional Copy *
                </label>
                <textarea
                  rows={8}
                  required
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="w-full p-3 border border-slate-300 rounded-lg text-sm font-sans focus:outline-none focus:ring-2 focus:ring-forest-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Reason for Revision (Changelog description) *
                </label>
                <input
                  type="text"
                  required
                  value={editReason}
                  onChange={(e) => setEditReason(e.target.value)}
                  placeholder="e.g. Addressed AI compliance flags and corrected restricted wording"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-forest-800"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
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
                  <span>Save Revision</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* HISTORICAL REVISION PREVIEW MODAL */}
      {previewRevision && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Revision #{previewRevision.revision_number} Snapshot
                </h3>
                <p className="text-[11px] text-slate-400">
                  Recorded by {previewRevision.created_by} on{' '}
                  {new Date(previewRevision.created_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setPreviewRevision(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mb-3 p-2.5 bg-slate-50 border border-slate-100 rounded-lg text-xs text-slate-600">
              <span className="font-semibold text-slate-800">Revision Reason: </span>
              <span>{previewRevision.reason || 'None provided'}</span>
            </div>

            <div className="p-3.5 bg-slate-100/60 rounded-lg border border-slate-200 text-xs text-slate-800 font-sans leading-relaxed whitespace-pre-line max-h-60 overflow-y-auto">
              {previewRevision.content_text}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 text-right">
              <button
                onClick={() => setPreviewRevision(null)}
                className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg"
              >
                Close Snapshot
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONFIRM PUBLISH MODAL */}
      {showPublishModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center">
                  <Globe className="w-4 h-4 text-teal-700" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Confirm Publication</h3>
                  <p className="text-[11px] text-slate-500">In-App Publication Governance</p>
                </div>
              </div>
              <button
                onClick={() => {
                  if (!publishing) {
                    setShowPublishModal(false);
                    setPublishError('');
                  }
                }}
                disabled={publishing}
                className="text-slate-400 hover:text-slate-600 disabled:opacity-50"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {publishError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                <span>{publishError}</span>
              </div>
            )}

            <div className="space-y-3 mb-5">
              <p className="text-xs text-slate-700 leading-relaxed">
                Are you sure you want to publish this approved promotional content in-app?
              </p>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Campaign:</span>
                  <span className="text-slate-900 font-bold truncate max-w-xs">{submission.title}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Governed Brand:</span>
                  <span className="text-forest-900 font-semibold">{submission.brand_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 font-medium">Content Revision:</span>
                  <span className="font-mono text-slate-700">Revision #{submission.revision_count || 1}</span>
                </div>
              </div>

              <div className="p-3 bg-teal-50/70 border border-teal-200 rounded-lg flex items-start gap-2 text-xs text-teal-900">
                <Info className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
                <p className="text-[11px] leading-relaxed">
                  Upon publishing, this submission status transitions to <strong>Published</strong>. The content will be locked permanently and visible as published across governance dashboards.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => {
                  setShowPublishModal(false);
                  setPublishError('');
                }}
                disabled={publishing}
                className="px-4 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handlePublish}
                disabled={publishing}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-lg text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors"
              >
                {publishing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Publishing...</span>
                  </>
                ) : (
                  <>
                    <Globe className="w-3.5 h-3.5 text-teal-200" />
                    <span>Confirm & Publish</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
};

export default SubmissionDetails;
