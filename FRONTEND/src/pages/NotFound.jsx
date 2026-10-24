import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

const NotFound = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-forest-100 text-forest-800 flex items-center justify-center mb-4">
        <ShieldAlert className="w-8 h-8 text-forest-800" />
      </div>
      <h1 className="text-3xl font-bold text-slate-900 mb-2">404 - Page Not Found</h1>
      <p className="text-sm text-slate-600 max-w-md mb-6">
        The requested URL was not found on BrandGuard AI. Check the path or return to your dashboard.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold text-white bg-forest-900 hover:bg-forest-800 transition-colors shadow-sm"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Dashboard</span>
      </Link>
    </div>
  );
};

export default NotFound;
