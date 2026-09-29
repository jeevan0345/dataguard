import React, { useState, useEffect } from 'react';
import { AuditDossier, GeneratedReport } from '../types';
import { api } from '../services/api';
import {
  FileText,
  FileDown,
  CheckCircle2,
  Calendar,
  FileSpreadsheet,
  DownloadCloud,
  ShieldAlert,
  Archive,
  RefreshCw,
} from 'lucide-react';

interface ReportsViewProps {
  dossier: AuditDossier | null;
  onNavigate: (tab: string) => void;
}

export const ReportsView: React.FC<ReportsViewProps> = ({ dossier, onNavigate }) => {
  const [reportsList, setReportsList] = useState<GeneratedReport[]>([]);
  const [loading, setLoading] = useState(true);

  const loadReports = async () => {
    setLoading(true);
    try {
      const list = await api.agents.getReports();
      setReportsList(list);
    } catch (err) {
      console.error('Failed to load reports archive:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const activeReports = dossier?.reports;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <FileText className="w-5 h-5 text-emerald-400" />
            <h2 className="text-2xl font-black text-white tracking-tight">Audit Reports & Compliance Center</h2>
          </div>
          <p className="text-sm text-slate-400">
            Official compliance documentation generated automatically by the Reporter Agent in PDF (ReportLab) and Excel (OpenPyXL).
          </p>
        </div>
        <button
          onClick={loadReports}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition self-start md:self-auto"
          title="Refresh Reports"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Active Audit Reports (if present) */}
      {activeReports && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Latest Audit Reports</span>
            <span className="font-mono text-emerald-400 font-normal">({dossier?.dataset_name || dossier?.dataset_path})</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* PDF Report Card */}
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between space-y-6 shadow-xl">
              <div>
                <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center justify-center mb-4">
                  <FileText className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white">Executive PDF Audit Report</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Multi-page executive report generated with ReportLab. Includes summary tables, root cause findings, and verification audit trails.
                </p>
                <div className="mt-4 p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(activeReports.generated_at).toLocaleString()}</span>
                  </div>
                  <div className="text-emerald-400 truncate">{activeReports.pdf_filename}</div>
                </div>
              </div>

              <a
                href={api.agents.getReportDownloadUrl(activeReports.pdf_filename)}
                target="_blank"
                rel="noreferrer"
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg transition"
              >
                <FileDown className="w-4 h-4" />
                <span>Download Official PDF Report</span>
              </a>
            </div>

            {/* Excel Workbook Card */}
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between space-y-6 shadow-xl">
              <div>
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mb-4">
                  <FileSpreadsheet className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white">Multi-Tab Audit Workbook</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Detailed technical log generated with OpenPyXL. Includes raw findings, schema drift metrics, and anomaly parameters.
                </p>
                <div className="mt-4 p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(activeReports.generated_at).toLocaleString()}</span>
                  </div>
                  <div className="text-teal-400 truncate">{activeReports.excel_filename}</div>
                </div>
              </div>

              <a
                href={api.agents.getReportDownloadUrl(activeReports.excel_filename)}
                target="_blank"
                rel="noreferrer"
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg transition"
              >
                <DownloadCloud className="w-4 h-4" />
                <span>Download OpenPyXL Workbook (.xlsx)</span>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Complete Generated Reports Archive */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Archive className="w-4 h-4 text-emerald-400" />
            <h3 className="text-base font-bold text-white tracking-tight">Generated Reports Archive</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">{reportsList.length} files stored</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400 font-mono text-xs flex items-center justify-center gap-2">
            <div className="w-4 h-4 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
            <span>Scanning reports directory...</span>
          </div>
        ) : reportsList.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            No report files found. Execute an audit or simulator run to generate PDF and Excel compliance artifacts.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/60 text-slate-400 uppercase tracking-wider font-mono">
                <tr>
                  <th className="p-3 rounded-l-lg">Report Filename</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Format</th>
                  <th className="p-3">Size</th>
                  <th className="p-3">Generated At</th>
                  <th className="p-3 rounded-r-lg text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {reportsList.map((r) => (
                  <tr key={r.filename} className="hover:bg-slate-800/30 transition">
                    <td className="p-3 font-mono font-bold text-white flex items-center gap-2">
                      {r.format === 'PDF' ? (
                        <FileText className="w-4 h-4 text-red-400" />
                      ) : (
                        <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                      )}
                      <span>{r.filename}</span>
                    </td>
                    <td className="p-3 text-slate-300">{r.report_type}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${
                        r.format === 'PDF' ? 'bg-red-500/20 text-red-300' : 'bg-emerald-500/20 text-emerald-300'
                      }`}>
                        {r.format}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-slate-400">{(r.file_size / 1024).toFixed(1)} KB</td>
                    <td className="p-3 font-mono text-slate-400">
                      {r.created_at ? new Date(r.created_at).toLocaleString() : 'N/A'}
                    </td>
                    <td className="p-3 text-right">
                      <a
                        href={api.agents.getReportDownloadUrl(r.filename)}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 text-xs font-bold border border-emerald-500/30 inline-flex items-center gap-1.5 transition"
                      >
                        <FileDown className="w-3.5 h-3.5" />
                        <span>Download</span>
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
