import React, { useState } from 'react';
import { api } from '../services/api';
import {
  PlayCircle,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
  FileDown,
  Sparkles,
  Zap,
} from 'lucide-react';

interface SimulatorViewProps {
  onInspectionDone: (dossier: any) => void;
  onNavigate: (tab: string) => void;
}

export const SimulatorView: React.FC<SimulatorViewProps> = ({ onInspectionDone, onNavigate }) => {
  const [datasetPath, setDatasetPath] = useState('olist/olist_orders_dataset.csv');
  const [mode, setMode] = useState('MISSING_VALUES');
  const [sampleSize, setSampleSize] = useState(500);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const faultModes = [
    {
      id: 'CLEAN',
      title: 'Clean Baseline Run',
      desc: 'Simulates normal healthy ETL pipeline with no anomalies.',
      badge: 'Normal',
      color: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
    },
    {
      id: 'MISSING_VALUES',
      title: 'Missing Values Injection',
      desc: 'Injects 20% null / empty strings into critical key columns.',
      badge: 'Quality Anomaly',
      color: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
    },
    {
      id: 'DUPLICATES',
      title: 'Duplicate Records Surge',
      desc: 'Injects duplicate transaction records simulating replay failure.',
      badge: 'Integrity Anomaly',
      color: 'border-red-500/40 bg-red-500/10 text-red-300',
    },
    {
      id: 'SCHEMA_DRIFT',
      title: 'Breaking Schema Drift',
      desc: 'Removes an expected column from the extraction stream.',
      badge: 'Schema Drift',
      color: 'border-purple-500/40 bg-purple-500/10 text-purple-300',
    },
    {
      id: 'ML_OUTLIERS',
      title: 'ML Numerical Outliers',
      desc: 'Injects multivariate outliers detected by Isolation Forest.',
      badge: 'ML Anomaly',
      color: 'border-blue-500/40 bg-blue-500/10 text-blue-300',
    },
    {
      id: 'DISASTER',
      title: 'Composite Disaster Scenario',
      desc: 'Simultaneous multi-fault corruption: nulls + dups + schema break + outliers.',
      badge: 'Critical Multi-Fault',
      color: 'border-red-600/50 bg-red-900/20 text-red-400',
    },
  ];

  const [availableDatasets, setAvailableDatasets] = useState<Array<{ name: string; path: string }>>([
    { name: 'Olist Orders (E-Commerce Transactions)', path: 'olist/olist_orders_dataset.csv' },
    { name: 'Olist Order Items (Prices & Freight)', path: 'olist/olist_order_items_dataset.csv' },
    { name: 'Olist Customers (Geo & Customer IDs)', path: 'olist/olist_customers_dataset.csv' },
    { name: 'Olist Products (Categories & Dimensions)', path: 'olist/olist_products_dataset.csv' },
    { name: 'Test Anomaly Sample (Controlled Faults)', path: 'test/inspection_anomaly_dataset.csv' },
  ]);

  React.useEffect(() => {
    Promise.all([
      api.datasets.getBenchmarks().catch(() => []),
      api.datasets.list().catch(() => []),
    ]).then(([benchmarks, registered]) => {
      const combined: Array<{ name: string; path: string }> = [];
      benchmarks.forEach((b: any) => combined.push({ name: `${b.name} (${b.category})`, path: b.file_path }));
      registered.forEach((r: any) => combined.push({ name: `${r.dataset_name} (Uploaded)`, path: r.file_path }));
      if (combined.length > 0) {
        setAvailableDatasets(combined);
      }
    });
  }, []);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.agents.simulatePipeline(datasetPath, mode, sampleSize);
      setResult(res);
      onInspectionDone(res.audit);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Simulation execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-5 h-5 text-emerald-400" />
          <h2 className="text-2xl font-black text-white tracking-tight">ETL Pipeline Fault Simulator</h2>
        </div>
        <p className="text-sm text-slate-400">
          Inject controlled anomalies into real Olist datasets and observe the DataGuard multi-agent swarm detect, diagnose, and propose recovery.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Simulator Control Panel */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        {/* Dataset and sample selector */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Select Target Dataset
            </label>
            <select
              value={datasetPath}
              onChange={(e) => setDatasetPath(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white font-mono focus:border-emerald-500 outline-none"
            >
              {availableDatasets.map((ds) => (
                <option key={ds.path} value={ds.path}>
                  {ds.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Pipeline Batch Size
            </label>
            <div className="grid grid-cols-4 gap-2">
              {[100, 300, 500, 1000].map((size) => (
                <button
                  key={size}
                  type="button"
                  onClick={() => setSampleSize(size)}
                  className={`py-2 rounded-xl text-xs font-mono font-bold border transition ${
                    sampleSize === size
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  {size} rows
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Fault Injection Modes */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
            Select Anomaly Injection Scenario
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {faultModes.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setMode(item.id)}
                className={`p-4 rounded-xl border text-left transition relative flex flex-col justify-between ${
                  mode === item.id
                    ? `${item.color} shadow-lg ring-1 ring-white/10`
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-400'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-sm text-white">{item.title}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border border-current">
                      {item.badge}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Trigger Button */}
        <div className="pt-2">
          <button
            onClick={runSimulation}
            disabled={loading}
            className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-xl shadow-emerald-950 flex items-center justify-center gap-2.5 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Simulating ETL Pipeline & Triggering Agents...</span>
              </>
            ) : (
              <>
                <Zap className="w-5 h-5 text-yellow-300" />
                <span>Execute Pipeline & Trigger Multi-Agent Swarm</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Live Simulation Results */}
      {result && (
        <div className="space-y-6 animate-fadeIn">
          {/* Status Bar */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              {result.audit.audit_status === 'HEALTHY' ? (
                <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
              ) : (
                <div className="w-10 h-10 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30 flex items-center justify-center">
                  <ShieldAlert className="w-6 h-6" />
                </div>
              )}
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-black text-white">{result.audit.audit_status}</span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                    {result.final_row_count} rows audited
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Injected: {result.injected_faults.join('; ') || 'Zero faults (clean baseline)'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {result.audit.reports?.pdf_filename && (
                <a
                  href={api.agents.getReportDownloadUrl(result.audit.reports.pdf_filename)}
                  target="_blank"
                  rel="noreferrer"
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 transition"
                >
                  <FileDown className="w-4 h-4 text-emerald-400" />
                  <span>Download PDF Audit</span>
                </a>
              )}
              <button
                onClick={() => onNavigate('recovery')}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow transition"
              >
                <span>Go to Recovery Console</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Root Cause & Recommendations preview cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Root Cause Card */}
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-400">
                Root Cause Agent Diagnosis
              </span>
              <h3 className="text-base font-extrabold text-white">
                {result.audit.root_cause?.primary_cause || 'Healthy Pipeline'}
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                {result.audit.root_cause?.summary}
              </p>
              <div className="text-xs font-mono text-emerald-400 font-semibold pt-1">
                Diagnostic Confidence: {(result.audit.root_cause?.overall_confidence || 0) * 100}%
              </div>
            </div>

            {/* Recommendations Card */}
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-teal-400">
                Recommendation Agent Action Plan
              </span>
              <div className="space-y-2">
                {result.audit.recommendations?.recommendations.slice(0, 2).map((rec: any) => (
                  <div key={rec.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-xs">
                    <div className="flex items-center justify-between text-slate-200 font-bold mb-1">
                      <span>{rec.title}</span>
                      <span className="text-[10px] text-emerald-400 font-mono">{rec.priority}</span>
                    </div>
                    <p className="text-slate-400 line-clamp-2">{rec.rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
