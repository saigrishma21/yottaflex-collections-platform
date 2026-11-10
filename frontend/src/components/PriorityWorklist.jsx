import React from 'react';
import { Search, Filter, HelpCircle, Eye, AlertCircle, RefreshCw } from 'lucide-react';

export default function PriorityWorklist({
  cases = [],
  onSelectCase,
  onExplainScore,
  selectedPriority,
  setSelectedPriority,
  searchQuery,
  setSearchQuery,
  loading,
  onRefresh,
}) {
  const priorityFilters = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Controls Bar */}
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Priority Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          <span className="text-xs font-bold text-slate-500 uppercase mr-1">Tier:</span>
          {priorityFilters.map((p) => {
            const isSelected = selectedPriority === p;
            return (
              <button
                key={p}
                onClick={() => setSelectedPriority(p)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                  isSelected
                    ? 'bg-slate-900 text-white shadow-2xs'
                    : 'bg-white text-slate-600 hover:bg-slate-200 border border-slate-200'
                }`}
              >
                {p}
              </button>
            );
          })}
        </div>

        {/* Search Input & Refresh Button */}
        <div className="flex items-center space-x-2 max-w-sm w-full">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by case, loan, or borrower..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            />
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              title="Refresh queue"
              className="p-1.5 bg-white border border-slate-300 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-xs">
          <thead className="bg-slate-50/75">
            <tr>
              <th className="px-4 py-3 text-left font-bold text-slate-600">Case ID</th>
              <th className="px-4 py-3 text-left font-bold text-slate-600">Borrower</th>
              <th className="px-4 py-3 text-right font-bold text-slate-600">Arrears (₹)</th>
              <th className="px-4 py-3 text-center font-bold text-slate-600">DPD</th>
              <th className="px-4 py-3 text-center font-bold text-slate-600">Priority Score</th>
              <th className="px-4 py-3 text-center font-bold text-slate-600">Workflow State</th>
              <th className="px-4 py-3 text-right font-bold text-slate-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {loading ? (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-slate-400">
                  <div className="flex items-center justify-center space-x-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-sky-600" />
                    <span>Loading prioritized collections queue...</span>
                  </div>
                </td>
              </tr>
            ) : cases.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-slate-400">
                  No collection cases matched your filters.
                </td>
              </tr>
            ) : (
              cases.map((c) => {
                const caseId = c.case_id || c.id || 'N/A';
                const customerName = c.customer_name || c.name || c.customer_id || 'Unknown';
                const arrearsAmount = Number(c.outstanding_amount ?? c.amount ?? c.arrears ?? 0);
                const dpd = c.days_past_due ?? c.dpd ?? 0;
                const score = Number(c.priority_score ?? c.score ?? 0);
                const priorityLevel = (c.priority_level || c.level || 'MEDIUM').toUpperCase();
                const caseStatus = c.case_status || c.status || 'OPEN';

                return (
                  <tr key={caseId} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-slate-900">{caseId}</td>
                    <td className="px-4 py-3 font-medium text-slate-800">{customerName}</td>
                    <td className="px-4 py-3 text-right font-bold text-rose-600">
                      ₹{arrearsAmount.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-center font-bold text-slate-700">
                      <span className="bg-slate-100 px-2 py-0.5 rounded font-mono">{dpd}d</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center space-x-1.5">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-2xs font-extrabold uppercase tracking-wider ${
                            priorityLevel === 'CRITICAL'
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : priorityLevel === 'HIGH'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : priorityLevel === 'MEDIUM'
                              ? 'bg-sky-100 text-sky-800 border border-sky-200'
                              : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          }`}
                        >
                          {priorityLevel} ({score.toFixed(1)})
                        </span>
                        <button
                          onClick={() => onExplainScore(caseId)}
                          title="Explain this score"
                          className="text-slate-400 hover:text-sky-600 p-0.5"
                        >
                          <HelpCircle className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center font-semibold text-slate-700">
                      <span className="text-2xs font-mono bg-slate-100 px-2 py-0.5 rounded">
                        {caseStatus}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onSelectCase(caseId)}
                        className="inline-flex items-center space-x-1 px-3 py-1 bg-slate-100 hover:bg-sky-50 text-slate-700 hover:text-sky-700 rounded-lg text-xs font-semibold border border-slate-200 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View Dossier</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
