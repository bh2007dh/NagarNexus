import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldAlert, Play, Filter } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import api, { extractErrorMessage } from '../services/api';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const LEVEL_BADGE = {
  Low: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  Moderate: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  High: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  Critical: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
};

const LEVEL_COLORS = {
  Low: '#10b981',
  Moderate: '#f59e0b',
  High: '#f97316',
  Critical: '#ef4444',
};

const RiskDetection = () => {
  const [datasets, setDatasets] = useState([]);
  const [locations, setLocations] = useState([]);
  const [selectedDsId, setSelectedDsId] = useState('');
  const [selectedLocId, setSelectedLocId] = useState('');
  const [useIsoForest, setUseIsoForest] = useState(true);
  const [riskFilter, setRiskFilter] = useState('all');
  const [riskData, setRiskData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([api.get('/datasets'), api.get('/locations/search'), api.get('/risk/alerts')])
      .then(([dsRes, locRes, alertRes]) => {
        setDatasets(dsRes.data.datasets || []);
        setLocations(locRes.data.locations || []);
        setRiskData(alertRes.data);
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const handleRunRiskEngine = async (e) => {
    e.preventDefault();
    setAnalyzing(true);
    setError('');
    try {
      const res = await api.post('/risk/analyze', {
        dataset_id: selectedDsId ? Number(selectedDsId) : undefined,
        location_id: selectedLocId ? Number(selectedLocId) : undefined,
        use_isolation_forest: useIsoForest,
        contamination: 0.05,
      });
      setRiskData(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading && !riskData) return <LoadingSkeleton rows={5} label="Loading Urban Risk Detection Engine..." />;

  const alerts = (riskData?.alerts || []).filter(
    (a) => riskFilter === 'all' || a.risk_level === riskFilter
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Urban Environmental Risk & Anomaly Detection</h1>
        <p className="text-xs text-slate-400 mt-1">
          Detects extreme heat, particulate pollution spikes, abnormal rainfall, waterlogging indicators, and Isolation Forest multivariate anomalies.
        </p>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />

      {/* Risk Scanner Controls */}
      <form
        onSubmit={handleRunRiskEngine}
        className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end text-xs"
      >
        <div>
          <label className="block text-slate-400 mb-1">Target Dataset</label>
          <select
            value={selectedDsId}
            onChange={(e) => setSelectedDsId(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          >
            <option value="">All Stored Telemetry</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1">Target Locality</label>
          <select
            value={selectedLocId}
            onChange={(e) => setSelectedLocId(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          >
            <option value="">All Monitored Localities</option>
            {locations.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1">Filter by Severity</label>
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          >
            <option value="all">All Risk Tiers</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Moderate">Moderate</option>
            <option value="Low">Low</option>
          </select>
        </div>

        <label className="flex items-center gap-2 text-slate-300 cursor-pointer pb-2">
          <input
            type="checkbox"
            checked={useIsoForest}
            onChange={(e) => setUseIsoForest(e.target.checked)}
          />
          <span>Include Isolation Forest ML</span>
        </label>

        <button
          type="submit"
          disabled={analyzing}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold"
        >
          <Play className="w-3.5 h-3.5" />
          <span>{analyzing ? 'Scanning...' : 'Run Risk Scan'}</span>
        </button>
      </form>

      {/* Risk Summary Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-3">Detected Risk Level Distribution</h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData?.risk_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="level" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {(riskData?.risk_distribution || []).map((entry, idx) => (
                    <Cell key={idx} fill={LEVEL_COLORS[entry.level] || '#38bdf8'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[11px] text-slate-400 mt-3 italic">
            Disclaimer: Thresholds combine CPCB/WHO/IMD reference guidelines with labeled project experimental thresholds.
            Estimated risk alerts are analytical indicators, not verified emergency declarations.
          </p>
        </div>

        {/* Alerts List */}
        <div className="lg:col-span-7 space-y-3 max-h-[520px] overflow-y-auto pr-1">
          {alerts.map((alert, idx) => (
            <div
              key={idx}
              className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-2 text-xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2.5 py-0.5 rounded-full border font-bold text-[11px] ${
                      LEVEL_BADGE[alert.risk_level] || LEVEL_BADGE.Moderate
                    }`}
                  >
                    {alert.risk_level.toUpperCase()}
                  </span>
                  <span className="font-bold text-slate-100 text-sm">{alert.risk_category}</span>
                </div>
                <span className="text-slate-400">{alert.location}</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                <div>
                  <span className="text-slate-400">Indicator: </span>
                  <strong className="text-sky-400">{alert.indicator}</strong>
                </div>
                <div>
                  <span className="text-slate-400">Measured: </span>
                  <strong className="text-white">
                    {alert.measured_value} {alert.unit}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-400">Threshold: </span>
                  <strong className="text-amber-300">
                    {alert.threshold} {alert.unit}
                  </strong>
                </div>
              </div>

              <div className="text-slate-300">{alert.reason}</div>
              <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-200">
                <strong>Suggested Action: </strong> {alert.suggested_action}
              </div>
              <div className="flex flex-wrap items-center justify-between text-[10px] text-slate-500 pt-1">
                <span>Reference: {alert.threshold_reference}</span>
                <span>Source: {alert.data_source}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RiskDetection;

