"use client"

import { useQuery } from "@tanstack/react-query"
import { supervisorApi } from "@/lib/api/client"
import { Cpu, Crosshair, Ghost, Shield } from "lucide-react"

const NODES = [
    { id: "orchestrator", label: "Orchestrator", icon: Cpu, x: 50, y: 20 },
    { id: "hunter", label: "Hunter", icon: Crosshair, x: 20, y: 55 },
    { id: "stealth", label: "Stealth", icon: Ghost, x: 50, y: 55 },
    { id: "defense", label: "Defense", icon: Shield, x: 80, y: 55 },
] as const

const EDGES: { from: string; to: string }[] = [
    { from: "orchestrator", to: "hunter" },
    { from: "orchestrator", to: "stealth" },
    { from: "orchestrator", to: "defense" },
    { from: "hunter", to: "orchestrator" },
    { from: "stealth", to: "orchestrator" },
    { from: "defense", to: "orchestrator" },
]

function getStatusColor(status: string) {
    switch (status?.toLowerCase()) {
        case "healthy":
            return "text-green-400 border-green-500/50 bg-green-500/10"
        case "degraded":
        case "recovering":
            return "text-amber-400 border-amber-500/50 bg-amber-500/10"
        case "failed":
        case "stopped":
            return "text-red-400 border-red-500/50 bg-red-500/10"
        default:
            return "text-muted-foreground border-white/20 bg-white/5"
    }
}

export default function PipelineViz() {
    const { data: statuses } = useQuery({
        queryKey: ["supervisor", "status"],
        queryFn: () => supervisorApi.getStatus(),
    })

    const statusMap = (statuses ?? []).reduce(
        (acc, s) => {
            acc[s.agent_name.toLowerCase()] = s.status
            return acc
        },
        {} as Record<string, string>
    )

    return (
        <div className="w-full rounded-lg border border-white/10 bg-black/40 p-4">
            <h3 className="text-sm font-semibold text-white mb-3">Pipeline</h3>
            <div className="relative h-[140px]">
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 80" preserveAspectRatio="xMidYMid meet">
                    {EDGES.map(({ from: fromId, to: toId }, i) => {
                        const from = NODES.find((n) => n.id === fromId)!
                        const to = NODES.find((n) => n.id === toId)!
                        const midY = (from.y + to.y) / 2
                        const path =
                            from.y < to.y
                                ? `M ${from.x} ${from.y} C ${from.x} ${midY}, ${to.x} ${midY}, ${to.x} ${to.y}`
                                : `M ${from.x} ${from.y} L ${from.x} ${midY} L ${to.x} ${midY} L ${to.x} ${to.y}`
                        return (
                            <path
                                key={i}
                                d={path}
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="0.5"
                                className="text-scout-neon/30"
                            />
                        )
                    })}
                </svg>
                {NODES.map((node) => {
                    const Icon = node.icon
                    const status = statusMap[node.id] ?? "unknown"
                    const statusClass = getStatusColor(status)
                    return (
                        <div
                            key={node.id}
                            className="absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-0.5"
                            style={{ left: `${node.x}%`, top: `${node.y}%` }}
                        >
                            <div
                                className={`flex items-center justify-center w-9 h-9 rounded-full border ${statusClass}`}
                                title={`${node.label}: ${status}`}
                            >
                                <Icon className="w-4 h-4" />
                            </div>
                            <span className="text-[10px] text-muted-foreground font-mono">{node.label}</span>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
