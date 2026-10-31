import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  Search,
  Download,
  Trash2,
  Eye,
  Sparkles,
  BarChart3,
  Cpu,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import api, { extractErrorMessage } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const DatasetExplorer = () => {
  const { setActiveDatasetId } = useAuth();
  const navigate = useNavigate();

  const [datasets, setDatasets] = useState([]);
  const [selectedDs, setSelectedDs] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const fetchDatasets = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/datasets', {
        params: { search: search || undefined, source_type: sourceFilter },
      });
      const list = res.data.datasets || [];
      setDatasets(list);
      if (list.length > 0 && !selectedDs) {
        inspectDataset(list[0]);
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const inspectDataset = async (ds) => {
    setSelectedDs(ds);
    setActiveDatasetId(ds.id);
    try {
      const [detailRes, prevRes] = await Promise.all([
        api.get(`/datasets/${ds.id}`),
        api.get(`/datasets/${ds.id}/preview?limit=25`),
      ]);
      setSelectedDs(detailRes.data);
      setPreviewData(prevRes.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setError('');
    setSuccess('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', file.name.replace(/\.[^/.]+$/, ''));
      const res = await api.post('/datasets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSuccess(`Uploaded and profiled '${res.data.name}' (${res.data.row_count} rows, Quality: ${res.data.quality_score}%).`);
      await fetchDatasets();
      inspectDataset(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (ds, version = 'active') => {
    try {
      const res = await api.get(`/datasets/${ds.id}/download`, {
        params: { version },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${ds.name}_${version}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/datasets/${id}`);
      setSuccess('Dataset deleted.');
      setConfirmDeleteId(null);
      setSelectedDs(null);
      setPreviewData(null);
      await fetchDatasets();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, [sourceFilter]);

  const profile = selectedDs?.profile_json || {};
  const dq = profile.data_quality || {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dataset Management & Automatic Profiler</h1>
        <p className="text-xs text-slate-400 mt-1">
          Upload CSV, XLSX, or XLS datasets with MIME/signature validation and automatic 12-point data quality profiling.
        </p>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />
      <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />

      {/* Drag and Drop Upload Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          if (e.dataTransfer.files?.[0]) handleFileUpload(e.dataTransfer.files[0]);
        }}
        className={`p-6 rounded-2xl border-2 border-dashed text-center transition ${
          dragActive ? 'border-sky-400 bg-sky-500/10' : 'border-slate-700 bg-slate-900/40'
        }`}
      >
        <UploadCloud className="w-10 h-10 text-sky-400 mx-auto mb-2" />
        <p className="text-sm font-semibold text-slate-200">
          {uploading ? 'Validating & profiling dataset...' : 'Drag & drop CSV, XLSX, or XLS dataset here'}
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Original uploaded file is preserved intact. Automatic row, column, missing value, duplicate, and outlier profiling runs immediately.
        </p>
        <label className="mt-3 inline-block px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs cursor-pointer transition">
          <span>Select File from Computer</span>
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
            className="hidden"
          />
        </label>
      </div>

      {/* Search & Filter Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search datasets by name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchDatasets()}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white"
            />
          </div>
          <button
            onClick={fetchDatasets}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold"
          >
            Search
          </button>
        </div>

        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200"
        >
          <option value="all">All Sources (Sample + User Uploads)</option>
          <option value="user_upload">My Uploaded Datasets</option>
          <option value="sample">Pre-Integrated Sample Datasets</option>
        </select>
      </div>

      {loading && datasets.length === 0 ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Dataset Catalog List */}
          <div className="lg:col-span-4 space-y-2.5 max-h-[680px] overflow-y-auto pr-1">
            {datasets.map((ds) => {
              const isSelected = selectedDs?.id === ds.id;
              return (
                <div
                  key={ds.id}
                  onClick={() => inspectDataset(ds)}
                  className={`p-4 rounded-2xl border cursor-pointer transition ${
                    isSelected
                      ? 'bg-sky-500/15 border-sky-500/50'
                      : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-xs font-bold text-slate-100">{ds.name}</h3>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] uppercase text-sky-400 font-semibold shrink-0">
                      {ds.file_type}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {ds.row_count} rows × {ds.column_count} cols | Quality: {ds.quality_score}%
                  </div>
                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/80 text-[11px]">
                    <span className="text-slate-400">Source: {ds.source_type}</span>
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleDownload(ds, 'original')}
                        title="Download Dataset"
                        className="p-1 text-sky-400 hover:bg-sky-500/10 rounded"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                      {ds.source_type === 'user_upload' && (
                        <button
                          onClick={() => setConfirmDeleteId(ds.id)}
                          title="Delete Dataset"
                          className="p-1 text-rose-400 hover:bg-rose-500/10 rounded"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  {confirmDeleteId === ds.id && (
                    <div
                      onClick={(e) => e.stopPropagation()}
                      className="mt-2 p-2 rounded-lg bg-rose-950/80 border border-rose-500/40 text-xs flex items-center justify-between"
                    >
                      <span>Confirm delete?</span>
                      <div className="space-x-2">
                        <button
                          onClick={() => handleDelete(ds.id)}
                          className="px-2 py-1 rounded bg-rose-500 text-white font-semibold"
                        >
                          Delete
                        </button>
                        <button
                          onClick={() => setConfirmDeleteId(null)}
                          className="px-2 py-1 rounded bg-slate-800 text-slate-300"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Selected Dataset Profile, Column Panel & Preview */}
          <div className="lg:col-span-8 space-y-6">
            {selectedDs && (
              <>
                {/* Profile Summary & Quick Launch Actions */}
                <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-lg font-bold text-white">{selectedDs.name}</h2>
                      <p className="text-xs text-slate-400">{selectedDs.description}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => { setActiveDatasetId(selectedDs.id); navigate('/cleaning'); }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-sky-500/20 border border-sky-500/40 text-sky-300 text-xs font-semibold"
                      >
                        <Sparkles className="w-3.5 h-3.5" /> Clean Data
                      </button>
                      <button
                        onClick={() => { setActiveDatasetId(selectedDs.id); navigate('/eda'); }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-semibold"
                      >
                        <BarChart3 className="w-3.5 h-3.5" /> Launch EDA
                      </button>
                      <button
                        onClick={() => { setActiveDatasetId(selectedDs.id); navigate('/ml-lab'); }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 text-xs font-semibold"
                      >
                        <Cpu className="w-3.5 h-3.5" /> Train ML
                      </button>
                    </div>
                  </div>

                  {/* 12-Point Automated Profile Metrics */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">Rows × Columns</span>
                      <div className="text-base font-bold mt-0.5">
                        {profile.row_count} × {profile.column_count}
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">Numerical / Categorical / Date</span>
                      <div className="text-base font-bold mt-0.5 text-sky-400">
                        {(profile.numerical_columns || []).length} / {(profile.categorical_columns || []).length} / {(profile.date_columns || []).length}
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">Missing / Duplicates / Outliers</span>
                      <div className="text-base font-bold mt-0.5 text-amber-400">
                        {profile.missing_values_total ?? 0} / {profile.duplicate_records ?? 0} / {profile.total_outliers_detected ?? 0}
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-slate-400">Composite Data Quality</span>
                      <div className="text-base font-bold mt-0.5 text-emerald-400">
                        {dq.overall_score ?? selectedDs.quality_score}%
                      </div>
                    </div>
                  </div>
                </div>

                {/* Column Information Panel */}
                <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
                  <h3 className="text-sm font-semibold mb-3">Column Information & Data Type Profile</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400">
                          <th className="py-2 px-3">Column Name</th>
                          <th className="py-2 px-3">Detected Type</th>
                          <th className="py-2 px-3">Missing</th>
                          <th className="py-2 px-3">Unique</th>
                          <th className="py-2 px-3">Sample Values</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(selectedDs.columns || []).map((col) => (
                          <tr key={col.id} className="border-b border-slate-800/60 hover:bg-slate-800/30">
                            <td className="py-2 px-3 font-semibold text-slate-200">{col.column_name}</td>
                            <td className="py-2 px-3">
                              <span className="px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 text-[11px]">
                                {col.data_type}
                              </span>
                            </td>
                            <td className="py-2 px-3">{col.missing_count}</td>
                            <td className="py-2 px-3">{col.unique_count}</td>
                            <td className="py-2 px-3 text-slate-400 truncate max-w-xs">
                              {(col.sample_values || []).slice(0, 3).join(', ')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Dataset Preview Table */}
                {previewData && (
                  <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold">
                        Dataset Preview (Showing {previewData.rows?.length || 0} of {previewData.total_rows} rows)
                      </h3>
                      <span className="text-xs text-sky-400">Version: {previewData.version_shown}</span>
                    </div>
                    <div className="overflow-x-auto max-h-80">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400 bg-slate-950">
                            {(previewData.columns || []).map((c) => (
                              <th key={c} className="py-2 px-3 whitespace-nowrap">{c}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {(previewData.rows || []).map((row, rIdx) => (
                            <tr key={rIdx} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                              {(previewData.columns || []).map((c) => (
                                <td key={c} className="py-2 px-3 whitespace-nowrap text-slate-300">
                                  {row[c] === null || row[c] === undefined ? (
                                    <span className="text-rose-400 italic">NULL</span>
                                  ) : (
                                    String(row[c])
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetExplorer;

