import React, { useState, useEffect } from 'react';
import {
  AuditDossier,
  AuditSummaryItem,
  MLDetectionProofResponse,
  ZScoreMethodProof,
  IQRMethodProof,
  IsolationForestMethodProof,
  KSTestMethodProof,
  ZScoreColumnProof,
  IQRColumnProof,
  KSTestColumnProof,
} from '../types';
import { api } from '../services/api';
import {
  Binary,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Clock,
  Database,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Info,
  RefreshCw,
  Search,
  Filter,
  BarChart2,
  Activity,
  Layers,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ScatterChart,
  Scatter,
  ZAxis,
  Cell,
  Legend,
} from 'recharts';

interface MLDetectionProofViewProps {
  dossier: AuditDossier | null;
  onNavigate: (tab: string) => void;
  onSelectDossier?: (dossier: AuditDossier) => void;
}

type MethodType = 'z_score' | 'iqr' | 'isolation_forest' | 'ks_test';

export const MLDetectionProofView: React.FC<MLDetectionProofViewProps> = ({
  dossier,
  onNavigate,
  onSelectDossier,
}) => {
  const [audits, setAudits] = useState<AuditSummaryItem[]>([]);
  const [selectedAuditId, setSelectedAuditId] = useState<string>(dossier?.id || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [proofData, setProofData] = useState<MLDetectionProofResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Active detail modal/tab
  const [activeMethodDetail, setActiveMethodDetail] = useState<MethodType | null>(null);
  const [selectedZColumn, setSelectedZColumn] = useState<string>('');
  const [selectedIQRColumn, setSelectedIQRColumn] = useState<string>('');
  const [selectedKSColumn, setSelectedKSColumn] = useState<string>('');

  // Load audit list for dropdown
  useEffect(() => {
    api.agents
      .listAudits()
      .then((list) => {
        setAudits(list);
        if (!selectedAuditId && list.length > 0) {
          setSelectedAuditId(list[0].id);
        }
      })
      .catch((err) => console.debug('Failed to list audits:', err));
  }, []);

  // Update selectedAuditId when dossier changes
  useEffect(() => {
    if (dossier?.id && dossier.id !== selectedAuditId) {
      setSelectedAuditId(dossier.id);
    }
  }, [dossier?.id]);

  // Load ML proof for selected audit
  const loadProof = async (auditId: string) => {
    if (!auditId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.agents.getMLProof(auditId);
      setProofData(res);
      // Initialize selected columns for drill-down
      if (res.methods.z_score?.columns?.length > 0) {
        setSelectedZColumn(res.methods.z_score.columns[0].column);
      }
      if (res.methods.iqr?.columns?.length > 0) {
        setSelectedIQRColumn(res.methods.iqr.columns[0].column);
      }
      if (res.methods.ks_test?.columns?.length > 0) {
        setSelectedKSColumn(res.methods.ks_test.columns[0].column);
      }
    } catch (err: any) {
      console.error('Failed to load ML proof:', err);
      setError(err.response?.data?.detail || 'Failed to retrieve ML detection proof for this audit run.');
      setProofData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedAuditId) {
      loadProof(selectedAuditId);
    }
  }, [selectedAuditId]);

  const handleAuditChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    setSelectedAuditId(newId);
    if (onSelectDossier) {
      try {
        const fullDossier = await api.agents.getAuditById(newId);
        onSelectDossier(fullDossier);
      } catch (err) {
        console.debug('Failed to sync full dossier:', err);
      }
    }
  };

  const methods = proofData?.methods;
  const zScore = methods?.z_score;
  const iqr = methods?.iqr;
  const isoForest = methods?.isolation_forest;
  const ksTest = methods?.ks_test;

  const renderStatusBadge = (status: string, executed: boolean) => {
    if (!executed || status === 'NOT_EXECUTED' || status === 'NOT_APPLICABLE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/60 text-amber-300 border border-amber-600/40">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          NOT EXECUTED
        </span>
      );
    }
    if (status === 'ANOMALY_DETECTED' || status === 'OUTLIER_DETECTED' || status === 'DRIFT_DETECTED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-950/60 text-rose-300 border border-rose-600/40">
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          DETECTED
        </span>
      );
    }
    if (status === 'HEALTHY' || status === 'STABLE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-600/40">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          HEALTHY
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
        {status}
      </span>
    );
  };

  const getActiveZCol = (): ZScoreColumnProof | undefined => {
    if (!zScore?.columns?.length) return undefined;
    return zScore.columns.find((c) => c.column === selectedZColumn) || zScore.columns[0];
  };

  const getActiveIQRCol = (): IQRColumnProof | undefined => {
    if (!iqr?.columns?.length) return undefined;
    return iqr.columns.find((c) => c.column === selectedIQRColumn) || iqr.columns[0];
  };

  const getActiveKSCol = (): KSTestColumnProof | undefined => {
    if (!ksTest?.columns?.length) return undefined;
    return ksTest.columns.find((c) => c.column === selectedKSColumn) || ksTest.columns[0];
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner & Audit Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider font-mono mb-1">
            <Binary className="w-4 h-4" />
            Auditable Evidence Engine &bull; DataGuard 2.0
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            ML Detection Proof
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Mathematical parameters, statistical bounds, CDF curves, and unsupervised machine learning proofs
            generated on real dataset observations. Fully transparent and verifiable without synthetic accuracy metrics.
          </p>
        </div>

        {/* Audit Run Selector */}
        <div className="flex items-center gap-3 bg-slate-900/80 p-2 rounded-xl border border-slate-800">
          <Database className="w-4 h-4 text-emerald-400 shrink-0" />
          <div className="flex flex-col">
            <span className="text-[10px] uppercase font-mono text-slate-400">Selected Audit Run</span>
            <select
              value={selectedAuditId}
              onChange={handleAuditChange}
              disabled={loading || audits.length === 0}
              aria-label="Selected Audit Run"
              className="bg-transparent text-sm text-slate-200 font-medium focus:outline-none cursor-pointer pr-4"
            >
              {audits.map((a) => (
                <option key={a.id} value={a.id} className="bg-slate-900 text-slate-200">
                  {a.friendly_name || a.dataset_path.split(/[\\/]/).pop()} ({a.status}) —{' '}
                  {new Date(a.created_at).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={() => loadProof(selectedAuditId)}
            disabled={loading}
            title="Refresh ML Proofs"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Meta Bar */}
      {proofData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 text-xs font-mono">
          <div>
            <span className="text-slate-500 block">Inspection ID</span>
            <span className="text-slate-300 font-bold truncate block">{proofData.inspection_id}</span>
          </div>
          <div>
            <span className="text-slate-500 block">Dataset</span>
            <span className="text-emerald-400 font-bold truncate block">{proofData.dataset}</span>
          </div>
          <div>
            <span className="text-slate-500 block">Audited At</span>
            <span className="text-slate-300 block">
              {proofData.created_at ? new Date(proofData.created_at).toLocaleString() : 'Recent Execution'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Governing Agents</span>
            <span className="text-teal-300 block">Inspector Agent & Drift Agent</span>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-300 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">ML Proof Notice:</span> {error}
          </div>
        </div>
      )}

      {/* 4 Method Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* CARD 1: Z-SCORE */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 hover:border-blue-500/40 transition flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-mono uppercase text-blue-400 tracking-wider font-semibold">
                  Method 1 &bull; {zScore?.agent || 'Inspector Agent'}
                </span>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                  Z-Score Anomaly Detection
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Statistical standardized deviation test for extreme values.
                </p>
              </div>
              {renderStatusBadge(zScore?.status || 'NOT_APPLICABLE', !!zScore?.executed)}
            </div>

            {/* Formula Block */}
            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80 font-mono text-xs space-y-1">
              <div className="text-slate-500 text-[10px] uppercase">Mathematical Formula</div>
              <div className="text-blue-300 font-bold">z = (x - μ) / σ</div>
              <div className="text-slate-400 text-[11px]">Flagged when: |z| &gt; 3.0 (99.73% normal range)</div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">COLUMNS</span>
                <span className="text-slate-200 font-bold text-sm">{zScore?.columns_analyzed || 0}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">FLAGGED</span>
                <span className={`font-bold text-sm ${zScore?.total_flagged_count ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {zScore?.total_flagged_count || 0}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">MAX |z|</span>
                <span className="text-cyan-300 font-bold text-sm">
                  {zScore?.max_z_score ? zScore.max_z_score.toFixed(2) : '0.00'}
                </span>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between">
            <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {zScore?.execution_time_ms ? `${zScore.execution_time_ms.toFixed(1)}ms` : 'Instant'}
            </span>
            <button
              onClick={() => setActiveMethodDetail('z_score')}
              className="px-3 py-1.5 rounded-lg bg-blue-600/20 text-blue-300 hover:bg-blue-600/30 border border-blue-500/30 text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <span>View Detailed Evidence</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* CARD 2: IQR */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 hover:border-amber-500/40 transition flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-mono uppercase text-amber-400 tracking-wider font-semibold">
                  Method 2 &bull; {iqr?.agent || 'Inspector Agent'}
                </span>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                  Interquartile Range (IQR)
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Non-parametric quartile outlier fences resistant to skewed distributions.
                </p>
              </div>
              {renderStatusBadge(iqr?.status || 'NOT_APPLICABLE', !!iqr?.executed)}
            </div>

            {/* Formula Block */}
            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80 font-mono text-xs space-y-1">
              <div className="text-slate-500 text-[10px] uppercase">Mathematical Formula</div>
              <div className="text-amber-300 font-bold">IQR = Q3 - Q1</div>
              <div className="text-slate-400 text-[11px]">
                Fences: [Q1 - 1.5×IQR, Q3 + 1.5×IQR]
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">COLUMNS</span>
                <span className="text-slate-200 font-bold text-sm">{iqr?.columns_analyzed || 0}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">OUTLIERS</span>
                <span className={`font-bold text-sm ${iqr?.total_outliers_count ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {iqr?.total_outliers_count || 0}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">MULTIPLIER</span>
                <span className="text-cyan-300 font-bold text-sm">1.5 × IQR</span>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between">
            <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {iqr?.execution_time_ms ? `${iqr.execution_time_ms.toFixed(1)}ms` : 'Instant'}
            </span>
            <button
              onClick={() => setActiveMethodDetail('iqr')}
              className="px-3 py-1.5 rounded-lg bg-amber-600/20 text-amber-300 hover:bg-amber-600/30 border border-amber-500/30 text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <span>View Detailed Evidence</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* CARD 3: ISOLATION FOREST */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 hover:border-purple-500/40 transition flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-mono uppercase text-purple-400 tracking-wider font-semibold">
                  Method 3 &bull; {isoForest?.agent || 'Inspector Agent'}
                </span>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                  Isolation Forest ML
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Ensemble tree-based unsupervised isolation of multivariate anomalies.
                </p>
              </div>
              {renderStatusBadge(isoForest?.status || 'NOT_APPLICABLE', !!isoForest?.executed)}
            </div>

            {/* Parameter Block */}
            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80 font-mono text-xs space-y-1">
              <div className="text-slate-500 text-[10px] uppercase">Model Specification</div>
              <div className="text-purple-300 font-bold">
                n_estimators={isoForest?.model_parameters?.n_estimators || 100}, contamination={String(isoForest?.contamination || 'auto')}
              </div>
              <div className="text-slate-400 text-[11px]">
                Separation threshold: {isoForest?.separation_threshold?.toFixed(4) || '0.0000'} | Decision: -1 = anomaly
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">FEATURES</span>
                <span className="text-slate-200 font-bold text-sm">{isoForest?.features_count || 0}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">ANOMALIES</span>
                <span className={`font-bold text-sm ${isoForest?.anomalies_detected ? 'text-purple-400' : 'text-emerald-400'}`}>
                  {isoForest?.anomalies_detected || 0}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">SAMPLES</span>
                <span className="text-cyan-300 font-bold text-sm">{isoForest?.samples || 0}</span>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between">
            <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {isoForest?.execution_time_ms ? `${isoForest.execution_time_ms.toFixed(1)}ms` : 'Instant'}
            </span>
            <button
              onClick={() => setActiveMethodDetail('isolation_forest')}
              className="px-3 py-1.5 rounded-lg bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 border border-purple-500/30 text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <span>View Detailed Evidence</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* CARD 4: KS TWO-SAMPLE TEST */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 hover:border-teal-500/40 transition flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-mono uppercase text-teal-400 tracking-wider font-semibold">
                  Method 4 &bull; {ksTest?.agent || 'Drift Agent'}
                </span>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                  Kolmogorov-Smirnov Test
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Non-parametric empirical cumulative distribution shift (two-sample).
                </p>
              </div>
              {renderStatusBadge(ksTest?.status || 'NOT_EXECUTED', !!ksTest?.executed)}
            </div>

            {/* Formula Block / Transparent Reason */}
            {ksTest?.executed ? (
              <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80 font-mono text-xs space-y-1">
                <div className="text-slate-500 text-[10px] uppercase">Decision Rule</div>
                <div className="text-teal-300 font-bold">D = sup|F_curr(x) - F_base(x)|</div>
                <div className="text-slate-400 text-[11px]">
                  Drift flagged when: p &lt; 0.05 AND D &ge; 0.10
                </div>
              </div>
            ) : (
              <div className="p-3 bg-amber-950/40 rounded-xl border border-amber-800/60 font-mono text-xs space-y-1">
                <div className="text-amber-400 text-[10px] uppercase font-bold flex items-center gap-1">
                  <Info className="w-3 h-3" />
                  Transparent Execution State
                </div>
                <div className="text-amber-200">
                  Status: NOT EXECUTED &bull; Reason: {ksTest?.reason || 'historical baseline unavailable'}
                </div>
                <div className="text-slate-400 text-[11px]">
                  First audit of dataset. Set as baseline to compare future audits.
                </div>
              </div>
            )}

            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">TESTED</span>
                <span className="text-slate-200 font-bold text-sm">{ksTest?.columns_tested || 0}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">DRIFT COLS</span>
                <span className={`font-bold text-sm ${ksTest?.drift_detected_count ? 'text-teal-400' : 'text-emerald-400'}`}>
                  {ksTest?.drift_detected_count || 0}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                <span className="text-slate-500 text-[10px] block">ALPHA (α)</span>
                <span className="text-cyan-300 font-bold text-sm">0.05</span>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between">
            <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {ksTest?.execution_time_ms ? `${ksTest.execution_time_ms.toFixed(1)}ms` : 'N/A'}
            </span>
            <button
              onClick={() => setActiveMethodDetail('ks_test')}
              className="px-3 py-1.5 rounded-lg bg-teal-600/20 text-teal-300 hover:bg-teal-600/30 border border-teal-500/30 text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <span>View Detailed Evidence</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* DETAILED EVIDENCE MODAL / DRAWER */}
      {activeMethodDetail && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-slate-800 text-emerald-400">
                  <Binary className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-100">
                    {activeMethodDetail === 'z_score' && 'Z-Score Statistical Evidence Proof'}
                    {activeMethodDetail === 'iqr' && 'Interquartile Range (IQR) Outlier Proof'}
                    {activeMethodDetail === 'isolation_forest' && 'Isolation Forest ML Decision Score Proof'}
                    {activeMethodDetail === 'ks_test' && 'Kolmogorov-Smirnov Two-Sample Test Proof'}
                  </h2>
                  <p className="text-xs font-mono text-slate-400">
                    {activeMethodDetail === 'z_score' && 'Audited by Inspector Agent &bull; Formula: z = (x - mean) / std'}
                    {activeMethodDetail === 'iqr' && 'Audited by Inspector Agent &bull; Formula: IQR = Q3 - Q1'}
                    {activeMethodDetail === 'isolation_forest' && 'Audited by Inspector Agent &bull; Model: Scikit-Learn IsolationForest'}
                    {activeMethodDetail === 'ks_test' && 'Audited by Drift Agent &bull; Method: scipy.stats.ks_2samp'}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setActiveMethodDetail(null)}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* DETAIL 1: Z-SCORE */}
              {activeMethodDetail === 'z_score' && (
                <div className="space-y-6">
                  {/* Column Selector */}
                  {zScore && zScore.columns.length > 0 ? (
                    <>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-slate-400">Select Analyzed Column:</span>
                        <div className="flex flex-wrap gap-2">
                          {zScore.columns.map((col) => (
                            <button
                              key={col.column}
                              onClick={() => setSelectedZColumn(col.column)}
                              className={`px-3 py-1 rounded-lg text-xs font-mono font-medium transition ${
                                (selectedZColumn || zScore.columns[0].column) === col.column
                                  ? 'bg-blue-600 text-white font-bold'
                                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                              }`}
                            >
                              {col.column} ({col.flagged_count} flagged)
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Active Column Parameters Table */}
                      {(() => {
                        const activeCol = getActiveZCol();
                        if (!activeCol) return null;
                        return (
                          <>
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs font-mono border border-slate-800 rounded-xl overflow-hidden">
                                <thead className="bg-slate-950 text-slate-400 text-left border-b border-slate-800">
                                  <tr>
                                    <th className="p-3">COLUMN</th>
                                    <th className="p-3">SAMPLE SIZE (N)</th>
                                    <th className="p-3">MEAN (μ)</th>
                                    <th className="p-3">STD DEV (σ)</th>
                                    <th className="p-3">THRESHOLD</th>
                                    <th className="p-3">MAX |Z|</th>
                                    <th className="p-3">FLAGGED</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800 bg-slate-900/40">
                                  <tr>
                                    <td className="p-3 font-bold text-slate-200">{activeCol.column}</td>
                                    <td className="p-3 text-slate-300">{activeCol.sample_size}</td>
                                    <td className="p-3 text-cyan-300">{activeCol.mean.toFixed(4)}</td>
                                    <td className="p-3 text-cyan-300">{activeCol.std_dev.toFixed(4)}</td>
                                    <td className="p-3 text-blue-300 font-bold">{activeCol.threshold}</td>
                                    <td className="p-3 text-rose-300 font-bold">{activeCol.max_z_score.toFixed(3)}</td>
                                    <td className="p-3 text-amber-300 font-bold">{activeCol.flagged_count}</td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>

                            {/* Chart: Z-Score Sample Distribution */}
                            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
                              <div className="flex items-center justify-between text-xs font-mono">
                                <span className="text-slate-400 font-bold">Standardized Deviation Plot (|z| Distribution)</span>
                                <span className="text-slate-500">Threshold: ±3.0σ</span>
                              </div>
                              <div className="h-56 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                  <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis
                                      type="number"
                                      dataKey="value"
                                      name="Value"
                                      stroke="#94a3b8"
                                      fontSize={11}
                                      tickFormatter={(v) => Number(v).toFixed(1)}
                                    />
                                    <YAxis
                                      type="number"
                                      dataKey="z_score"
                                      name="Z-Score"
                                      stroke="#94a3b8"
                                      fontSize={11}
                                      domain={['auto', 'auto']}
                                    />
                                    <Tooltip
                                      cursor={{ strokeDasharray: '3 3' }}
                                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                                    />
                                    <ReferenceLine y={3.0} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: '+3.0 Threshold', fill: '#f43f5e', fontSize: 10 }} />
                                    <ReferenceLine y={-3.0} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: '-3.0 Threshold', fill: '#f43f5e', fontSize: 10 }} />
                                    <Scatter
                                      name="Observations"
                                      data={activeCol.distribution_sample || []}
                                      fill="#38bdf8"
                                    >
                                      {(activeCol.distribution_sample || []).map((entry, index) => (
                                        <Cell
                                          key={`cell-${index}`}
                                          fill={entry.is_anomaly ? '#f43f5e' : '#38bdf8'}
                                        />
                                      ))}
                                    </Scatter>
                                  </ScatterChart>
                                </ResponsiveContainer>
                              </div>
                            </div>

                            {/* Flagged Observations Table */}
                            {activeCol.flagged_values.length > 0 ? (
                              <div className="space-y-2">
                                <span className="text-xs font-mono font-bold text-slate-300 block">
                                  Flagged Anomaly Instances (Rows with |z| &gt; 3.0)
                                </span>
                                <div className="max-h-48 overflow-y-auto border border-slate-800 rounded-xl">
                                  <table className="w-full text-xs font-mono">
                                    <thead className="bg-slate-950 text-slate-400 text-left sticky top-0 border-b border-slate-800">
                                      <tr>
                                        <th className="p-2.5">ROW INDEX</th>
                                        <th className="p-2.5">OBSERVED VALUE</th>
                                        <th className="p-2.5">CALCULATED Z-SCORE</th>
                                        <th className="p-2.5">THRESHOLD</th>
                                        <th className="p-2.5 text-right">ACTION</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800 bg-slate-900/30">
                                      {activeCol.flagged_values.map((item, idx) => (
                                        <tr key={idx} className="hover:bg-slate-800/40">
                                          <td className="p-2.5 text-slate-300 font-bold">{item.row_index}</td>
                                          <td className="p-2.5 text-rose-300 font-bold">{item.value}</td>
                                          <td className="p-2.5 text-cyan-300">{item.z_score.toFixed(4)}</td>
                                          <td className="p-2.5 text-slate-400">|z| &gt; {item.threshold}</td>
                                          <td className="p-2.5 text-right">
                                            <button
                                              onClick={() => onNavigate('findings')}
                                              className="text-[11px] text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-1 font-semibold"
                                            >
                                              View Finding <ExternalLink className="w-3 h-3" />
                                            </button>
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            ) : (
                              <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-center text-xs font-mono text-emerald-400">
                                ✓ No observations exceeded the |z| &gt; 3.0 threshold for column &quot;{activeCol.column}&quot;.
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </>
                  ) : (
                    <div className="p-6 text-center text-sm font-mono text-slate-400">
                      No numerical columns evaluated for Z-Score on this dataset.
                    </div>
                  )}
                </div>
              )}

              {/* DETAIL 2: IQR */}
              {activeMethodDetail === 'iqr' && (
                <div className="space-y-6">
                  {iqr && iqr.columns.length > 0 ? (
                    <>
                      {/* Column Selector */}
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-slate-400">Select Analyzed Column:</span>
                        <div className="flex flex-wrap gap-2">
                          {iqr.columns.map((col) => (
                            <button
                              key={col.column}
                              onClick={() => setSelectedIQRColumn(col.column)}
                              className={`px-3 py-1 rounded-lg text-xs font-mono font-medium transition ${
                                (selectedIQRColumn || iqr.columns[0].column) === col.column
                                  ? 'bg-amber-600 text-white font-bold'
                                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                              }`}
                            >
                              {col.column} ({col.outlier_count} outliers)
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Active Column Parameters Table */}
                      {(() => {
                        const activeCol = getActiveIQRCol();
                        if (!activeCol) return null;
                        return (
                          <>
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs font-mono border border-slate-800 rounded-xl overflow-hidden">
                                <thead className="bg-slate-950 text-slate-400 text-left border-b border-slate-800">
                                  <tr>
                                    <th className="p-3">COLUMN</th>
                                    <th className="p-3">Q1 (25%)</th>
                                    <th className="p-3">MEDIAN</th>
                                    <th className="p-3">Q3 (75%)</th>
                                    <th className="p-3">IQR</th>
                                    <th className="p-3">LOWER BOUND</th>
                                    <th className="p-3">UPPER BOUND</th>
                                    <th className="p-3">OUTLIERS</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800 bg-slate-900/40">
                                  <tr>
                                    <td className="p-3 font-bold text-slate-200">{activeCol.column}</td>
                                    <td className="p-3 text-cyan-300">{activeCol.q1.toFixed(2)}</td>
                                    <td className="p-3 text-cyan-300">{activeCol.median.toFixed(2)}</td>
                                    <td className="p-3 text-cyan-300">{activeCol.q3.toFixed(2)}</td>
                                    <td className="p-3 text-amber-300 font-bold">{activeCol.iqr.toFixed(2)}</td>
                                    <td className="p-3 text-rose-300 font-bold">{activeCol.lower_bound.toFixed(2)}</td>
                                    <td className="p-3 text-rose-300 font-bold">{activeCol.upper_bound.toFixed(2)}</td>
                                    <td className="p-3 text-amber-300 font-bold">{activeCol.outlier_count}</td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>

                            {/* Visual Boxplot Breakdown Card */}
                            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-3">
                              <span className="text-xs font-mono font-bold text-slate-400 block">
                                Quartile Range & Outlier Boundaries:
                              </span>
                              <div className="relative pt-6 pb-2 px-4 font-mono text-xs">
                                {/* Visual Bar representing distribution */}
                                <div className="h-6 w-full bg-slate-800 rounded-lg relative overflow-hidden flex items-center">
                                  <div className="absolute inset-y-0 bg-blue-600/30 border-x-2 border-blue-400 w-1/2 left-1/4 flex items-center justify-center text-[10px] text-blue-200">
                                    IQR Box [Q1 to Q3]
                                  </div>
                                </div>
                                <div className="flex justify-between text-[11px] text-slate-400 mt-2">
                                  <span>Lower Fence: {activeCol.lower_bound.toFixed(2)}</span>
                                  <span>Q1: {activeCol.q1.toFixed(2)}</span>
                                  <span>Median: {activeCol.median.toFixed(2)}</span>
                                  <span>Q3: {activeCol.q3.toFixed(2)}</span>
                                  <span>Upper Fence: {activeCol.upper_bound.toFixed(2)}</span>
                                </div>
                              </div>
                            </div>

                            {/* Outliers Table */}
                            {activeCol.outliers.length > 0 ? (
                              <div className="space-y-2">
                                <span className="text-xs font-mono font-bold text-slate-300 block">
                                  Flagged Outlier Instances
                                </span>
                                <div className="max-h-48 overflow-y-auto border border-slate-800 rounded-xl">
                                  <table className="w-full text-xs font-mono">
                                    <thead className="bg-slate-950 text-slate-400 text-left sticky top-0 border-b border-slate-800">
                                      <tr>
                                        <th className="p-2.5">ROW INDEX</th>
                                        <th className="p-2.5">OBSERVED VALUE</th>
                                        <th className="p-2.5">VIOLATED BOUND</th>
                                        <th className="p-2.5">BOUND LIMIT</th>
                                        <th className="p-2.5 text-right">ACTION</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800 bg-slate-900/30">
                                      {activeCol.outliers.map((item, idx) => (
                                        <tr key={idx} className="hover:bg-slate-800/40">
                                          <td className="p-2.5 text-slate-300 font-bold">{item.row_index}</td>
                                          <td className="p-2.5 text-amber-300 font-bold">{item.value}</td>
                                          <td className="p-2.5 text-rose-300 uppercase">{item.bound_violated}</td>
                                          <td className="p-2.5 text-slate-400">{item.bound_value.toFixed(2)}</td>
                                          <td className="p-2.5 text-right">
                                            <button
                                              onClick={() => onNavigate('findings')}
                                              className="text-[11px] text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-1 font-semibold"
                                            >
                                              View Finding <ExternalLink className="w-3 h-3" />
                                            </button>
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            ) : (
                              <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-center text-xs font-mono text-emerald-400">
                                ✓ No outliers detected outside the 1.5×IQR fences for column &quot;{activeCol.column}&quot;.
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </>
                  ) : (
                    <div className="p-6 text-center text-sm font-mono text-slate-400">
                      No IQR calculations available for this dataset.
                    </div>
                  )}
                </div>
              )}

              {/* DETAIL 3: ISOLATION FOREST */}
              {activeMethodDetail === 'isolation_forest' && (
                <div className="space-y-6">
                  {isoForest ? (
                    <>
                      {/* Parameters Table */}
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs font-mono border border-slate-800 rounded-xl overflow-hidden">
                          <thead className="bg-slate-950 text-slate-400 text-left border-b border-slate-800">
                            <tr>
                              <th className="p-3">ESTIMATORS</th>
                              <th className="p-3">CONTAMINATION</th>
                              <th className="p-3">RANDOM STATE</th>
                              <th className="p-3">SAMPLES</th>
                              <th className="p-3">FEATURES COUNT</th>
                              <th className="p-3">SEPARATION THRESHOLD</th>
                              <th className="p-3">ANOMALIES</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800 bg-slate-900/40">
                            <tr>
                              <td className="p-3 font-bold text-slate-200">
                                {isoForest.model_parameters?.n_estimators || 100}
                              </td>
                              <td className="p-3 text-cyan-300">{String(isoForest.contamination || 'auto')}</td>
                              <td className="p-3 text-cyan-300">
                                {isoForest.model_parameters?.random_state || 42}
                              </td>
                              <td className="p-3 text-slate-300">{isoForest.samples}</td>
                              <td className="p-3 text-slate-300">{isoForest.features_count}</td>
                              <td className="p-3 text-purple-300 font-bold">
                                {isoForest.separation_threshold?.toFixed(4) || '0.0000'}
                              </td>
                              <td className="p-3 text-rose-300 font-bold">{isoForest.anomalies_detected}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>

                      {/* Analyzed Features Pill List */}
                      <div className="space-y-1.5 font-mono text-xs">
                        <span className="text-slate-400">Trained Features:</span>
                        <div className="flex flex-wrap gap-2">
                          {isoForest.features.map((feat) => (
                            <span key={feat} className="px-2.5 py-1 bg-slate-800 border border-slate-700 rounded-lg text-slate-200">
                              {feat}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Chart: Anomaly Score Distribution Histogram */}
                      {isoForest.score_distribution?.length > 0 && (
                        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="text-slate-400 font-bold">
                              Isolation Forest Decision Score Histogram
                            </span>
                            <span className="text-purple-400">Score &lt; 0.0 denotes Anomaly</span>
                          </div>
                          <div className="h-56 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={isoForest.score_distribution} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="bin" stroke="#94a3b8" fontSize={11} />
                                <YAxis stroke="#94a3b8" fontSize={11} />
                                <Tooltip
                                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                                />
                                <Bar dataKey="count" name="Observations">
                                  {isoForest.score_distribution.map((entry, index) => (
                                    <Cell
                                      key={`bar-${index}`}
                                      fill={entry.is_anomaly_bin ? '#ec4899' : '#14b8a6'}
                                    />
                                  ))}
                                </Bar>
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>
                      )}

                      {/* Flagged Anomalies Table */}
                      {isoForest.flagged_anomalies?.length > 0 ? (
                        <div className="space-y-2">
                          <span className="text-xs font-mono font-bold text-slate-300 block">
                            Flagged Multidimensional Anomaly Instances (prediction = -1)
                          </span>
                          <div className="max-h-48 overflow-y-auto border border-slate-800 rounded-xl">
                            <table className="w-full text-xs font-mono">
                              <thead className="bg-slate-950 text-slate-400 text-left sticky top-0 border-b border-slate-800">
                                <tr>
                                  <th className="p-2.5">ROW INDEX</th>
                                  <th className="p-2.5">DECISION SCORE</th>
                                  <th className="p-2.5">PREDICTION</th>
                                  <th className="p-2.5">SAMPLE FEATURES</th>
                                  <th className="p-2.5 text-right">ACTION</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-800 bg-slate-900/30">
                                {isoForest.flagged_anomalies.map((item, idx) => (
                                  <tr key={idx} className="hover:bg-slate-800/40">
                                    <td className="p-2.5 text-slate-300 font-bold">{item.row_index}</td>
                                    <td className="p-2.5 text-purple-300 font-bold">
                                      {item.decision_score?.toFixed(4)}
                                    </td>
                                    <td className="p-2.5 text-rose-400 font-bold">{item.prediction}</td>
                                    <td className="p-2.5 text-slate-400 truncate max-w-xs">
                                      {JSON.stringify(item.features)}
                                    </td>
                                    <td className="p-2.5 text-right">
                                      <button
                                        onClick={() => onNavigate('findings')}
                                        className="text-[11px] text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-1 font-semibold"
                                      >
                                        View Finding <ExternalLink className="w-3 h-3" />
                                      </button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ) : (
                        <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-center text-xs font-mono text-emerald-400">
                          ✓ No multivariate isolation forest anomalies detected.
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="p-6 text-center text-sm font-mono text-slate-400">
                      Isolation Forest model not executed.
                    </div>
                  )}
                </div>
              )}

              {/* DETAIL 4: KS TWO-SAMPLE TEST */}
              {activeMethodDetail === 'ks_test' && (
                <div className="space-y-6">
                  {ksTest?.executed ? (
                    <>
                      {/* Column Selector */}
                      {ksTest.columns.length > 0 && (
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-slate-400">Select Analyzed Column:</span>
                          <div className="flex flex-wrap gap-2">
                            {ksTest.columns.map((col) => (
                              <button
                                key={col.column}
                                onClick={() => setSelectedKSColumn(col.column)}
                                className={`px-3 py-1 rounded-lg text-xs font-mono font-medium transition ${
                                  (selectedKSColumn || ksTest.columns[0].column) === col.column
                                    ? 'bg-teal-600 text-white font-bold'
                                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                }`}
                              >
                                {col.column} ({col.decision})
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Active Column Parameters Table */}
                      {(() => {
                        const activeCol = getActiveKSCol();
                        if (!activeCol) return null;
                        return (
                          <>
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs font-mono border border-slate-800 rounded-xl overflow-hidden">
                                <thead className="bg-slate-950 text-slate-400 text-left border-b border-slate-800">
                                  <tr>
                                    <th className="p-3">COLUMN</th>
                                    <th className="p-3">N_BASE</th>
                                    <th className="p-3">N_CURR</th>
                                    <th className="p-3">KS STATISTIC (D)</th>
                                    <th className="p-3">P-VALUE</th>
                                    <th className="p-3">THRESHOLD</th>
                                    <th className="p-3">DECISION</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800 bg-slate-900/40">
                                  <tr>
                                    <td className="p-3 font-bold text-slate-200">{activeCol.column}</td>
                                    <td className="p-3 text-slate-300">{activeCol.baseline_sample_size}</td>
                                    <td className="p-3 text-slate-300">{activeCol.current_sample_size}</td>
                                    <td className="p-3 text-teal-300 font-bold">{activeCol.ks_statistic.toFixed(4)}</td>
                                    <td className="p-3 text-cyan-300">{activeCol.p_value.toExponential(4)}</td>
                                    <td className="p-3 text-slate-400">p &lt; 0.05, D &ge; 0.10</td>
                                    <td className="p-3 font-bold">
                                      {activeCol.is_drift ? (
                                        <span className="text-rose-400">DRIFT DETECTED</span>
                                      ) : (
                                        <span className="text-emerald-400">NO DRIFT</span>
                                      )}
                                    </td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>

                            {/* Empirical CDF Curves Chart */}
                            {activeCol.cdf_curve?.length > 0 && (
                              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
                                <div className="flex items-center justify-between text-xs font-mono">
                                  <span className="text-slate-400 font-bold">
                                    Empirical Cumulative Distribution Functions (eCDF)
                                  </span>
                                  <span className="text-teal-400 font-semibold">
                                    D-Statistic = {activeCol.ks_statistic.toFixed(4)} (Max vertical delta)
                                  </span>
                                </div>
                                <div className="h-56 w-full">
                                  <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={activeCol.cdf_curve} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                      <XAxis
                                        dataKey="x"
                                        stroke="#94a3b8"
                                        fontSize={11}
                                        tickFormatter={(v) => Number(v).toFixed(1)}
                                      />
                                      <YAxis
                                        stroke="#94a3b8"
                                        fontSize={11}
                                        domain={[0, 1]}
                                        tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                                      />
                                      <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                                      />
                                      <Legend />
                                      <Line
                                        type="stepAfter"
                                        dataKey="baseline_cdf"
                                        name="Baseline eCDF"
                                        stroke="#38bdf8"
                                        strokeWidth={2}
                                        dot={false}
                                      />
                                      <Line
                                        type="stepAfter"
                                        dataKey="current_cdf"
                                        name="Current eCDF"
                                        stroke="#f59e0b"
                                        strokeWidth={2}
                                        dot={false}
                                      />
                                    </LineChart>
                                  </ResponsiveContainer>
                                </div>
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </>
                  ) : (
                    /* Transparent NOT EXECUTED Explanation */
                    <div className="p-6 rounded-2xl bg-amber-950/30 border border-amber-800/60 space-y-4">
                      <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl bg-amber-900/50 text-amber-400">
                          <AlertTriangle className="w-6 h-6" />
                        </div>
                        <div>
                          <h3 className="text-base font-bold text-amber-200">
                            Transparent State: Kolmogorov-Smirnov Test Not Executed
                          </h3>
                          <p className="text-xs font-mono text-amber-400/80">
                            Reason: {ksTest?.reason || 'historical baseline unavailable'}
                          </p>
                        </div>
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed">
                        The Kolmogorov-Smirnov Two-Sample Test requires two empirical datasets: a verified reference
                        baseline distribution and the current audit batch. Because this is the initial audit of this
                        dataset, no prior distribution was registered. Rather than inventing or fabricating synthetic
                        confidence metrics, DataGuard 2.0 strictly reports{' '}
                        <span className="font-bold text-amber-300">NOT EXECUTED</span>.
                      </p>

                      <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 font-mono text-xs text-slate-400 space-y-1">
                        <div>&bull; Test: Two-sample KS test (scipy.stats.ks_2samp)</div>
                        <div>&bull; Required Baseline Size: &ge; 10 numeric observations</div>
                        <div>&bull; Action: Set this audit as the reference baseline in the Findings tab to enable KS drift testing on subsequent ingestion runs.</div>
                      </div>

                      <button
                        onClick={() => onNavigate('findings')}
                        className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-2 transition"
                      >
                        <span>Go to Findings Tab to Set Baseline</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-500">
                Auditable ML Evidence &bull; DataGuard 2.0 Mathematical Engine
              </span>
              <button
                onClick={() => setActiveMethodDetail(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
