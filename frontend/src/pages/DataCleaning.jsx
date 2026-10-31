import React, { useState, useEffect } from 'react';
import { Sparkles, Download, CheckCircle2, ArrowRight } from 'lucide-react';
import api, { extractErrorMessage } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const DataCleaning = () => {
  const { activeDatasetId, setActiveDatasetId } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [selectedId, setSelectedId] = useState(activeDatasetId || '');
  const [qualityData, setQualityData] = useState(null);
  const [cleaningResult, setCleaningResult] = useState(null);

  // Cleaning controls
  const [missingStrategy, setMissingStrategy] = useState('median');
  const [removeDuplicates, setRemoveDuplicates] = useState(true);
  const [outlierAction, setOutlierAction] = useState('clip_iqr');
  const [scalingMethod, setScalingMethod] = useState('none');
  const [encodingMethod, setEncodingMethod] = useState('none');
  const [renameFrom, setRenameFrom] = useState('');
  const [renameTo, setRenameTo] = useState('');
  const [convertCol, setConvertCol] = useState('');
  const [convertType, setConvertType] = useState('float');

  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    api
      .get('/datasets')
      .then((res) => {
        const list = res.data.datasets || [];
        setDatasets(list);
        const initial = activeDatasetId || (list[0] ? list[0].id : '');
        if (initial) {
          setSelectedId(initial);
          loadQuality(initial);
        }
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const loadQuality = async (id) => {
    if (!id) return;
    setError('');
    try {
      const res = await api.get(`/analysis/${id}/quality`);
      setQualityData(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const handleRunCleaning = async (e) => {
    e.preventDefault();
    if (!selectedId) return;
    setProcessing(true);
    setError('');
    setSuccess('');
    try {
      const payload = {
        missing_strategy: missingStrategy,
        remove_duplicates: removeDuplicates,
        outlier_action: outlierAction,
        scaling_method: scalingMethod,
        encoding_method: encodingMethod,
        date_columns: qualityData?.profile?.date_columns || [],
        rename_columns: renameFrom && renameTo ? { [renameFrom]: renameTo } : undefined,
        convert_types: convertCol ? { [convertCol]: convertType } : undefined,
      };
      const res = await api.post(`/analysis/${selectedId}/clean`, payload);
      setCleaningResult(res.data);
      setSuccess('Dataset cleaned and saved to datasets/processed/ without modifying the original uploaded file.');
      await loadQuality(selectedId);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setProcessing(false);
    }
  };

  const handleDownloadCleaned = async () => {
    if (!selectedId) return;
    try {
      const res = await api.get(`/datasets/${selectedId}/download?version=processed`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.setAttribute('download', `cleaned_dataset_${selectedId}.csv`);
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  if (loading) return <LoadingSkeleton rows={5} label="Loading Data Cleaning Engine..." />;

  const prof = qualityData?.profile || {};
  const cols = (prof.columns || []).map((c) => c.column_name);
  const comp = cleaningResult?.comparison;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Data Cleaning & Preprocessing Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure missing value imputation, deduplication, outlier clipping, scaling, and encoding. Original files are never altered.
          </p>
        </div>

        <select
          value={selectedId}
          onChange={(e) => {
            const id = Number(e.target.value);
            setSelectedId(id);
            setActiveDatasetId(id);
            setCleaningResult(null);
            loadQuality(id);
          }}
          className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white"
        >
          {datasets.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} ({d.row_count} rows)
            </option>
          ))}
        </select>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />
      <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />

      {/* Current Dataset Health Summary */}
      {qualityData && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/50">
            <div className="text-xs text-slate-400">Total Rows</div>
            <div className="text-xl font-bold mt-1">{prof.row_count}</div>
          </div>
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/50">
            <div className="text-xs text-slate-400">Missing Values</div>
            <div className="text-xl font-bold text-amber-400 mt-1">{prof.missing_values_total}</div>
          </div>
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/50">
            <div className="text-xs text-slate-400">Duplicate Records</div>
            <div className="text-xl font-bold text-rose-400 mt-1">{prof.duplicate_records}</div>
          </div>
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/50">
            <div className="text-xs text-slate-400">Outliers (1.5×IQR)</div>
            <div className="text-xl font-bold text-sky-400 mt-1">{prof.total_outliers_detected}</div>
          </div>
          <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/50">
            <div className="text-xs text-slate-400">Data Quality Score</div>
            <div className="text-xl font-bold text-emerald-400 mt-1">
              {prof.data_quality?.overall_score}%
            </div>
          </div>
        </div>
      )}

      {/* Cleaning Configuration Form */}
      <form
        onSubmit={handleRunCleaning}
        className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-5"
      >
        <h3 className="text-sm font-semibold text-sky-400">Configure Preprocessing Pipeline</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">1. Missing Value Strategy</label>
            <select
              value={missingStrategy}
              onChange={(e) => setMissingStrategy(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              <option value="none">Do Not Impute</option>
              <option value="mean">Mean Imputation (Numeric) + Mode (Text)</option>
              <option value="median">Median Imputation (Robust to Outliers)</option>
              <option value="mode">Mode (Most Frequent Value) Imputation</option>
              <option value="forward_fill">Chronological Forward/Backward Fill</option>
              <option value="drop_rows">Drop Rows Containing Missing Values</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">2. Outlier Handling Strategy</label>
            <select
              value={outlierAction}
              onChange={(e) => setOutlierAction(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              <option value="none">Keep Outliers Unchanged</option>
              <option value="clip_iqr">Clip Outliers to 1.5×IQR Fences (Winsorize)</option>
              <option value="clip_zscore">Clip Extreme Values Beyond ±3.0 Z-Score</option>
              <option value="remove_iqr">Remove Rows Exceeding 1.5×IQR Fences</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">3. Feature Scaling</label>
            <select
              value={scalingMethod}
              onChange={(e) => setScalingMethod(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              <option value="none">Preserve Original Physical Units</option>
              <option value="normalize">Min-Max Normalization [0, 1]</option>
              <option value="standardize">Z-Score Standardization (μ=0, σ=1)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">4. Categorical Encoding</label>
            <select
              value={encodingMethod}
              onChange={(e) => setEncodingMethod(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
            >
              <option value="none">None</option>
              <option value="label">Label Encoding (Append _encoded columns)</option>
              <option value="onehot">One-Hot Encoding (Binary Indicator Columns)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">5. Data Type Conversion (Optional)</label>
            <div className="flex gap-2">
              <select
                value={convertCol}
                onChange={(e) => setConvertCol(e.target.value)}
                className="flex-1 px-2 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
              >
                <option value="">Select Column</option>
                {cols.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <select
                value={convertType}
                onChange={(e) => setConvertType(e.target.value)}
                className="w-28 px-2 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
              >
                <option value="float">Float</option>
                <option value="int">Integer</option>
                <option value="str">String</option>
                <option value="datetime">Date</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">6. Column Renaming (Optional)</label>
            <div className="flex gap-2">
              <select
                value={renameFrom}
                onChange={(e) => setRenameFrom(e.target.value)}
                className="flex-1 px-2 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
              >
                <option value="">Column</option>
                {cols.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <input
                type="text"
                placeholder="New Name"
                value={renameTo}
                onChange={(e) => setRenameTo(e.target.value)}
                className="flex-1 px-2 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
              />
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-slate-800">
          <label className="flex items-center gap-2 text-xs text-slate-200 cursor-pointer">
            <input
              type="checkbox"
              checked={removeDuplicates}
              onChange={(e) => setRemoveDuplicates(e.target.checked)}
              className="rounded border-slate-700"
            />
            <span>Automatically detect and remove exact duplicate records</span>
          </label>

          <button
            type="submit"
            disabled={processing}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-400 to-blue-600 text-slate-950 font-bold text-xs shadow-lg transition"
          >
            <Sparkles className="w-4 h-4" />
            <span>{processing ? 'Executing Cleaning Engine...' : 'Execute Data Cleaning Pipeline'}</span>
          </button>
        </div>
      </form>

      {/* Before-and-After Comparison Results */}
      {cleaningResult && comp && (
        <div className="p-6 rounded-2xl border border-emerald-500/30 bg-slate-900/70 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5" />
                <span>Before-and-After Data Cleaning Verification</span>
              </h3>
              <p className="text-xs text-slate-400">
                Saved as: {cleaningResult.processed_filename}
              </p>
            </div>
            <button
              onClick={handleDownloadCleaned}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition"
            >
              <Download className="w-4 h-4" />
              <span>Download Cleaned CSV</span>
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400">Row Count</div>
              <div className="font-bold text-sm mt-1 flex items-center gap-1">
                <span>{comp.rows_before}</span>
                <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                <span className="text-emerald-400">{comp.rows_after}</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400">Missing Cells</div>
              <div className="font-bold text-sm mt-1 flex items-center gap-1">
                <span>{comp.missing_before}</span>
                <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                <span className="text-emerald-400">{comp.missing_after}</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400">Duplicate Rows</div>
              <div className="font-bold text-sm mt-1 flex items-center gap-1">
                <span>{comp.duplicates_before}</span>
                <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                <span className="text-emerald-400">{comp.duplicates_after}</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400">Outliers Detected</div>
              <div className="font-bold text-sm mt-1 flex items-center gap-1">
                <span>{comp.outliers_before}</span>
                <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                <span className="text-emerald-400">{comp.outliers_after}</span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-slate-400">Quality Score</div>
              <div className="font-bold text-sm mt-1 flex items-center gap-1">
                <span>{comp.quality_score_before}%</span>
                <ArrowRight className="w-3.5 h-3.5 text-sky-400" />
                <span className="text-emerald-400">{comp.quality_score_after}%</span>
              </div>
            </div>
          </div>

          <div className="space-y-1 text-xs">
            <div className="font-semibold text-slate-300">Operations Log:</div>
            {(cleaningResult.operations_applied || []).map((op, i) => (
              <div key={i} className="text-slate-400">• {op}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DataCleaning;

