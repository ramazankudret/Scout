"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Bot, Activity, Clock, CheckCircle, AlertCircle, Loader2, Pause } from "lucide-react"

// Agent status types
type AgentStatus = "active" | "idle" | "busy" | "error" | "paused"

interface Agent {
    id: string
    name: string
    status: AgentStatus
    currentTask: string | null
    lastAction: string
    tasksCompleted: number
    uptime: string
}

const statusConfig = {
    active: { icon: CheckCircle, color: "text-green-500", bg: "bg-green-500", label: "Active", animate: false },
    idle: { icon: Clock, color: "text-slate-400", bg: "bg-slate-400", label: "Idle", animate: false },
    busy: { icon: Loader2, color: "text-yellow-500", bg: "bg-yellow-500", label: "Busy", animate: true },
    error: { icon: AlertCircle, color: "text-red-500", bg: "bg-red-500", label: "Error", animate: false },
    paused: { icon: Pause, color: "text-blue-500", bg: "bg-blue-500", label: "Paused", animate: false },
    // Handle 'starting' state map to busy
    starting: { icon: Loader2, color: "text-purple-500", bg: "bg-purple-500", label: "Starting", animate: true },
    stopping: { icon: Pause, color: "text-orange-500", bg: "bg-orange-500", label: "Stopping", animate: false },
    stopped: { icon: Pause, color: "text-gray-500", bg: "bg-gray-500", label: "Stopped", animate: false },
} as const

export default function AgentsPage() {
    const [agents, setAgents] = useState<Agent[]>([])
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        const fetchAgents = async () => {
            const token = localStorage.getItem("token")
            if (!token) return

            try {
                const res = await fetch("http://localhost:8000/api/v1/modules", {
                    headers: {
                        "Authorization": `Bearer ${token}`
                    }
                })
                const data = await res.json()
                if (data.modules) {
                    setAgents(data.modules)
                }
            } catch (error) {
                console.error("Failed to fetch agents", error)
            } finally {
                setIsLoading(false)
            }
        }

        fetchAgents()
        // Poll every 2 seconds for real-time feel
        const interval = setInterval(fetchAgents, 2000)
        return () => clearInterval(interval)
    }, [])

    const activeCount = agents.filter(a => a.status === "active" || a.status === "busy" || a.status === "running").length
    const totalTasks = agents.reduce((sum, a) => sum + (a.tasksCompleted || 0), 0)

    if (isLoading && agents.length === 0) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-scout-neon" />
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-white">Agent Monitor</h1>
                <p className="text-slate-400 text-sm">Real-time multi-agent system status</p>
            </div>

            {/* Overview Stats */}
            <div className="grid grid-cols-4 gap-4">
                <Card className="bg-scout-neon/10 border-scout-neon/30">
                    <CardContent className="p-4 text-center">
                        <p className="text-3xl font-bold text-scout-neon">{agents.length}</p>
                        <p className="text-xs text-scout-neon/70">Total Agents</p>
                    </CardContent>
                </Card>
                <Card className="bg-green-500/10 border-green-500/30">
                    <CardContent className="p-4 text-center">
                        <p className="text-3xl font-bold text-green-500">{activeCount}</p>
                        <p className="text-xs text-green-400">Active / Running</p>
                    </CardContent>
                </Card>
                <Card className="bg-purple-500/10 border-purple-500/30">
                    <CardContent className="p-4 text-center">
                        <p className="text-3xl font-bold text-purple-500">{totalTasks}</p>
                        <p className="text-xs text-purple-400">Total Actions</p>
                    </CardContent>
                </Card>
                <Card className="bg-blue-500/10 border-blue-500/30">
                    <CardContent className="p-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                            </span>
                        </div>
                        <p className="text-xs text-blue-400 mt-2">System Online</p>
                    </CardContent>
                </Card>
            </div>

            {/* Agent Cards */}
            <div className="grid grid-cols-2 gap-4">
                {agents.map((agent) => {
                    // Fallback to idle config if status not found
                    // @ts-ignore
                    const config = statusConfig[agent.status] || statusConfig.idle
                    const Icon = config.icon

                    return (
                        <Card key={agent.id} className="bg-slate-900/50 border-white/5 hover:border-scout-neon/30 transition-colors">
                            <CardHeader className="pb-2">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-white flex items-center gap-2">
                                        <Bot className="w-5 h-5 text-scout-neon" />
                                        {agent.name}
                                    </CardTitle>
                                    <div className="flex items-center gap-2">
                                        <span className={`w-2 h-2 rounded-full ${config.bg} ${config.animate ? "animate-pulse" : ""}`} />
                                        <span className={`text-xs ${config.color}`}>{config.label}</span>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {/* Current Task */}
                                <div className="bg-black/30 rounded-lg p-3">
                                    <p className="text-xs text-slate-500 mb-1">Current Task</p>
                                    <p className="text-sm text-white font-mono truncate">
                                        {agent.currentTask || "— Awaiting instructions —"}
                                    </p>
                                </div>

                                {/* Stats */}
                                <div className="grid grid-cols-3 gap-2 text-center">
                                    <div>
                                        <p className="text-lg font-bold text-scout-neon">{agent.tasksCompleted}</p>
                                        <p className="text-[10px] text-slate-500">Tasks</p>
                                    </div>
                                    <div>
                                        <p className="text-lg font-bold text-white">{agent.uptime}</p>
                                        <p className="text-[10px] text-slate-500">Uptime</p>
                                    </div>
                                    <div>
                                        <p className="text-lg font-bold text-slate-400">{agent.lastAction}</p>
                                        <p className="text-[10px] text-slate-500">Last Action</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )
                })}
            </div>

            {/* Activity Timeline (Placeholder until we have real event logs API for agent activities) */}
            <Card className="bg-slate-900/50 border-white/5 opacity-50">
                <CardHeader>
                    <CardTitle className="text-scout-neon flex items-center gap-2">
                        <Activity className="w-4 h-4" /> Live Activity Feed (Connecting...)
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-slate-500">Waiting for agent events stream...</p>
                </CardContent>
            </Card>
        </div>
    )
}
