import React, { useState, useEffect, useCallback } from 'react';
import {
  Database,
  FileSpreadsheet,
  MapPin,
  TrendingUp,
  AlertTriangle,
  ShieldAlert,
  RefreshCw,
  Filter,
  Activity,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import api, { extractErrorMessage } from '../services/api';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const RISK_COLORS = {
  Low: '#10b981',
  Moderate: '#f59e0b',
  High: '#f97316',
  Critical: '#ef4444',
};

const OverviewDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [locationId, setLocationId] = useState('');
  const [datasetId, setDatasetId] = useState('');
  const [indicator, setIndicator] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (locationId) params.location_id = locationId;
      if (datasetId) params.dataset_id = datasetId;
      if (indicator) params.indicator = indicator;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const [sumRes, actRes] = await Promise.all([
        api.get('/dashboard/summary', { params }),
        api.get('/dashboard/recent-activity?limit=10'),
      ]);
      setSummary(sumRes.data);
      setActivities(actRes.data.activities || []);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [locationId, datasetId, indicator, startDate, endDate]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  if (loading && !summary) {
    return <LoadingSkeleton rows={6} label="Synthesizing urban telemetry and ML metrics..." />;
  }

  const kpis = summary?.kpis || {};
  const charts = summary?.charts || {};
  const filters = summary?.available_filters || { locations: [], datasets: [], indicators: [] };

  const kpiCards = [
    {
      label: 'Uploaded & Sample Datasets',
      value: kpis.total_uploaded_datasets ?? 0,
      icon: Database,
      accent: 'text-sky-400 bg-sky-500/10 border-sky-500/30',
    },
    {
      label: 'Total Records Analyzed',
      value: (kpis.total_records_analyzed ?? 0).toLocaleString(),
      icon: FileSpreadsheet,
      accent: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
    },
    {
      label: 'Locations Monitored',
      value: kpis.total_locations_monitored ?? 0,
      icon: MapPin,
      accent: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    },
    {
      label: 'Predictions Generated',
      value: kpis.total_predictions_generated ?? 0,
      icon: TrendingUp,
      accent: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30',
    },
    {
      label: 'Detected Anomalies & Alerts',
      value: kpis.total_detected_anomalies ?? 0,
      icon: AlertTriangle,
      accent: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    },
    {
      label: 'High / Critical Risk Events',
      value: kpis.high_risk_observations ?? 0,
      icon: ShieldAlert,
      accent: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Urban Intelligence Overview Dashboard</h1>
          <p className="text-xs text-slate-400 mt-1">
            Live database metrics across pre-integrated urban benchmarks, user-uploaded datasets, and trained ML models.
          </p>
        </div>
        <button
          onClick={fetchDashboard}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs transition self-start"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
        <div>
          <label className="block text-[11px] text-slate-400 mb-1 flex items-center gap-1">
            <Filter className="w-3 h-3 text-sky-400" /> Location Filter
          </label>
          <select
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200"
          >
            <option value="">All Monitored Locations</option>
            {filters.locations.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Dataset Filter</label>
          <select
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200"
          >
            <option value="">All Datasets</option>
            {filters.datasets.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Environmental Indicator</label>
          <select
            value={indicator}
            onChange={(e) => setIndicator(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200"
          >
            <option value="">All Indicators</option>
            {filters.indicators.map((ind) => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200"
          />
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200"
          />
        </div>
      </div>

      {/* 6 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpiCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className="p-4 rounded-2xl border border-slate-800/90 bg-slate-900/50 flex flex-col justify-between hover:border-sky-500/40 transition"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-slate-400 font-medium">{card.label}</span>
                <div className={`p-2 rounded-xl border ${card.accent}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-bold tracking-tight">{card.value}</div>
            </div>
          );
        })}
      </div>

      {/* Charts Row 1: Temperature Trend & Air Quality Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-1">Surface Temperature Trend (°C)</h3>
          <p className="text-xs text-slate-400 mb-4">Historical thermal observations from monitored localities</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={charts.temperature_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timestamp" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                <Area type="monotone" dataKey="value" name="Temp (°C)" stroke="#38bdf8" fill="#0284c7" fillOpacity={0.25} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-1">Air Quality Particulate Trend (PM2.5 µg/m³)</h3>
          <p className="text-xs text-slate-400 mb-4">Fine particulate concentration across urban stations</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={charts.air_quality_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timestamp" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                <Line type="monotone" dataKey="value" name="PM2.5 (µg/m³)" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Charts Row 2: Rainfall Trend & Environmental Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-1">Precipitation & Rainfall Dynamics (mm)</h3>
          <p className="text-xs text-slate-400 mb-4">Daily rainfall accumulation across hydrological basins</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.rainfall_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timestamp" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                <Bar dataKey="value" name="Rainfall (mm)" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-1">Cross-Locality Environmental Comparison</h3>
          <p className="text-xs text-slate-400 mb-4">Mean Temperature (°C), PM2.5 (µg/m³), and Rainfall (mm) by zone</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.environmental_comparison || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="location" stroke="#94a3b8" fontSize={10} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="temperature_c" name="Temp (°C)" fill="#38bdf8" />
                <Bar dataKey="pm25" name="PM2.5 (µg/m³)" fill="#f59e0b" />
                <Bar dataKey="rainfall_mm" name="Rain (mm)" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Charts Row 3: Risk Distribution & Dataset Quality Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-1">Urban Risk Alert Distribution</h3>
          <p className="text-xs text-slate-400 mb-4">Breakdown of detected alerts by severity tier</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={charts.risk_distribution || []}
                  dataKey="count"
                  nameKey="level"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  label={({ level, count }) => `${level}: ${count}`}
                >
                  {(charts.risk_distribution || []).map((entry, index) => (
                    <Cell key={index} fill={RISK_COLORS[entry.level] || '#38bdf8'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-1">Dataset Quality & Volume Statistics</h3>
          <p className="text-xs text-slate-400 mb-4">Row counts and automated quality scores across platform datasets</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.dataset_statistics || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                <YAxis dataKey="name" type="category" width={150} stroke="#94a3b8" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="rows" name="Row Count" fill="#38bdf8" />
                <Bar dataKey="quality_score" name="Quality Score (%)" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row: Latest Predictions & Recent Activities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-3">Latest ML Prediction Results</h3>
          <div className="space-y-2.5">
            {(summary?.latest_predictions || []).map((pred) => (
              <div
                key={pred.id}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">{pred.model_name}</div>
                  <div className="text-slate-400">Category: {pred.category}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-sky-400">{pred.predicted_value}</div>
                  <div className="text-[10px] text-slate-500">
                    {pred.created_at ? new Date(pred.created_at).toLocaleString() : ''}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-sky-400" />
            <span>Recent Platform Analytical Activities</span>
          </h3>
          <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
            {activities.map((act) => (
              <div
                key={act.id}
                className="flex items-start justify-between gap-3 p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs"
              >
                <div>
                  <span className="inline-block px-2 py-0.5 rounded bg-sky-500/15 text-sky-400 font-semibold text-[10px] mr-2">
                    {act.activity_type}
                  </span>
                  <span className="text-slate-300">{act.description}</span>
                </div>
                <span className="text-[10px] text-slate-500 shrink-0">
                  {act.created_at ? new Date(act.created_at).toLocaleTimeString() : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverviewDashboard;

