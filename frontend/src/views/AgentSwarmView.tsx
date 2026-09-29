import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AgentStatus, SwarmStatusResponse } from '../types';
import {
  ShieldCheck,
  Cpu,
  GitPullRequest,
  Search,
  Sparkles,
  HelpCircle,
  FileCheck2,
  Bot,
  Activity,
  Workflow,
  RefreshCw,
} from 'lucide-react';

export const AgentSwarmView: React.FC = () => {
  const [liveSwarm, setLiveSwarm] = useState<SwarmStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const loadSwarmStatus = async () => {
    setLoading(true);
    try {
      const data = await api.agents.getSwarmStatus();
      setLiveSwarm(data);
    } catch (err) {
      console.debug('Failed to fetch live swarm status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSwarmStatus();
  }, []);

  const agentDefinitions = [
    {
      id: 'inspector',
      name: 'Inspector Agent',
      role: 'Quality & Schema Auditing',
      icon: Search,
      color: 'from-blue-600 to-cyan-500',
      responsibilities: [
        'Missing / null values detection',
        'Duplicate records identification',
        'Schema drift & column type checking',
        'Z-score & IQR numerical outliers',
      ],
      input: 'Raw tabular row dictionaries (Pandas-free)',
      output: 'Unified findings array & statistical profiles',
    },
    {
      id: 'drift',
      name: 'Drift Agent',
      role: 'Statistical Drift Tracking',
      icon: Activity,
      color: 'from-cyan-600 to-teal-500',
      responsibilities: [
        'Two-sample Kolmogorov-Smirnov test',
        'Empirical cumulative distribution shift',
        'Categorical frequency divergence',
        'Batch volume trend tracking',
      ],
      input: 'Current batch rows vs. reference baseline',
      output: 'Drift metrics, KS-statistic, p-values',
    },
    {
      id: 'root_cause',
      name: 'Root Cause Agent',
      role: 'Cross-Finding Diagnostic Synthesis',
      icon: GitPullRequest,
      color: 'from-purple-600 to-indigo-500',
      responsibilities: [
        'Cross-finding pattern correlation',
        'Upstream schema break identification',
        'Replay & non-idempotent ingestion diagnosis',
        'Ranked hypotheses with confidence scores',
      ],
      input: 'Evidence Engine items (E1, E2, ...)',
      output: 'Ranked candidate causes & affected stages',
    },
    {
      id: 'recommendation',
      name: 'Recommendation Agent',
      role: 'Actionable Engineering Advice',
      icon: Sparkles,
      color: 'from-amber-600 to-orange-500',
      responsibilities: [
        'Severity-ranked remediation steps (P0 - P3)',
        'Synthesizes SQL fix scripts',
        'Schema migration recommendations',
        'Pipeline safeguard & dead-letter queue rules',
      ],
      input: 'Inspection findings & Root Cause summary',
      output: 'Actionable recommendations & SQL snippets',
    },
    {
      id: 'recovery',
      name: 'Recovery Agent',
      role: 'Controlled Self-Healing & Verification',
      icon: ShieldCheck,
      color: 'from-emerald-600 to-green-500',
      responsibilities: [
        'Policy constraint checks (e.g. max drop %)',
        'Deduplication & missing value imputation',
        'Dead-letter quarantine execution',
        'Post-remediation PASS/FAIL verification',
      ],
      input: 'Approved remediation candidate actions',
      output: 'Remediated dataset buffer & verification report',
    },
    {
      id: 'reporter',
      name: 'Reporter Agent',
      role: 'Compliance & Audit Artifacts',
      icon: FileCheck2,
      color: 'from-rose-600 to-pink-500',
      responsibilities: [
        'Multi-page executive PDF report generation',
        'OpenPyXL multi-tab Excel audit workbooks',
        'Tamper-evident audit timestamping',
        'Stakeholder compliance summaries',
      ],
      input: 'Comprehensive audit dossier & verification log',
      output: 'ReportLab PDF & OpenPyXL Excel files',
    },
    {
      id: 'copilot',
      name: 'AI Copilot Agent',
      role: 'Natural Language Interactive Assistant',
      icon: Bot,
      color: 'from-violet-600 to-purple-500',
      responsibilities: [
        'Grounded conversational answering',
        'Queries structured audit logs and metrics',
        'Explains root-cause logic and fixes',
        'Evidence-Grounded 4-tier output (FACT, CANDIDATE, REC, UNKNOWN)',
      ],
      input: 'Operator natural language prompts',
      output: 'Structured answers with verified evidence citations',
    },
  ];

  const getLiveStatus = (agentName: string) => {
    if (!liveSwarm?.agents) return 'ONLINE';
    const match = liveSwarm.agents.find(
      (a) => a.name.toLowerCase().includes(agentName.toLowerCase()) ||
             agentName.toLowerCase().includes(a.name.toLowerCase())
    );
    return match?.status || 'ONLINE';
  };

  const vivaQuestions = [
    {
      q: 'Why a Multi-Agent Architecture?',
      a: 'Separation of concerns. Instead of an unmaintainable monolithic script, specialized agents handle inspection, statistical drift, diagnostic reasoning, policy-controlled healing, compliance reporting, and conversational interaction independently with explicit contracts.',
    },
    {
      q: 'Why Was Pandas Intentionally Excluded?',
      a: 'DataGuard intentionally selected a streamlined processing core (standard Python csv/json streaming, NumPy, and SciPy) to eliminate unnecessary memory overhead, avoid unpredictable dtype casting, and achieve deterministic throughput in ETL validation pipelines.',
    },
    {
      q: 'Why ML + Quantitative Reasoning instead of raw LLM?',
      a: 'Quantitative anomaly detection requires mathematical precision (3-sigma, IQR, Isolation Forest, KS-test). Raw LLMs hallucinate numbers. DataGuard calculates exact statistics first, constructs structured evidence, and uses agentic reasoning strictly over verified facts.',
    },
    {
      q: 'How is Self-Healing / Recovery Made Safe?',
      a: 'Zero uncontrolled production changes. Recovery proposals undergo strict policy checks (e.g. max allowable drop threshold, immutable primary keys), require operator sign-off for high risks, and execute dry-runs with post-remediation PASS/FAIL verification.',
    },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Workflow className="w-5 h-5 text-emerald-400" />
            <h2 className="text-2xl font-black text-white tracking-tight">Multi-Agent Swarm Visualizer</h2>
          </div>
          <p className="text-sm text-slate-400">
            Exactly 7 autonomous agents powering DataGuard 2.0. Operating with specialized contracts, shared evidence, and policy controls.
          </p>
        </div>
        <button
          onClick={loadSwarmStatus}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition self-start md:self-auto"
          title="Refresh Swarm Telemetry"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {agentDefinitions.map((agent) => {
          const Icon = agent.icon;
          const status = getLiveStatus(agent.name);
          return (
            <div
              key={agent.id}
              className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition group shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-11 h-11 rounded-xl bg-gradient-to-tr ${agent.color} flex items-center justify-center shadow-lg`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold border ${
                    status === 'ONLINE'
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                      : status === 'RUNNING'
                      ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30 animate-pulse'
                      : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                  }`}>
                    {status}
                  </span>
                </div>

                <h3 className="text-base font-extrabold text-white tracking-tight">{agent.name}</h3>
                <div className="text-xs text-emerald-400 font-medium mb-3">{agent.role}</div>

                <div className="space-y-1.5 mb-4">
                  <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Responsibilities:</div>
                  <ul className="text-xs text-slate-300 space-y-1">
                    {agent.responsibilities.map((r, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-500">•</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 font-mono space-y-1">
                <div><span className="text-slate-500">In:</span> {agent.input}</div>
                <div><span className="text-slate-500">Out:</span> {agent.output}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Faculty / Viva Positioning Section */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-bold text-white tracking-tight">Academic & Faculty Defense Positioning</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {vivaQuestions.map((item, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
              <h4 className="text-xs font-bold text-emerald-300">{item.q}</h4>
              <p className="text-xs text-slate-400 leading-relaxed">{item.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
