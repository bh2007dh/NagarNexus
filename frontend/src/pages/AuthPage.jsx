import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Lock, Mail, User, Building2, MapPin, ShieldCheck, KeyRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api, { extractErrorMessage } from '../services/api';
import { AlertBanner } from '../components/LoadingSkeleton';

const AuthPage = () => {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState('login'); // login | register | reset
  const [email, setEmail] = useState('analyst@nagarnexus.org');
  const [password, setPassword] = useState('NagarNexus@2026');
  const [fullName, setFullName] = useState('');
  const [organization, setOrganization] = useState('Urban Analytics Division');
  const [preferredCity, setPreferredCity] = useState('Metro Coastal Belt');
  const [newPassword, setNewPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const switchMode = (newMode) => {
    setMode(newMode);
    setError('');
    setSuccess('');
    if (newMode === 'register') {
      if (email === 'analyst@nagarnexus.org') setEmail('');
      if (password === 'NagarNexus@2026') setPassword('');
    } else if (newMode === 'login') {
      if (!email) setEmail('analyst@nagarnexus.org');
      if (!password) setPassword('NagarNexus@2026');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(email, password);
        navigate('/');
      } else if (mode === 'register') {
        await register({
          full_name: fullName,
          email,
          password,
          organization,
          preferred_city: preferredCity,
        });
        navigate('/');
      } else if (mode === 'reset') {
        const res = await api.post('/auth/reset-password', {
          email,
          new_password: newPassword,
        });
        setSuccess(res.data.message || 'Password updated! You can now sign in.');
        setMode('login');
        setPassword(newPassword);
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const handleQuickDemoLogin = async () => {
    setError('');
    setBusy(true);
    try {
      await login('analyst@nagarnexus.org', 'NagarNexus@2026');
      navigate('/');
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#060b19] text-slate-100 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full grid grid-cols-1 lg:grid-cols-12 rounded-2xl overflow-hidden border border-slate-800 bg-[#0b132b] shadow-2xl">
        {/* Left Hero Panel */}
        <div className="lg:col-span-5 p-8 bg-gradient-to-br from-sky-900/50 via-blue-950/60 to-[#060b19] flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-slate-800">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center shadow-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight text-white">NAGARNEXUS</h1>
                <p className="text-xs text-sky-400">Hyperlocal Urban Intelligence</p>
              </div>
            </div>

            <h2 className="text-2xl font-bold text-slate-100 leading-snug mb-3">
              Turning Urban Data Into Intelligent Decisions.
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed mb-6">
              Analyze real-world weather, air quality, and hydrological datasets with automated data cleaning,
              statistical hypothesis testing, leak-free Machine Learning pipelines, and spatial risk detection.
            </p>

            <div className="space-y-3 text-xs text-slate-300">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-400 shrink-0" />
                <span>Bcrypt password hashing & JWT Bearer protection</span>
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-400 shrink-0" />
                <span>14 connected Data Science & ML modules</span>
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-400 shrink-0" />
                <span>Private dataset isolation & PDF/CSV report export</span>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-slate-800/80">
            <button
              type="button"
              onClick={handleQuickDemoLogin}
              disabled={busy}
              className="w-full py-2.5 px-4 rounded-xl bg-sky-500/20 hover:bg-sky-500/30 border border-sky-400/40 text-sky-300 text-xs font-semibold transition"
            >
              One-Click Demo Analyst Login (analyst@nagarnexus.org)
            </button>
          </div>
        </div>

        {/* Right Form Panel */}
        <div className="lg:col-span-7 p-8">
          <div className="flex items-center gap-2 mb-6 border-b border-slate-800 pb-3">
            <button
              type="button"
              onClick={() => switchMode('login')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition ${
                mode === 'login' ? 'bg-sky-500 text-slate-950' : 'text-slate-400 hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => switchMode('register')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition ${
                mode === 'register' ? 'bg-sky-500 text-slate-950' : 'text-slate-400 hover:text-white'
              }`}
            >
              Create Account
            </button>
            <button
              type="button"
              onClick={() => switchMode('reset')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition ${
                mode === 'reset' ? 'bg-sky-500 text-slate-950' : 'text-slate-400 hover:text-white'
              }`}
            >
              Reset Password
            </button>
          </div>

          <AlertBanner type="error" message={error} onClose={() => setError('')} />
          <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Dr. Aarav Ramanathan"
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-sky-400 outline-none"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="naga@nagarnexus.org"
                  className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-sky-400 outline-none"
                />
              </div>
            </div>

            {mode !== 'reset' ? (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-sky-400 outline-none"
                  />
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">New Password</label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password (min 6 chars)"
                    className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-sky-400 outline-none"
                  />
                </div>
              </div>
            )}

            {mode === 'register' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Organization</label>
                  <div className="relative">
                    <Building2 className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      value={organization}
                      onChange={(e) => setOrganization(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-sky-400 outline-none"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Primary Monitored City</label>
                  <div className="relative">
                    <MapPin className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      value={preferredCity}
                      onChange={(e) => setPreferredCity(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:border-sky-400 outline-none"
                    />
                  </div>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-sky-400 to-blue-600 hover:from-sky-300 hover:to-blue-500 text-slate-950 font-bold text-sm shadow-lg shadow-sky-500/20 transition"
            >
              {busy
                ? 'Processing...'
                : mode === 'login'
                ? 'Sign In to NagarNexus'
                : mode === 'register'
                ? 'Create Analyst Account'
                : 'Reset Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
