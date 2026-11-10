import React from 'react';
import { ShieldCheck, BarChart3, Users, AlertTriangle, CheckCircle2, FileSpreadsheet } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, complianceCount = 0 }) {
  const tabs = [
    { id: 'dashboard', label: 'Executive Dashboard', icon: BarChart3 },
    { id: 'worklist', label: 'Priority Worklist', icon: Users },
    { id: 'promises', label: 'Commitments (PTP)', icon: CheckCircle2 },
    { 
      id: 'compliance', 
      label: 'Compliance & Audit', 
      icon: AlertTriangle,
      badge: complianceCount > 0 ? complianceCount : null 
    },
    { id: 'benchmark', label: 'Ground Truth Benchmark', icon: ShieldCheck },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
              Y
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">YottaFlex.ai</span>
                <span className="text-xs bg-sky-100 text-sky-800 font-semibold px-2 py-0.5 rounded-full">
                  FDE Collections
                </span>
              </div>
              <p className="text-xs text-slate-500">Fair Debt Prioritization & Compliance Guard</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-sky-50 text-sky-700 border border-sky-200'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-sky-600' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span className="ml-1.5 px-1.5 py-0.5 text-xs font-bold bg-amber-100 text-amber-800 rounded-full border border-amber-300">
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Seed badge & status */}
          <div className="flex items-center space-x-3">
            <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2.5 py-1 rounded border border-slate-200">
              Seed: 20261022
            </span>
            <div className="flex items-center space-x-1.5 bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full text-xs font-medium border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>API Live</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
