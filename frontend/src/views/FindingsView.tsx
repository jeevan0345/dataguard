import React, { useState, useEffect } from 'react';
import { AuditDossier, Finding, AuditSummaryItem } from '../types';
import { api } from '../services/api';
import {
  AlertTriangle,
  SearchCode,
  Filter,
  Layers,
  ChevronRight,
  ShieldAlert,
  ArrowRight,
  Database,
  Calendar,
  Sparkles,
  GitBranch,
  BookmarkCheck,
  CheckCircle2,
} from 'lucide-react';

interface FindingsViewProps {
  dossier: AuditDossier | null;
  onNavigate: (tab: string) => void;
  onSelectDossier?: (dossier: AuditDossier) => void;
}

export const FindingsView: React.FC<FindingsViewProps> = ({ dossier, onNavigate, onSelectDossier }) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [audits, setAudits] = useState<AuditSummaryItem[]>([]);
  const [loadingAudits, setLoadingAudits] = useState<boolean>(false);
  const [localDossier, setLocalDossier] = useState<AuditDossier | null>(dossier);
  const [settingBaseline, setSettingBaseline] = useState<boolean>(false);
  const [baselineMessage, setBaselineMessage] = useState<string | null>(null);

  useEffect(() => {
    setLocalDossier(dossier);
  }, [dossier]);

  // Load audit list for dropdown
  useEffect(() => {
    api.agents.listAudits()
      .then((list) => setAudits(list))
      .catch((err) => console.debug('Could not load audits list:', err));
  }, []);

  // If no dossier passed, try fetching latest persisted audit
  useEffect(() => {
    if (!localDossier) {
      setLoadingAudits(true);
      api.agents.getLatestAudit()
        .then((latest) => {
          if (latest) {
            setLocalDossier(latest);
            if (onSelectDossier) onSelectDossier(latest);
          }
        })
        .catch((err) => console.debug('No prior audit found:', err))
        .finally(() => setLoadingAudits(false));
    }
  }, [localDossier, onSelectDossier]);

  const handleSelectAuditId = async (auditId: string) => {
    if (!auditId) return;
    setLoadingAudits(true);
    try {
      const selected = await api.agents.getAuditById(auditId);
      setLocalDossier(selected);
      if (onSelectDossier) onSelectDossier(selected);
    } catch (err) {
      console.error('Failed to load audit:', err);
    } finally {
      setLoadingAudits(false);
    }
  };

  const currentDossier = localDossier;
  const findings: Finding[] = currentDossier?.inspection?.findings || [];
  const evidenceItems = currentDossier?.evidence?.evidence || [];
  const rcaCandidates = currentDossier?.root_cause?.candidates || [];

  const handleSetBaseline = async () => {
    if (!currentDossier?.id) return;
    setSettingBaseline(true);
    setBaselineMessage(null);
    try {
      await api.agents.setAuditAsBaseline(currentDossier.id);
      setBaselineMessage('Baseline updated successfully! Future audits will compare against this baseline.');
      setTimeout(() => setBaselineMessage(null), 5000);
    } catch (err: any) {
      setBaselineMessage(`Failed to set baseline: ${err.response?.data?.detail || err.message}`);
      setTimeout(() => setBaselineMessage(null), 5000);
    } finally {
      setSettingBaseline(false);
    }
  };

  const filteredFindings = selectedSeverity === 'ALL'
    ? findings
    : findings.filter((f) => f.severity === selectedSeverity);

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'HIGH':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header with Audit Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <SearchCode className="w-5 h-5 text-emerald-400" />
            <h2 className="text-2xl font-black text-white tracking-tight">Inspection Findings & Evidence</h2>
          </div>
          <p className="text-sm text-slate-400">
            Multimodal audit discoveries categorized by Data Quality, Schema Drift, and ML Anomaly detection.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Audit Selector Dropdown */}
          {audits.length > 0 && (
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl text-xs">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <select
                value={currentDossier?.id || ''}
                onChange={(e) => handleSelectAuditId(e.target.value)}
                className="bg-transparent text-white outline-none cursor-pointer font-mono"
              >
                <option value="" disabled className="bg-slate-900 text-slate-400">
                  Switch Historical Audit...
                </option>
                {audits.map((a) => (
                  <option key={a.id} value={a.id} className="bg-slate-900 text-white">
                    {a.friendly_name} ({a.finding_count} findings)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Severity Filter */}
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded-xl">
            <Filter className="w-3.5 h-3.5 text-slate-500 ml-2" />
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition ${
                  selectedSeverity === sev
                    ? 'bg-emerald-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loadingAudits && (
        <div className="p-8 text-center text-slate-400 font-mono text-xs flex items-center justify-center gap-2">
          <div className="w-4 h-4 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
          <span>Loading audit dossier from PostgreSQL...</span>
        </div>
      )}

      {!currentDossier ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/60 border border-slate-800">
          <ShieldAlert className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white">No Active Audit Dossier Loaded</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-4">
            Run an automated audit or execute a fault simulation to populate real-time findings and structured evidence.
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
          {/* Audit Metadata Banner */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-4">
              <div>
                <span className="text-slate-400">Target Dataset: </span>
                <span className="font-bold text-white">{currentDossier.dataset_name || currentDossier.dataset_path.split('/').pop()}</span>
                <span className="text-[10px] text-slate-500 font-mono ml-2">({currentDossier.dataset_path})</span>
              </div>
            </div>
            <div className="flex items-center gap-4 text-slate-400 font-mono">
              {currentDossier.id && (
                <div>Audit ID: <span className="text-slate-300">{currentDossier.id.slice(0, 8)}...</span></div>
              )}
              <div>Rows: <span className="text-slate-300">{currentDossier.row_count.toLocaleString()}</span></div>
              <div>Columns: <span className="text-slate-300">{currentDossier.column_count}</span></div>
              <div>Status: <span className="text-emerald-400 font-bold">{currentDossier.audit_status}</span></div>
              {currentDossier.id && (
                <button
                  onClick={handleSetBaseline}
                  disabled={settingBaseline}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30 disabled:opacity-50 transition text-xs font-semibold cursor-pointer"
                  title="Designate this audit as the authoritative baseline for schema and drift comparison"
                >
                  <BookmarkCheck className="w-3.5 h-3.5" />
                  <span>{settingBaseline ? 'Saving...' : 'Set as Baseline'}</span>
                </button>
              )}
            </div>
          </div>

          {baselineMessage && (
            <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{baselineMessage}</span>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Findings List (2 cols) */}
            <div className="lg:col-span-2 space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span>Showing {filteredFindings.length} of {findings.length} findings</span>
                <span>Severity: <code className="text-slate-300">{selectedSeverity}</code></span>
              </div>

              {filteredFindings.length === 0 ? (
                <div className="p-8 text-center rounded-2xl bg-slate-900/80 border border-slate-800 text-slate-400 text-sm">
                  No findings matching severity filter '{selectedSeverity}'.
                </div>
              ) : (
                filteredFindings.map((f, idx) => {
                  const isExpanded = expandedIndex === idx;
                  return (
                    <div
                      key={idx}
                      className="rounded-2xl bg-slate-900/80 border border-slate-800 overflow-hidden hover:border-slate-700 transition"
                    >
                      <div
                        onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                        className="p-4 cursor-pointer flex items-center justify-between gap-4"
                      >
                        <div className="flex items-center gap-3">
                          <span className={`text-[10px] font-mono px-2.5 py-1 rounded-full font-bold border ${getSeverityBadge(f.severity)}`}>
                            {f.severity}
                          </span>
                          <div>
                            <div className="text-sm font-bold text-white flex items-center gap-2">
                              <span>{f.type}</span>
                              {f.column && (
                                <span className="text-xs font-mono text-emerald-400">({f.column})</span>
                              )}
                            </div>
                            <p className="text-xs text-slate-400 mt-0.5">{f.message}</p>
                          </div>
                        </div>
                        <ChevronRight className={`w-4 h-4 text-slate-500 transition-transform ${isExpanded ? 'rotate-90 text-white' : ''}`} />
                      </div>

                      {isExpanded && (
                        <div className="p-4 bg-slate-950/80 border-t border-slate-800 text-xs space-y-3">
                          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Structured Evidence Payload:</div>
                          <pre className="p-3 rounded-xl bg-slate-900 text-emerald-300 font-mono text-[11px] overflow-x-auto border border-slate-800">
                            {JSON.stringify(f.evidence, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>

            {/* Sidebar: RCA Candidates & Evidence Items (1 col) */}
            <div className="space-y-5">
              {/* Root Cause Candidates */}
              {rcaCandidates.length > 0 && (
                <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-400" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">Root-Cause Hypotheses</h3>
                  </div>
                  <div className="space-y-2">
                    {rcaCandidates.map((rc, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-amber-300">
                            Potential {rc.cause}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-bold">
                            {(rc.confidence * 100).toFixed(1)}% conf
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400">{rc.explanation}</p>
                        <div className="text-[10px] font-mono text-slate-500 pt-1">
                          Area: {rc.affected_area}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Evidence Engine Side Drawer */}
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">Evidence Engine Items</h3>
                </div>
                <p className="text-xs text-slate-400">
                  Downstream reasoning artifacts generated for Recovery and Remediation agents.
                </p>

                <div className="space-y-2.5 max-h-[350px] overflow-y-auto pr-1">
                  {evidenceItems.length === 0 ? (
                    <div className="text-xs text-slate-500">No evidence items built.</div>
                  ) : (
                    evidenceItems.map((ev) => (
                      <div key={ev.evidence_id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold text-emerald-400">{ev.evidence_id}</span>
                          <span className="text-[10px] text-slate-500 font-mono">{ev.finding_type}</span>
                        </div>
                        <p className="text-slate-300 line-clamp-2">{ev.message}</p>
                      </div>
                    ))
                  )}
                </div>

                <div className="pt-3 border-t border-slate-800">
                  <button
                    onClick={() => onNavigate('recovery')}
                    className="w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold flex items-center justify-center gap-1.5 transition"
                  >
                    <span>View Proposed Recovery Actions</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
