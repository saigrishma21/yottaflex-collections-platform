import React from 'react';
import { CreditCard, AlertCircle, ShieldAlert, CheckCircle2, TrendingUp, Users } from 'lucide-react';

export default function KPICards({ summary }) {
  if (!summary) return null;

  const cards = [
    {
      title: 'Total Loan Portfolio',
      value: summary.total_loans.toLocaleString(),
      subtitle: `${summary.total_customers.toLocaleString()} active borrowers`,
      icon: CreditCard,
      color: 'sky',
    },
    {
      title: 'Delinquent Arrears',
      value: `₹${(Number(summary.total_outstanding_delinquent) / 10000000).toFixed(2)} Cr`,
      subtitle: 'Overdue installment balances',
      icon: TrendingUp,
      color: 'rose',
    },
    {
      title: 'Active Collection Cases',
      value: summary.active_cases_count.toLocaleString(),
      subtitle: 'Requiring outreach workflow',
      icon: Users,
      color: 'indigo',
    },
    {
      title: 'Critical Priority Tier',
      value: summary.critical_cases_count.toLocaleString(),
      subtitle: 'Explainable Score ≥ 80.0',
      icon: AlertCircle,
      color: 'amber',
    },
    {
      title: 'Promise Fulfillment',
      value: `${summary.promises_fulfilled_rate}%`,
      subtitle: 'PTP payment reconciliation',
      icon: CheckCircle2,
      color: 'emerald',
    },
    {
      title: 'Compliance Exceptions',
      value: summary.compliance_issues_count,
      subtitle: 'Statutory window / DNC alerts',
      icon: ShieldAlert,
      color: 'red',
    },
  ];

  const colorStyles = {
    sky: 'border-sky-200 bg-sky-50 text-sky-600',
    rose: 'border-rose-200 bg-rose-50 text-rose-600',
    indigo: 'border-indigo-200 bg-indigo-50 text-indigo-600',
    amber: 'border-amber-200 bg-amber-50 text-amber-600',
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-600',
    red: 'border-red-200 bg-red-50 text-red-600',
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 mb-8">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:shadow transition-shadow"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {c.title}
              </span>
              <div className={`p-2 rounded-lg border ${colorStyles[c.color]}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900 tracking-tight">{c.value}</div>
            <div className="text-xs text-slate-500 mt-1 truncate">{c.subtitle}</div>
          </div>
        );
      })}
    </div>
  );
}

