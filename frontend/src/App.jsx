import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Database,
  RefreshCw,
  AlertTriangle,
  HelpCircle,
  Server,
  FileCheck2,
  Copy,
  Check,
  PlusCircle,
  X
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

export default function App() {
  const [chain, setChain] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState(null);
  const [integrityStatus, setIntegrityStatus] = useState('UNKNOWN'); // UNKNOWN | VERIFIED | TAMPER DETECTED
  const [lastVerifiedAt, setLastVerifiedAt] = useState(null);
  const [ledgerStatus, setLedgerStatus] = useState('CHECKING...');
  const [copiedHash, setCopiedHash] = useState(null);

  // Modal for manual evidence submission
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [formData, setFormData] = useState({
    event_id: 'TEST-004',
    event_type: 'DATA_EXFILTRATION',
    severity: 'CRITICAL',
    user: 'analyst_bob',
    ip: '192.168.1.120'
  });

  // Fetch the real evidence chain from Member 3 backend
  const fetchChain = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/evidence/chain`);
      if (!res.ok) {
        throw new Error(`Evidence service returned status: ${res.status}`);
      }
      const data = await res.json();
      setChain(Array.isArray(data) ? data : []);
      setLedgerStatus('ACTIVE');
    } catch (err) {
      setError(err.message || 'Unable to connect to evidence backend service.');
      setLedgerStatus('OFFLINE');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Trigger real verification endpoint
  const handleVerify = async () => {
    setIsVerifying(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/evidence/verify`);
      if (!res.ok) {
        throw new Error(`Verification service returned status: ${res.status}`);
      }
      const data = await res.json();
      if (data.valid === true) {
        setIntegrityStatus('VERIFIED');
      } else {
        setIntegrityStatus('TAMPER DETECTED');
      }
      setLastVerifiedAt(new Date().toLocaleTimeString());
    } catch (err) {
      setError(`Integrity verification failed: ${err.message}`);
      setIntegrityStatus('UNKNOWN');
    } finally {
      setIsVerifying(false);
    }
  };

  // Submit new evidence to POST /evidence/add
  const handleAddEvidence = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSubmitSuccess(null);
    try {
      const res = await fetch(`${API_BASE}/evidence/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!res.ok) {
        throw new Error(`Evidence ingestion failed with HTTP ${res.status}`);
      }
      const result = await res.json();
      setSubmitSuccess(`Committed Block #${result.block.index} to hash chain.`);
      // Re-fetch chain to reflect updated state
      await fetchChain();
      // Auto-increment test event id for convenient testing
      setFormData(prev => ({
        ...prev,
        event_id: `TEST-${String(chain.length + 1).padStart(3, '0')}`
      }));
      setTimeout(() => {
        setIsAddModalOpen(false);
        setSubmitSuccess(null);
      }, 1200);
    } catch (err) {
      setError(`Failed to add evidence: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    fetchChain();
  }, [fetchChain]);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  // Filter evidence events (excluding genesis block)
  const evidenceRecords = chain.filter(block => block.index > 0);

  const getSeverityBadge = (severity) => {
    const s = (severity || 'UNKNOWN').toUpperCase();
    switch (s) {
      case 'CRITICAL':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'HIGH':
        return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'LOW':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      default:
        return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="min-h-screen bg-[#070a13] text-slate-100 flex flex-col items-center justify-start p-4 sm:p-8 md:p-12">
      <div className="w-full max-w-6xl space-y-8">
        
        {/* Header Section */}
        <header className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800/80 gap-4">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.15)]">
              <Shield className="w-8 h-8 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold tracking-wider text-cyan-400 uppercase bg-cyan-950/60 border border-cyan-800/60 px-2.5 py-0.5 rounded-full">
                  Member 3 Subsystem
                </span>
                <span className="text-xs text-slate-500 font-mono">v1.0.0-soc</span>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white mt-1">
                LOGLENS SECURITY
              </h1>
              <p className="text-sm text-slate-400">
                Evidence Integrity Dashboard
              </p>
            </div>
          </div>

          <div className="flex items-center flex-wrap gap-3">
            {/* Quick Evidence Ingestion Button */}
            <button
              onClick={() => setIsAddModalOpen(true)}
              disabled={ledgerStatus === 'OFFLINE'}
              className="inline-flex items-center px-3.5 py-2.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-cyan-500/50 text-slate-200 hover:text-white font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <PlusCircle className="w-4 h-4 mr-2 text-cyan-400" />
              Add Evidence
            </button>

            {/* VERIFY NOW Button */}
            <button
              onClick={handleVerify}
              disabled={isVerifying || ledgerStatus === 'OFFLINE'}
              className="inline-flex items-center px-4 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm tracking-wide transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:shadow-[0_0_25px_rgba(6,182,212,0.5)] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isVerifying ? 'animate-spin' : ''}`} />
              {isVerifying ? 'VERIFYING...' : 'VERIFY NOW'}
            </button>

            {/* Refresh Chain Button */}
            <button
              onClick={fetchChain}
              disabled={isLoading}
              title="Refresh ledger state"
              className="p-2.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white transition-colors cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </header>

        {/* Backend Error State Banner */}
        {error && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl flex items-start space-x-3 text-rose-300 animate-fadeIn">
            <AlertTriangle className="w-5 h-5 mt-0.5 shrink-0 text-rose-400" />
            <div className="flex-1 text-sm">
              <div className="font-semibold text-rose-200">Backend Communication Issue</div>
              <div className="text-xs text-rose-300/80 mt-0.5">{error}</div>
            </div>
            <button
              onClick={fetchChain}
              className="text-xs font-semibold px-2.5 py-1 bg-rose-900/60 hover:bg-rose-800 border border-rose-700 rounded text-rose-200 transition-colors"
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* Summary Cards */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Card 1: Evidence Records */}
          <div className="bg-[#0f1523] border border-slate-800/90 rounded-xl p-6 shadow-lg relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Evidence Records
              </span>
              <div className="p-2 bg-cyan-500/10 border border-cyan-500/20 rounded-lg">
                <FileCheck2 className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-3">
              <span className="text-3xl font-bold text-white tracking-tight font-mono">
                {isLoading ? '...' : evidenceRecords.length}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {chain.length > 0 ? `(${chain.length} total blocks incl. Genesis)` : 'empty'}
              </span>
            </div>
            <p className="mt-3 text-xs text-slate-400 leading-relaxed">
              Real cryptographic evidence entries verified in local ledger.
            </p>
          </div>

          {/* Card 2: Ledger Status */}
          <div className="bg-[#0f1523] border border-slate-800/90 rounded-xl p-6 shadow-lg relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Ledger Status
              </span>
              <div className={`p-2 rounded-lg border ${
                ledgerStatus === 'ACTIVE'
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                  : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
              }`}>
                <Database className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className={`text-3xl font-bold tracking-wide font-mono ${
                ledgerStatus === 'ACTIVE' ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {ledgerStatus}
              </span>
            </div>
            <p className="mt-3 text-xs text-slate-400 leading-relaxed">
              Target storage: <code className="text-cyan-300 font-mono">data/evidence_ledger.json</code>
            </p>
          </div>

          {/* Card 3: Integrity Status */}
          <div className="bg-[#0f1523] border border-slate-800/90 rounded-xl p-6 shadow-lg relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Integrity Status
              </span>
              <div className={`p-2 rounded-lg border ${
                integrityStatus === 'VERIFIED'
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                  : integrityStatus === 'TAMPER DETECTED'
                  ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                  : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
              }`}>
                {integrityStatus === 'VERIFIED' && <ShieldCheck className="w-5 h-5" />}
                {integrityStatus === 'TAMPER DETECTED' && <ShieldAlert className="w-5 h-5" />}
                {integrityStatus === 'UNKNOWN' && <HelpCircle className="w-5 h-5" />}
              </div>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className={`text-3xl font-bold tracking-wide font-mono ${
                integrityStatus === 'VERIFIED'
                  ? 'text-emerald-400'
                  : integrityStatus === 'TAMPER DETECTED'
                  ? 'text-rose-400 animate-pulse'
                  : 'text-amber-400'
              }`}>
                {integrityStatus}
              </span>
            </div>
            <p className="mt-3 text-xs text-slate-400 leading-relaxed">
              {lastVerifiedAt ? `Last verified at ${lastVerifiedAt}` : 'Awaiting verification ("VERIFY NOW").'}
            </p>
          </div>

        </section>

        {/* Recent Evidence Table & Ledger Inspection */}
        <section className="bg-[#0f1523] border border-slate-800/90 rounded-xl overflow-hidden shadow-xl">
          <div className="p-5 border-b border-slate-800 flex items-center justify-between flex-wrap gap-2">
            <div>
              <h2 className="text-base font-semibold text-white tracking-wide">
                Recent Evidence Chain
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Full chronological ledger with SHA-256 block hashes and parent hash linkage
              </p>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/50 px-3 py-1 rounded-full">
              SHA-256 Hash Chain
            </span>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="py-20 flex flex-col items-center justify-center space-y-4">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              <div className="text-sm text-slate-400 font-mono tracking-wider">
                QUERYING EVIDENCE LEDGER...
              </div>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && evidenceRecords.length === 0 && (
            <div className="py-20 flex flex-col items-center justify-center text-center px-4">
              <div className="p-4 bg-slate-900 border border-slate-800 rounded-full text-slate-500 mb-4">
                <Database className="w-8 h-8" />
              </div>
              <h3 className="text-base font-semibold text-slate-300">No Evidence Records Found</h3>
              <p className="text-xs text-slate-400 max-w-md mt-1 leading-relaxed">
                The evidence ledger currently contains only the Genesis block.
                Click "Add Evidence" or submit to <code className="text-cyan-400">/evidence/add</code> to record verified hash blocks.
              </p>
            </div>
          )}

          {/* Evidence Table */}
          {!isLoading && !error && evidenceRecords.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#0b0f19] border-b border-slate-800 text-slate-400 font-mono text-xs uppercase tracking-wider">
                    <th className="py-3 px-4">Event ID</th>
                    <th className="py-3 px-4">Event Type</th>
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">IP</th>
                    <th className="py-3 px-4">Hash</th>
                    <th className="py-3 px-4 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs">
                  {evidenceRecords.map((block) => {
                    const evt = block.event || {};
                    const isTampered = integrityStatus === 'TAMPER DETECTED';
                    const isVerified = integrityStatus === 'VERIFIED';
                    
                    return (
                      <tr
                        key={block.index}
                        className="hover:bg-slate-900/40 transition-colors font-sans"
                      >
                        <td className="py-3 px-4 font-mono font-medium text-cyan-300">
                          {evt.event_id || `EVT-${block.index}`}
                        </td>
                        <td className="py-3 px-4 font-semibold text-slate-200">
                          {evt.event_type || 'UNKNOWN'}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-block px-2.5 py-0.5 rounded text-[11px] font-semibold border ${getSeverityBadge(evt.severity)}`}>
                            {evt.severity || 'MEDIUM'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-300 font-mono">
                          {evt.user || 'SYSTEM'}
                        </td>
                        <td className="py-3 px-4 text-slate-300 font-mono">
                          {evt.ip || '127.0.0.1'}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-400">
                          <div className="flex items-center space-x-2">
                            <span title={block.hash}>
                              {block.hash.slice(0, 10)}...{block.hash.slice(-8)}
                            </span>
                            <button
                              onClick={() => copyToClipboard(block.hash, block.index)}
                              title="Copy SHA-256 hash"
                              className="text-slate-500 hover:text-cyan-400 transition-colors p-1"
                            >
                              {copiedHash === block.index ? (
                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded text-[11px] font-semibold border ${
                              isTampered
                                ? 'bg-rose-500/15 text-rose-400 border-rose-500/30 animate-pulse'
                                : isVerified
                                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                                : 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}
                          >
                            {isTampered ? 'FLAGGED' : isVerified ? 'VERIFIED' : 'COMMITTED'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Chain Linkage Summary */}
          {chain.length > 0 && (
            <div className="p-3 bg-[#0a0e17] border-t border-slate-800 text-slate-400 text-[11px] font-mono flex items-center justify-between flex-wrap gap-2">
              <div>
                Genesis Hash: <span className="text-slate-300">{chain[0]?.hash.slice(0, 16)}...</span>
              </div>
              <div>
                Total Chained Blocks: <span className="text-cyan-400 font-semibold">{chain.length}</span>
              </div>
            </div>
          )}
        </section>

        {/* Modal: Add Test Evidence */}
        {isAddModalOpen && (
          <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[#0f1523] border border-slate-700 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-cyan-400" />
                  <h3 className="text-base font-semibold text-white">Record Evidence Event</h3>
                </div>
                <button
                  onClick={() => setIsAddModalOpen(false)}
                  className="text-slate-400 hover:text-white p-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {submitSuccess && (
                <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded-lg text-emerald-300 text-xs">
                  {submitSuccess}
                </div>
              )}

              <form onSubmit={handleAddEvidence} className="space-y-4 text-xs font-mono">
                <div>
                  <label className="block text-slate-400 mb-1">Event ID</label>
                  <input
                    type="text"
                    required
                    value={formData.event_id}
                    onChange={(e) => setFormData({ ...formData, event_id: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Event Type</label>
                  <input
                    type="text"
                    required
                    value={formData.event_type}
                    onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 mb-1">Severity</label>
                    <select
                      value={formData.severity}
                      onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                    >
                      <option value="CRITICAL">CRITICAL</option>
                      <option value="HIGH">HIGH</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="LOW">LOW</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Target User</label>
                    <input
                      type="text"
                      value={formData.user}
                      onChange={(e) => setFormData({ ...formData, user: e.target.value })}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Source IP</label>
                  <input
                    type="text"
                    value={formData.ip}
                    onChange={(e) => setFormData({ ...formData, ip: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsAddModalOpen(false)}
                    className="px-3.5 py-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? 'Recording...' : 'Commit to Chain'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="text-center text-xs text-slate-600 font-mono pt-4">
          LogLens Security Subsystem &bull; Member 3 Evidence Integrity &bull; Tamper-Detection Engine
        </footer>

      </div>
    </div>
  );
}
