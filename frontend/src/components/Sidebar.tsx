import React from 'react';
import {
  LayoutDashboard,
  Cpu,
  PlayCircle,
  Database,
  SearchCode,
  ShieldCheck,
  FileText,
  BotMessageSquare,
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Executive Overview', icon: LayoutDashboard },
    { id: 'agents', label: 'Agent Swarm', icon: Cpu },
    { id: 'simulator', label: 'Pipeline Simulator', icon: PlayCircle },
    { id: 'findings', label: 'Findings & Evidence', icon: SearchCode },
    { id: 'recovery', label: 'Recovery Console', icon: ShieldCheck },
    { id: 'reports', label: 'Audit Reports', icon: FileText },
    { id: 'copilot', label: 'AI Copilot Assistant', icon: BotMessageSquare },
    { id: 'datasets', label: 'Dataset Registry', icon: Database },
  ];

  return (
    <aside className="w-64 bg-slate-900/60 border-r border-slate-800 p-4 flex flex-col justify-between hidden md:flex">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
          Platform Navigation
        </div>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const active = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition ${
                active
                  ? 'bg-gradient-to-r from-emerald-600/30 to-teal-500/20 text-emerald-300 border border-emerald-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Icon className={`w-4 h-4 ${active ? 'text-emerald-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* System info badge */}
      <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-800 text-xs text-slate-400 space-y-1.5">
        <div className="flex items-center justify-between font-mono">
          <span>Engine</span>
          <span className="text-emerald-400 font-bold">FastAPI + Py3.12</span>
        </div>
        <div className="flex items-center justify-between font-mono">
          <span>ML Models</span>
          <span className="text-teal-400">Isolation Forest</span>
        </div>
        <div className="flex items-center justify-between font-mono">
          <span>ETL Library</span>
          <span className="text-slate-300">Pandas-Free</span>
        </div>
      </div>
    </aside>
  );
};
