import React, { useState, useEffect } from 'react';
import { fetchComplianceIssues } from '../services/api';
import { ShieldAlert, AlertTriangle, CheckCircle, RefreshCw, Info } from 'lucide-react';

export default function ComplianceView() {
  const [issues, setIssues] = useState([]);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIssues();
  }, []);

  const loadIssues = async () => {
    setLoading(true);
    try {
      const data = await fetchComplianceIssues();
      setIssues(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredIssues = filterSeverity === 'ALL'
    ? issues
    : issues.filter((i) => i.severity === filterSeverity);

  return (
    <div className="space-y-4">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-red-500 to-rose-600 rounded-xl p-5 text-white shadow-md flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-6 h-6 text-white" />
            <h2 className="text-lg font-bold">Automated Statutory & Policy Compliance Scanner</h2>
          </div>
          <p className="text-xs text-rose-100 mt-1 max-w-2xl">
            Continuously monitors loan collections against Fair Debt Collection Practices Act (FDCPA),
            TCPA permissible contact windows, accounting reconciliation, and consumer dispute regulations.
          </p>
        </div>
        <button
          onClick={loadIssues}
          className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-xs font-bold transition-colors flex items-center space-x-1"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Scan Portfolio</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between bg-white p-3 rounded-xl border border-slate-200">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold text-slate-500 uppercase mr-1">Severity:</span>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                filterSeverity === sev
                  ? 'bg-slate-900 text-white shadow-2xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
        <span className="text-xs font-bold text-slate-500">
          Showing {filteredIssues.length} of {issues.length} flagged exceptions
        </span>
      </div>

      {/* Issues Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-bold text-slate-600">Severity</th>
                <th className="px-4 py-3 text-left font-bold text-slate-600">Violation Code</th>
                <th className="px-4 py-3 text-left font-bold text-slate-600">Affected Record</th>
                <th className="px-4 py-3 text-left font-bold text-slate-600">Violation Description</th>
                <th className="px-4 py-3 text-left font-bold text-slate-600">Recommended Remedial Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-slate-400">
                    Running compliance verification engine...
                  </td>
                </tr>
              ) : filteredIssues.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-emerald-600 font-bold">
                    Zero compliance violations detected in this tier.
                  </td>
                </tr>
              ) : (
                filteredIssues.map((issue, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-2xs font-extrabold uppercase ${
                          issue.severity === 'CRITICAL'
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : issue.severity === 'HIGH'
                            ? 'bg-amber-100 text-amber-800 border border-amber-200'
                            : 'bg-sky-100 text-sky-800 border border-sky-200'
                        }`}
                      >
                        {issue.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono font-bold text-slate-800">
                      {issue.violation_code}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-600">
                      <span className="bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                        {issue.record_id}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-700 max-w-xs">{issue.description}</td>
                    <td className="px-4 py-3 text-indigo-700 font-medium max-w-xs">
                      {issue.recommended_action}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

