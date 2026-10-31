import React, { useState, useEffect } from 'react';
import { FileText, Download, PlusCircle } from 'lucide-react';
import api, { extractErrorMessage } from '../services/api';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const ReportCenter = () => {
  const [datasets, setDatasets] = useState([]);
  const [models, setModels] = useState([]);
  const [reports, setReports] = useState([]);

  const [title, setTitle] = useState('NagarNexus Comprehensive Urban Intelligence Report');
  const [reportType, setReportType] = useState('dataset');
  const [datasetId, setDatasetId] = useState('');
  const [modelId, setModelId] = useState('');
  const [notes, setNotes] = useState('');

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [dsRes, modRes, repRes] = await Promise.all([
        api.get('/datasets'),
        api.get('/ml/models'),
        api.get('/reports'),
      ]);
      const dsList = dsRes.data.datasets || [];
      const modList = modRes.data.models || [];
      setDatasets(dsList);
      setModels(modList);
      setReports(repRes.data.reports || []);
      if (dsList[0] && !datasetId) setDatasetId(dsList[0].id);
      if (modList[0] && !modelId) setModelId(modList[0].id);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setError('');
    setSuccess('');
    try {
      const res = await api.post('/reports/generate', {
        title,
        report_type: reportType,
        dataset_id: datasetId ? Number(datasetId) : undefined,
        model_id: modelId ? Number(modelId) : undefined,
        notes: notes || undefined,
      });
      setReports((prev) => [res.data, ...prev]);
      setSuccess(`Generated PDF & CSV report '${res.data.title}' (ID: ${res.data.summary_json?.report_uid}).`);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (rep, format = 'pdf') => {
    try {
      const res = await api.get(`/reports/${rep.id}/download`, {
        params: { format },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.setAttribute('download', `${rep.title.replace(/\s+/g, '_')}.${format}`);
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  if (loading && reports.length === 0) return <LoadingSkeleton rows={5} label="Loading Automated Report Center..." />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Automated Analytical Report Center</h1>
        <p className="text-xs text-slate-400 mt-1">
          Generate publication-ready PDF dossiers (with embedded charts, statistical results, ML metrics, risk analysis, and limitations) & CSV exports.
        </p>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />
      <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Report Builder Form */}
        <form
          onSubmit={handleGenerate}
          className="lg:col-span-5 p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4 text-xs"
        >
          <h3 className="text-sm font-bold text-sky-400 flex items-center gap-2">
            <PlusCircle className="w-4 h-4" />
            <span>Generate New PDF & CSV Report</span>
          </h3>

          <div>
            <label className="block text-slate-300 mb-1">Report Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            />
          </div>

          <div>
            <label className="block text-slate-300 mb-1">Report Category</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              <option value="dataset">Dataset Analysis Report</option>
              <option value="eda">Exploratory Data Analysis (EDA) Report</option>
              <option value="statistical">Statistical Hypothesis Report</option>
              <option value="ml">Machine Learning Evaluation Report</option>
              <option value="prediction">Predictive Forecast Report</option>
              <option value="comparison">Location Comparison Report</option>
              <option value="risk">Environmental Risk Assessment Report</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 mb-1">Source Dataset</label>
            <select
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 mb-1">Include Trained ML Model</label>
            <select
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>{m.model_name} (v{m.model_version})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 mb-1">Analyst Notes / Executive Commentary</label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional executive summary notes to embed in the PDF header..."
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            />
          </div>

          <button
            type="submit"
            disabled={generating}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-sky-400 to-blue-600 text-slate-950 font-bold transition"
          >
            {generating ? 'Compiling PDF Dossier & CSV...' : 'Generate Analytical Report'}
          </button>
        </form>

        {/* Generated Reports Archive */}
        <div className="lg:col-span-7 p-5 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-3">
          <h3 className="text-sm font-semibold">Generated Reports Archive ({reports.length})</h3>
          {reports.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">
              No reports generated yet. Use the form on the left to compile your first PDF & CSV analytical report.
            </div>
          ) : (
            <div className="space-y-3 max-h-[540px] overflow-y-auto pr-1">
              {reports.map((rep) => (
                <div
                  key={rep.id}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-sky-400" />
                      <span className="font-bold text-slate-100 text-sm">{rep.title}</span>
                    </div>
                    <div className="text-slate-400 mt-1">
                      ID: {rep.summary_json?.report_uid || `#${rep.id}`} | Type: {rep.report_type.toUpperCase()} |
                      Dataset: {rep.summary_json?.dataset_name}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Generated: {rep.created_at ? new Date(rep.created_at).toLocaleString() : ''}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDownload(rep, 'pdf')}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download PDF</span>
                    </button>
                    {rep.has_csv && (
                      <button
                        onClick={() => handleDownload(rep, 'csv')}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold"
                      >
                        <Download className="w-3.5 h-3.5 text-emerald-400" />
                        <span>CSV</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportCenter;

