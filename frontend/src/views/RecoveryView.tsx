import React, { useState, useEffect } from 'react';
import { AuditDossier, VerificationResult, RecoveryCandidate, AuditSummaryItem, RecoveryExecutionResult } from '../types';
import { api } from '../services/api';
import {
  ShieldCheck,
  CheckCircle2,
  AlertOctagon,
  Wrench,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Clock,
  Terminal,
  Database,
  Lock,
  FileCheck,
  Download,
  FileSpreadsheet,
  FileText,
  UserCheck,
  AlertTriangle,
  Info,
  Check,
  XCircle,
  Hash,
} from 'lucide-react';

interface RecoveryViewProps {
  dossier: AuditDossier | null;
  onNavigate: (tab: string) => void;
  onDossierUpdated?: (dossier: AuditDossier) => void;
}

export const RecoveryView: React.FC<RecoveryViewProps> = ({ dossier, onNavigate, onDossierUpdated }) => {
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<RecoveryExecutionResult | null>(null);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [audits, setAudits] = useState<AuditSummaryItem[]>([]);
  const [localDossier, setLocalDossier] = useState<AuditDossier | null>(dossier);
  const [loadingAudits, setLoadingAudits] = useState(false);

  useEffect(() => {
    setLocalDossier(dossier);
  }, [dossier]);

  // Load audit list for switcher
  useEffect(() => {
    api.agents.listAudits()
      .then((list) => setAudits(list))
      .catch((err) => console.debug('Could not load audits list:', err));
  }, []);

  // Auto-load latest audit from PostgreSQL if null
  useEffect(() => {
    if (!localDossier) {
      setLoadingAudits(true);
      api.agents.getLatestAudit()
        .then((latest) => {
          if (latest) {
            setLocalDossier(latest);
            if (onDossierUpdated) onDossierUpdated(latest);
          }
        })
        .catch((err) => console.debug('No prior audit found:', err))
        .finally(() => setLoadingAudits(false));
    }
  }, [localDossier, onDossierUpdated]);

  const handleSelectAuditId = async (auditId: string) => {
    if (!auditId) return;
    setLoadingAudits(true);
    try {
      const selected = await api.agents.getAuditById(auditId);
      setLocalDossier(selected);
      setVerification(null);
      setExecutionResult(null);
      setError(null);
      if (onDossierUpdated) onDossierUpdated(selected);
    } catch (err) {
      console.error('Failed to load audit:', err);
    } finally {
      setLoadingAudits(false);
    }
  };

  const currentDossier = localDossier;
  const candidates: RecoveryCandidate[] = currentDossier?.recovery?.candidates || [];
  const policyStatus = currentDossier?.recovery?.overall_policy || 'READY_FOR_EXECUTION';
  const findings = currentDossier?.inspection?.findings || [];

  // Summary counts for "Before" stage
  const missingValFindings = findings.filter(f => f.type === 'MISSING_VALUES');
  const duplicateFindings = findings.filter(f => f.type === 'DUPLICATE_RECORDS');
  const mlAnomalyFindings = findings.filter(f => f.type === 'ML_ISOLATION_FOREST_ANOMALY' || f.type === 'NUMERICAL_OUTLIERS');

  const handleExecuteRecovery = async () => {
    if (!currentDossier) return;
    setExecuting(true);
    setError(null);
    try {
      const res = await api.agents.executeRecovery(currentDossier.dataset_path, candidates, currentDossier.id);
      setExecutionResult(res);
      setVerification(res.verification);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        (err.code === 'ECONNABORTED'
          ? 'Recovery execution timed out. The backend server may be restarting or processing a large batch.'
          : null) ||
        (err.message === 'Network Error'
          ? 'Network error: Backend server is temporarily unreachable or restarting on Render.'
          : null) ||
        err.message ||
        'Recovery execution failed.';
      setError(msg);
    } finally {
      setExecuting(false);
    }
  };

  const recoveryRunId = executionResult?.recovery_run_id;
  const xlsxDownloadUrl = recoveryRunId ? api.agents.getRemediatedDownloadUrl(recoveryRunId, 'xlsx') : null;
  const csvDownloadUrl = recoveryRunId ? api.agents.getRemediatedDownloadUrl(recoveryRunId, 'csv') : null;
  const pdfDownloadUrl = recoveryRunId ? api.agents.getRemediatedDownloadUrl(recoveryRunId, 'pdf') : null;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <h2 className="text-2xl font-black text-white tracking-tight">Controlled Recovery & Verification Console</h2>
          </div>
          <p className="text-sm text-slate-400">
            Policy-governed self-healing with RBAC enforcement, cryptographic auditing, and clean Excel / CSV / PDF export.
          </p>
        </div>

        {/* Audit Switcher */}
        {audits.length > 0 && (
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl text-xs">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <select
              value={currentDossier?.id || ''}
              onChange={(e) => handleSelectAuditId(e.target.value)}
              className="bg-transparent text-white outline-none cursor-pointer font-mono"
            >
              <option value="" disabled className="bg-slate-900 text-slate-400">
                Switch Target Audit...
              </option>
              {audits.map((a) => (
                <option key={a.id} value={a.id} className="bg-slate-900 text-white">
                  {a.friendly_name} ({a.finding_count} findings)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loadingAudits && (
        <div className="p-4 text-center text-slate-400 font-mono text-xs flex items-center justify-center gap-2">
          <div className="w-4 h-4 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
          <span>Loading recovery plan from PostgreSQL...</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!currentDossier ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/60 border border-slate-800">
          <ShieldAlert className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white">No Recovery Plan Available</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-4">
            Run an inspection or fault simulation first to generate recovery proposals.
          </p>
          <button
            onClick={() => onNavigate('simulator')}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shadow"
          >
            Go to Pipeline Simulator
          </button>
        </div>
      ) : (
        <div className="space-y-6">

          {/* 1. BEFORE REMEDIATION: Pre-Audit Snapshot */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Phase 1: Pre-Remediation Baseline</span>
                <h3 className="text-base font-black text-white mt-0.5">
                  Target Dataset: <span className="text-emerald-400 font-mono">{currentDossier.dataset_name || currentDossier.dataset_path.split('/').pop()}</span>
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
                  {currentDossier.row_count} Initial Rows
                </span>
                <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-red-500/20 text-red-300 border border-red-500/30">
                  {findings.length} Quality Finding(s)
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80">
                <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Missing Value Cols</div>
                <div className="text-lg font-bold font-mono text-amber-400 mt-1">{missingValFindings.length}</div>
                <div className="text-[10px] text-slate-500 truncate mt-0.5">
                  {missingValFindings.map(f => f.column).filter(Boolean).join(', ') || 'None'}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80">
                <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Duplicate Records</div>
                <div className="text-lg font-bold font-mono text-amber-400 mt-1">
                  {duplicateFindings.length > 0 ? (duplicateFindings[0].evidence?.duplicate_count ?? 'Yes') : '0'}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  {duplicateFindings.length > 0 ? 'Exact row matches' : 'Clean'}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80">
                <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">ML Outliers</div>
                <div className="text-lg font-bold font-mono text-purple-400 mt-1">
                  {mlAnomalyFindings.length > 0 ? (mlAnomalyFindings[0].evidence?.anomalous_row_count ?? mlAnomalyFindings[0].evidence?.outlier_count ?? 'Detected') : '0'}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Isolation Forest Detector</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80">
                <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Health Status</div>
                <div className="text-lg font-bold font-mono text-red-400 mt-1">
                  {currentDossier.audit_status || 'ANOMALY_DETECTED'}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Critical Attention Required</div>
              </div>
            </div>
          </div>

          {/* 2. PROPOSED CANDIDATES: Recovery Policy & Candidate Actions */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-5">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Phase 2: Remediation Plan & Policy</span>
                <div className="flex flex-wrap items-center gap-2 mt-1">
                  <span
                    className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                      policyStatus === 'READY_FOR_EXECUTION'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    }`}
                  >
                    Policy Posture: {policyStatus}
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1">
                    <Lock className="w-3 h-3 text-emerald-400" />
                    Primary Keys Protected
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    Max Drop Bound: &lt;15%
                  </span>
                </div>
              </div>

              <button
                onClick={handleExecuteRecovery}
                disabled={executing || candidates.length === 0}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-xl shadow-emerald-950 flex items-center justify-center gap-2 transition disabled:opacity-50"
              >
                {executing ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Applying Remediation & Verifying...</span>
                  </>
                ) : (
                  <>
                    <Wrench className="w-4 h-4" />
                    <span>Approve & Execute Controlled Recovery</span>
                  </>
                )}
              </button>
            </div>

            {/* Candidates Table */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Formulated Candidate Actions ({candidates.length})
              </h4>

              {candidates.length === 0 ? (
                <div className="p-8 text-center rounded-2xl bg-slate-950 border border-slate-800 text-slate-400 text-xs">
                  No recovery actions required. Dataset is already healthy or zero anomalies detected.
                </div>
              ) : (
                <div className="space-y-3">
                  {candidates.map((act) => {
                    const reqRole = act.required_role || (act.risk_level === 'HIGH' ? 'ADMIN' : 'DATA_ENGINEER');
                    const isHighRisk = act.risk_level === 'HIGH';

                    return (
                      <div
                        key={act.action_id}
                        className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2.5 hover:border-slate-700 transition"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-lg bg-emerald-500/20 text-emerald-300">
                              {act.action_id}
                            </span>
                            <span className="font-bold text-sm text-white">{act.action_type}</span>
                            <span className="text-xs font-mono text-slate-400">Target: {act.target}</span>
                          </div>

                          <div className="flex flex-wrap items-center gap-2">
                            {/* Required Role Badge */}
                            <span
                              className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-md flex items-center gap-1 ${
                                reqRole === 'ADMIN'
                                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                              }`}
                            >
                              <UserCheck className="w-3 h-3" />
                              Role: {reqRole}
                            </span>

                            {/* Risk Level Badge */}
                            <span
                              className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                                isHighRisk
                                  ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                                  : 'bg-slate-800 text-slate-300'
                              }`}
                            >
                              Risk: {act.risk_level}
                            </span>

                            {/* Policy Status Badge */}
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                              {act.policy_status}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-slate-300 leading-relaxed">{act.estimated_impact}</p>

                        {/* Code snippet preview */}
                        <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                          <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500 mb-1">
                            <Terminal className="w-3 h-3" />
                            <span>Remediation Logic:</span>
                          </div>
                          <pre className="text-xs font-mono text-emerald-300 overflow-x-auto">
                            {act.remediation_code}
                          </pre>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* 3. AFTER EXECUTION: Verification Sign-Off & Download Center */}
          {verification && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-emerald-500/40 shadow-2xl space-y-6 animate-fadeIn">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    verification.verdict === 'PASS'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                  }`}>
                    {verification.verdict === 'PASS' ? (
                      <CheckCircle2 className="w-7 h-7" />
                    ) : (
                      <AlertTriangle className="w-7 h-7" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xl font-extrabold text-white">Post-Remediation Verification:</span>
                      <span className={`text-base font-mono font-black px-3 py-0.5 rounded-full ${
                        verification.verdict === 'PASS'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                      }`}>
                        {verification.verdict}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1">{verification.message}</p>
                    {executionResult && (
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Executed by: <span className="font-mono text-white">{executionResult.executed_by}</span> (Role: <span className="font-bold text-emerald-400">{executionResult.user_role}</span>)
                      </p>
                    )}
                  </div>
                </div>

                <div className="text-right font-mono text-xs text-slate-400 hidden sm:block">
                  <div className="text-emerald-400 font-bold">CERTIFIED AUDIT SIGN-OFF</div>
                  <div>{new Date(verification.verified_at).toLocaleTimeString()} UTC</div>
                </div>
              </div>

              {/* Verified Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-950 text-center border border-slate-800">
                  <div className="text-[11px] text-slate-400">Row Count (Before → After)</div>
                  <div className="text-xl font-bold font-mono text-white mt-1">
                    {verification.metrics.original_row_count} → <span className="text-emerald-400">{verification.metrics.remediated_row_count}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Delta: {verification.metrics.row_delta} rows dropped
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950 text-center border border-slate-800">
                  <div className="text-[11px] text-slate-400">Findings (Before → After)</div>
                  <div className="text-xl font-bold font-mono text-white mt-1">
                    <span className="text-red-400">{verification.metrics.before_finding_count}</span> → <span className="text-emerald-400">{verification.metrics.after_finding_count}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    {verification.metrics.resolved_finding_count} finding(s) resolved
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950 text-center border border-slate-800">
                  <div className="text-[11px] text-slate-400">Anomaly Reduction</div>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                    {verification.metrics.anomaly_reduction_rate_pct}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Clean data retention: 100%</div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950 text-center border border-slate-800">
                  <div className="text-[11px] text-slate-400">Audit Status Post-Run</div>
                  <div className="text-xl font-bold font-mono text-white mt-1">
                    {verification.audit_trail?.post_status || 'HEALTHY'}
                  </div>
                  <div className="text-[10px] text-emerald-400 mt-0.5">Tamper-evident record saved</div>
                </div>
              </div>

              {/* Action Breakdown: Executed vs Skipped */}
              {executionResult && (
                <div className="space-y-3 pt-2 border-t border-slate-800">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Executed Actions */}
                    <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/20 space-y-2">
                      <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
                        <Check className="w-4 h-4 text-emerald-400" />
                        <span>Executed Actions ({executionResult.actions_executed.length})</span>
                      </div>
                      <div className="space-y-1.5">
                        {executionResult.actions_executed.map((act) => (
                          <div key={act.action_id} className="text-xs font-mono text-slate-300 flex items-center justify-between bg-slate-900/60 px-2.5 py-1.5 rounded-lg">
                            <span>{act.action_id}: <span className="text-white font-bold">{act.action_type}</span> ({act.target})</span>
                            <span className="text-[10px] text-emerald-400 font-bold">APPLIED</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Skipped Actions (if any) */}
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                      <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
                        <Info className="w-4 h-4 text-amber-400" />
                        <span>Skipped Actions ({executionResult.actions_skipped.length})</span>
                      </div>
                      {executionResult.actions_skipped.length === 0 ? (
                        <p className="text-xs text-slate-500">None. All proposed candidate actions were permitted and applied.</p>
                      ) : (
                        <div className="space-y-1.5">
                          {executionResult.actions_skipped.map((act) => (
                            <div key={act.action_id} className="text-xs font-mono text-slate-300 bg-amber-500/10 border border-amber-500/20 p-2 rounded-lg space-y-0.5">
                              <div className="flex items-center justify-between">
                                <span className="text-amber-300 font-bold">{act.action_id}: {act.action_type}</span>
                                <span className="text-[10px] text-amber-400 font-bold uppercase">SKIPPED (RBAC)</span>
                              </div>
                              <p className="text-[11px] text-slate-400 font-sans">{act.reason}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Artifact Download Center */}
              {recoveryRunId && (
                <div className="pt-4 border-t border-slate-800 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 text-xs text-slate-300">
                      <FileCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>Certified Remediated Artifacts Generated:</span>
                      {executionResult?.remediated_file_hash && (
                        <span className="text-[10px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 flex items-center gap-1">
                          <Hash className="w-3 h-3 text-emerald-400" />
                          SHA-256: {executionResult.remediated_file_hash.slice(0, 16)}...
                        </span>
                      )}
                    </div>
                  </div>

                  {/* 3 Download Buttons */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {/* 1. Excel (.xlsx) Download - Primary */}
                    {xlsxDownloadUrl && (
                      <a
                        href={xlsxDownloadUrl}
                        download
                        className="inline-flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-950/50 transition cursor-pointer"
                      >
                        <FileSpreadsheet className="w-4 h-4" />
                        <span>Download Remediated Excel (.xlsx)</span>
                      </a>
                    )}

                    {/* 2. CSV (.csv) Download */}
                    {csvDownloadUrl && (
                      <a
                        href={csvDownloadUrl}
                        download
                        className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white font-bold text-xs border border-slate-700 transition cursor-pointer"
                      >
                        <Download className="w-4 h-4 text-emerald-400" />
                        <span>Download Clean CSV (.csv)</span>
                      </a>
                    )}

                    {/* 3. PDF (.pdf) Download */}
                    {pdfDownloadUrl && (
                      <a
                        href={pdfDownloadUrl}
                        download
                        className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white font-bold text-xs border border-slate-700 transition cursor-pointer"
                      >
                        <FileText className="w-4 h-4 text-teal-400" />
                        <span>Download Audit Sign-Off (.pdf)</span>
                      </a>
                    )}
                  </div>
                </div>
              )}

            </div>
          )}

        </div>
      )}
    </div>
  );
};
