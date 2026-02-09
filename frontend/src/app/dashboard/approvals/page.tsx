"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { approvalsApi, PendingAction } from "@/lib/api/client";
import { AlertCircle, CheckCircle, XCircle, ShieldAlert, Clock, Activity } from "lucide-react";

export default function ApprovalsPage() {
    const [actions, setActions] = useState<PendingAction[]>([]);
    const [loading, setLoading] = useState(true);
    const [processingId, setProcessingId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const fetchActions = async () => {
        try {
            const data = await approvalsApi.listPending({ status: "pending" });
            setActions(data);
            setError(null);
        } catch (err) {
            console.error("Failed to fetch pending actions:", err);
            // Don't show error on background refresh to avoid flickering unless it's the first load
            if (loading) setError("Failed to load pending actions");
        } finally {
            if (loading) setLoading(false);
        }
    };

    useEffect(() => {
        fetchActions();
        // Poll every 5 seconds
        const interval = setInterval(fetchActions, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleApprove = async (id: string) => {
        setProcessingId(id);
        try {
            await approvalsApi.approve(id);
            // Remove from list immediately (Optimistic update)
            setActions(prev => prev.filter(a => a.id !== id));
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Failed to approve action";
            alert(msg);
        } finally {
            setProcessingId(null);
        }
    };

    const handleReject = async (id: string) => {
        setProcessingId(id);
        try {
            await approvalsApi.reject(id, "Rejected by user from dashboard");
            setActions(prev => prev.filter(a => a.id !== id));
        } catch (err) {
            console.error(err);
            alert("Failed to reject action");
        } finally {
            setProcessingId(null);
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case "critical": return "destructive"; // Red
            case "high": return "destructive"; // Red
            case "medium": return "default"; // Primary/Blue
            case "low": return "secondary"; // Gray/Blue
            default: return "outline";
        }
    };

    const formatTimeRemaining = (expiresAt?: string) => {
        if (!expiresAt) return "No expiration";
        const now = new Date();
        const expiry = new Date(expiresAt);
        const diffMs = expiry.getTime() - now.getTime();

        if (diffMs <= 0) return "Expired";

        const minutes = Math.floor(diffMs / 60000);
        const seconds = Math.floor((diffMs % 60000) / 1000);

        return `${minutes}m ${seconds}s remaining`;
    };

    if (loading) {
        return (
            <div className="p-8 space-y-4 animate-pulse">
                <div className="h-8 w-64 bg-slate-800 rounded"></div>
                <div className="h-48 w-full bg-slate-900 rounded-lg border border-slate-800"></div>
                <div className="h-48 w-full bg-slate-900 rounded-lg border border-slate-800"></div>
            </div>
        );
    }

    return (
        <div className="p-8 space-y-6">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                    <ShieldAlert className="h-8 w-8 text-blue-500" />
                    Pending Approvals
                </h1>
                <p className="text-slate-400">
                    Review and authorize automated defense actions.
                </p>
            </div>

            {error && (
                <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg text-red-200">
                    {error}
                </div>
            )}

            {actions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 border border-dashed border-slate-700 rounded-lg bg-slate-900/50">
                    <CheckCircle className="h-16 w-16 text-green-500 mb-4" />
                    <h3 className="text-xl font-semibold text-white">All Clear!</h3>
                    <p className="text-slate-400 mt-2">No pending actions require your attention.</p>
                </div>
            ) : (
                <div className="grid gap-6">
                    {actions.map((action) => (
                        <Card key={action.id} className="bg-slate-900/50 border-slate-800 hover:border-blue-500/50 transition-colors">
                            <CardHeader className="pb-3">
                                <div className="flex justify-between items-start">
                                    <div className="flex items-center gap-3">
                                        <Badge variant={getSeverityColor(action.severity) as any} className="uppercase">
                                            {action.severity}
                                        </Badge>
                                        <CardTitle className="text-xl text-white font-mono">
                                            {action.action_type}
                                        </CardTitle>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-slate-400 font-mono">
                                        <Clock className="h-4 w-4" />
                                        {formatTimeRemaining(action.expires_at)}
                                    </div>
                                </div>
                                <CardDescription className="text-slate-400 mt-2 font-mono text-xs">
                                    ID: {action.id} • Module: {action.module_name}
                                </CardDescription>
                            </CardHeader>

                            <CardContent className="space-y-4">
                                <div className="bg-slate-950/50 p-4 rounded-md border border-slate-800">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <span className="text-xs uppercase text-slate-500 font-semibold block mb-1">Target</span>
                                            <span className="text-blue-300 font-mono text-lg">{action.target}</span>
                                            <span className="text-xs text-slate-500 ml-2">({action.target_type})</span>
                                        </div>
                                        <div>
                                            <span className="text-xs uppercase text-slate-500 font-semibold block mb-1">Confidence</span>
                                            <div className="flex items-center gap-2">
                                                <div className="h-2 w-24 bg-slate-800 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full ${action.confidence_score > 0.8 ? 'bg-green-500' : 'bg-yellow-500'}`}
                                                        style={{ width: `${action.confidence_score * 100}%` }}
                                                    />
                                                </div>
                                                <span className="text-white font-mono">{Math.round(action.confidence_score * 100)}%</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <span className="text-xs uppercase text-slate-500 font-semibold block mb-1">Reason</span>
                                    <p className="text-slate-300 leading-relaxed">{action.reason}</p>
                                </div>

                                {action.auto_action === 'approve' && (
                                    <div className="flex items-center gap-2 text-yellow-500 text-sm mt-2">
                                        <AlertCircle className="h-4 w-4" />
                                        <span>Warning: This action will auto-approve if not decided upon.</span>
                                    </div>
                                )}
                            </CardContent>

                            <CardFooter className="flex justify-end gap-3 pt-2">
                                <Button
                                    variant="outline"
                                    onClick={() => handleReject(action.id)}
                                    disabled={!!processingId}
                                    className="border-red-500/50 text-red-500 hover:bg-red-950 hover:text-red-400"
                                >
                                    {processingId === action.id ? <Activity className="h-4 w-4 animate-spin mr-2" /> : <XCircle className="h-4 w-4 mr-2" />}
                                    Reject
                                </Button>
                                <Button
                                    onClick={() => handleApprove(action.id)}
                                    disabled={!!processingId}
                                    className="bg-green-600 hover:bg-green-700 text-white"
                                >
                                    {processingId === action.id ? <Activity className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                                    Approve Action
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
