import React, { useState, useEffect } from 'react';
import { Sigma, Play } from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import api, { extractErrorMessage } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const StatisticalAnalysis = () => {
  const { activeDatasetId, setActiveDatasetId } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [selectedId, setSelectedId] = useState(activeDatasetId || '');
  const [numCols, setNumCols] = useState([]);
  const [targetCol, setTargetCol] = useState('');
  const [compCol, setCompCol] = useState('');
  const [confidenceLevel, setConfidenceLevel] = useState(0.95);
  const [hypothesisTest, setHypothesisTest] = useState('auto');
  const [statsResult, setStatsResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/datasets')
      .then((res) => {
        const list = res.data.datasets || [];
        setDatasets(list);
        const initDs = list.find((d) => d.id === activeDatasetId) || list[0];
        if (initDs) {
          setSelectedId(initDs.id);
          const cols = initDs.profile_json?.numerical_columns || [];
          setNumCols(cols);
          const tCol = cols[0] || '';
          const cCol = cols[1] || tCol;
          setTargetCol(tCol);
          setCompCol(cCol);
          if (tCol) runCalculation(initDs.id, tCol, cCol, 0.95, 'auto');
        }
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const runCalculation = async (dsId, tCol, cCol, conf, hTest) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post(`/statistics/${dsId}/calculate`, {
        target_column: tCol,
        comparison_column: cCol,
        confidence_level: Number(conf),
        hypothesis_test: hTest,
      });
      setStatsResult(res.data.results);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDatasetChange = (id) => {
    setSelectedId(id);
    setActiveDatasetId(id);
    const ds = datasets.find((d) => d.id === id);
    const cols = ds?.profile_json?.numerical_columns || [];
    setNumCols(cols);
    const tCol = cols[0] || '';
    const cCol = cols[1] || tCol;
    setTargetCol(tCol);
    setCompCol(cCol);
    if (tCol) runCalculation(id, tCol, cCol, confidenceLevel, hypothesisTest);
  };

  if (loading && !statsResult) return <LoadingSkeleton rows={6} label="Running SciPy & Statsmodels Statistical Engine..." />;

  const sections = statsResult
    ? [
        statsResult.Descriptive_Statistics,
        statsResult.Normal_Distribution,
        statsResult.Z_Score_Analysis,
        statsResult.Correlation_And_Covariance,
        statsResult.Hypothesis_Testing,
        statsResult.Confidence_Intervals,
        statsResult.Outlier_Detection,
        statsResult.Trend_Analysis,
      ].filter(Boolean)
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Statistical Analysis & Hypothesis Testing</h1>
        <p className="text-xs text-slate-400 mt-1">
          Every test includes mathematical formula, calculated values, formal statistical interpretation, and plain-English explanation.
        </p>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />

      {/* Control Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          runCalculation(selectedId, targetCol, compCol, confidenceLevel, hypothesisTest);
        }}
        className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 items-end text-xs"
      >
        <div>
          <label className="block text-slate-400 mb-1">Dataset</label>
          <select
            value={selectedId}
            onChange={(e) => handleDatasetChange(Number(e.target.value))}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1">Target Variable (X)</label>
          <select
            value={targetCol}
            onChange={(e) => setTargetCol(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          >
            {numCols.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1">Comparison Variable (Y)</label>
          <select
            value={compCol}
            onChange={(e) => setCompCol(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          >
            {numCols.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1">Confidence Level</label>
          <select
            value={confidenceLevel}
            onChange={(e) => setConfidenceLevel(Number(e.target.value))}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          >
            <option value={0.9}>90% (α = 0.10)</option>
            <option value={0.95}>95% (α = 0.05)</option>
            <option value={0.99}>99% (α = 0.01)</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1">Hypothesis Test</label>
          <select
            value={hypothesisTest}
            onChange={(e) => setHypothesisTest(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
          >
            <option value="auto">Auto-Select Based on Normality</option>
            <option value="t_test_ind">Welch Two-Sample t-Test</option>
            <option value="mann_whitney">Mann-Whitney U Non-Parametric</option>
            <option value="t_test_1samp">One-Sample t-Test</option>
          </select>
        </div>

        <button
          type="submit"
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold"
        >
          <Play className="w-3.5 h-3.5" />
          <span>Calculate</span>
        </button>
      </form>

      {/* Visualizations for Normal Fit & OLS Trend */}
      {statsResult && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
            <h3 className="text-sm font-semibold mb-1">Empirical Density vs Fitted Normal Distribution</h3>
            <p className="text-xs text-slate-400 mb-3">Target: {statsResult.target_column}</p>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={statsResult.Normal_Distribution?.visualization_data || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="x" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="empirical_density" name="Observed Density" fill="#0284c7" fillOpacity={0.5} />
                  <Line type="monotone" dataKey="normal_pdf" name="Gaussian PDF" stroke="#f59e0b" strokeWidth={2.5} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
            <h3 className="text-sm font-semibold mb-1">OLS Linear Regression Trend Line</h3>
            <p className="text-xs text-slate-400 mb-3">Actual observations vs Statsmodels OLS fitted trend</p>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={statsResult.Trend_Analysis?.visualization_data || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="step" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="actual" name="Observed" stroke="#38bdf8" strokeWidth={1.5} dot={false} />
                  <Line type="monotone" dataKey="trend_line" name="OLS Trend" stroke="#10b981" strokeWidth={2.5} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Statistical Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {sections.map((sec, idx) => (
          <div key={idx} className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-sky-400">{sec.title}</h3>
              <Sigma className="w-4 h-4 text-slate-500" />
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 font-mono text-xs text-amber-300">
              Formula: {sec.formula}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              {Object.entries(sec.calculated_value || {}).map(([k, v]) => (
                <div key={k} className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">{k.replace(/_/g, ' ')}</div>
                  <div className="font-semibold text-slate-200 mt-0.5 truncate">
                    {Array.isArray(v) ? v.join(', ') : String(v)}
                  </div>
                </div>
              ))}
            </div>

            <div className="text-xs space-y-1.5 pt-2 border-t border-slate-800/70">
              <div>
                <span className="font-semibold text-slate-300">Statistical Interpretation: </span>
                <span className="text-slate-400">{sec.interpretation}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-200">
                <span className="font-semibold">In Simple English: </span>
                {sec.simple_english}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatisticalAnalysis;

