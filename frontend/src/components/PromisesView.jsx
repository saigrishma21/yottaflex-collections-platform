import React, { useState, useEffect } from 'react';
import { fetchPromises } from '../services/api';
import { CheckCircle2, Clock, AlertOctagon, AlertTriangle } from 'lucide-react';

export default function PromisesView() {
  const [promises, setPromises] = useState([]);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPromises();
  }, [filterStatus]);

  const loadPromises = async () => {
    setLoading(true);
    try {
      const params = filterStatus !== 'ALL' ? { status: filterStatus } : {};
      const data = await fetchPromises(params);
      setPromises(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const statusPills = ['ALL', 'PENDING', 'FULFILLED', 'PARTIALLY_FULFILLED', 'BROKEN'];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center space-x-2 bg-white p-3 rounded-xl border border-slate-200">
        <span className="text-xs font-bold text-slate-500 uppercase mr-1">Status:</span>
        {statusPills.map((s) => (
          <button
            key={s}
            onClick={() => setFilterStatus(s)}
            className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
              filterStatus === s
                ? 'bg-indigo-600 text-white shadow-2xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-bold text-slate-600">Promise ID</th>
                <th className="px-4 py-3 text-left font-bold text-slate-600">Case ID</th>
                <th className="px-4 py-3 text-left font-bold text-slate-600">Target Date</th>
                <th className="px-4 py-3 text-right font-bold text-slate-600">Promised (₹)</th>
                <th className="px-4 py-3 text-right font-bold text-slate-600">Actual Paid (₹)</th>
                <th className="px-4 py-3 text-left font-bold text-slate-600">Reconciliation Progress</th>
                <th className="px-4 py-3 text-center font-bold text-slate-600">Lifecycle Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center text-slate-400">
                    Loading payment commitments...
                  </td>
                </tr>
              ) : promises.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center text-slate-400">
                    No promises found.
                  </td>
                </tr>
              ) : (
                promises.map((p) => {
                  const promised = Number(p.promised_amount);
                  const paid = Number(p.actual_paid_amount);
                  const pct = Math.min(100, Math.round((paid / (promised || 1)) * 100));

                  return (
                    <tr key={p.promise_id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{p.promise_id}</td>
                      <td className="px-4 py-3 font-mono text-slate-600">{p.case_id}</td>
                      <td className="px-4 py-3 font-semibold text-slate-800">{p.promised_date}</td>
                      <td className="px-4 py-3 text-right font-bold text-slate-900">
                        ₹{promised.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-emerald-600">
                        ₹{paid.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 w-48">
                        <div className="flex items-center space-x-2">
                          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-2 rounded-full ${
                                pct >= 100 ? 'bg-emerald-500' : pct > 0 ? 'bg-sky-500' : 'bg-slate-300'
                              }`}
                              style={{ width: `${pct}%` }}
                            ></div>
                          </div>
                          <span className="text-2xs font-mono font-bold text-slate-500">{pct}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-2xs font-extrabold uppercase ${
                            p.status === 'FULFILLED'
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                              : p.status === 'PARTIALLY_FULFILLED'
                              ? 'bg-sky-100 text-sky-800 border border-sky-200'
                              : p.status === 'BROKEN'
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : 'bg-amber-100 text-amber-800 border border-amber-200'
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
