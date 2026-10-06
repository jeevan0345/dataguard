import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { LoginView } from './views/LoginView';
import { DashboardView } from './views/DashboardView';
import { AgentSwarmView } from './views/AgentSwarmView';
import { SimulatorView } from './views/SimulatorView';
import { FindingsView } from './views/FindingsView';
import { MLDetectionProofView } from './views/MLDetectionProofView';
import { RecoveryView } from './views/RecoveryView';
import { ReportsView } from './views/ReportsView';
import { CopilotView } from './views/CopilotView';
import { DatasetsView } from './views/DatasetsView';
import { AuditDossier } from './types';
import { api } from './services/api';
import { ErrorBoundary } from './components/ErrorBoundary';

export const App: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [activeDossier, setActiveDossier] = useState<AuditDossier | null>(null);

  // Auto-fetch latest persisted audit from PostgreSQL on mount
  useEffect(() => {
    if (user && !activeDossier) {
      api.agents.getLatestAudit()
        .then((latest) => {
          if (latest) {
            setActiveDossier(latest);
          }
        })
        .catch((err) => {
          console.debug('No prior audit found or backend starting up:', err);
        });
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
          <p className="text-xs font-mono text-slate-400">Initializing DataGuard 2.0 Platform...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginView />;
  }

  const loadAuditById = async (auditId: string) => {
    try {
      const res = await api.agents.getAuditById(auditId);
      setActiveDossier(res);
      setCurrentTab('findings');
    } catch (err) {
      console.error('Failed to load audit by ID:', err);
    }
  };

  const handleDirectAudit = async (filePath: string) => {
    try {
      const res = await api.agents.orchestrateAudit(filePath, 1000);
      setActiveDossier(res);
      setCurrentTab('findings');
    } catch (err) {
      console.error('Audit failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />
        <main className="flex-1 overflow-y-auto">
          <ErrorBoundary fallbackTitle="DataGuard Workspace View Notice">
            {currentTab === 'dashboard' && (
              <DashboardView
                onNavigate={setCurrentTab}
                onSelectAudit={loadAuditById}
              />
            )}
            {currentTab === 'agents' && <AgentSwarmView />}
            {currentTab === 'simulator' && (
              <SimulatorView
                onInspectionDone={setActiveDossier}
                onNavigate={setCurrentTab}
              />
            )}
            {currentTab === 'findings' && (
              <FindingsView
                dossier={activeDossier}
                onNavigate={setCurrentTab}
                onSelectDossier={setActiveDossier}
              />
            )}
            {currentTab === 'ml-proof' && (
              <MLDetectionProofView
                dossier={activeDossier}
                onNavigate={setCurrentTab}
                onSelectDossier={setActiveDossier}
              />
            )}
            {currentTab === 'recovery' && (
              <RecoveryView
                dossier={activeDossier}
                onNavigate={setCurrentTab}
                onDossierUpdated={setActiveDossier}
              />
            )}
            {currentTab === 'reports' && (
              <ReportsView dossier={activeDossier} onNavigate={setCurrentTab} />
            )}
            {currentTab === 'copilot' && <CopilotView dossier={activeDossier} />}
            {currentTab === 'datasets' && (
              <DatasetsView
                onAuditDataset={handleDirectAudit}
                onNavigate={setCurrentTab}
                onAuditDossierLoaded={setActiveDossier}
              />
            )}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};
