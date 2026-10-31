import React, { useState, useEffect } from 'react';
import { Cpu, Play, CheckCircle2, Sparkles } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import api, { extractErrorMessage } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const MachineLearningLab = () => {
  const { activeDatasetId, setActiveDatasetId } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [algorithms, setAlgorithms] = useState([]);
  const [models, setModels] = useState([]);

  const [selectedDsId, setSelectedDsId] = useState(activeDatasetId || '');
  const [algorithm, setAlgorithm] = useState('random_forest_regressor');
  const [modelName, setModelName] = useState('');
  const [targetCol, setTargetCol] = useState('');
  const [featureCols, setFeatureCols] = useState([]);
  const [chronological, setChronological] = useState(false);
  const [testSize, setTestSize] = useState(0.2);
  const [nClusters, setNClusters] = useState(3);

  const [activeModel, setActiveModel] = useState(null);
  const [predInputs, setPredInputs] = useState({});
  const [predResult, setPredResult] = useState(null);

  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    Promise.all([api.get('/datasets'), api.get('/ml/algorithms'), api.get('/ml/models')])
      .then(([dsRes, algRes, modRes]) => {
        const dsList = dsRes.data.datasets || [];
        const algList = algRes.data.algorithms || [];
        const modList = modRes.data.models || [];
        setDatasets(dsList);
        setAlgorithms(algList);
        setModels(modList);

        const initDs = dsList.find((d) => d.id === activeDatasetId) || dsList[0];
        if (initDs) {
          configureDatasetColumns(initDs);
        }
        if (modList.length > 0) {
          selectTrainedModel(modList[0]);
        }
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const configureDatasetColumns = (ds) => {
    setSelectedDsId(ds.id);
    setActiveDatasetId(ds.id);
    const numCols = ds.profile_json?.numerical_columns || [];
    if (numCols.length >= 2) {
      setTargetCol(numCols[0]);
      setFeatureCols(numCols.slice(1));
    } else if (numCols.length === 1) {
      setTargetCol(numCols[0]);
      setFeatureCols(numCols);
    }
  };

  const selectTrainedModel = (m) => {
    setActiveModel(m);
    setPredResult(null);
    const initInputs = {};
    (m.feature_columns || []).forEach((f) => {
      initInputs[f] = 30.0;
    });
    setPredInputs(initInputs);
  };

  const toggleFeature = (col) => {
    setFeatureCols((prev) =>
      prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]
    );
  };

  const handleTrainModel = async (e) => {
    e.preventDefault();
    setTraining(true);
    setError('');
    setSuccess('');
    try {
      const res = await api.post('/ml/train', {
        dataset_id: Number(selectedDsId),
        model_name: modelName || undefined,
        algorithm,
        feature_columns: featureCols,
        target_column: targetCol || undefined,
        test_size: Number(testSize),
        chronological_split: chronological,
        n_clusters: Number(nClusters),
      });
      const newMod = res.data;
      setModels((prev) => [newMod, ...prev]);
      selectTrainedModel(newMod);
      setSuccess(`Trained and verified model '${newMod.model_name}' (v${newMod.model_version}).`);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setTraining(false);
    }
  };

  const handleQuickPredict = async (e) => {
    e.preventDefault();
    if (!activeModel) return;
    setError('');
    try {
      const res = await api.post(`/ml/models/${activeModel.id}/predict`, {
        features: predInputs,
      });
      setPredResult(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  if (loading) return <LoadingSkeleton rows={6} label="Initializing Machine Learning Lab..." />;

  const currentDs = datasets.find((d) => d.id === Number(selectedDsId));
  const availableCols = (currentDs?.columns || []).map((c) => c.column_name);
  const currentAlgMeta = algorithms.find((a) => a.id === algorithm);
  const metrics = activeModel?.metrics_json || {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Interactive Machine Learning Laboratory</h1>
        <p className="text-xs text-slate-400 mt-1">
          Leak-free train/test pipelines for Regression, Classification, K-Means Clustering, and Isolation Forest Anomaly Detection.
        </p>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />
      <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Model Configuration & Training Form */}
        <form
          onSubmit={handleTrainModel}
          className="lg:col-span-5 p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4 text-xs"
        >
          <h3 className="text-sm font-bold text-sky-400 flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            <span>Configure & Train New ML Model</span>
          </h3>

          <div>
            <label className="block text-slate-300 mb-1">1. Select Dataset</label>
            <select
              value={selectedDsId}
              onChange={(e) => {
                const ds = datasets.find((d) => d.id === Number(e.target.value));
                if (ds) configureDatasetColumns(ds);
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>{d.name} ({d.row_count} rows)</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 mb-1">2. Select Algorithm</label>
            <select
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              {algorithms.map((a) => (
                <option key={a.id} value={a.id}>
                  [{a.category.toUpperCase()}] {a.name}
                </option>
              ))}
            </select>
            {currentAlgMeta && (
              <p className="text-[11px] text-slate-400 mt-1">{currentAlgMeta.description}</p>
            )}
          </div>

          {currentAlgMeta?.requires_target && (
            <div>
              <label className="block text-slate-300 mb-1">3. Target Column (y)</label>
              <select
                value={targetCol}
                onChange={(e) => setTargetCol(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
              >
                {availableCols.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-slate-300 mb-1">4. Feature Columns (X)</label>
            <div className="grid grid-cols-2 gap-1.5 max-h-36 overflow-y-auto p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              {availableCols
                .filter((c) => !currentAlgMeta?.requires_target || c !== targetCol)
                .map((col) => (
                  <label key={col} className="flex items-center gap-1.5 text-slate-300 cursor-pointer truncate">
                    <input
                      type="checkbox"
                      checked={featureCols.includes(col)}
                      onChange={() => toggleFeature(col)}
                    />
                    <span className="truncate">{col}</span>
                  </label>
                ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 mb-1">Holdout Test Split</label>
              <select
                value={testSize}
                onChange={(e) => setTestSize(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
              >
                <option value={0.15}>15% Test / 85% Train</option>
                <option value={0.2}>20% Test / 80% Train</option>
                <option value={0.3}>30% Test / 70% Train</option>
              </select>
            </div>
            {algorithm === 'kmeans' ? (
              <div>
                <label className="block text-slate-300 mb-1">Clusters (k)</label>
                <input
                  type="number"
                  min={2}
                  max={10}
                  value={nClusters}
                  onChange={(e) => setNClusters(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
                />
              </div>
            ) : (
              <div>
                <label className="block text-slate-300 mb-1">Custom Model Name</label>
                <input
                  type="text"
                  placeholder="Optional label"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
                />
              </div>
            )}
          </div>

          <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={chronological}
              onChange={(e) => setChronological(e.target.checked)}
            />
            <span>Preserve chronological time-series order during train/test split</span>
          </label>

          <button
            type="submit"
            disabled={training || featureCols.length === 0}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-sky-400 to-blue-600 text-slate-950 font-bold text-xs shadow-lg transition"
          >
            {training ? 'Training & Validating Pipeline...' : 'Train & Evaluate Model'}
          </button>
        </form>

        {/* Right: Evaluation Metrics, Visualizations & Live Inference */}
        <div className="lg:col-span-7 space-y-6">
          {/* Trained Model Selector */}
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/50 flex flex-wrap items-center justify-between gap-3">
            <span className="text-xs font-semibold text-slate-300">
              Trained Model Registry ({models.length} saved models):
            </span>
            <select
              value={activeModel?.id || ''}
              onChange={(e) => {
                const m = models.find((mod) => mod.id === Number(e.target.value));
                if (m) selectTrainedModel(m);
              }}
              className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-sky-400 font-semibold"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.model_name} (v{m.model_version} — {m.algorithm})
                </option>
              ))}
            </select>
          </div>

          {activeModel && (
            <>
              {/* Evaluation Metrics Display */}
              <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-bold text-white">{activeModel.model_name}</h3>
                    <p className="text-xs text-slate-400">
                      Algorithm: {activeModel.algorithm} | Version: {activeModel.model_version} | Task: {activeModel.model_type}
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-400 text-xs font-semibold">
                    Verified & Reloadable
                  </span>
                </div>

                {/* Regression Metrics */}
                {(activeModel.model_type === 'regression' || activeModel.model_type === 'time_series') && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">MAE</span>
                      <div className="text-lg font-bold text-sky-400 mt-0.5">{metrics.MAE}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">MSE</span>
                      <div className="text-lg font-bold text-slate-200 mt-0.5">{metrics.MSE}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">RMSE</span>
                      <div className="text-lg font-bold text-amber-400 mt-0.5">{metrics.RMSE}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">R² Score</span>
                      <div className="text-lg font-bold text-emerald-400 mt-0.5">{metrics.R2_score}</div>
                    </div>
                  </div>
                )}

                {/* Classification Metrics */}
                {activeModel.model_type === 'classification' && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-slate-400">Accuracy</span>
                        <div className="text-lg font-bold text-emerald-400 mt-0.5">{(metrics.accuracy * 100).toFixed(1)}%</div>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-slate-400">Precision</span>
                        <div className="text-lg font-bold text-sky-400 mt-0.5">{(metrics.precision * 100).toFixed(1)}%</div>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-slate-400">Recall</span>
                        <div className="text-lg font-bold text-amber-400 mt-0.5">{(metrics.recall * 100).toFixed(1)}%</div>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-slate-400">F1-Score</span>
                        <div className="text-lg font-bold text-indigo-400 mt-0.5">{(metrics.f1_score * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                    {metrics.confusion_matrix && (
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                        <div className="font-semibold text-slate-300 mb-2">
                          Confusion Matrix (Classes: {(metrics.classes || []).join(', ')})
                        </div>
                        <div className="space-y-1 font-mono">
                          {metrics.confusion_matrix.map((row, rIdx) => (
                            <div key={rIdx} className="flex gap-3">
                              <span className="w-24 text-slate-400">{metrics.classes?.[rIdx] || `Class ${rIdx}`}:</span>
                              <span>[{row.join(', ')}]</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Clustering Metrics */}
                {activeModel.model_type === 'clustering' && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-3 text-xs">
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-slate-400">Clusters (k)</span>
                        <div className="text-lg font-bold text-sky-400 mt-0.5">{metrics.n_clusters}</div>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-slate-400">Silhouette Score</span>
                        <div className="text-lg font-bold text-emerald-400 mt-0.5">{metrics.silhouette_score}</div>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                        <span className="text-slate-400">Inertia</span>
                        <div className="text-lg font-bold text-slate-200 mt-0.5">{metrics.inertia}</div>
                      </div>
                    </div>
                    {metrics.pca_scatter && (
                      <div className="h-52">
                        <ResponsiveContainer width="100%" height="100%">
                          <ScatterChart>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="pc1" name="PC1" stroke="#94a3b8" fontSize={11} />
                            <YAxis dataKey="pc2" name="PC2" stroke="#94a3b8" fontSize={11} />
                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                            <Scatter data={metrics.pca_scatter} fill="#38bdf8" />
                          </ScatterChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>
                )}

                {/* Anomaly Detection Metrics */}
                {activeModel.model_type === 'anomaly_detection' && (
                  <div className="grid grid-cols-3 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">Anomalies Flagged</span>
                      <div className="text-lg font-bold text-rose-400 mt-0.5">{metrics.anomaly_count}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">Normal Observations</span>
                      <div className="text-lg font-bold text-emerald-400 mt-0.5">{metrics.normal_count}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">Anomaly Share</span>
                      <div className="text-lg font-bold text-amber-400 mt-0.5">{metrics.anomaly_ratio_pct}%</div>
                    </div>
                  </div>
                )}

                {/* Validation Actual vs Predicted Chart */}
                {metrics.validation_predictions && (
                  <div className="h-52 pt-2">
                    <div className="text-xs text-slate-400 mb-1">Holdout Validation: Actual vs Predicted</div>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={metrics.validation_predictions}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="index" stroke="#94a3b8" fontSize={10} />
                        <YAxis stroke="#94a3b8" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                        <Line type="monotone" dataKey="actual" name="Actual" stroke="#38bdf8" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="predicted" name="Predicted" stroke="#f59e0b" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Instant Model Prediction Sandbox */}
              <form
                onSubmit={handleQuickPredict}
                className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-4 text-xs"
              >
                <h3 className="text-sm font-semibold text-sky-400">Test Prediction Using Selected Model</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {(activeModel.feature_columns || []).map((col) => (
                    <div key={col}>
                      <label className="block text-slate-400 mb-1">{col}</label>
                      <input
                        type="text"
                        value={predInputs[col] ?? ''}
                        onChange={(e) => setPredInputs({ ...predInputs, [col]: e.target.value })}
                        className="w-full px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white"
                      />
                    </div>
                  ))}
                </div>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold transition"
                >
                  Run Model Inference
                </button>

                {predResult && (
                  <div className="p-4 rounded-xl bg-sky-950/40 border border-sky-500/30 flex items-center justify-between">
                    <div>
                      <div className="text-slate-400">Predicted Output ({activeModel.target_column || activeModel.model_type}):</div>
                      <div className="text-2xl font-bold text-sky-400 mt-0.5">{predResult.predicted_value}</div>
                    </div>
                    {predResult.confidence_metadata?.confidence_interval_95 && (
                      <div className="text-right text-slate-300">
                        <div>95% Confidence Interval:</div>
                        <div className="font-mono font-semibold text-emerald-400">
                          [{predResult.confidence_metadata.confidence_interval_95.join(' , ')}]
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default MachineLearningLab;

