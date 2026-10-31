import React, { useState } from 'react';
import { UserCheck, Save } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api, { extractErrorMessage } from '../services/api';
import { AlertBanner } from '../components/LoadingSkeleton';

const UserProfile = () => {
  const { user, setUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [organization, setOrganization] = useState(user?.organization || 'Urban Analytics Division');
  const [preferredCity, setPreferredCity] = useState(user?.preferred_city || 'Chennai');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const res = await api.put('/auth/profile', {
        full_name: fullName,
        organization,
        preferred_city: preferredCity,
      });
      setUser(res.data);
      localStorage.setItem('nagarnexus_user', JSON.stringify(res.data));
      setSuccess('User profile updated.');
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analyst Profile & Credentials</h1>
        <p className="text-xs text-slate-400 mt-1">
          Manage your NagarNexus identity, organization affiliation, and default urban monitoring zone.
        </p>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />
      <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />

      <form onSubmit={handleSave} className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4 text-xs">
        <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400 font-bold text-lg">
            {(user?.full_name || 'U')[0]}
          </div>
          <div>
            <div className="text-base font-bold text-white">{user?.full_name}</div>
            <div className="text-slate-400">{user?.email} | Role: {user?.role?.toUpperCase()}</div>
          </div>
        </div>

        <div>
          <label className="block text-slate-300 mb-1">Full Name</label>
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          />
        </div>

        <div>
          <label className="block text-slate-300 mb-1">Organization / Research Group</label>
          <input
            type="text"
            value={organization}
            onChange={(e) => setOrganization(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          />
        </div>

        <div>
          <label className="block text-slate-300 mb-1">Default Monitored City / Corridor</label>
          <input
            type="text"
            value={preferredCity}
            onChange={(e) => setPreferredCity(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          />
        </div>

        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Saving...' : 'Save Profile Changes'}</span>
        </button>
      </form>
    </div>
  );
};

export default UserProfile;

