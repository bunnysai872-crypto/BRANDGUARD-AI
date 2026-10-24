import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck,
  LayoutDashboard,
  FileText,
  FileCheck2,
  BookOpen,
  Building2,
  CheckSquare,
  History,
  LogOut,
  Sparkles,
  PlusCircle,
  Globe,
  BarChart3
} from 'lucide-react';

const Sidebar = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const creatorNavItems = [
    { label: 'Overview', to: '/creator-dashboard', icon: LayoutDashboard },
    { label: 'Create Content', to: '/creator/submissions/new', icon: PlusCircle },
    { label: 'My Submissions', to: '/creator/submissions', icon: FileText },
    { label: 'Brand Guidelines', to: '/creator/guidelines', icon: BookOpen },
    { label: 'Published Content', to: '/published-content', icon: Globe },
    { label: 'Governance Analytics', to: '/analytics', icon: BarChart3 },
  ];

  const managerNavItems = [
    { label: 'Overview', to: '/manager-dashboard', icon: LayoutDashboard },
    { label: 'Brand Profiles', to: '/manager/brands', icon: Building2 },
    { label: 'Brand Guidelines', to: '/manager/guidelines', icon: BookOpen },
    { label: 'Approval Queue', to: '/manager/approvals', icon: CheckSquare },
    { label: 'All Submissions', to: '/creator/submissions', icon: FileCheck2 },
    { label: 'Published Content', to: '/published-content', icon: Globe },
    { label: 'Governance Analytics', to: '/analytics', icon: BarChart3 },
  ];

  const navItems = isAdmin ? managerNavItems : creatorNavItems;

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen sticky top-0 select-none">
      {/* Brand Logo Header */}
      <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-200">
        <div className="w-9 h-9 rounded-lg bg-forest-900 flex items-center justify-center text-white shadow-sm">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
        </div>
        <div>
          <span className="font-bold text-slate-900 text-base tracking-tight block">
            BrandGuard <span className="text-forest-700">AI</span>
          </span>
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">
            Governance Platform
          </span>
        </div>
      </div>

      {/* Role Indicator Banner */}
      <div className="px-6 py-3 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500">Current Role</span>
        <span
          className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
            isAdmin
              ? 'bg-amber-50 text-amber-800 border-amber-200'
              : 'bg-emerald-50 text-emerald-800 border-emerald-200'
          }`}
        >
          {isAdmin ? 'Brand Manager' : 'Content Creator'}
        </span>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 py-4 px-3 overflow-y-auto space-y-1">
        <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-forest-900 text-white shadow-sm'
                    : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                        isActive
                          ? 'bg-forest-800 text-emerald-200 border border-forest-700'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* User Information & Logout */}
      <div className="p-4 border-t border-slate-200 bg-white">
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-forest-100 border border-forest-200 flex items-center justify-center text-forest-800 font-semibold text-xs">
              {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-slate-900 truncate">
                {user?.full_name || user?.username}
              </p>
              <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-slate-700 bg-slate-100 hover:bg-red-50 hover:text-red-700 border border-slate-200 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
