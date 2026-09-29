import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Bell, CheckCircle2, AlertTriangle, LogOut, UserCircle } from 'lucide-react';
import { api } from '../services/api';
import { Alert } from '../types';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await api.agents.getAlerts();
        setAlerts(res.alerts);
      } catch (err) {
        console.error('Failed to load alerts', err);
      }
    };
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, []);

  const unreadCount = alerts.filter(a => !a.is_read).length;

  const markAllRead = async () => {
    try {
      await api.agents.markAlertsRead();
      setAlerts(alerts.map(a => ({ ...a, is_read: true })));
    } catch (err) {
      console.error(err);
    }
  };

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'DATA_ENGINEER':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      default:
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
    }
  };

  return (
    <header className="h-16 bg-slate-900/90 backdrop-blur border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-900/40">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-extrabold tracking-tight text-white">DataGuard</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-mono font-semibold border border-emerald-500/30">v2.0</span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">Agentic ETL Pipeline Auditing Platform</p>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-4">
        {/* Live status badge */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-300 font-medium">Postgres 17 Connected</span>
        </div>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="relative p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
            title="Notifications"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center animate-bounce">
                {unreadCount}
              </span>
            )}
          </button>

          {showDropdown && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50">
              <div className="p-3 bg-slate-800/90 border-b border-slate-700 flex items-center justify-between">
                <span className="text-sm font-semibold text-white">Operational Alerts</span>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    className="text-xs text-emerald-400 hover:underline"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-80 overflow-y-auto divide-y divide-slate-800">
                {alerts.length === 0 ? (
                  <div className="p-6 text-center text-slate-400 text-sm">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-60" />
                    No active anomaly alerts
                  </div>
                ) : (
                  alerts.slice(0, 10).map((a) => (
                    <div
                      key={a.id}
                      className={`p-3 text-xs transition ${
                        a.is_read ? 'bg-slate-900 opacity-60' : 'bg-slate-800/40'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className={`w-3.5 h-3.5 ${a.severity === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}`} />
                        <span className="font-bold text-white truncate">{a.title}</span>
                      </div>
                      <p className="text-slate-300 line-clamp-2">{a.message}</p>
                      <div className="mt-1 text-[10px] text-slate-500 font-mono">
                        {new Date(a.timestamp).toLocaleTimeString()} • {a.dataset}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User profile */}
        {user && (
          <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-semibold text-white">{user.full_name}</div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${getRoleBadge(user.role)}`}>
                {user.role}
              </span>
            </div>
            <UserCircle className="w-8 h-8 text-slate-400" />
            <button
              onClick={logout}
              className="p-2 rounded-lg bg-slate-800 hover:bg-red-500/20 hover:text-red-400 text-slate-400 transition"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
