import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import KPICards from './components/KPICards';
import ChartsView from './components/ChartsView';
import PriorityWorklist from './components/PriorityWorklist';
import ExplainabilityModal from './components/ExplainabilityModal';
import CaseDetailModal from './components/CaseDetailModal';
import PromisesView from './components/PromisesView';
import ComplianceView from './components/ComplianceView';
import BenchmarkView from './components/BenchmarkView';
import {
  fetchDashboardSummary,
  fetchDashboardMetrics,
  fetchCollections,
  fetchCaseDetail,
} from './services/api';
import { AlertTriangle } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [summary, setSummary] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [cases, setCases] = useState([]);
  const [selectedPriority, setSelectedPriority] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingCases, setLoadingCases] = useState(false);
  const [apiError, setApiError] = useState(null);

  // Modals state
  const [selectedCaseDetail, setSelectedCaseDetail] = useState(null);
  const [selectedExplanation, setSelectedExplanation] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
    if (activeTab === 'dashboard' || activeTab === 'worklist') {
      loadCases();
    }
  }, [selectedPriority, searchQuery, activeTab]);

  const loadDashboardData = async () => {
    try {
      const [sumData, metData] = await Promise.all([
        fetchDashboardSummary(),
        fetchDashboardMetrics(),
      ]);
      setSummary(sumData);
      setMetrics(metData);
      setApiError(null);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setApiError('Unable to connect to FastAPI backend at port 8000. Ensure the server is running.');
    }
  };

  const loadCases = async () => {
    setLoadingCases(true);
    try {
      const params = {};
      if (selectedPriority !== 'ALL') params.priority = selectedPriority;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      params.limit = 50;

      const data = await fetchCollections(params);
      setCases(data);
      setApiError(null);
    } catch (err) {
      console.error('Failed to load collection cases:', err);
      setApiError(err.message || 'Error loading collection cases');
    } finally {
      setLoadingCases(false);
    }
  };

  const handleSelectCase = async (caseId) => {
    try {
      const detail = await fetchCaseDetail(caseId);
      setSelectedCaseDetail(detail);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExplainScore = async (caseId) => {
    try {
      const detail = await fetchCaseDetail(caseId);
      if (detail.score_explanation) {
        setSelectedExplanation(detail.score_explanation);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        complianceCount={summary?.compliance_issues_count || 0}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Connection Warning Banner */}
        {apiError && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 text-amber-900 rounded-xl flex items-center space-x-3 text-sm">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <div className="flex-1">
              <strong>Connection Notice:</strong> {apiError}
            </div>
            <button
              onClick={() => { loadDashboardData(); loadCases(); }}
              className="px-3 py-1 bg-amber-600 text-white rounded-lg text-xs font-bold hover:bg-amber-700"
            >
              Retry
            </button>
          </div>
        )}

        {/* TAB 1: EXECUTIVE DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <KPICards summary={summary} />
            <ChartsView metrics={metrics} />
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                  Prioritized Overdue Accounts Queue
                </h3>
                <button
                  onClick={() => setActiveTab('worklist')}
                  className="text-xs font-bold text-sky-600 hover:text-sky-700"
                >
                  View Full Worklist &rarr;
                </button>
              </div>
              <PriorityWorklist
                cases={cases.slice(0, 10)}
                onSelectCase={handleSelectCase}
                onExplainScore={handleExplainScore}
                selectedPriority={selectedPriority}
                setSelectedPriority={setSelectedPriority}
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
                loading={loadingCases}
                onRefresh={loadCases}
              />
            </div>
          </div>
        )}

        {/* TAB 2: PRIORITY WORKLIST */}
        {activeTab === 'worklist' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  Delinquent Accounts Prioritization Queue
                </h2>
                <p className="text-xs text-slate-500">
                  Ranked by explainable multi-factor scoring algorithm (DPD 40%, Balance 35%, Risk 25%)
                </p>
              </div>
            </div>
            <PriorityWorklist
              cases={cases}
              onSelectCase={handleSelectCase}
              onExplainScore={handleExplainScore}
              selectedPriority={selectedPriority}
              setSelectedPriority={setSelectedPriority}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              loading={loadingCases}
              onRefresh={loadCases}
            />
          </div>
        )}

        {/* TAB 3: PROMISES TO PAY */}
        {activeTab === 'promises' && <PromisesView />}

        {/* TAB 4: COMPLIANCE & AUDIT */}
        {activeTab === 'compliance' && <ComplianceView />}

        {/* TAB 5: GROUND TRUTH BENCHMARK */}
        {activeTab === 'benchmark' && <BenchmarkView />}
      </main>

      {/* Explainability Modal Drawer */}
      {selectedExplanation && (
        <ExplainabilityModal
          explanation={selectedExplanation}
          onClose={() => setSelectedExplanation(null)}
        />
      )}

      {/* Case 360 Dossier Modal */}
      {selectedCaseDetail && (
        <CaseDetailModal
          caseDetail={selectedCaseDetail}
          onClose={() => setSelectedCaseDetail(null)}
          onRefresh={handleSelectCase}
        />
      )}
    </div>
  );
}
