import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

const Navbar = ({ title = 'Dashboard' }) => {
  const { user } = useAuth();
  const [backendStatus, setBackendStatus] = useState('checking'); // 'healthy', 'error', 'checking'

  const checkHealth = async () => {
    try {
      setBackendStatus('checking');
      const res = await api.get('/health');
      if (res.data?.status === 'healthy') {
        setBackendStatus('healthy');
      } else {
        setBackendStatus('error');
      }
    } catch {
      setBackendStatus('error');
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h1>
        <p className="text-xs text-slate-500">Brand compliance and rule governance</p>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend Connectivity Status Badge */}
        <div
          onClick={checkHealth}
          title="Click to re-verify backend connectivity"
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border cursor-pointer select-none transition-colors ${
            backendStatus === 'healthy'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : backendStatus === 'checking'
              ? 'bg-slate-100 text-slate-600 border-slate-200'
              : 'bg-red-50 text-red-800 border-red-200'
          }`}
        >
          {backendStatus === 'healthy' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
          {backendStatus === 'checking' && <RefreshCw className="w-3.5 h-3.5 text-slate-500 animate-spin" />}
          {backendStatus === 'error' && <AlertCircle className="w-3.5 h-3.5 text-red-600" />}
          <span>
            {backendStatus === 'healthy'
              ? 'Backend API Connected'
              : backendStatus === 'checking'
              ? 'Checking API...'
              : 'Backend Offline'}
          </span>
        </div>

        {/* User Identity Chip */}
        <div className="text-right hidden sm:block">
          <p className="text-xs font-semibold text-slate-800">{user?.full_name || user?.username}</p>
          <p className="text-[11px] text-slate-400 capitalize">{user?.role} Account</p>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
