import React, { useState, useEffect } from 'react';
import { Lightbulb, Sparkles, CheckCircle2, ShieldCheck } from 'lucide-react';
import api, { extractErrorMessage } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const AIInsights = () => {
  const { activeDatasetId } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [selectedDsId, setSelectedDsId] = useState(activeDatasetId || '');
  const [insightData, setInsightData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/datasets')
      .then((res) => {
        const list = res.data.datasets || [];
        setDatasets(list);
        const initId = activeDatasetId || (list[0] ? list[0].id : '');
        setSelectedDsId(initId);
        generateInsights(initId);
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const generateInsights = async (dsId) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/insights/generate', {
        dataset_id: dsId ? Number(dsId) : undefined,
      });
      setInsightData(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading && !insightData) return <LoadingSkeleton rows={5} label="Synthesizing evidence-backed AI insights..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Intelligent Insight & Recommendation Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Translates statistical trends, correlations, ML evaluation metrics, and risk alerts into plain-English insights with verifiable quantitative evidence.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedDsId}
            onChange={(e) => {
              const id = Number(e.target.value);
              setSelectedDsId(id);
              generateInsights(id);
            }}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          <button
            onClick={() => generateInsights(selectedDsId)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Regenerate Insights</span>
          </button>
        </div>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />

      {/* Insights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {(insightData?.insights || []).map((item, idx) => (
          <div key={idx} className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-0.5 rounded-full bg-sky-500/15 text-sky-400 text-[11px] font-semibold">
                {item.category}
              </span>
              <span className="text-[11px] text-emerald-400">Confidence: {item.confidence}</span>
            </div>

            <h3 className="text-sm font-bold text-slate-100 leading-snug">{item.headline}</h3>
            <p className="text-xs text-slate-400">{item.explanation}</p>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-xs">
              <div className="text-[10px] text-slate-400 uppercase font-semibold mb-1.5">
                Supporting Empirical Evidence:
              </div>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(item.evidence || {}).map(([k, v]) => (
                  <div key={k}>
                    <span className="text-slate-400">{k.replace(/_/g, ' ')}: </span>
                    <strong className="text-sky-300">{String(v)}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Actionable Urban Recommendations */}
      <div className="p-5 rounded-2xl border border-emerald-500/30 bg-slate-900/60 space-y-4">
        <h3 className="text-base font-bold text-emerald-400 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5" />
          <span>Actionable Urban Planning & Environmental Recommendations</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(insightData?.recommendations || []).map((rec, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sky-400">{rec.target_area}</span>
                <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 text-[10px] font-bold">
                  Priority: {rec.priority}
                </span>
              </div>
              <div className="text-slate-200 font-medium">{rec.recommendation}</div>
              <div className="text-[11px] text-slate-400">Rationale: {rec.rationale}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AIInsights;

