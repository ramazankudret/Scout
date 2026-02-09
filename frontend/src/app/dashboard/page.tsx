"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, Eye, Target, Zap, Loader2 } from "lucide-react"
import dynamic from "next/dynamic"
import { useQuery } from "@tanstack/react-query"
import {
    threatsApi,
    assetsApi,
    incidentsApi,
    approvalsApi,
    supervisorApi,
} from "@/lib/api/client"
import PipelineViz from "@/components/dashboard/PipelineViz"
import Link from "next/link"

const VectorSpace = dynamic(
    () => import("@/components/dashboard/VectorSpace").then((m) => m.default),
    {
        ssr: false,
        loading: () => (
            <div className="w-full h-full flex items-center justify-center">
                <div className="text-scout-neon animate-pulse">Loading 3D Space...</div>
            </div>
        ),
    }
)

function useDashboardData() {
    const threatStats = useQuery({
        queryKey: ["threats", "stats"],
        queryFn: () => threatsApi.getStatsSummary(),
    })
    const assets = useQuery({
        queryKey: ["assets", "list"],
        queryFn: () => assetsApi.list({ limit: 1000 }),
    })
    const incidentStats = useQuery({
        queryKey: ["incidents", "stats"],
        queryFn: () => incidentsApi.getStats(),
    })
    const approvalStats = useQuery({
        queryKey: ["approvals", "stats"],
        queryFn: () => approvalsApi.getStats(),
    })
    const supervisorSummary = useQuery({
        queryKey: ["supervisor", "summary"],
        queryFn: () => supervisorApi.getSummary(),
    })
    const recentIncidents = useQuery({
        queryKey: ["incidents", "recent"],
        queryFn: () => incidentsApi.getRecent(24, 10),
    })
    return {
        threatStats,
        assets,
        incidentStats,
        approvalStats,
        supervisorSummary,
        recentIncidents,
    }
}

function KpiCard({
    title,
    value,
    subtitle,
    icon: Icon,
    borderClass,
    isLoading,
}: {
    title: string
    value: string | number
    subtitle: string
    icon: React.ElementType
    borderClass: string
    isLoading?: boolean
}) {
    return (
        <Card className={borderClass}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
                <Icon className="h-4 w-4 opacity-80" />
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                    <div className="text-2xl font-bold text-white">{value}</div>
                )}
                <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
            </CardContent>
        </Card>
    )
}

export default function DashboardPage() {
    const {
        threatStats,
        assets,
        incidentStats,
        approvalStats,
        supervisorSummary,
        recentIncidents,
    } = useDashboardData()

    const threatData = threatStats.data
    const assetTotal = assets.data?.total ?? 0
    const openIncidents = incidentStats.data?.by_status?.["open"] ?? incidentStats.data?.by_status?.["Open"] ?? 0
    const pendingApprovals = approvalStats.data?.pending ?? 0
    const healthyAgents = supervisorSummary.data?.healthy ?? 0
    const totalAgents = supervisorSummary.data?.total_agents ?? 0
    const systemStatus =
        totalAgents === 0
            ? "N/A"
            : healthyAgents === totalAgents
              ? "OPTIMAL"
              : (supervisorSummary.data?.failed ?? 0) > 0
                ? "DEGRADED"
                : "OPERATIONAL"

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Command Center</h1>
                    <p className="text-muted-foreground">
                        System Status: <span className="text-scout-neon">{systemStatus}</span>
                    </p>
                </div>
                <PipelineViz />
            </div>

            <div className="grid gap-4 md:grid-cols-4">
                <KpiCard
                    title="Active Threats"
                    value={threatData?.active_count ?? threatData?.critical_count ?? 0}
                    subtitle={
                        threatData
                            ? `${threatData.total} total • ${threatData.critical_count} critical`
                            : "Loading..."
                    }
                    icon={Shield}
                    borderClass="border-scout-neon/20"
                    isLoading={threatStats.isLoading}
                />
                <KpiCard
                    title="Monitored Assets"
                    value={assetTotal}
                    subtitle={assets.data ? "From asset registry" : "Loading..."}
                    icon={Eye}
                    borderClass="border-purple-500/20"
                    isLoading={assets.isLoading}
                />
                <KpiCard
                    title="Pending Approvals"
                    value={pendingApprovals}
                    subtitle={approvalStats.data ? `${approvalStats.data.total} total actions` : "Loading..."}
                    icon={Target}
                    borderClass="border-blue-500/20"
                    isLoading={approvalStats.isLoading}
                />
                <KpiCard
                    title="Open Incidents"
                    value={openIncidents}
                    subtitle={
                        incidentStats.data
                            ? `${incidentStats.data.total} total • by severity`
                            : "Loading..."
                    }
                    icon={Zap}
                    borderClass="border-red-500/20"
                    isLoading={incidentStats.isLoading}
                />
            </div>

            <div className="grid gap-4 md:grid-cols-7 h-[600px]">
                <Card className="col-span-5 relative overflow-hidden flex items-center justify-center border-white/10 bg-black/60 h-full">
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-scout-neon/5 via-black/0 to-black/0 pointer-events-none" />
                    <div className="w-full h-full">
                        <VectorSpace />
                    </div>
                </Card>
                <Card className="col-span-2">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Recent Activity</CardTitle>
                        <Link
                            href="/dashboard/incidents"
                            className="text-xs text-scout-neon hover:underline"
                        >
                            View all
                        </Link>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {recentIncidents.isLoading && (
                                <div className="flex items-center justify-center py-8">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            )}
                            {!recentIncidents.isLoading &&
                                (recentIncidents.data?.length ? (
                                    recentIncidents.data.map((inc) => (
                                        <Link
                                            key={inc.id}
                                            href={`/dashboard/incidents?id=${inc.id}`}
                                            className="flex items-center gap-4 text-sm p-2 rounded hover:bg-white/5 transition-colors cursor-pointer group block"
                                        >
                                            <div
                                                className={`w-2 h-2 rounded-full flex-shrink-0 ${
                                                    inc.severity === "critical"
                                                        ? "bg-red-500"
                                                        : inc.severity === "high"
                                                          ? "bg-orange-500"
                                                          : "bg-scout-neon"
                                                }`}
                                            />
                                            <div className="min-w-0">
                                                <p className="text-white group-hover:text-scout-neon transition-colors truncate">
                                                    {inc.title}
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {inc.detected_at
                                                        ? new Date(inc.detected_at).toLocaleString()
                                                        : "—"}
                                                </p>
                                            </div>
                                        </Link>
                                    ))
                                ) : (
                                    <p className="text-sm text-muted-foreground">No recent incidents.</p>
                                ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
