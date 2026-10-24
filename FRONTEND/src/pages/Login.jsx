import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowRight, Loader2, Sparkles, UserCheck } from 'lucide-react';

const Login = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier || !password) {
      setError('Please provide your username/email and password.');
      return;
    }

    setError('');
    setIsSubmitting(true);

    const result = await login(identifier, password);
    setIsSubmitting(false);

    if (result.success) {
      if (from) {
        navigate(from, { replace: true });
      } else {
        navigate(result.user.role === 'admin' ? '/manager-dashboard' : '/creator-dashboard', { replace: true });
      }
    } else {
      setError(result.error);
    }
  };

  // Quick Demo Account Helper (for evaluators)
  const handleQuickLogin = async (role) => {
    setError('');
    setIsSubmitting(true);

    // Clear any stale token/session that could cause auth conflicts
    localStorage.removeItem('brandguard_token');
    localStorage.removeItem('brandguard_user');

    try {
      const res = await api.post('/auth/demo-login', { role });

      setIsSubmitting(false);

      if (res.data?.success) {
        const { user, token } = res.data;
        localStorage.setItem('brandguard_token', token);
        localStorage.setItem('brandguard_user', JSON.stringify(user));
        // Hard navigate so AuthContext re-initializes cleanly with the new token
        const dest = role === 'admin' ? '/manager-dashboard' : '/creator-dashboard';
        window.location.href = dest;
      } else {
        setError(res.data?.error || `Demo ${role} login failed. Please try again.`);
      }
    } catch (err) {
      setIsSubmitting(false);
      const status = err.response?.status;
      const serverMsg = err.response?.data?.error;
      if (!err.response) {
        setError('Cannot reach the server. Please make sure the backend is running on port 5000.');
      } else if (serverMsg) {
        setError(serverMsg);
      } else {
        setError(`Demo ${role} login failed (${status ?? 'network error'}). Please try again.`);
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-forest-900 text-white shadow-sm mb-4">
          <ShieldCheck className="w-8 h-8 text-emerald-400" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Sign in to BrandGuard <span className="text-forest-700">AI</span>
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          Intelligent brand governance and content compliance platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-xl sm:px-10">
          {error && (
            <div className="mb-5 p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2.5 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Username or Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-4 w-4 text-slate-400" />
                </div>
                <input
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="name@company.com or username"
                  required
                  className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-forest-800 focus:border-forest-800 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 text-slate-400" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-forest-800 focus:border-forest-800 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border border-transparent rounded-lg text-sm font-semibold text-white bg-forest-900 hover:bg-forest-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-forest-900 disabled:opacity-60 transition-colors shadow-sm"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Signing In...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-6 border-t border-slate-200">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider text-center mb-3">
              One-Click Hackathon Evaluator Login
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin')}
                disabled={isSubmitting}
                className="flex flex-col items-center justify-center p-2.5 rounded-lg border border-amber-200 bg-amber-50 hover:bg-amber-100 text-amber-900 text-xs font-medium transition-colors"
              >
                <UserCheck className="w-4 h-4 text-amber-700 mb-1" />
                <span>Brand Manager</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('creator')}
                disabled={isSubmitting}
                className="flex flex-col items-center justify-center p-2.5 rounded-lg border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 text-emerald-900 text-xs font-medium transition-colors"
              >
                <Sparkles className="w-4 h-4 text-emerald-700 mb-1" />
                <span>Content Creator</span>
              </button>
            </div>
          </div>

          <div className="mt-6 text-center">
            <p className="text-xs text-slate-600">
              Don't have an account?{' '}
              <Link to="/register" className="font-semibold text-forest-800 hover:text-forest-700">
                Register here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
