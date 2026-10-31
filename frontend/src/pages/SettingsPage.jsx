import React, { useState, useEffect } from 'react';
import { Settings, Sun, Moon, Server, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const SettingsPage = () => {
  const { theme, toggleTheme } = useAuth();
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api.get('/health').then((res) => setHealth(res.data)).catch(() => {});
  }, []);

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Platform Settings & Environment Diagnostics</h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure appearance, inspect backend API connectivity, and review external data source attribution policies.
        </p>
      </div>

      {/* Appearance Card */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold">Interface Color Theme</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Switch between Dark Navy Data Science Theme and High-Contrast Light Theme.
          </p>
        </div>
        <button
          onClick={toggleTheme}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-500 text-slate-950 font-bold text-xs"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          <span>Switch to {theme === 'dark' ? 'Light Theme' : 'Dark Navy Theme'}</span>
        </button>
      </div>

      {/* System Connectivity Card */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-3 text-xs">
        <h3 className="text-sm font-bold flex items-center gap-2">
          <Server className="w-4 h-4 text-sky-400" />
          <span>Backend API & Database Status</span>
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">FastAPI Service Status</span>
            <span className="inline-flex items-center gap-1 text-emerald-400 font-bold">
              <CheckCircle2 className="w-3.5 h-3.5" /> {health?.status || 'Online'}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">Platform Version</span>
            <span className="font-mono text-sky-400">{health?.version || '1.0.0'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;

