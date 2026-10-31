import React, { useState, useEffect } from 'react';
import { GitCompare, Play } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import api, { extractErrorMessage } from '../services/api';
import UrbanLeafletMap from '../maps/UrbanLeafletMap';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const LocationComparison = () => {
  const [locations, setLocations] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [compResult, setCompResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/locations/search')
      .then((res) => {
        const list = res.data.locations || [];
        setLocations(list);
        if (list.length >= 2) {
          const initialIds = [list[0].id, list[1].id, ...(list[2] ? [list[2].id] : [])];
          setSelectedIds(initialIds);
          runComparison(initialIds);
        }
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const runComparison = async (ids) => {
    if (ids.length < 2) {
      setError('Please select at least 2 locations to compare.');
      return;
    }
    setError('');
    try {
      const res = await api.post('/comparison/run', { location_ids: ids });
      setCompResult(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const toggleLoc = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  if (loading && !compResult) return <LoadingSkeleton rows={5} label="Comparing multi-locality telemetry..." />;

  const comparedLocations = locations.filter((l) => selectedIds.includes(l.id));
  const table = compResult?.comparison_table || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Multi-Locality Comparison Engine</h1>
        <p className="text-xs text-slate-400 mt-1">
          Compare temperature, rainfall, humidity, air quality indicators, historical shifts, and projections across compatible urban zones.
        </p>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />

      {/* Location Selector */}
      <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-semibold text-slate-300">
            Select 2 or more locations to compare ({selectedIds.length} selected):
          </span>
          <button
            onClick={() => runComparison(selectedIds)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Compare Selected Localities</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5 text-xs">
          {locations.map((loc) => {
            const active = selectedIds.includes(loc.id);
            return (
              <label
                key={loc.id}
                className={`p-3 rounded-xl border cursor-pointer transition flex items-start gap-2 ${
                  active
                    ? 'bg-sky-500/15 border-sky-500/50 text-sky-200'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400'
                }`}
              >
                <input
                  type="checkbox"
                  checked={active}
                  onChange={() => toggleLoc(loc.id)}
                  className="mt-0.5"
                />
                <div className="truncate">
                  <div className="font-semibold truncate">{loc.name}</div>
                  <div className="text-[10px] opacity-80">{loc.geographical_resolution}</div>
                </div>
              </label>
            );
          })}
        </div>
      </div>

      {/* Compatibility Notice */}
      {compResult?.compatibility_check && (
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-sky-300">
          <strong>Resolution & Unit Compatibility Check:</strong> {compResult.compatibility_check.note}
        </div>
      )}

      {/* Map + Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <UrbanLeafletMap locations={comparedLocations} zoom={11} />
        </div>

        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-3">PM2.5 & Temperature Comparison Across Localities</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={compResult?.indicator_charts?.pm25 || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="location" stroke="#94a3b8" fontSize={10} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="average" name="Average PM2.5 (µg/m³)" fill="#f59e0b" />
                <Bar dataKey="projected" name="Projected Next Step" fill="#38bdf8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Side-by-Side Comparison Matrix Table */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
        <h3 className="text-sm font-semibold mb-3">Side-by-Side Locality Telemetry Matrix</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2 px-3">Locality Name</th>
                <th className="py-2 px-3">Resolution</th>
                <th className="py-2 px-3">Avg Temp (°C)</th>
                <th className="py-2 px-3">Avg Rainfall (mm)</th>
                <th className="py-2 px-3">Avg Humidity (%)</th>
                <th className="py-2 px-3">Avg PM2.5 (µg/m³)</th>
                <th className="py-2 px-3">Avg AQI</th>
                <th className="py-2 px-3">Risk Alerts</th>
              </tr>
            </thead>
            <tbody>
              {table.map((row) => (
                <tr key={row.location_id} className="border-b border-slate-800/60 hover:bg-slate-800/30">
                  <td className="py-2.5 px-3 font-bold text-slate-100">{row.name}</td>
                  <td className="py-2.5 px-3 text-slate-400">{row.geographical_resolution}</td>
                  <td className="py-2.5 px-3 text-sky-400 font-semibold">
                    {row.indicators?.temperature_c?.average ?? 'N/A'}
                  </td>
                  <td className="py-2.5 px-3">
                    {row.indicators?.rainfall_mm?.average ?? 'N/A'}
                  </td>
                  <td className="py-2.5 px-3">
                    {row.indicators?.humidity_pct?.average ?? 'N/A'}
                  </td>
                  <td className="py-2.5 px-3 text-amber-400 font-semibold">
                    {row.indicators?.pm25?.average ?? 'N/A'}
                  </td>
                  <td className="py-2.5 px-3">
                    {row.indicators?.aqi?.average ?? 'N/A'}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-300 font-semibold">
                      {row.risk_alert_count}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LocationComparison;

