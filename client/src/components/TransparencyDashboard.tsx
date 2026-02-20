import React, { useState, useEffect } from 'react';
import { useClimateRWA } from '../hooks/useClimateRWA';
import {
    Activity,
    ShieldCheck,
    Globe,
    Database,
    AlertTriangle,
    ExternalLink,
    ChevronRight
} from 'lucide-react';

interface TransparencyDashboardProps {
    txHash?: string;
}

const TransparencyDashboard: React.FC<TransparencyDashboardProps> = ({ txHash }) => {
    const { loading, error, fetchAuditTrail, fetchVaultStats } = useClimateRWA();
    const [auditData, setAuditData] = useState<any>(null);
    const [vaultStats, setVaultStats] = useState<any>(null);

    useEffect(() => {
        const loadData = async () => {
            if (txHash) {
                const audit = await fetchAuditTrail(txHash);
                setAuditData(audit);
            }
            const stats = await fetchVaultStats();
            setVaultStats(stats);
        };
        loadData();
    }, [txHash, fetchAuditTrail, fetchVaultStats]);

    return (
        <div className="p-6 space-y-8 bg-slate-900 text-white min-h-screen">
            <header className="flex justify-between items-center bg-slate-800 p-6 rounded-2xl border border-slate-700">
                <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                        Transparency & Audit Engine
                    </h1>
                    <p className="text-slate-400 text-sm mt-1">Institutional Proof of Climate RWA Settlement</p>
                </div>
                <div className="flex space-x-4">
                    <div className="flex items-center space-x-2 px-4 py-2 bg-emerald-500/10 rounded-full border border-emerald-500/20">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">Verified by GCP</span>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl">
                    <div className="flex items-center space-x-3 mb-4">
                        <Activity className="w-5 h-5 text-cyan-400" />
                        <h3 className="font-semibold">Vault TVL</h3>
                    </div>
                    <p className="text-3xl font-bold font-mono">
                        {vaultStats ? `$${(vaultStats.tvl_usdc / 1000000).toFixed(2)}M` : 'Loading...'}
                    </p>
                    <div className="mt-2 text-xs text-slate-400">Locked in RWA Risk Pools</div>
                </div>

                <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl">
                    <div className="flex items-center space-x-3 mb-4">
                        <Globe className="w-5 h-5 text-emerald-400" />
                        <h3 className="font-semibold">Current Yield (APY)</h3>
                    </div>
                    <p className="text-3xl font-bold text-emerald-400 font-mono">
                        {vaultStats ? vaultStats.current_apy : 'Loading...'}
                    </p>
                    <div className="mt-2 text-xs text-slate-400">Based on Global Premiums</div>
                </div>

                <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-xl">
                    <div className="flex items-center space-x-3 mb-4">
                        <AlertTriangle className="w-5 h-5 text-amber-400" />
                        <h3 className="font-semibold">Active Claims</h3>
                    </div>
                    <p className="text-3xl font-bold font-mono">
                        {vaultStats ? `$${(vaultStats.total_claims_paid / 1000).toFixed(1)}k` : 'Loading...'}
                    </p>
                    <div className="mt-2 text-xs text-slate-400">Automated Payouts to Date</div>
                </div>
            </div>

            {auditData && (
                <section className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
                    <div className="p-6 border-b border-slate-700 bg-slate-800/50 flex justify-between items-center">
                        <div className="flex items-center space-x-3">
                            <Database className="w-5 h-5 text-indigo-400" />
                            <h2 className="text-xl font-semibold">Transaction Proof of Evidence</h2>
                        </div>
                        <a
                            href={`https://polygonscan.com/tx/${txHash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center space-x-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
                        >
                            <span>View on Chain</span>
                            <ExternalLink className="w-4 h-4" />
                        </a>
                    </div>

                    <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-12">
                        <div className="space-y-6">
                            <div>
                                <label className="text-xs uppercase tracking-widest text-slate-500 font-bold">Satellite Data (GEE)</label>
                                <div className="mt-4 p-6 bg-slate-900 rounded-xl border border-slate-700">
                                    <div className="flex justify-between items-center mb-6">
                                        <span className="text-slate-400">Source</span>
                                        <span className="font-mono text-emerald-400">{auditData.satellite_evidence.source}</span>
                                    </div>
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <span className="text-slate-400 text-sm font-semibold">NDVI Index (Relative)</span>
                                            <span className="font-mono text-amber-400 font-bold">{auditData.satellite_evidence.ndvi_at_payout}</span>
                                        </div>
                                        <div className="w-full bg-slate-800 rounded-full h-2">
                                            <div
                                                className="bg-amber-500 h-2 rounded-full shadow-[0_0_8px_rgba(245,158,11,0.5)]"
                                                style={{ width: `${auditData.satellite_evidence.ndvi_at_payout * 100}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-6">
                            <div>
                                <label className="text-xs uppercase tracking-widest text-slate-500 font-bold">Actuarial Validation (Vertex AI)</label>
                                <div className="mt-4 p-6 bg-slate-900 rounded-xl border border-slate-700">
                                    <div className="flex justify-between items-center mb-6">
                                        <span className="text-slate-400">Severity Score</span>
                                        <span className="text-2xl font-bold text-red-400 font-mono">{auditData.actuarial_proof.severity_score} / 5</span>
                                    </div>
                                    <div className="p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/20 flex justify-between items-center">
                                        <span className="text-xs text-emerald-400">Monte Carlo Confidence</span>
                                        <span className="font-mono text-emerald-400 text-sm font-bold">{auditData.actuarial_proof.monte_carlo_confidence}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="px-8 py-4 bg-indigo-500 text-white flex justify-between items-center">
                        <span className="text-xs font-bold tracking-tight uppercase">Immutable Audit Hash (BigQuery)</span>
                        <span className="text-xs font-mono opacity-80">{auditData.tx_hash}</span>
                    </div>
                </section>
            )}

            {error && (
                <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-500 flex items-center space-x-3">
                    <AlertTriangle className="w-5 h-5" />
                    <p className="text-sm font-semibold">{error}</p>
                </div>
            )}
        </div>
    );
};

export default TransparencyDashboard;
