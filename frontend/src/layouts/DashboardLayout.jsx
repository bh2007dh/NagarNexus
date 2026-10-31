import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  MapPin,
  Database,
  Sparkles,
  BarChart3,
  Sigma,
  Cpu,
  TrendingUp,
  AlertTriangle,
  GitCompare,
  Lightbulb,
  FileText,
  UserCheck,
  Settings,
  LogOut,
  Sun,
  Moon,
  Menu,
  X,
  Activity,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const SIDEBAR_NAV_ITEMS = [
  { path: '/', label: 'Overview Dashboard', icon: LayoutDashboard },
  { path: '/locations', label: 'Location Intelligence', icon: MapPin },
  { path: '/datasets', label: 'Dataset Explorer', icon: Database },
  { path: '/cleaning', label: 'Data Cleaning', icon: Sparkles },
  { path: '/eda', label: 'Exploratory Data Analysis', icon: BarChart3 },
  { path: '/statistics', label: 'Statistical Analysis', icon: Sigma },
  { path: '/ml-lab', label: 'Machine Learning Lab', icon: Cpu },
  { path: '/predictions', label: 'Predictive Analytics', icon: TrendingUp },
  { path: '/risk', label: 'Risk Detection', icon: AlertTriangle },
  { path: '/comparison', label: 'Location Comparison', icon: GitCompare },
  { path: '/insights', label: 'AI Insights', icon: Lightbulb },
  { path: '/reports', label: 'Report Center', icon: FileText },
  { path: '/profile', label: 'User Profile', icon: UserCheck },
  { path: '/settings', label: 'Settings', icon: Settings },
];

const DashboardLayout = ({ children }) => {
  const { user, logout, theme, toggleTheme } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  const isLight = theme === 'light';

  return (
    <div
      className={`min-h-screen flex ${
        isLight ? 'bg-slate-50 text-slate-900' : 'bg-[#060b19] text-slate-100'
      }`}
    >
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0 flex flex-col border-r ${
          isLight
            ? 'bg-white border-slate-200 text-slate-800'
            : 'bg-[#0b132b] border-slate-800/80 text-slate-200'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Brand Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800/60">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold tracking-tight text-base leading-none bg-gradient-to-r from-sky-400 to-blue-400 bg-clip-text text-transparent">
                NAGARNEXUS
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5 uppercase tracking-wider">
                Urban Intelligence AI
              </div>
            </div>
          </div>
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1 text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Links (All 14 Modules) */}
        <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
          {SIDEBAR_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-sky-500/20 to-blue-600/15 text-sky-400 border border-sky-500/30 shadow-sm'
                      : isLight
                      ? 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-100'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer User Card */}
        <div className="p-3 border-t border-slate-800/60">
          <div className="flex items-center justify-between px-2 py-1.5">
            <div className="truncate">
              <div className="text-xs font-semibold truncate">{user?.full_name || 'Urban Analyst'}</div>
              <div className="text-[11px] text-slate-400 truncate">{user?.email}</div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-2 rounded-lg text-rose-400 hover:bg-rose-500/10 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header
          className={`sticky top-0 z-30 flex items-center justify-between px-6 py-3.5 border-b backdrop-blur-md ${
            isLight
              ? 'bg-white/90 border-slate-200'
              : 'bg-[#0b132b]/85 border-slate-800/80'
          }`}
        >
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-lg border border-slate-700 text-slate-300"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <span className="text-xs font-medium text-sky-400 uppercase tracking-wider">
                Turning Urban Data Into Intelligent Decisions
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              aria-label="Toggle Theme"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition ${
                isLight
                  ? 'border-slate-300 bg-slate-100 text-slate-800 hover:bg-slate-200'
                  : 'border-slate-700 bg-slate-800/70 text-slate-200 hover:bg-slate-800'
              }`}
            >
              {isLight ? <Moon className="w-3.5 h-3.5 text-indigo-600" /> : <Sun className="w-3.5 h-3.5 text-amber-400" />}
              <span>{isLight ? 'Dark Navy' : 'Light Mode'}</span>
            </button>
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-xs text-sky-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Role: {user?.role?.toUpperCase() || 'ANALYST'}</span>
            </div>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 p-4 md:p-6 overflow-x-hidden max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;

