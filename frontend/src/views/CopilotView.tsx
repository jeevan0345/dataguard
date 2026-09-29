import React, { useState, useRef, useEffect } from 'react';
import { AuditDossier } from '../types';
import { api } from '../services/api';
import {
  BotMessageSquare,
  Send,
  Sparkles,
  User,
  Shield,
  Layers,
  HelpCircle,
} from 'lucide-react';

interface CopilotViewProps {
  dossier: AuditDossier | null;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'copilot';
  text: string;
  citations?: string[];
  timestamp: string;
}

export const CopilotView: React.FC<CopilotViewProps> = ({ dossier }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'copilot',
      text: "Hello! I am your **DataGuard AI Copilot**. I analyze real-time audit logs, schema drift, statistical anomalies, and evidence records strictly without numerical hallucination.\n\nAsk me anything about current pipeline health, root-cause diagnoses, or remediation SQL!",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const [activeDossier, setActiveDossier] = useState<AuditDossier | null>(dossier);

  useEffect(() => {
    setActiveDossier(dossier);
  }, [dossier]);

  useEffect(() => {
    if (!activeDossier) {
      api.agents.getLatestAudit()
        .then((latest) => {
          if (latest) setActiveDossier(latest);
        })
        .catch(() => {});
    }
  }, [activeDossier]);

  const samplePrompts = [
    'What is the current system health?',
    'What caused the latest anomaly?',
    'Show me all active findings',
    'How can I fix the duplicate records?',
  ];

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (queryText?: string) => {
    const q = queryText || input;
    if (!q.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const res = await api.agents.chatCopilot(q, activeDossier);
      const botMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'copilot',
        text: res.reply,
        citations: res.citations,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'copilot',
        text: 'Sorry, I encountered an error querying the audit trail. Please check your backend connection.',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto h-[calc(100vh-4rem)] flex flex-col space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BotMessageSquare className="w-5 h-5 text-purple-400" />
            <h2 className="text-2xl font-black text-white tracking-tight">DataGuard AI Copilot</h2>
          </div>
          <p className="text-xs text-slate-400">
            Interactive reasoning assistant grounded strictly in verified quantitative evidence.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs font-mono">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Evidence-Grounded (4-Tier Verification)</span>
        </div>
      </div>

      {/* Chat Messages Window */}
      <div className="flex-1 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 overflow-y-auto space-y-4 shadow-xl">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                msg.sender === 'user'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-gradient-to-tr from-purple-600 to-indigo-500 text-white shadow-lg'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-5 h-5" /> : <Shield className="w-5 h-5" />}
            </div>

            <div className={`max-w-2xl space-y-2 ${msg.sender === 'user' ? 'text-right' : ''}`}>
              <div
                className={`p-4 rounded-2xl text-xs leading-relaxed inline-block text-left whitespace-pre-wrap ${
                  msg.sender === 'user'
                    ? 'bg-emerald-600 text-white font-medium rounded-tr-none'
                    : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none font-mono text-[11px]'
                }`}
              >
                {msg.text}
              </div>

              {msg.citations && msg.citations.length > 0 && (
                <div className="flex items-center gap-1.5 flex-wrap text-[10px] font-mono text-purple-300">
                  <Layers className="w-3 h-3 text-purple-400" />
                  <span>Grounded in Evidence:</span>
                  {msg.citations.slice(0, 4).map((cit, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded-md bg-purple-500/10 border border-purple-500/30">
                      {cit}
                    </span>
                  ))}
                </div>
              )}
              <div className="text-[10px] text-slate-500 font-mono">{msg.timestamp}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-600/30 text-purple-400 flex items-center justify-center">
              <Sparkles className="w-5 h-5 animate-spin" />
            </div>
            <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
              <span>Copilot is reasoning over audit evidence...</span>
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 whitespace-nowrap transition"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-2xl p-2 pl-4 focus-within:border-purple-500 transition shadow-xl"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask DataGuard Copilot about pipeline health, root causes, or SQL fixes..."
          className="flex-1 bg-transparent text-sm text-white focus:outline-none placeholder:text-slate-500"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="p-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white transition disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
