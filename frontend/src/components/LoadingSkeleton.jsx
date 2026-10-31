import React from 'react';
import { AlertCircle, CheckCircle2, Database } from 'lucide-react';

export const LoadingSkeleton = ({ rows = 4, label = 'Loading urban intelligence telemetry...' }) => (
  <div className="space-y-4 p-6 rounded-xl border border-slate-800/80 bg-slate-900/50 animate-pulse">
    <div className="flex items-center gap-3 text-sky-400 text-sm font-medium">
      <div className="w-4 h-4 rounded-full border-2 border-sky-400 border-t-transparent animate-spin" />
      <span>{label}</span>
    </div>
    {Array.from({ length: rows }).map((_, idx) => (
      <div key={idx} className="h-10 bg-slate-800/70 rounded-lg w-full" />
    ))}
  </div>
);

export const AlertBanner = ({ type = 'error', message, onClose }) => {
  if (!message) return null;
  const isSuccess = type === 'success';
  return (
    <div
      className={`flex items-center justify-between gap-3 px-4 py-3 rounded-xl border text-sm mb-4 ${
        isSuccess
          ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-200'
          : 'bg-rose-950/60 border-rose-500/40 text-rose-200'
      }`}
    >
      <div className="flex items-center gap-2.5">
        {isSuccess ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" /> : <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />}
        <span>{message}</span>
      </div>
      {onClose && (
        <button onClick={onClose} className="text-xs opacity-75 hover:opacity-100 underline">
          Dismiss
        </button>
      )}
    </div>
  );
};

export const EmptyState = ({ title, description, actionLabel, onAction }) => (
  <div className="flex flex-col items-center justify-center text-center p-10 rounded-xl border border-dashed border-slate-700 bg-slate-900/30">
    <Database className="w-10 h-10 text-sky-400/70 mb-3" />
    <h3 className="text-base font-semibold text-slate-200">{title}</h3>
    <p className="text-sm text-slate-400 max-w-md mt-1">{description}</p>
    {actionLabel && onAction && (
      <button
        onClick={onAction}
        className="mt-4 px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-sm transition"
      >
        {actionLabel}
      </button>
    )}
  </div>
);

