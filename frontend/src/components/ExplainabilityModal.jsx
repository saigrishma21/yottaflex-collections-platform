import React from 'react';
import { X, Sparkles, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';

export default function ExplainabilityModal({ explanation, onClose }) {
  if (!explanation) return null;

  const factors = explanation.factors || [];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden transform transition-all animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-sky-600 to-indigo-700 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/10 rounded-lg">
              <Sparkles className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <h3 className="font-bold text-base">Explainable Decision Attribution</h3>
              <p className="text-xs text-sky-100 font-mono">Case: {explanation.case_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Score Banner */}
        <div className="p-6 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Priority Score
            </span>
            <div className="text-3xl font-extrabold text-slate-900 tracking-tight">
              {explanation.priority_score?.toFixed(1) || '0.0'}
              <span className="text-sm font-normal text-slate-500 ml-1">/ 100</span>
            </div>
          </div>
          <span className="px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-200">
            {explanation.priority_level} Priority
          </span>
        </div>

        {/* Factor Breakdown */}
        <div className="p-6 space-y-4">
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
            Mathematical Factor Attribution
          </h4>

          {factors.map((f, i) => (
            <div key={i} className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-semibold text-slate-800">{f.factor}</span>
                <span className="text-xs font-mono font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                  +{f.contribution} pts ({(f.weight * 100).toFixed(0)}% Wt)
                </span>
              </div>
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Observed: <strong className="text-slate-700">{f.raw_value}</strong></span>
                <span>Norm Score: {f.normalized_score} / 100</span>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
                <div
                  className="bg-sky-600 h-1.5 rounded-full"
                  style={{ width: `${Math.min(100, f.normalized_score)}%` }}
                ></div>
              </div>
            </div>
          ))}

          {/* Decision Summary */}
          {explanation.decision_summary && (
            <div className="p-3.5 bg-indigo-50/60 rounded-xl border border-indigo-100 text-xs text-indigo-950 flex items-start space-x-2.5">
              <ShieldCheck className="w-4 h-4 text-indigo-600 mt-0.5 shrink-0" />
              <div>
                <strong className="font-semibold block mb-0.5">Policy Rationale:</strong>
                {explanation.decision_summary}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-semibold hover:bg-slate-800 transition-colors shadow-xs"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
