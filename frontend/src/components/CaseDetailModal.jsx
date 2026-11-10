import React, { useState } from 'react';
import {
  X,
  Phone,
  Mail,
  MapPin,
  Calendar,
  AlertTriangle,
  Clock,
  CheckCircle,
  FileText,
  DollarSign,
  UserCheck,
  Send,
  PlusCircle,
} from 'lucide-react';
import { recordContactAttempt, recordPromise } from '../services/api';

export default function CaseDetailModal({ caseDetail, onClose, onRefresh }) {
  if (!caseDetail) return null;

  const { case: c, customer, loan, installments = [], contact_attempts = [], promises_to_pay = [], events = [] } = caseDetail;

  const [activeTab, setActiveTab] = useState('schedule');
  const [channel, setChannel] = useState('PHONE');
  const [outcome, setOutcome] = useState('ANSWERED_PROMISED');
  const [notes, setNotes] = useState('');
  const [submittingContact, setSubmittingContact] = useState(false);
  const [contactError, setContactError] = useState(null);

  // Promise Form state
  const [showPromiseForm, setShowPromiseForm] = useState(false);
  const [promiseAmount, setPromiseAmount] = useState(c.outstanding_amount || '');
  const [promiseDate, setPromiseDate] = useState('2026-11-15');
  const [submittingPromise, setSubmittingPromise] = useState(false);
  const [promiseError, setPromiseError] = useState(null);

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    setSubmittingContact(true);
    setContactError(null);
    try {
      await recordContactAttempt(c.case_id, {
        contact_channel: channel,
        outcome: outcome,
        notes: notes,
        agent_id: 'Agent_Alpha',
      });
      setNotes('');
      if (onRefresh) onRefresh(c.case_id);
    } catch (err) {
      setContactError(err.message);
    } finally {
      setSubmittingContact(false);
    }
  };

  const handlePromiseSubmit = async (e) => {
    e.preventDefault();
    setSubmittingPromise(true);
    setPromiseError(null);
    try {
      await recordPromise(c.case_id, {
        promised_amount: parseFloat(promiseAmount),
        promised_date: promiseDate,
        grace_period_days: 3,
      });
      setShowPromiseForm(false);
      if (onRefresh) onRefresh(c.case_id);
    } catch (err) {
      setPromiseError(err.message);
    } finally {
      setSubmittingPromise(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg">{c.case_id}</span>
              <span className="text-xs px-2 py-0.5 rounded font-mono bg-slate-800 text-slate-300">
                Loan: {c.loan_id}
              </span>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                  c.priority_level === 'CRITICAL'
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                }`}
              >
                {c.priority_level} Priority ({c.priority_score})
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">360-Degree Delinquency Dossier & Compliance Monitor</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Top Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6 bg-slate-50 border-b border-slate-200">
          {/* Customer Card */}
          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center justify-between">
              <span>Customer Information</span>
              <span className="px-2 py-0.5 rounded text-2xs font-bold bg-slate-100 text-slate-700">
                {customer?.risk_segment} Risk
              </span>
            </div>
            <div className="font-bold text-slate-900 text-sm">
              {customer?.first_name} {customer?.last_name}
            </div>
            <div className="text-xs text-slate-600 space-y-0.5 mt-1.5">
              <div className="flex items-center space-x-1.5">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                <span>{customer?.phone}</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                <span className="truncate">{customer?.email}</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <span>{customer?.city}, {customer?.state}</span>
              </div>
            </div>
          </div>

          {/* Loan Card */}
          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
              Credit Facility Terms
            </div>
            <div className="font-bold text-slate-900 text-sm">
              ₹{Number(loan?.principal_amount || 0).toLocaleString()} ({loan?.loan_type})
            </div>
            <div className="text-xs text-slate-600 space-y-0.5 mt-1.5">
              <div>Interest: <strong>{loan?.interest_rate}% p.a.</strong></div>
              <div>Tenure: <strong>{loan?.tenure_months} Months</strong></div>
              <div>Status: <span className="font-semibold text-indigo-700">{loan?.loan_status}</span></div>
            </div>
          </div>

          {/* Delinquency Status Card */}
          <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-2xs">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
              Delinquency Arrears
            </div>
            <div className="text-xl font-bold text-rose-600">
              ₹{Number(c.outstanding_amount || 0).toLocaleString()}
            </div>
            <div className="text-xs text-slate-600 space-y-0.5 mt-1.5">
              <div>Days Past Due: <strong className="text-rose-700">{c.days_past_due} DPD</strong></div>
              <div>Workflow State: <strong className="text-slate-900">{c.case_status}</strong></div>
              <div>Assigned: <strong>{c.assigned_to}</strong></div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 bg-white px-6">
          {[
            { id: 'schedule', label: `Installments (${installments.length})` },
            { id: 'outreach', label: `Contact Log (${contact_attempts.length})` },
            { id: 'promises', label: `Promises to Pay (${promises_to_pay.length})` },
            { id: 'audit', label: `Audit Events (${events.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-sky-600 text-sky-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* TAB 1: INSTALLMENT SCHEDULE */}
          {activeTab === 'schedule' && (
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-2.5 text-left font-bold text-slate-600">#</th>
                    <th className="px-4 py-2.5 text-left font-bold text-slate-600">Due Date</th>
                    <th className="px-4 py-2.5 text-right font-bold text-slate-600">Due Amount</th>
                    <th className="px-4 py-2.5 text-right font-bold text-slate-600">Paid Amount</th>
                    <th className="px-4 py-2.5 text-center font-bold text-slate-600">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {installments.map((inst) => (
                    <tr key={inst.installment_id}>
                      <td className="px-4 py-2 font-mono text-slate-500">{inst.installment_number}</td>
                      <td className="px-4 py-2 font-semibold text-slate-800">{inst.due_date}</td>
                      <td className="px-4 py-2 text-right font-bold text-slate-900">
                        ₹{Number(inst.due_amount).toLocaleString()}
                      </td>
                      <td className="px-4 py-2 text-right font-semibold text-emerald-600">
                        ₹{Number(inst.paid_amount).toLocaleString()}
                      </td>
                      <td className="px-4 py-2 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-2xs font-bold uppercase ${
                            inst.status === 'PAID'
                              ? 'bg-emerald-100 text-emerald-800'
                              : inst.status === 'OVERDUE'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {inst.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 2: OUTREACH & CONTACT SCHEDULER */}
          {activeTab === 'outreach' && (
            <div className="space-y-6">
              {/* Log Outreach Form */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center space-x-2">
                  <Send className="w-3.5 h-3.5 text-sky-600" />
                  <span>Log Outreach Attempt (Statutory Window Guarded)</span>
                </h4>

                {contactError && (
                  <div className="mb-3 p-2.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>{contactError}</span>
                  </div>
                )}

                <form onSubmit={handleContactSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-2xs font-semibold text-slate-500 uppercase mb-1">
                      Channel
                    </label>
                    <select
                      value={channel}
                      onChange={(e) => setChannel(e.target.value)}
                      className="w-full text-xs p-2 border border-slate-300 rounded-lg bg-white"
                    >
                      <option value="PHONE">Phone Voice Call</option>
                      <option value="SMS">SMS Text</option>
                      <option value="EMAIL">Email</option>
                      <option value="WHATSAPP">WhatsApp</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-2xs font-semibold text-slate-500 uppercase mb-1">
                      Borrower Outcome
                    </label>
                    <select
                      value={outcome}
                      onChange={(e) => setOutcome(e.target.value)}
                      className="w-full text-xs p-2 border border-slate-300 rounded-lg bg-white"
                    >
                      <option value="ANSWERED_PROMISED">Answered - Promised to Pay</option>
                      <option value="ANSWERED_CALLBACK_REQUESTED">Answered - Callback Requested</option>
                      <option value="ANSWERED_DISPUTED">Answered - Debt Disputed</option>
                      <option value="NO_ANSWER">No Answer</option>
                      <option value="BUSY">Line Busy</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-2xs font-semibold text-slate-500 uppercase mb-1">
                      Conversation Notes
                    </label>
                    <input
                      type="text"
                      placeholder="Add agent notes..."
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      className="w-full text-xs p-2 border border-slate-300 rounded-lg bg-white"
                    />
                  </div>
                  <div className="md:col-span-3 flex justify-end">
                    <button
                      type="submit"
                      disabled={submittingContact}
                      className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-bold transition-colors shadow-xs"
                    >
                      {submittingContact ? 'Validating Window...' : 'Log Outreach Attempt'}
                    </button>
                  </div>
                </form>
              </div>

              {/* Outreach History Table */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-2.5 text-left font-bold text-slate-600">ID</th>
                      <th className="px-4 py-2.5 text-left font-bold text-slate-600">Channel</th>
                      <th className="px-4 py-2.5 text-left font-bold text-slate-600">Time</th>
                      <th className="px-4 py-2.5 text-left font-bold text-slate-600">Outcome</th>
                      <th className="px-4 py-2.5 text-center font-bold text-slate-600">Compliance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {contact_attempts.map((att) => (
                      <tr key={att.contact_id}>
                        <td className="px-4 py-2 font-mono text-slate-500">{att.contact_id}</td>
                        <td className="px-4 py-2 font-semibold">{att.contact_channel}</td>
                        <td className="px-4 py-2 text-slate-600">
                          {new Date(att.contact_time).toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-slate-800">{att.outcome}</td>
                        <td className="px-4 py-2 text-center">
                          <span
                            className={`px-2 py-0.5 rounded-full text-2xs font-bold ${
                              att.compliance_status === 'COMPLIANT'
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {att.compliance_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: PROMISES TO PAY */}
          {activeTab === 'promises' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center mb-2">
                <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                  Payment Commitments
                </h4>
                <button
                  onClick={() => setShowPromiseForm(!showPromiseForm)}
                  className="flex items-center space-x-1.5 px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-lg text-xs font-bold border border-indigo-200"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>{showPromiseForm ? 'Cancel' : 'Record New Promise'}</span>
                </button>
              </div>

              {showPromiseForm && (
                <form onSubmit={handlePromiseSubmit} className="bg-indigo-50/50 p-4 rounded-xl border border-indigo-200 mb-4">
                  {promiseError && (
                    <div className="mb-3 p-2 bg-rose-100 text-rose-800 text-xs rounded-lg">
                      {promiseError}
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="block text-2xs font-semibold text-slate-600 uppercase mb-1">
                        Promised Amount (₹)
                      </label>
                      <input
                        type="number"
                        value={promiseAmount}
                        onChange={(e) => setPromiseAmount(e.target.value)}
                        className="w-full text-xs p-2 border border-slate-300 rounded bg-white"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-2xs font-semibold text-slate-600 uppercase mb-1">
                        Target Payment Date
                      </label>
                      <input
                        type="date"
                        value={promiseDate}
                        onChange={(e) => setPromiseDate(e.target.value)}
                        className="w-full text-xs p-2 border border-slate-300 rounded bg-white"
                        required
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={submittingPromise}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700"
                  >
                    {submittingPromise ? 'Recording...' : 'Commit Promise'}
                  </button>
                </form>
              )}

              {/* Promises Table */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="min-w-full divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-2.5 text-left font-bold text-slate-600">Promise ID</th>
                      <th className="px-4 py-2.5 text-left font-bold text-slate-600">Promised Date</th>
                      <th className="px-4 py-2.5 text-right font-bold text-slate-600">Promised (₹)</th>
                      <th className="px-4 py-2.5 text-right font-bold text-slate-600">Actual Paid (₹)</th>
                      <th className="px-4 py-2.5 text-center font-bold text-slate-600">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {promises_to_pay.map((p) => (
                      <tr key={p.promise_id}>
                        <td className="px-4 py-2 font-mono text-slate-500">{p.promise_id}</td>
                        <td className="px-4 py-2 font-semibold text-slate-800">{p.promised_date}</td>
                        <td className="px-4 py-2 text-right font-bold text-slate-900">
                          ₹{Number(p.promised_amount).toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-right font-bold text-emerald-600">
                          ₹{Number(p.actual_paid_amount).toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-center">
                          <span
                            className={`px-2 py-0.5 rounded-full text-2xs font-bold uppercase ${
                              p.status === 'FULFILLED'
                                ? 'bg-emerald-100 text-emerald-800'
                                : p.status === 'PARTIALLY_FULFILLED'
                                ? 'bg-sky-100 text-sky-800'
                                : p.status === 'BROKEN'
                                ? 'bg-rose-100 text-rose-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: AUDIT EVENTS LOG */}
          {activeTab === 'audit' && (
            <div className="space-y-3">
              {events.map((evt) => (
                <div key={evt.event_id} className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-slate-800">{evt.event_type}</span>
                    <span className="font-mono text-slate-400 text-2xs">
                      {new Date(evt.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-slate-600">{evt.reason}</p>
                  <div className="flex items-center space-x-2 mt-2 text-2xs text-slate-400">
                    <span>Actor: <strong>{evt.created_by}</strong></span>
                    <span>•</span>
                    <span>State: {evt.previous_state || 'NONE'} &rarr; <strong>{evt.new_state}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg text-xs font-bold hover:bg-slate-700"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
}

