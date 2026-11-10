import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

export default function ChartsView({ metrics }) {
  if (!metrics) return null;

  const PRIORITY_COLORS = {
    CRITICAL: '#e11d48',
    HIGH: '#f59e0b',
    MEDIUM: '#0284c7',
    LOW: '#10b981',
  };

  const priorityData = (metrics.priority_distribution || []).map((item) => ({
    name: item.level,
    value: item.count,
    color: PRIORITY_COLORS[item.level] || '#64748b',
  }));

  const bucketData = (metrics.delinquency_buckets || []).map((item) => ({
    name: item.bucket.replace('BUCKET_', 'B_').replace('_PLUS', '+'),
    Accounts: item.count,
  }));

  const statusData = (metrics.loan_status_distribution || []).map((item) => ({
    name: item.status,
    Volume: item.count,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      {/* 1. Delinquency Aging Buckets */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div className="mb-4">
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">Delinquency Aging Buckets</h3>
          <p className="text-xs text-slate-500">Distribution across 30-day DPD intervals</p>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bucketData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="Accounts" fill="#0284c7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2. Priority Distribution */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div className="mb-4">
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">Priority Tier Allocation</h3>
          <p className="text-xs text-slate-500">Explainable score-based case distribution</p>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={priorityData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={4}
                dataKey="value"
              >
                {priorityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend verticalAlign="bottom" height={36} iconType="circle" />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Portfolio Loan Status */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div className="mb-4">
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">Portfolio Loan Status</h3>
          <p className="text-xs text-slate-500">Lifecycle states across 10,000 credit facilities</p>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={statusData} layout="vertical" margin={{ top: 10, right: 10, left: 20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="Volume" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
