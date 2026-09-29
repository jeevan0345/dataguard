import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  BenchmarkDataset,
  RegisteredDataset,
  SyntheticScenario,
} from '../types';
import {
  Database,
  Upload,
  Play,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Sparkles,
  ArrowRight,
  RefreshCw,
  HardDrive,
  FileCheck,
} from 'lucide-react';
import { ErrorBoundary } from '../components/ErrorBoundary';

interface DatasetsViewProps {
  onAuditDataset: (path: string) => void;
  onNavigate?: (tab: string) => void;
  onAuditDossierLoaded?: (dossier: any) => void;
}

export const DatasetsView: React.FC<DatasetsViewProps> = ({
  onAuditDataset,
  onNavigate,
  onAuditDossierLoaded,
}) => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'upload' | 'benchmark' | 'synthetic'>('upload');
  
  // Datasets state
  const [benchmarks, setBenchmarks] = useState<BenchmarkDataset[]>([]);
  const [scenarios, setScenarios] = useState<SyntheticScenario[]>([]);
  const [registered, setRegistered] = useState<RegisteredDataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState<{ message: string; status?: number } | null>(null);

  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<RegisteredDataset | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const canUpload = user?.role === 'ADMIN' || user?.role === 'DATA_ENGINEER';

  const loadData = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const [benchList, scenList, regList] = await Promise.all([
        api.datasets.getBenchmarks().catch(() => []),
        api.datasets.getSyntheticScenarios().catch(() => []),
        api.datasets.list().catch(() => []),
      ]);
      setBenchmarks(Array.isArray(benchList) ? benchList : []);
      setScenarios(Array.isArray(scenList) ? scenList : []);
      setRegistered(Array.isArray(regList) ? regList : []);
    } catch (err: any) {
      console.error('Failed to load dataset registry:', err);
      setApiError({
        message: err.response?.data?.detail || err.message || 'Failed to connect to Dataset Registry backend.',
        status: err.response?.status,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    setUploadSuccess(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const validExts = ['.csv', '.json', '.xlsx'];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!validExts.includes(ext)) {
        setUploadError(`Invalid file format: ${ext}. Supported: CSV, JSON, XLSX`);
        return;
      }
      if (file.size > 50 * 1024 * 1024) {
        setUploadError('File size exceeds the 50MB maximum limit.');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    setUploadError(null);
    try {
      const result = await api.datasets.upload(selectedFile);
      setUploadSuccess(result);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      loadData();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload dataset to server.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <ErrorBoundary fallbackTitle="Dataset Registry Interface Error" onReset={loadData}>
      <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Database className="w-5 h-5 text-emerald-400" />
            <h2 className="text-2xl font-black text-white tracking-tight">Dataset Registry & Sources</h2>
          </div>
          <p className="text-sm text-slate-400">
            Select, upload, or generate datasets to trigger multi-agent pipeline audits.
          </p>
        </div>
        <button
          onClick={loadData}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition self-start md:self-auto"
          title="Refresh Registry"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* 3 Source Options Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => setActiveTab('upload')}
          className={`p-5 rounded-2xl border text-left transition flex flex-col justify-between ${
            activeTab === 'upload'
              ? 'bg-emerald-500/10 border-emerald-500/50 shadow-lg shadow-emerald-950/40'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-emerald-400 uppercase tracking-wider">Source Option A</span>
            <Upload className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <h3 className="text-base font-bold text-white">Upload File</h3>
            <p className="text-xs text-slate-400 mt-1">Upload CSV, JSON, or XLSX up to 50MB with path-safe backend storage.</p>
          </div>
        </button>

        <button
          onClick={() => setActiveTab('benchmark')}
          className={`p-5 rounded-2xl border text-left transition flex flex-col justify-between ${
            activeTab === 'benchmark'
              ? 'bg-teal-500/10 border-teal-500/50 shadow-lg shadow-teal-950/40'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-teal-400 uppercase tracking-wider">Source Option B</span>
            <Layers className="w-4 h-4 text-teal-400" />
          </div>
          <div className="mt-3">
            <h3 className="text-base font-bold text-white">Olist Benchmark</h3>
            <p className="text-xs text-slate-400 mt-1">Curated real-world e-commerce datasets (100k+ rows) with hidden paths.</p>
          </div>
        </button>

        <button
          onClick={() => setActiveTab('synthetic')}
          className={`p-5 rounded-2xl border text-left transition flex flex-col justify-between ${
            activeTab === 'synthetic'
              ? 'bg-purple-500/10 border-purple-500/50 shadow-lg shadow-purple-950/40'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-purple-400 uppercase tracking-wider">Source Option C</span>
            <Sparkles className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-3">
            <h3 className="text-base font-bold text-white">Synthetic Scenarios</h3>
            <p className="text-xs text-slate-400 mt-1">Fault injection benchmark connected to the autonomous pipeline simulator.</p>
          </div>
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'upload' && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Source A: Direct Dataset Upload</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Upload custom ETL batches. Files are sanitized, registered in PostgreSQL, and canonicalized against path-traversal attacks.
              </p>
            </div>
            {!canUpload && (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Viewer Role: Upload restricted to Admin & Data Engineer
              </span>
            )}
          </div>

          <form onSubmit={handleUploadSubmit} className="space-y-4">
            <div className="border-2 border-dashed border-slate-800 hover:border-emerald-500/50 rounded-2xl p-8 text-center bg-slate-950/50 transition">
              <input
                ref={fileInputRef}
                type="file"
                id="file-upload"
                accept=".csv,.json,.xlsx"
                disabled={!canUpload || uploading}
                onChange={handleFileChange}
                className="hidden"
              />
              <label
                htmlFor="file-upload"
                className={`cursor-pointer flex flex-col items-center gap-3 ${!canUpload ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <Upload className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">
                    {selectedFile ? selectedFile.name : 'Click to browse or drop dataset here'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Supports .csv, .json, .xlsx up to 50MB
                  </p>
                </div>
                {selectedFile && (
                  <span className="px-3 py-1 rounded-full text-xs font-mono bg-emerald-500/20 text-emerald-300">
                    {(selectedFile.size / 1024).toFixed(1)} KB selected
                  </span>
                )}
              </label>
            </div>

            {uploadError && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3 text-red-300 text-xs">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            {uploadSuccess && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-3 text-emerald-300">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                  <div>
                    <span className="font-bold text-white">{uploadSuccess.dataset_name}</span> successfully registered!
                    <div className="text-slate-400 font-mono mt-0.5">
                      Rows: {uploadSuccess.row_count.toLocaleString()} • Columns: {uploadSuccess.column_count} • Format: {uploadSuccess.file_format}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => onAuditDataset(uploadSuccess.file_path)}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold flex items-center gap-2 shadow self-start sm:self-auto transition"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Audit Now</span>
                </button>
              </div>
            )}

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={!selectedFile || uploading || !canUpload}
                className={`px-5 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 transition shadow-lg ${
                  selectedFile && !uploading && canUpload
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-950'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                }`}
              >
                {uploading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Registering Dataset...</span>
                  </>
                ) : (
                  <>
                    <FileCheck className="w-4 h-4" />
                    <span>Upload & Register</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* API Connection Error Notice */}
      {apiError && (
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-red-500/30 shadow-xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Dataset Registry Communication Notice</h3>
              <p className="text-xs text-slate-400">
                {apiError.status ? `HTTP Status ${apiError.status}: ` : ''}
                {apiError.message}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={loadData}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-2 shadow-lg transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
            <button
              onClick={() => {
                setApiError(null);
                setActiveTab('upload');
              }}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition"
            >
              Return to Dataset Registry
            </button>
          </div>
        </div>
      )}

      {activeTab === 'benchmark' && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
          <div>
            <h3 className="text-lg font-bold text-white">Source B: Olist Benchmark Collection</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Production e-commerce transaction logs with real schema drift, categorical anomalies, and multi-table integrity. Internal server paths are shielded.
            </p>
          </div>

          {benchmarks.length === 0 && !loading ? (
            <div className="p-8 rounded-2xl bg-slate-950/60 border border-slate-800 text-center text-slate-400 text-xs">
              No benchmark datasets currently loaded. Ensure backend datasets/olist directory is accessible.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {benchmarks.map((b) => {
                const recordsCount = b.records ?? (b as any).row_count ?? 0;
                const tagsList = b.tags ?? [];
                const categoryName = b.category ?? 'Benchmark';

                return (
                  <div
                    key={b.id}
                    className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between hover:border-slate-700 transition"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-teal-400 font-bold">
                          {categoryName}
                        </span>
                        <span className="text-xs font-mono text-slate-400">
                          {recordsCount.toLocaleString()} rows
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-white">{b.name}</h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">{b.description}</p>
                      {tagsList.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-3">
                          {tagsList.map((t) => (
                            <span key={t} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between">
                      <span className="text-[11px] text-slate-500 font-mono">Benchmark Source</span>
                      <button
                        onClick={() => onAuditDataset(b.file_path)}
                        className="px-3.5 py-1.5 rounded-xl bg-teal-600/20 hover:bg-teal-600/30 text-teal-300 text-xs font-bold flex items-center gap-1.5 border border-teal-500/30 transition"
                      >
                        <Play className="w-3.5 h-3.5" />
                        <span>Audit Now</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {activeTab === 'synthetic' && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Source C: Synthetic Data & Fault Scenarios</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Controlled failure benchmarks connected to DataGuard's Pipeline Fault Simulator.
              </p>
            </div>
            {onNavigate && (
              <button
                onClick={() => onNavigate('simulator')}
                className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-2 shadow-lg transition"
              >
                <span>Open Full Simulator</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {scenarios.length === 0 && !loading ? (
            <div className="p-8 rounded-2xl bg-slate-950/60 border border-slate-800 text-center text-slate-400 text-xs">
              No simulation scenarios currently returned from backend.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {scenarios.map((s) => {
                const modeKey = s.mode || (s as any).id || 'UNKNOWN';
                const nameTitle = s.name || (s as any).title || modeKey;
                const categoryBadge = s.category || (s as any).badge || 'Synthetic Scenario';
                const anomaliesList = s.anomalies || [(s as any).description || 'Injected fault scenario'];

                return (
                  <div
                    key={modeKey}
                    className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between hover:border-slate-700 transition"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-purple-400 font-bold">
                          {categoryBadge}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 uppercase">{modeKey}</span>
                      </div>
                      <h4 className="text-base font-bold text-white">{nameTitle}</h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">{s.description}</p>
                      <div className="mt-3 space-y-1">
                        {anomaliesList.map((a, idx) => (
                          <div key={idx} className="text-[11px] text-slate-400 flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                            <span>{a}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between gap-2">
                      <span className="text-[11px] text-slate-500 font-mono">Simulation Mode</span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={async () => {
                            if (onAuditDossierLoaded) {
                              try {
                                setLoading(true);
                                const simResult = await api.agents.simulatePipeline(
                                  'olist/olist_orders_dataset.csv',
                                  modeKey,
                                  500
                                );
                                if (simResult?.audit) {
                                  onAuditDossierLoaded(simResult.audit);
                                  if (onNavigate) onNavigate('findings');
                                }
                              } catch (err: any) {
                                setUploadError(err.response?.data?.detail || 'Simulation execution failed.');
                              } finally {
                                setLoading(false);
                              }
                            } else if (onNavigate) {
                              onNavigate('simulator');
                            }
                          }}
                          className="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center gap-1.5 shadow transition"
                        >
                          <Play className="w-3 h-3" />
                          <span>Audit Scenario</span>
                        </button>
                        {onNavigate && (
                          <button
                            onClick={() => onNavigate('simulator')}
                            className="p-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 text-xs font-bold border border-purple-500/30 transition"
                            title="Open Full Simulator"
                          >
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Registered Datasets Table (PostgreSQL) */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-emerald-400" />
            <h3 className="text-base font-bold text-white tracking-tight">Registered Datasets (PostgreSQL)</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">{registered.length} registered</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/60 text-slate-400 uppercase tracking-wider font-mono">
              <tr>
                <th className="p-3 rounded-l-lg">Dataset Name</th>
                <th className="p-3">Type</th>
                <th className="p-3">Source</th>
                <th className="p-3">Format</th>
                <th className="p-3">Rows</th>
                <th className="p-3">Columns</th>
                <th className="p-3">Registered At</th>
                <th className="p-3 rounded-r-lg text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {registered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-6 text-center text-slate-500">
                    No custom datasets registered yet. Use Source A to upload a dataset or Source B to audit benchmark data.
                  </td>
                </tr>
              ) : (
                registered.map((ds) => (
                  <tr key={ds.id} className="hover:bg-slate-800/30 transition">
                    <td className="p-3 font-bold text-white flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                      <span>{ds.dataset_name}</span>
                    </td>
                    <td className="p-3 font-mono text-slate-300">{ds.dataset_type}</td>
                    <td className="p-3 font-mono text-slate-400">{ds.source}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded font-mono font-bold bg-slate-800 text-slate-300 text-[10px]">
                        {ds.file_format.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-slate-300">{ds.row_count.toLocaleString()}</td>
                    <td className="p-3 font-mono text-slate-300">{ds.column_count}</td>
                    <td className="p-3 text-slate-400 font-mono">
                      {ds.created_at ? new Date(ds.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => onAuditDataset(ds.file_path)}
                        className="px-3 py-1 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 text-xs font-bold border border-emerald-500/30 transition"
                      >
                        Audit
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      </div>
    </ErrorBoundary>
  );
};
