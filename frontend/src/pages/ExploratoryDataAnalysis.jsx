import React, { useState, useEffect } from 'react';
import { BarChart3, Download, Play } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
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
import { useAuth } from '../context/AuthContext';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const COLORS = ['#38bdf8', '#f59e0b', '#10b981', '#6366f1', '#ec4899', '#f97316', '#14b8a6'];

const ExploratoryDataAnalysis = () => {
  const { activeDatasetId, setActiveDatasetId } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [selectedId, setSelectedId] = useState(activeDatasetId || '');
  const [eda, setEda] = useState(null);
  const [viz, setViz] = useState(null);

  // Interactive Chart Builder Controls
  const [chartType, setChartType] = useState('histogram');
  const [xCol, setXCol] = useState('');
  const [yCol, setYCol] = useState('');
  const [bins, setBins] = useState(15);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/datasets')
      .then((res) => {
        const list = res.data.datasets || [];
        setDatasets(list);
        const initId = activeDatasetId || (list[0] ? list[0].id : '');
        if (initId) {
          setSelectedId(initId);
          runEDA(initId);
        }
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const runEDA = async (id) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post(`/eda/${id}/run`);
      const edaData = res.data.eda;
      setEda(edaData);
      const numCols = edaData.overview?.numerical_columns || [];
      const firstX = numCols[0] || '';
      const secondY = numCols[1] || firstX;
      setXCol(firstX);
      setYCol(secondY);
      if (firstX) {
        const vizRes = await api.post(`/eda/${id}/visualization`, {
          chart_type: 'histogram',
          x_column: firstX,
          y_column: secondY,
          bins: 15,
        });
        setViz(vizRes.data);
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateChart = async (e) => {
    if (e) e.preventDefault();
    if (!selectedId) return;
    setError('');
    try {
      const res = await api.post(`/eda/${selectedId}/visualization`, {
        chart_type: chartType,
        x_column: xCol,
        y_column: yCol,
        bins: Number(bins),
      });
      setViz(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const handleExportEDAJson = () => {
    if (!eda) return;
    const blob = new Blob([JSON.stringify(eda, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `eda_results_dataset_${selectedId}.json`;
    a.click();
  };

  const handleDownloadChartPng = () => {
    if (!viz?.matplotlib_image) return;
    const a = document.createElement('a');
    a.href = viz.matplotlib_image;
    a.download = `nagarnexus_${chartType}_${xCol}.png`;
    a.click();
  };

  if (loading && !eda) return <LoadingSkeleton rows={6} label="Running Pandas, NumPy, Matplotlib & Seaborn EDA Engine..." />;

  const allCols = [
    ...(eda?.overview?.numerical_columns || []),
    ...(eda?.overview?.categorical_columns || []),
  ];
  const descStats = eda?.descriptive_statistics || {};

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Automated Exploratory Data Analysis (EDA)</h1>
          <p className="text-xs text-slate-400 mt-1">
            Descriptive statistics, quartiles, IQR, correlation & covariance matrices, outlier analysis, and dual Recharts + Matplotlib rendering.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedId}
            onChange={(e) => {
              const id = Number(e.target.value);
              setSelectedId(id);
              setActiveDatasetId(id);
              runEDA(id);
            }}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          <button
            onClick={handleExportEDAJson}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold"
          >
            <Download className="w-3.5 h-3.5 text-sky-400" />
            <span>Export EDA JSON</span>
          </button>
        </div>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />

      {/* Interactive Chart Studio */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4">
        <form onSubmit={handleGenerateChart} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end text-xs">
          <div>
            <label className="block text-slate-400 mb-1">Chart Type</label>
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              <option value="histogram">Histogram</option>
              <option value="distribution">Distribution + KDE</option>
              <option value="bar">Bar Chart</option>
              <option value="line">Line Chart</option>
              <option value="scatter">Scatter Plot</option>
              <option value="boxplot">Box Plot (Quartiles & Fences)</option>
              <option value="pie">Pie Chart</option>
              <option value="correlation_heatmap">Correlation Matrix Heatmap</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1">X-Axis Column</label>
            <select
              value={xCol}
              onChange={(e) => setXCol(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              {allCols.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Y-Axis Column</label>
            <select
              value={yCol}
              onChange={(e) => setYCol(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              {allCols.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Histogram Bins</label>
            <input
              type="number"
              min={5}
              max={50}
              value={bins}
              onChange={(e) => setBins(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            />
          </div>

          <button
            type="submit"
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold transition"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Generate Visualization</span>
          </button>
        </form>

        {viz && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-3">
            {/* Interactive Recharts View */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-xs font-semibold text-slate-300 mb-3">
                Interactive Chart ({viz.chart_type.toUpperCase()} — {viz.x_column})
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  {viz.chart_type === 'scatter' ? (
                    <ScatterChart>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="x" name={viz.x_column} stroke="#94a3b8" fontSize={11} />
                      <YAxis dataKey="y" name={viz.y_column} stroke="#94a3b8" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                      <Scatter data={viz.chart_data || []} fill="#38bdf8" />
                    </ScatterChart>
                  ) : viz.chart_type === 'line' ? (
                    <LineChart data={viz.chart_data || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="x" stroke="#94a3b8" fontSize={10} />
                      <YAxis stroke="#94a3b8" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                      <Line type="monotone" dataKey="y" stroke="#38bdf8" strokeWidth={2} dot={false} />
                    </LineChart>
                  ) : viz.chart_type === 'pie' ? (
                    <PieChart>
                      <Pie data={viz.chart_data || []} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                        {(viz.chart_data || []).map((_, idx) => (
                          <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  ) : (
                    <BarChart data={viz.chart_data || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey={viz.chart_data?.[0]?.bin ? 'bin' : 'name'} stroke="#94a3b8" fontSize={10} />
                      <YAxis stroke="#94a3b8" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                      <Bar dataKey={viz.chart_data?.[0]?.count !== undefined ? 'count' : 'value'} fill="#38bdf8" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
            </div>

            {/* Rendered Matplotlib/Seaborn High-DPI Figure */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-300">Matplotlib / Seaborn High-DPI Plot</span>
                <button
                  onClick={handleDownloadChartPng}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-500/20 text-sky-300 text-[11px] font-semibold"
                >
                  <Download className="w-3 h-3" /> Download PNG
                </button>
              </div>
              {viz.matplotlib_image && (
                <img
                  src={viz.matplotlib_image}
                  alt="Matplotlib EDA Plot"
                  className="w-full h-60 object-contain rounded-lg"
                />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Descriptive Statistics Table */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
        <h3 className="text-sm font-semibold mb-3">Comprehensive Descriptive Statistics</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2 px-3">Feature</th>
                <th className="py-2 px-3">Mean</th>
                <th className="py-2 px-3">Median</th>
                <th className="py-2 px-3">Mode</th>
                <th className="py-2 px-3">Std Dev</th>
                <th className="py-2 px-3">Variance</th>
                <th className="py-2 px-3">Min</th>
                <th className="py-2 px-3">Q1 (25%)</th>
                <th className="py-2 px-3">Q3 (75%)</th>
                <th className="py-2 px-3">IQR</th>
                <th className="py-2 px-3">Max</th>
                <th className="py-2 px-3">Skewness</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(descStats).map(([col, st]) => (
                <tr key={col} className="border-b border-slate-800/60 hover:bg-slate-800/30">
                  <td className="py-2 px-3 font-semibold text-sky-400">{col}</td>
                  <td className="py-2 px-3">{st.mean}</td>
                  <td className="py-2 px-3">{st.median}</td>
                  <td className="py-2 px-3">{st.mode}</td>
                  <td className="py-2 px-3">{st.std_dev}</td>
                  <td className="py-2 px-3">{st.variance}</td>
                  <td className="py-2 px-3">{st.min}</td>
                  <td className="py-2 px-3">{st.q1}</td>
                  <td className="py-2 px-3">{st.q3}</td>
                  <td className="py-2 px-3">{st.iqr}</td>
                  <td className="py-2 px-3">{st.max}</td>
                  <td className="py-2 px-3">{st.skewness}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Feature Correlations & Outlier Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-3">Top Feature Correlations & Covariances</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {(eda?.top_correlations || []).map((c, idx) => (
              <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                <div>
                  <span className="font-semibold text-slate-200">{c.feature_a}</span>
                  <span className="text-slate-500 mx-1.5">↔</span>
                  <span className="font-semibold text-slate-200">{c.feature_b}</span>
                </div>
                <div className="text-right">
                  <span className="text-sky-400 font-bold">r = {c.correlation}</span>
                  <span className="text-slate-400 ml-2">(Cov: {c.covariance})</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-sm font-semibold mb-3">Outlier Analysis (Tukey 1.5×IQR Fences)</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {(eda?.outlier_analysis || []).map((o, idx) => (
              <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                <div>
                  <div className="font-semibold text-slate-200">{o.column}</div>
                  <div className="text-[11px] text-slate-400">
                    Fences: [{o.lower_fence}, {o.upper_fence}]
                  </div>
                </div>
                <div className="text-right">
                  <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 font-semibold">
                    {o.outlier_count} outliers ({o.outlier_pct}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExploratoryDataAnalysis;

