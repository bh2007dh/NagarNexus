import React, { useState, useEffect } from 'react';
import { TrendingUp, Play, History } from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import api, { extractErrorMessage } from '../services/api';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const PredictiveAnalytics = () => {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [category, setCategory] = useState('temperature');
  const [inputs, setInputs] = useState({});
  const [actualObs, setActualObs] = useState('');
  const [horizonSteps, setHorizonSteps] = useState(7);
  const [predictionOutput, setPredictionOutput] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadModelsAndHistory = async () => {
    setLoading(true);
    try {
      const [modRes, histRes] = await Promise.all([
        api.get('/ml/models'),
        api.get('/predictions/history?limit=25'),
      ]);
      const modList = modRes.data.models || [];
      setModels(modList);
      setHistory(histRes.data.predictions || []);
      if (modList.length > 0 && !selectedModel) {
        handleSelectModel(modList[0]);
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSelectModel = (m) => {
    setSelectedModel(m);
    const defaults = {};
    (m.feature_columns || []).forEach((f) => {
      defaults[f] = 32.0;
    });
    setInputs(defaults);
  };

  const handleRunForecast = async (e) => {
    e.preventDefault();
    if (!selectedModel) return;
    setError('');
    try {
      const res = await api.post('/predictions/run', {
        model_id: selectedModel.id,
        category,
        features: inputs,
        actual_value: actualObs !== '' ? parseFloat(actualObs) : undefined,
        horizon_steps: Number(horizonSteps),
      });
      setPredictionOutput(res.data);
      const histRes = await api.get('/predictions/history?limit=25');
      setHistory(histRes.data.predictions || []);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  useEffect(() => {
    loadModelsAndHistory();
  }, []);

  if (loading && models.length === 0) {
    return <LoadingSkeleton rows={5} label="Loading Predictive Analytics Engine..." />;
  }

  const horizonSeries = predictionOutput?.confidence_metadata?.horizon_forecast || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Predictive Analytics & Multi-Step Forecasting</h1>
        <p className="text-xs text-slate-400 mt-1">
          Generate temperature, rainfall, air quality, and waterlogging risk predictions with uncertainty bounds and actual-vs-predicted verification.
        </p>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Prediction Configuration Form */}
        <form
          onSubmit={handleRunForecast}
          className="lg:col-span-5 p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4 text-xs"
        >
          <h3 className="text-sm font-bold text-sky-400">Configure Prediction Request</h3>

          <div>
            <label className="block text-slate-300 mb-1">Prediction Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              <option value="temperature">Temperature Forecast (°C)</option>
              <option value="rainfall">Rainfall & Precipitation (mm)</option>
              <option value="air_quality">Air Quality (PM2.5 / AQI)</option>
              <option value="environmental">Composite Environmental Indicator</option>
              <option value="waterlogging_risk">Waterlogging Risk (Requires Hydrological Features)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 mb-1">Select Trained Model</label>
            <select
              value={selectedModel?.id || ''}
              onChange={(e) => {
                const m = models.find((mod) => mod.id === Number(e.target.value));
                if (m) handleSelectModel(m);
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.model_name} (v{m.model_version})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {(selectedModel?.feature_columns || []).map((col) => (
              <div key={col}>
                <label className="block text-slate-400 mb-1">{col}</label>
                <input
                  type="text"
                  value={inputs[col] ?? ''}
                  onChange={(e) => setInputs({ ...inputs, [col]: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white"
                />
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-800">
            <div>
              <label className="block text-slate-400 mb-1">Actual Observation (Optional)</label>
              <input
                type="number"
                step="any"
                placeholder="Compare if known"
                value={actualObs}
                onChange={(e) => setActualObs(e.target.value)}
                className="w-full px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Forecast Horizon Steps</label>
              <input
                type="number"
                min={1}
                max={30}
                value={horizonSteps}
                onChange={(e) => setHorizonSteps(e.target.value)}
                className="w-full px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-sky-400 to-blue-600 text-slate-950 font-bold transition"
          >
            Generate Prediction & Horizon Forecast
          </button>
        </form>

        {/* Prediction Result & Horizon Chart */}
        <div className="lg:col-span-7 space-y-6">
          {predictionOutput ? (
            <div className="p-5 rounded-2xl border border-sky-500/30 bg-slate-900/60 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <span className="text-xs uppercase text-sky-400 font-semibold">{predictionOutput.category}</span>
                  <h3 className="text-xl font-bold text-white mt-0.5">
                    Predicted Value: <span className="text-sky-400">{predictionOutput.predicted_value}</span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Model: {predictionOutput.model_name} (v{predictionOutput.model_version}) |{' '}
                    {predictionOutput.created_at ? new Date(predictionOutput.created_at).toLocaleString() : ''}
                  </p>
                </div>

                {predictionOutput.confidence_metadata?.confidence_interval_95 && (
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                    <div className="text-slate-400">95% Uncertainty Interval</div>
                    <div className="font-mono font-bold text-emerald-400 mt-0.5">
                      [{predictionOutput.confidence_metadata.confidence_interval_95.join(' to ')}]
                    </div>
                  </div>
                )}
              </div>

              {predictionOutput.actual_value !== null && predictionOutput.actual_value !== undefined && (
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                  <span>Actual Observation: <strong>{predictionOutput.actual_value}</strong></span>
                  <span>
                    Absolute Error:{' '}
                    <strong className="text-amber-400">
                      {Math.abs(Number(predictionOutput.numeric_prediction) - Number(predictionOutput.actual_value)).toFixed(3)}
                    </strong>
                  </span>
                </div>
              )}

              {horizonSeries.length > 0 && (
                <div className="h-56 pt-2">
                  <div className="text-xs font-semibold text-slate-300 mb-2">
                    Multi-Step Horizon Projection with 95% Uncertainty Band
                  </div>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={horizonSeries}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} />
                      <YAxis stroke="#94a3b8" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Area type="monotone" dataKey="upper_bound" name="Upper 95% Bound" stroke="#0284c7" fill="#0284c7" fillOpacity={0.15} />
                      <Area type="monotone" dataKey="predicted" name="Projected Value" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.3} />
                      <Area type="monotone" dataKey="lower_bound" name="Lower 95% Bound" stroke="#64748b" fill="#0f172a" fillOpacity={0.1} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div className="text-[11px] text-slate-400 italic border-t border-slate-800 pt-2">
                Limitations: {predictionOutput.confidence_metadata?.limitations}
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-2xl border border-slate-800 bg-slate-900/40 text-center text-xs text-slate-400">
              Select a trained model and click "Generate Prediction & Horizon Forecast" to inspect projections and uncertainty intervals.
            </div>
          )}

          {/* Prediction History Table */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <History className="w-4 h-4 text-sky-400" />
              <span>Prediction Audit History ({history.length})</span>
            </h3>
            <div className="overflow-x-auto max-h-64">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2 px-3">Model (Version)</th>
                    <th className="py-2 px-3">Category</th>
                    <th className="py-2 px-3">Predicted</th>
                    <th className="py-2 px-3">Actual</th>
                    <th className="py-2 px-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id} className="border-b border-slate-800/60">
                      <td className="py-2 px-3 font-medium text-slate-200">
                        {h.model_name} (v{h.model_version})
                      </td>
                      <td className="py-2 px-3">{h.category}</td>
                      <td className="py-2 px-3 font-bold text-sky-400">{h.predicted_value}</td>
                      <td className="py-2 px-3">{h.actual_value ?? '—'}</td>
                      <td className="py-2 px-3 text-slate-400">
                        {h.created_at ? new Date(h.created_at).toLocaleString() : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictiveAnalytics;
