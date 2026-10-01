import React, { useState, useEffect } from 'react';
import { AuditDossier, VerificationResult, RecoveryCandidate, AuditSummaryItem } from '../types';
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
} from 'lucide-react';

interface RecoveryViewProps {
  dossier: AuditDossier | null;
  onNavigate: (tab: string) => void;
  onDossierUpdated?: (dossier: AuditDossier) => void;
}

export const RecoveryView: React.FC<RecoveryViewProps> = ({ dossier, onNavigate, onDossierUpdated }) => {
  const [executing, setExecuting] = useState(false);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [remediatedHash, setRemediatedHash] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [audits, setAudits] = useState<AuditSummaryItem[]>([]);
  const [localDossier, setLocalDossier] = useState<AuditDossier | null>(dossier);
  const [loadingAudits, setLoadingAudits] = useState(false);
  const [isDryRun, setIsDryRun] = useState(false);

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

  const handleExecuteRecovery = async () => {
    if (!currentDossier) return;
    setExecuting(true);
    setError(null);
    setDownloadUrl(null);
    setRemediatedHash(null);
    try {
      const res = await api.agents.executeRecovery(currentDossier.dataset_path, candidates, currentDossier.id);
      setVerification(res.verification);
      if (res.recovery_run_id) {
        setDownloadUrl(api.agents.getRemediatedDownloadUrl(res.recovery_run_id));
        setRemediatedHash(res.remediated_file_hash);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Recovery execution failed.');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h2 className="text-2xl font-black text-white tracking-tight">Controlled Recovery & Verification Console</h2>
          </div>
          <p className="text-sm text-slate-400">
            Policy-governed self-healing with primary-key protection, safety bounds, and post-remediation PASS/FAIL verification.
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
          {/* Policy & Execution Banner */}
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Policy Posture:</span>
                <span
                  className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                    policyStatus === 'READY_FOR_EXECUTION'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}
                >
                  {policyStatus}
                </span>
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 flex items-center gap-1">
                  <Lock className="w-3 h-3 text-emerald-400" />
                  Primary Keys Protected
                </span>
                <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  Max Drop Limit: &lt;15%
                </span>
              </div>
              <p className="text-xs text-slate-300">
                Target: <span className="font-bold text-white">{currentDossier.dataset_name || currentDossier.dataset_path.split('/').pop()}</span> • {candidates.length} candidate action(s) formulated.
              </p>
            </div>

            <div className="flex items-center gap-3">
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
          </div>

          {/* Verification Verdict Card (Post Execution) */}
          {verification && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-emerald-500/40 shadow-2xl space-y-4 animate-fadeIn">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    verification.verdict === 'PASS' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    <CheckCircle2 className="w-7 h-7" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xl font-extrabold text-white">Verification Verdict:</span>
                      <span className={`text-base font-mono font-black px-3 py-0.5 rounded-full ${
                        verification.verdict === 'PASS'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                      }`}>
                        {verification.verdict}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1">{verification.message}</p>
                  </div>
                </div>

                <div className="text-right font-mono text-xs text-slate-400 hidden sm:block">
                  <div className="text-emerald-400 font-bold">CERTIFIED AUDIT SIGN-OFF</div>
                  <div>{new Date(verification.verified_at).toLocaleTimeString()} UTC</div>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-800">
                <div className="p-3 rounded-xl bg-slate-950 text-center">
                  <div className="text-[11px] text-slate-400">Before Findings</div>
                  <div className="text-xl font-bold font-mono text-red-400">{verification.metrics.before_finding_count}</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 text-center">
                  <div className="text-[11px] text-slate-400">After Findings</div>
                  <div className="text-xl font-bold font-mono text-emerald-400">{verification.metrics.after_finding_count}</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 text-center">
                  <div className="text-[11px] text-slate-400">Anomaly Reduction</div>
                  <div className="text-xl font-bold font-mono text-emerald-400">
                    {verification.metrics.anomaly_reduction_rate_pct}%
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 text-center">
                  <div className="text-[11px] text-slate-400">Clean Rows Retained</div>
                  <div className="text-xl font-bold font-mono text-white">
                    {verification.metrics.remediated_row_count}
                  </div>
                </div>
              </div>

              {downloadUrl && (
                <div className="pt-3 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-xs text-slate-300">
                    <FileCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>Remediated Clean CSV generated and cryptographic SHA-256 registered.</span>
                    {remediatedHash && (
                      <span className="text-[10px] font-mono text-slate-500 hidden md:inline">
                        ({remediatedHash.slice(0, 16)}...)
                      </span>
                    )}
                  </div>
                  <a
                    href={downloadUrl}
                    download
                    className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Remediated CSV</span>
                  </a>
                </div>
              )}
            </div>
          )}

          {/* Recovery Candidate Actions List */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Proposed Remediation Candidates ({candidates.length})
            </h3>

            {candidates.length === 0 ? (
              <div className="p-8 text-center rounded-2xl bg-slate-900/80 border border-slate-800 text-slate-400 text-xs">
                No recovery actions required. Dataset is already healthy or zero anomalies detected.
              </div>
            ) : (
              candidates.map((act) => (
                <div
                  key={act.action_id}
                  className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-lg bg-emerald-500/20 text-emerald-300">
                        {act.action_id}
                      </span>
                      <span className="font-bold text-sm text-white">{act.action_type}</span>
                      <span className="text-xs font-mono text-slate-400">({act.target})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                        Risk: {act.risk_level}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        {act.policy_status}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">{act.estimated_impact}</p>

                  {/* Remediation Snippet */}
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80">
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500 mb-1">
                      <Terminal className="w-3 h-3" />
                      <span>Remediation Execution Code:</span>
                    </div>
                    <pre className="text-xs font-mono text-emerald-300 overflow-x-auto">
                      {act.remediation_code}
                    </pre>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
