import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { DashboardSummary, SystemHealth } from '../types';
import {
  Activity,
  AlertOctagon,
  CheckCircle2,
  Database,
  ArrowUpRight,
  TrendingUp,
  Cpu,
  PlayCircle,
  RefreshCw,
  Server,
  ShieldCheck,
  Info,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';

interface DashboardViewProps {
  onNavigate: (tab: string) => void;
  onSelectAudit?: (runId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate, onSelectAudit }) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [data, healthData] = await Promise.all([
        api.agents.getDashboardSummary(),
        api.agents.getHealth().catch(() => null),
      ]);
      setSummary(data);
      if (healthData) setHealth(healthData);
    } catch (err) {
      console.error('Failed to load dashboard summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading || !summary) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-400 font-mono">Aggregating real-time audit telemetry...</p>
        </div>
      </div>
    );
  }

  const { health_index, health_status, kpis, severity_distribution, recent_runs, formula_explanation } = summary;
  const activeAgents = kpis.active_agents ?? 7;
  const totalAgents = kpis.total_agents ?? 7;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-black text-white tracking-tight">Executive Telemetry Overview</h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              v2.0 Production
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time pipeline health, deterministic anomaly detection, and 7-agent autonomous coordination.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {health && (
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono">
              <span className={`w-2 h-2 rounded-full ${health.database === 'CONNECTED' ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
              <span className="text-slate-400">PostgreSQL:</span>
              <span className={health.database === 'CONNECTED' ? 'text-emerald-400 font-bold' : 'text-red-400 font-bold'}>
                {health.database}
              </span>
            </div>
          )}
          <button
            onClick={loadData}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition"
            title="Refresh Metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => onNavigate('simulator')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm shadow-lg shadow-emerald-950 transition"
          >
            <PlayCircle className="w-4 h-4" />
            <span>Launch Fault Simulator</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* System Health Index */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Health Index</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-white font-mono">{health_index}%</span>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                health_status === 'OPTIMAL'
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : health_status === 'DEGRADED'
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'bg-red-500/20 text-red-400'
              }`}
            >
              {health_status}
            </span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                health_index >= 80 ? 'bg-emerald-500' : health_index >= 50 ? 'bg-amber-500' : 'bg-red-500'
              }`}
              style={{ width: `${health_index}%` }}
            />
          </div>
          <p className="text-[10px] text-slate-500 mt-2 font-mono truncate" title={formula_explanation || '100 - (20×Crit + 10×High + 3×Med + 1×Low)'}>
            Formula: {formula_explanation || '100 - (20×Crit + 10×High + 3×Med + 1×Low)'}
          </p>
        </div>

        {/* Total Inspections */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Inspections</span>
            <Database className="w-4 h-4 text-teal-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-white font-mono">{kpis.total_inspections}</span>
            <span className="text-xs text-slate-400 font-mono">audits stored</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">Continuous automated profiling</p>
        </div>

        {/* Active Findings */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Findings</span>
            <AlertOctagon className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-white font-mono">{kpis.total_findings}</span>
            <span className="text-xs text-amber-400 font-semibold">{kpis.critical_findings} Critical</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">Quality, schema & ML anomalies</p>
        </div>

        {/* Multi-Agent Swarm Status */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 cursor-pointer hover:border-slate-700 transition" onClick={() => onNavigate('agents')}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Agent Swarm</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-white font-mono">{activeAgents}/{totalAgents}</span>
            <span className="text-xs text-emerald-400 font-semibold">Active Swarm</span>
          </div>
          <p className="text-xs text-slate-500 mt-2 truncate">Inspector • Drift • RCA • Rec • Recov • Rep • Copilot</p>
        </div>
      </div>

      {/* Visual Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Distribution */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 lg:col-span-1 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">Finding Severity Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5">Categorized by operational pipeline risk</p>
          </div>
          <div className="h-56 my-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severity_distribution.filter(d => d.count > 0)}
                  dataKey="count"
                  nameKey="severity"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                >
                  {severity_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
            {severity_distribution.map((item) => (
              <div key={item.severity} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-slate-400">{item.severity}:</span>
                <span className="font-bold text-white font-mono">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Volume & Severity Bar Chart */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">Recent Pipeline Anomaly Counts</h3>
              <p className="text-xs text-slate-400">Findings identified across recent audit runs</p>
            </div>
            <button
              onClick={() => onNavigate('findings')}
              className="text-xs text-emerald-400 hover:underline flex items-center gap-1 font-semibold"
            >
              <span>Explore findings</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={recent_runs.slice(0, 8)}>
                <XAxis
                  dataKey="friendly_name"
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  tickFormatter={(val, index) => val || recent_runs[index]?.dataset_path?.split('/').pop() || val}
                />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="finding_count" name="Finding Count" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Historical Runs Table */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">Recent Historical Audits</h3>
            <p className="text-xs text-slate-400">PostgreSQL inspection audit records (Click any audit to load dossier)</p>
          </div>
          <button
            onClick={() => onNavigate('simulator')}
            className="text-xs text-emerald-400 hover:underline font-semibold"
          >
            Run new inspection
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/60 text-slate-400 uppercase tracking-wider font-mono">
              <tr>
                <th className="p-3 rounded-l-lg">Target Dataset</th>
                <th className="p-3">Status</th>
                <th className="p-3">Highest Severity</th>
                <th className="p-3">Rows</th>
                <th className="p-3">Findings</th>
                <th className="p-3 rounded-r-lg">Audited At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {recent_runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-slate-500">
                    No inspection runs recorded yet. Run an inspection from the simulator.
                  </td>
                </tr>
              ) : (
                recent_runs.map((run) => (
                  <tr
                    key={run.id}
                    onClick={() => {
                      if (onSelectAudit) {
                        onSelectAudit(run.id);
                      } else {
                        onNavigate('findings');
                      }
                    }}
                    className="hover:bg-slate-800/50 cursor-pointer transition group"
                    title="Click to view full dossier in Findings Console"
                  >
                    <td className="p-3 font-medium text-slate-200 group-hover:text-emerald-400">
                      <div>{run.friendly_name || run.dataset_path.split('/').pop()}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{run.dataset_path}</div>
                    </td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded-full font-semibold ${
                          run.status === 'HEALTHY'
                            ? 'bg-emerald-500/20 text-emerald-300'
                            : 'bg-red-500/20 text-red-300'
                        }`}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="p-3 font-semibold text-slate-300">
                      {run.highest_severity || 'NONE'}
                    </td>
                    <td className="p-3 font-mono text-slate-400">{run.row_count.toLocaleString()}</td>
                    <td className="p-3 font-mono font-bold text-white">{run.finding_count}</td>
                    <td className="p-3 text-slate-400">
                      {run.created_at ? new Date(run.created_at).toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
