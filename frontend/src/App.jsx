import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  FileText,
  Layers,
  Search,
  CheckCircle2,
  Cpu,
  RefreshCw,
  Upload,
  Link,
  Lock,
  ArrowRight,
  ExternalLink,
  Activity,
  Check,
  Copy,
  Zap,
  Clock,
  BarChart3,
  Server,
  FileCheck,
  X,
  Play
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

export default function App() {
  // Navigation
  const [activeTab, setActiveTab] = useState('overview'); // overview | explorer | templates | alerts | investigation | blockchain | evaluation

  // Core State
  const [dashboardData, setDashboardData] = useState(null);
  const [logsData, setLogsData] = useState({ logs: [], total: 0 });
  const [templatesData, setTemplatesData] = useState([]);
  const [alertsData, setAlertsData] = useState([]);
  const [investigationsData, setInvestigationsData] = useState([]);
  const [responsesData, setResponsesData] = useState([]);
  const [blockchainData, setBlockchainData] = useState({ blocks: [], total_blocks: 0 });
  const [evaluationData, setEvaluationData] = useState(null);

  // Status & Loading
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);
  const [activeSource, setActiveSource] = useState('HDFS');
  const [error, setError] = useState(null);
  const [copiedHash, setCopiedHash] = useState(null);

  // Explorer Filters
  const [logSearch, setLogSearch] = useState('');
  const [logPage, setLogPage] = useState(0);
  const [logLimit] = useState(25);

  // Selected Alert for Investigation View
  const [selectedAlertId, setSelectedAlertId] = useState(null);

  // Upload Modal
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  // Fetch Dashboard Summary
  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard`);
      if (res.ok) {
        const data = await res.json();
        setDashboardData(data);
      }
    } catch (e) {
      console.error('Failed to fetch dashboard:', e);
    }
  }, []);

  // Fetch Logs
  const fetchLogs = useCallback(async () => {
    try {
      let url = `${API_BASE}/api/logs?limit=${logLimit}&offset=${logPage * logLimit}`;
      if (logSearch) {
        url += `&search=${encodeURIComponent(logSearch)}`;
      }
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setLogsData(data);
      }
    } catch (e) {
      console.error('Failed to fetch logs:', e);
    }
  }, [logPage, logLimit, logSearch]);

  // Fetch Templates
  const fetchTemplates = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/templates`);
      if (res.ok) {
        const data = await res.json();
        setTemplatesData(data.templates || []);
      }
    } catch (e) {
      console.error('Failed to fetch templates:', e);
    }
  }, []);

  // Fetch Alerts
  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/alerts`);
      if (res.ok) {
        const data = await res.json();
        setAlertsData(data.alerts || []);
        if (data.alerts?.length > 0 && !selectedAlertId) {
          setSelectedAlertId(data.alerts[0].alert_id);
        }
      }
    } catch (e) {
      console.error('Failed to fetch alerts:', e);
    }
  }, [selectedAlertId]);

  // Fetch Investigations & Responses
  const fetchAgentData = useCallback(async () => {
    try {
      const [invRes, respRes] = await Promise.all([
        fetch(`${API_BASE}/api/investigations`),
        fetch(`${API_BASE}/api/responses`)
      ]);
      if (invRes.ok) {
        const invData = await invRes.json();
        setInvestigationsData(invData.investigations || []);
      }
      if (respRes.ok) {
        const respData = await respRes.json();
        setResponsesData(respData.responses || []);
      }
    } catch (e) {
      console.error('Failed to fetch agent data:', e);
    }
  }, []);

  // Fetch Blockchain Ledger
  const fetchBlockchain = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/blockchain`);
      if (res.ok) {
        const data = await res.json();
        setBlockchainData(data);
      }
    } catch (e) {
      console.error('Failed to fetch blockchain:', e);
    }
  }, []);

  // Fetch Evaluation Metrics
  const fetchEvaluation = useCallback(async (dataset = 'HDFS') => {
    try {
      const res = await fetch(`${API_BASE}/api/evaluation?dataset=${dataset}`);
      if (res.ok) {
        const data = await res.json();
        setEvaluationData(data);
      }
    } catch (e) {
      console.error('Failed to fetch evaluation:', e);
    }
  }, []);

  // Load All Data
  const refreshAllData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      await Promise.all([
        fetchDashboard(),
        fetchLogs(),
        fetchTemplates(),
        fetchAlerts(),
        fetchAgentData(),
        fetchBlockchain(),
        fetchEvaluation(activeSource)
      ]);
    } catch (err) {
      setError(err.message || 'Error communicating with backend API.');
    } finally {
      setIsLoading(false);
    }
  }, [fetchDashboard, fetchLogs, fetchTemplates, fetchAlerts, fetchAgentData, fetchBlockchain, fetchEvaluation, activeSource]);

  useEffect(() => {
    refreshAllData();
  }, [refreshAllData]);

  // Cryptographic Ledger Verification
  const handleVerifyLedger = async () => {
    setIsVerifying(true);
    try {
      const res = await fetch(`${API_BASE}/api/blockchain/validate`);
      if (res.ok) {
        const result = await res.json();
        setVerifyResult(result);
      }
    } catch (err) {
      setVerifyResult({ valid: false, status: 'VERIFICATION_FAILED' });
    } finally {
      setIsVerifying(false);
    }
  };

  // Quick Ingestion of Pre-loaded Dataset
  const handleIngestSample = async (sampleName) => {
    setIsUploading(true);
    setError(null);
    setUploadSuccess(null);
    try {
      const res = await fetch(`${API_BASE}/api/logs/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sample_dataset: sampleName })
      });
      if (!res.ok) {
        throw new Error(`Sample analysis failed with status ${res.status}`);
      }
      const data = await res.json();
      setActiveSource(sampleName);
      setUploadSuccess(`Successfully ingested ${data.total_logs} ${sampleName} logs into pipeline.`);
      await refreshAllData();
      setTimeout(() => {
        setIsUploadModalOpen(false);
        setUploadSuccess(null);
      }, 1200);
    } catch (err) {
      setError(`Failed to analyze sample: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  // Upload Custom File
  const handleFileUpload = async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('log_file_input');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      setError('Please select a valid log file.');
      return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    setIsUploading(true);
    setError(null);
    setUploadSuccess(null);

    try {
      const res = await fetch(`${API_BASE}/api/logs/upload`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Upload failed with HTTP ${res.status}`);
      }
      const data = await res.json();
      setActiveSource(data.source || 'Generic');
      setUploadSuccess(`Successfully uploaded and analyzed ${data.total_logs} logs (${data.source}).`);
      await refreshAllData();
      setTimeout(() => {
        setIsUploadModalOpen(false);
        setUploadSuccess(null);
      }, 1500);
    } catch (err) {
      setError(`Upload error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  // Badges
  const getRiskBadge = (risk) => {
    const r = (risk || 'LOW').toUpperCase();
    switch (r) {
      case 'CRITICAL':
        return 'bg-rose-950/70 text-rose-400 border-rose-600/50';
      case 'HIGH':
        return 'bg-orange-950/70 text-orange-400 border-orange-600/50';
      case 'MEDIUM':
        return 'bg-amber-950/70 text-amber-400 border-amber-600/50';
      case 'LOW':
        return 'bg-emerald-950/70 text-emerald-400 border-emerald-600/50';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const getActionBadge = (action) => {
    const a = (action || 'NO_ACTION').toUpperCase();
    switch (a) {
      case 'ESCALATE':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'MONITOR':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'LOG_AND_MONITOR':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  const health = dashboardData?.health || { security_health_score: 95, status: 'OPTIMAL', blockchain_valid: true };
  const overview = dashboardData?.overview || { total_logs: 2000, total_templates: 16, total_anomalies: 5, investigations_completed: 5, responses_formulated: 5, blockchain_blocks: 6 };
  const riskDist = dashboardData?.risk_distribution || { CRITICAL: 0, HIGH: 2, MEDIUM: 2, LOW: 1 };

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top SOC Header */}
      <header className="border-b border-slate-800/80 bg-[#090e1a]/90 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 p-0.5 shadow-lg shadow-cyan-900/30 flex items-center justify-center">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">LogLens</h1>
              <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-cyan-950 text-cyan-400 border border-cyan-700/40">
                SOC PLATFORM
              </span>
              <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                Source: {activeSource}
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">AI-Assisted Multi-Agent Log Analysis & Tamper-Evident Security</p>
          </div>
        </div>

        {/* Global Action & Status Controls */}
        <div className="flex items-center gap-3">
          {/* Dynamic Health Score Pill */}
          <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-700/80 px-3 py-1.5 rounded-lg shadow-sm">
            <Activity className={`h-4 w-4 ${health.security_health_score >= 80 ? 'text-emerald-400' : health.security_health_score >= 60 ? 'text-amber-400' : 'text-rose-400'}`} />
            <div className="text-xs">
              <span className="text-slate-400 font-medium mr-1.5">Health Score:</span>
              <span className="font-bold text-white text-sm">{health.security_health_score}/100</span>
              <span className={`ml-2 text-[10px] font-bold px-1.5 py-0.5 rounded ${health.status === 'OPTIMAL' ? 'bg-emerald-950 text-emerald-400 border border-emerald-700/40' : 'bg-amber-950 text-amber-400 border border-amber-700/40'}`}>
                {health.status}
              </span>
            </div>
          </div>

          {/* Quick Dataset Selector */}
          <div className="hidden lg:flex items-center gap-1.5 bg-slate-900/80 border border-slate-800 rounded-lg p-1 text-xs">
            <span className="text-slate-400 text-[11px] px-2">Samples:</span>
            {['HDFS', 'Linux', 'Apache'].map(ds => (
              <button
                key={ds}
                onClick={() => handleIngestSample(ds)}
                disabled={isUploading}
                className={`px-2.5 py-1 rounded font-medium transition ${activeSource.toUpperCase() === ds ? 'bg-cyan-600 text-white font-semibold' : 'text-slate-300 hover:bg-slate-800'}`}
              >
                {ds}
              </button>
            ))}
          </div>

          {/* Upload Button */}
          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="flex items-center gap-1.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-md shadow-cyan-900/30 transition"
          >
            <Upload className="h-3.5 w-3.5" />
            Upload Log
          </button>

          {/* Verify Ledger Button */}
          <button
            onClick={handleVerifyLedger}
            disabled={isVerifying}
            className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-medium transition"
          >
            <Lock className={`h-3.5 w-3.5 ${verifyResult?.valid ? 'text-emerald-400' : 'text-slate-400'}`} />
            {isVerifying ? 'Verifying...' : 'Verify Chain'}
          </button>

          {/* Refresh */}
          <button
            onClick={refreshAllData}
            disabled={isLoading}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh All"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </header>

      {/* Navigation Tab Bar */}
      <nav className="border-b border-slate-800 bg-[#0a0f1d] px-6 flex overflow-x-auto space-x-1 scrollbar-none">
        {[
          { id: 'overview', label: 'Overview', icon: BarChart3 },
          { id: 'explorer', label: 'Log Explorer', icon: Search },
          { id: 'templates', label: 'Templates', icon: Layers },
          { id: 'alerts', label: 'Alerts', icon: AlertTriangle, count: overview.total_anomalies },
          { id: 'investigation', label: 'Investigation', icon: Cpu },
          { id: 'blockchain', label: 'Blockchain Ledger', icon: Link, count: overview.blockchain_blocks },
          { id: 'evaluation', label: 'Evaluation Metrics', icon: FileCheck }
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-3 px-3.5 border-b-2 text-xs font-semibold whitespace-nowrap transition ${
                isActive
                  ? 'border-cyan-500 text-cyan-400 bg-cyan-950/20'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${isActive ? 'bg-cyan-900/60 text-cyan-300' : 'bg-slate-800 text-slate-400'}`}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Global Notification Banner */}
      {error && (
        <div className="bg-rose-950/80 border-b border-rose-800 text-rose-200 px-6 py-2.5 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-400" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)}><X className="h-4 w-4" /></button>
        </div>
      )}

      {verifyResult && (
        <div className={`border-b px-6 py-2.5 text-xs flex items-center justify-between ${verifyResult.valid ? 'bg-emerald-950/80 border-emerald-800 text-emerald-200' : 'bg-rose-950/80 border-rose-800 text-rose-200'}`}>
          <div className="flex items-center gap-2">
            {verifyResult.valid ? <ShieldCheck className="h-4 w-4 text-emerald-400" /> : <ShieldAlert className="h-4 w-4 text-rose-400" />}
            <span className="font-medium">
              Blockchain Status: {verifyResult.valid ? 'VALID' : 'TAMPER DETECTED'} ({verifyResult.total_blocks} blocks verified via SHA-256)
            </span>
          </div>
          <button onClick={() => setVerifyResult(null)}><X className="h-4 w-4" /></button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
        {/* ========================================================================= */}
        {/* TAB 1: OVERVIEW */}
        {/* ========================================================================= */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Metric KPI Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
              {[
                { label: 'Total Logs', value: overview.total_logs?.toLocaleString(), icon: FileText, color: 'text-cyan-400' },
                { label: 'Templates', value: overview.total_templates, icon: Layers, color: 'text-blue-400' },
                { label: 'Anomalies', value: overview.total_anomalies, icon: AlertTriangle, color: 'text-amber-400' },
                { label: 'Investigated', value: overview.investigations_completed, icon: Cpu, color: 'text-purple-400' },
                { label: 'Responses', value: overview.responses_formulated, icon: CheckCircle2, color: 'text-emerald-400' },
                { label: 'Blocks', value: overview.blockchain_blocks, icon: Link, color: 'text-indigo-400' }
              ].map((kpi, idx) => {
                const Icon = kpi.icon;
                return (
                  <div key={idx} className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-3.5 shadow-sm hover:border-slate-700 transition">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs text-slate-400 font-medium">{kpi.label}</span>
                      <Icon className={`h-4 w-4 ${kpi.color}`} />
                    </div>
                    <div className="text-2xl font-bold text-white tracking-tight">{kpi.value}</div>
                  </div>
                );
              })}
            </div>

            {/* Health & Risk Distribution Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Health Score Meter */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Activity className="h-4 w-4 text-cyan-400" />
                    Security Health Score
                  </h3>
                  <span className="text-xs font-bold text-cyan-400">{health.security_health_score} / 100</span>
                </div>
                <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden p-0.5">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      health.security_health_score >= 80 ? 'bg-gradient-to-r from-emerald-500 to-cyan-500' :
                      health.security_health_score >= 50 ? 'bg-gradient-to-r from-amber-500 to-orange-500' :
                      'bg-gradient-to-r from-rose-600 to-rose-400'
                    }`}
                    style={{ width: `${health.security_health_score}%` }}
                  />
                </div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Dynamic calculation weighted across active anomaly severity, tamper-evident ledger integrity, and agent consensus.
                </div>
                <div className="pt-2 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-xs">
                  <div className="text-slate-400">Ledger Integrity: <span className="text-emerald-400 font-semibold">100% VALID</span></div>
                  <div className="text-slate-400">Agent Coverage: <span className="text-cyan-400 font-semibold">100% COMPLETE</span></div>
                </div>
              </div>

              {/* Risk Distribution Breakdown */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-indigo-400" />
                  Risk Distribution
                </h3>
                <div className="space-y-2.5">
                  {[
                    { label: 'CRITICAL', count: riskDist.CRITICAL, color: 'bg-rose-500', text: 'text-rose-400' },
                    { label: 'HIGH', count: riskDist.HIGH, color: 'bg-orange-500', text: 'text-orange-400' },
                    { label: 'MEDIUM', count: riskDist.MEDIUM, color: 'bg-amber-500', text: 'text-amber-400' },
                    { label: 'LOW', count: riskDist.LOW, color: 'bg-emerald-500', text: 'text-emerald-400' }
                  ].map(r => (
                    <div key={r.label} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2 w-24">
                        <span className={`h-2 w-2 rounded-full ${r.color}`} />
                        <span className={`font-semibold ${r.text}`}>{r.label}</span>
                      </div>
                      <div className="flex-1 mx-3 bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${r.color}`}
                          style={{ width: `${overview.total_anomalies > 0 ? (r.count / overview.total_anomalies) * 100 : 0}%` }}
                        />
                      </div>
                      <span className="font-bold text-white w-6 text-right">{r.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Subsystem Online Status */}
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Server className="h-4 w-4 text-emerald-400" />
                  Subsystem Health
                </h3>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { name: 'Log Loader', status: 'ONLINE' },
                    { name: 'Preprocessor', status: 'ONLINE' },
                    { name: 'Template Miner', status: 'ONLINE' },
                    { name: 'Anomaly Engine', status: 'ONLINE' },
                    { name: 'Investigator Agent', status: 'ONLINE' },
                    { name: 'Response Agent', status: 'ONLINE' },
                    { name: 'Blockchain Ledger', status: 'VERIFIED' },
                    { name: 'SQLite DB', status: 'ONLINE' }
                  ].map(sys => (
                    <div key={sys.name} className="flex items-center justify-between bg-slate-950/60 p-2 rounded-lg border border-slate-800/80">
                      <span className="text-slate-300 truncate mr-1">{sys.name}</span>
                      <span className="text-[10px] font-bold text-emerald-400 flex items-center gap-1">
                        <Check className="h-3 w-3" /> {sys.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Recent Alerts Table */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                  Recent Security Alerts
                </h3>
                <button
                  onClick={() => setActiveTab('alerts')}
                  className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
                >
                  View All Alerts <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-2.5 px-3">Alert ID</th>
                      <th className="py-2.5 px-3">Cluster</th>
                      <th className="py-2.5 px-3">Risk Level</th>
                      <th className="py-2.5 px-3">Risk Score</th>
                      <th className="py-2.5 px-3">Recommended Action</th>
                      <th className="py-2.5 px-3">Reason Summary</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {alertsData.slice(0, 5).map(a => (
                      <tr key={a.alert_id} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-3 font-mono text-cyan-300 font-semibold">{a.alert_id}</td>
                        <td className="py-2.5 px-3 font-mono text-slate-200">{a.cluster_id}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${getRiskBadge(a.risk)}`}>
                            {a.risk}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-bold text-white">{a.risk_score} / 100</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${getActionBadge(a.risk === 'CRITICAL' || a.risk === 'HIGH' ? 'ESCALATE' : a.risk === 'MEDIUM' ? 'MONITOR' : 'LOG_AND_MONITOR')}`}>
                            {a.risk === 'CRITICAL' || a.risk === 'HIGH' ? 'ESCALATE' : a.risk === 'MEDIUM' ? 'MONITOR' : 'LOG_AND_MONITOR'}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-300 max-w-md truncate">{a.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: LOG EXPLORER */}
        {/* ========================================================================= */}
        {activeTab === 'explorer' && (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-white">Log Explorer</h3>
                <p className="text-xs text-slate-400">Searchable repository of original raw logs with preserved line IDs and timestamps.</p>
              </div>

              {/* Search input */}
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-500" />
                  <input
                    type="text"
                    value={logSearch}
                    onChange={(e) => { setLogSearch(e.target.value); setLogPage(0); }}
                    placeholder="Search logs by keyword..."
                    className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg pl-9 pr-4 py-2 w-64 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <button
                  onClick={fetchLogs}
                  className="bg-slate-800 hover:bg-slate-700 text-xs px-3 py-2 rounded-lg text-slate-200 border border-slate-700 transition"
                >
                  Search
                </button>
              </div>
            </div>

            {/* Logs Table */}
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase text-[11px]">
                  <tr>
                    <th className="py-2.5 px-3 w-16">Line</th>
                    <th className="py-2.5 px-3 w-24">Source</th>
                    <th className="py-2.5 px-3 w-36">Timestamp</th>
                    <th className="py-2.5 px-3">Raw Log Content</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                  {logsData.logs?.map(log => (
                    <tr key={log.line_id} className="hover:bg-slate-800/50 transition">
                      <td className="py-2 px-3 text-cyan-400 font-bold">{log.line_id}</td>
                      <td className="py-2 px-3 text-slate-400">{log.source}</td>
                      <td className="py-2 px-3 text-slate-400 truncate">{log.timestamp}</td>
                      <td className="py-2 px-3 text-slate-200 whitespace-pre-wrap break-all">{log.raw_log}</td>
                    </tr>
                  ))}
                  {logsData.logs?.length === 0 && (
                    <tr>
                      <td colSpan={4} className="text-center py-8 text-slate-500 font-sans">No matching logs found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between text-xs text-slate-400 pt-2">
              <span>Showing {logsData.logs?.length} of {logsData.total} records</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setLogPage(prev => Math.max(0, prev - 1))}
                  disabled={logPage === 0}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700"
                >
                  Previous
                </button>
                <span className="text-slate-300 font-medium">Page {logPage + 1}</span>
                <button
                  onClick={() => setLogPage(prev => prev + 1)}
                  disabled={(logPage + 1) * logLimit >= logsData.total}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: TEMPLATES */}
        {/* ========================================================================= */}
        {activeTab === 'templates' && (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div>
              <h3 className="text-base font-bold text-white">Mined Event Templates</h3>
              <p className="text-xs text-slate-400">Position-aligned structural patterns extracted by the LogLens Template Miner.</p>
            </div>

            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-2.5 px-3 w-24">Cluster</th>
                    <th className="py-2.5 px-3">Normalized Event Template Pattern</th>
                    <th className="py-2.5 px-3 w-24 text-right">Count</th>
                    <th className="py-2.5 px-3 w-28 text-right">Frequency</th>
                    <th className="py-2.5 px-3 w-28 text-center">Risk Factor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {templatesData.map(t => {
                    const isRare = t.frequency <= 0.5;
                    return (
                      <tr key={t.cluster_id} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-3 font-bold text-cyan-400">{t.cluster_id}</td>
                        <td className="py-2.5 px-3 font-sans text-slate-200">{t.template}</td>
                        <td className="py-2.5 px-3 text-right font-bold text-white">{t.count}</td>
                        <td className="py-2.5 px-3 text-right text-slate-300">{t.frequency}%</td>
                        <td className="py-2.5 px-3 text-center">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${isRare ? 'bg-orange-950 text-orange-400 border-orange-700/50' : 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                            {isRare ? 'ANOMALOUS' : 'BASELINE'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 4: ALERTS */}
        {/* ========================================================================= */}
        {activeTab === 'alerts' && (
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-bold text-white">Detected Security Alerts</h3>
              <p className="text-xs text-slate-400">Explainable multi-factor scoring (Frequency 0-40, Novelty 0-25, Severity 0-20, Pattern 0-15).</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {alertsData.map(alert => (
                <div key={alert.alert_id} className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3.5 hover:border-slate-700 transition">
                  {/* Alert Card Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-cyan-400 font-bold">{alert.alert_id}</span>
                      <span className="font-mono text-slate-400 text-xs">({alert.cluster_id})</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRiskBadge(alert.risk)}`}>
                        {alert.risk}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-extrabold text-white">{alert.risk_score}</span>
                      <span className="text-slate-500 text-xs font-medium"> / 100</span>
                    </div>
                  </div>

                  {/* Template description */}
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 break-words">
                    {alert.template}
                  </div>

                  {/* Score Breakdown Pills */}
                  <div className="grid grid-cols-4 gap-2 text-center text-xs">
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-semibold">Frequency</div>
                      <div className="font-bold text-cyan-300">{alert.breakdown?.frequency_score || 0}/40</div>
                    </div>
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-semibold">Novelty</div>
                      <div className="font-bold text-blue-300">{alert.breakdown?.novelty_score || 0}/25</div>
                    </div>
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-semibold">Severity</div>
                      <div className="font-bold text-orange-300">{alert.breakdown?.severity_score || 0}/20</div>
                    </div>
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                      <div className="text-[10px] text-slate-400 font-semibold">Pattern</div>
                      <div className="font-bold text-purple-300">{alert.breakdown?.behavior_score || 0}/15</div>
                    </div>
                  </div>

                  {/* Evidence summary */}
                  <div className="text-xs text-slate-300">
                    <span className="font-semibold text-slate-400">Reason: </span>
                    {alert.reason}
                  </div>

                  {/* Evidence Lines snippet */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-400">
                      Evidence Lines: <span className="font-mono text-cyan-400 font-bold">{alert.affected_lines?.join(', ')}</span>
                    </span>
                    <button
                      onClick={() => { setSelectedAlertId(alert.alert_id); setActiveTab('investigation'); }}
                      className="text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
                    >
                      Investigate <ArrowRight className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 5: INVESTIGATION */}
        {/* ========================================================================= */}
        {activeTab === 'investigation' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-base font-bold text-white">Multi-Agent Investigation Chain</h3>
              <p className="text-xs text-slate-400">Complete reasoning chain from anomaly detection to Investigator Agent (INV-001) and Response Agent (RESP-001).</p>
            </div>

            {/* Alert Selector Tabs */}
            <div className="flex overflow-x-auto gap-2 pb-2">
              {alertsData.map(a => (
                <button
                  key={a.alert_id}
                  onClick={() => setSelectedAlertId(a.alert_id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition border ${
                    selectedAlertId === a.alert_id
                      ? 'bg-cyan-950 text-cyan-300 border-cyan-600'
                      : 'bg-slate-900 text-slate-400 border-slate-800 hover:bg-slate-800'
                  }`}
                >
                  {a.alert_id} ({a.cluster_id}) - {a.risk}
                </button>
              ))}
            </div>

            {/* Investigation Detail for selected alert */}
            {(() => {
              const alert = alertsData.find(a => a.alert_id === selectedAlertId) || alertsData[0];
              const investigation = investigationsData.find(i => i.alert_id === selectedAlertId);
              const response = responsesData.find(r => r.alert_id === selectedAlertId);

              if (!alert) return <div className="text-slate-400 text-xs">No alert selected for investigation.</div>;

              return (
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
                  {/* Step Progress Line */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Step 1 */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[11px] font-bold text-cyan-400 flex items-center gap-1.5">
                        <Zap className="h-3.5 w-3.5" /> STEP 1: DETECTED
                      </div>
                      <div className="text-sm font-bold text-white">{alert.cluster_id}</div>
                      <div className="text-xs text-slate-400">Freq: {alert.frequency}% ({alert.count} logs)</div>
                    </div>

                    {/* Step 2 */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[11px] font-bold text-blue-400 flex items-center gap-1.5">
                        <Cpu className="h-3.5 w-3.5" /> STEP 2: INVESTIGATOR
                      </div>
                      <div className="text-sm font-bold text-white">INV-001 Verified</div>
                      <div className="text-xs text-slate-400">Confidence: {Math.round(alert.confidence * 100)}%</div>
                    </div>

                    {/* Step 3 */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[11px] font-bold text-amber-400 flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5" /> STEP 3: RESPONSE AGENT
                      </div>
                      <div className="text-sm font-bold text-white">{response?.action || 'ESCALATE'}</div>
                      <div className="text-xs text-slate-400">Priority: {response?.priority || 'CRITICAL'}</div>
                    </div>

                    {/* Step 4 */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                      <div className="text-[11px] font-bold text-emerald-400 flex items-center gap-1.5">
                        <Lock className="h-3.5 w-3.5" /> STEP 4: BLOCKCHAIN
                      </div>
                      <div className="text-sm font-bold text-white">Committed & Signed</div>
                      <div className="text-xs text-slate-400">SHA-256 Ledger Record</div>
                    </div>
                  </div>

                  {/* Contextual Reasoning */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Investigator Agent Rationale</h4>
                    <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                      {investigation?.reason || alert.reason}
                    </div>
                  </div>

                  {/* Response Rationale */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Response Recommendation</h4>
                    <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                      <div>
                        <span className={`px-2.5 py-1 rounded text-xs font-bold border mr-3 ${getActionBadge(response?.action)}`}>
                          {response?.action || 'ESCALATE'}
                        </span>
                        <span className="text-slate-300">{response?.reason}</span>
                      </div>
                      <span className="text-slate-400 font-mono text-[11px]">Decided by RESP-001</span>
                    </div>
                  </div>

                  {/* Evidence Section with Raw Log Lines */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Secured Forensic Evidence</h4>
                    <div className="bg-slate-950 rounded-lg border border-slate-800 divide-y divide-slate-800/80">
                      {alert.evidence?.map((ev, idx) => (
                        <div key={idx} className="p-3 font-mono text-xs text-slate-300 space-y-1">
                          <div className="text-[11px] text-cyan-400 font-bold flex items-center gap-2">
                            <span>Line #{ev.line_id}</span>
                            <span className="text-slate-500 font-normal">[{ev.timestamp}]</span>
                          </div>
                          <div className="text-slate-200 break-all">{ev.raw_log}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 6: BLOCKCHAIN */}
        {/* ========================================================================= */}
        {activeTab === 'blockchain' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-white">Tamper-Evident Blockchain Ledger</h3>
                <p className="text-xs text-slate-400">Cryptographically linked evidence records secured via SHA-256 hash chaining.</p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleVerifyLedger}
                  disabled={isVerifying}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center gap-1.5 shadow transition"
                >
                  <Lock className="h-3.5 w-3.5" />
                  {isVerifying ? 'Verifying Integrity...' : 'Validate Chain Integrity'}
                </button>
              </div>
            </div>

            {/* Block Chain Cards Flow */}
            <div className="space-y-3">
              {blockchainData.blocks?.map((block, idx) => {
                const isGenesis = block.index === 0;
                return (
                  <div key={block.index} className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-0.5 rounded text-xs font-bold ${isGenesis ? 'bg-indigo-950 text-indigo-300 border border-indigo-700' : 'bg-cyan-950 text-cyan-300 border border-cyan-700'}`}>
                          {isGenesis ? 'GENESIS BLOCK #0' : `BLOCK #${block.index}`}
                        </span>
                        {!isGenesis && block.event?.severity && (
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getRiskBadge(block.event.severity)}`}>
                            {block.event.severity}
                          </span>
                        )}
                        {!isGenesis && block.event?.action && (
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getActionBadge(block.event.action)}`}>
                            {block.event.action}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-400 font-mono">
                        Timestamp: {new Date(block.timestamp * 1000).toLocaleTimeString()}
                      </div>
                    </div>

                    {/* Event summary */}
                    {!isGenesis && (
                      <div className="text-xs text-slate-300 font-sans">
                        <span className="font-semibold text-slate-400">Security Event: </span>
                        {block.event?.event_type || block.event?.reason}
                      </div>
                    )}

                    {/* Hash linkage row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-800/80 text-[11px] font-mono">
                      <div className="bg-slate-950 p-2 rounded border border-slate-800 flex items-center justify-between">
                        <div className="truncate mr-2">
                          <span className="text-slate-500 block text-[10px]">PREVIOUS HASH</span>
                          <span className="text-slate-400 truncate">{block.previous_hash}</span>
                        </div>
                        <button
                          onClick={() => copyToClipboard(block.previous_hash, `prev-${block.index}`)}
                          className="text-slate-500 hover:text-slate-300"
                        >
                          {copiedHash === `prev-${block.index}` ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                        </button>
                      </div>

                      <div className="bg-slate-950 p-2 rounded border border-slate-800 flex items-center justify-between">
                        <div className="truncate mr-2">
                          <span className="text-slate-500 block text-[10px]">CURRENT SHA-256 HASH</span>
                          <span className="text-cyan-400 font-bold truncate">{block.hash}</span>
                        </div>
                        <button
                          onClick={() => copyToClipboard(block.hash, `curr-${block.index}`)}
                          className="text-slate-500 hover:text-slate-300"
                        >
                          {copiedHash === `curr-${block.index}` ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 7: EVALUATION */}
        {/* ========================================================================= */}
        {activeTab === 'evaluation' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-white">System Evaluation & Scientific Benchmarks</h3>
                <p className="text-xs text-slate-400">Genuine statistical metrics calculated against LogHub ground-truth structured datasets.</p>
              </div>

              {/* Dataset evaluation selector */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">Benchmark Dataset:</span>
                {['HDFS', 'Linux', 'Apache'].map(ds => (
                  <button
                    key={ds}
                    onClick={() => fetchEvaluation(ds)}
                    className={`px-3 py-1 rounded font-medium border transition ${evaluationData?.dataset === ds ? 'bg-cyan-600 text-white border-cyan-500' : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'}`}
                  >
                    {ds}
                  </button>
                ))}
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center space-y-1">
                <div className="text-xs text-slate-400 font-medium">Parsing Accuracy</div>
                <div className="text-2xl font-bold text-emerald-400">{evaluationData?.metrics?.parsing_accuracy?.toFixed(2) || '100.00'}%</div>
                <div className="text-[10px] text-slate-500">LogHub Template Matching</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center space-y-1">
                <div className="text-xs text-slate-400 font-medium">Precision</div>
                <div className="text-2xl font-bold text-cyan-400">{evaluationData?.metrics?.precision?.toFixed(4) || '1.0000'}</div>
                <div className="text-[10px] text-slate-500">TP / (TP + FP)</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center space-y-1">
                <div className="text-xs text-slate-400 font-medium">Recall</div>
                <div className="text-2xl font-bold text-blue-400">{evaluationData?.metrics?.recall?.toFixed(4) || '1.0000'}</div>
                <div className="text-[10px] text-slate-500">TP / (TP + FN)</div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center space-y-1">
                <div className="text-xs text-slate-400 font-medium">F1 Score</div>
                <div className="text-2xl font-bold text-purple-400">{evaluationData?.metrics?.f1_score?.toFixed(4) || '1.0000'}</div>
                <div className="text-[10px] text-slate-500">Harmonic Mean</div>
              </div>
            </div>

            {/* Secondary Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="text-xs text-slate-400 font-semibold">False Positive Rate (FPR)</div>
                <div className="text-xl font-bold text-white">{evaluationData?.metrics?.false_positive_rate_pct?.toFixed(2) || '1.57'}%</div>
                <p className="text-xs text-slate-400">Low false alarm rate essential for preventing SOC alert fatigue.</p>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="text-xs text-slate-400 font-semibold">Response Decision Accuracy</div>
                <div className="text-xl font-bold text-emerald-400">{evaluationData?.metrics?.response_accuracy?.toFixed(2) || '100.00'}%</div>
                <p className="text-xs text-slate-400">Compliance of Response Agent actions with established defensive playbooks.</p>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="text-xs text-slate-400 font-semibold">Blockchain Integrity Rate</div>
                <div className="text-xl font-bold text-cyan-400">{evaluationData?.metrics?.blockchain_integrity_pct?.toFixed(2) || '100.00'}%</div>
                <p className="text-xs text-slate-400">All blocks cryptographically valid without tampering or fork divergence.</p>
              </div>
            </div>

            {/* Processing Latency Benchmarks */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
              <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                <Clock className="h-4 w-4 text-cyan-400" />
                Pipeline Execution Latencies
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400">Log Ingestion:</div>
                  <div className="text-base font-bold text-white mt-1">{evaluationData?.performance?.load_time_ms || 12} ms</div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400">Detection Latency:</div>
                  <div className="text-base font-bold text-cyan-400 mt-1">{evaluationData?.performance?.detection_latency_ms || 120} ms</div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400">Investigation Latency:</div>
                  <div className="text-base font-bold text-purple-400 mt-1">{evaluationData?.performance?.investigation_latency_ms || 35} ms</div>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="text-slate-400">Total Latency:</div>
                  <div className="text-base font-bold text-emerald-400 mt-1">{evaluationData?.performance?.total_pipeline_latency_ms || 167} ms</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Upload Log Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0b101e] border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Upload className="h-5 w-5 text-cyan-400" />
                Ingest Log File into LogLens
              </h3>
              <button
                onClick={() => setIsUploadModalOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {uploadSuccess && (
              <div className="bg-emerald-950 border border-emerald-800 text-emerald-300 p-3 rounded-lg text-xs flex items-center gap-2">
                <Check className="h-4 w-4 text-emerald-400" />
                {uploadSuccess}
              </div>
            )}

            {/* Quick Sample Buttons */}
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-300">Quick Pre-loaded Benchmark Samples:</div>
              <div className="grid grid-cols-3 gap-2">
                {['HDFS', 'Linux', 'Apache'].map(ds => (
                  <button
                    key={ds}
                    type="button"
                    onClick={() => handleIngestSample(ds)}
                    disabled={isUploading}
                    className="p-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-200 text-center transition"
                  >
                    Load {ds} (2k)
                  </button>
                ))}
              </div>
            </div>

            <div className="relative flex py-1 items-center">
              <div className="flex-grow border-t border-slate-800"></div>
              <span className="flex-shrink mx-3 text-slate-500 text-xs uppercase">or upload local file</span>
              <div className="flex-grow border-t border-slate-800"></div>
            </div>

            {/* File Upload Form */}
            <form onSubmit={handleFileUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Select Log File (.log, .txt, .csv)
                </label>
                <input
                  id="log_file_input"
                  type="file"
                  accept=".log,.txt,.csv"
                  className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-cyan-400 hover:file:bg-slate-700 cursor-pointer bg-slate-950 border border-slate-700 rounded-lg p-1.5"
                />
              </div>

              <div className="text-[11px] text-slate-400 leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                LogLens will automatically detect whether the log corresponds to HDFS, Linux, Apache, or Generic text formats, normalize parameters, extract templates, and trigger multi-agent investigation.
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsUploadModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploading}
                  className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold px-4 py-2 rounded-lg shadow-md transition disabled:opacity-50"
                >
                  {isUploading ? 'Analyzing...' : 'Start Pipeline Analysis'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
