"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { ShieldCheck, ShieldAlert, Activity, RefreshCw, BrainCircuit, AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"

interface AgentStatus {
    agent_name: string
    status: "healthy" | "degraded" | "failed" | "recovering" | "stopped"
    last_heartbeat: string | null
    last_error: string | null
    consecutive_failures: number
    total_executions: number
    success_rate: number
    restart_count: number
}

interface LearnedLesson {
    id: string
    agent_name: string
    action_type: string
    root_cause: string
    category: string
    severity: string
    prevention_strategy: string
    occurrence_count: number
    effectiveness_rate: number
}

export default function SupervisorDashboard() {
    const [agents, setAgents] = useState<AgentStatus[]>([])
    const [lessons, setLessons] = useState<LearnedLesson[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchData = async () => {
        try {
            setLoading(true)
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

            const agentsRes = await fetch(`${baseUrl}/supervisor/status`)
            const lessonsRes = await fetch(`${baseUrl}/supervisor/lessons`)

            if (!agentsRes.ok || !lessonsRes.ok) throw new Error("Failed to fetch supervisor data")

            const agentsData = await agentsRes.json()
            const lessonsData = await lessonsRes.json()

            setAgents(agentsData)
            setLessons(lessonsData)
            setError(null)
        } catch (err) {
            setError("Unable to connect to Supervisor Agent. Is the backend running?")
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
        // Auto-refresh every 5 seconds
        const interval = setInterval(fetchData, 5000)
        return () => clearInterval(interval)
    }, [])

    const getStatusColor = (status: string) => {
        switch (status) {
            case "healthy": return "bg-green-500/10 text-green-500 border-green-500/20"
            case "degraded": return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
            case "failed": return "bg-red-500/10 text-red-500 border-red-500/20"
            case "recovering": return "bg-blue-500/10 text-blue-500 border-blue-500/20"
            default: return "bg-gray-500/10 text-gray-500 border-gray-500/20"
        }
    }

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case "critical": return "bg-red-500 hover:bg-red-600"
            case "high": return "bg-orange-500 hover:bg-orange-600"
            case "medium": return "bg-yellow-500 hover:bg-yellow-600"
            case "low": return "bg-blue-500 hover:bg-blue-600"
            default: return "bg-gray-500 hover:bg-gray-600"
        }
    }

    return (
        <div className="p-6 space-y-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-3">
                        <ShieldCheck className="h-8 w-8 text-blue-500" />
                        Supervisor Agent
                    </h1>
                    <p className="text-muted-foreground">
                        Self-healing architecture monitor & adaptive learning engine
                    </p>
                </div>
                <Button variant="outline" onClick={fetchData} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                    Refresh
                </Button>
            </div>

            {error && (
                <Alert variant="destructive" className="mb-6 bg-red-900/20 border-red-900/50">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Connection Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {/* Agent Health Grid */}
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Activity className="h-5 w-5 text-green-400" />
                Agent Operations
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
                {agents.map((agent) => (
                    <Card key={agent.agent_name} className="bg-card border-white/5 overflow-hidden relative">
                        <div className={`absolute top-0 left-0 w-1 h-full ${agent.status === 'healthy' ? 'bg-green-500' :
                                agent.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                            }`} />
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-lg font-medium">{agent.agent_name}</CardTitle>
                                <Badge variant="outline" className={getStatusColor(agent.status)}>
                                    {agent.status.toUpperCase()}
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Success Rate</span>
                                    <span className={`font-mono ${agent.success_rate < 90 ? 'text-red-400' : 'text-green-400'}`}>
                                        {agent.success_rate.toFixed(1)}%
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Executions</span>
                                    <span className="font-mono text-white">{agent.total_executions}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Failures</span>
                                    <span className={`font-mono ${agent.consecutive_failures > 0 ? 'text-red-400' : 'text-muted-foreground'}`}>
                                        {agent.consecutive_failures}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Restarts</span>
                                    <span className="font-mono text-white">{agent.restart_count}</span>
                                </div>
                                {agent.last_error && (
                                    <div className="mt-2 text-xs text-red-300 bg-red-900/20 p-2 rounded">
                                        {agent.last_error}
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                ))}
                {agents.length === 0 && !loading && !error && (
                    <div className="col-span-full text-center py-12 text-muted-foreground border border-dashed border-white/10 rounded-lg">
                        No agents registered yet. Agents will appear here once they start executing.
                    </div>
                )}
            </div>

            {/* Learning Engine Insights */}
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <BrainCircuit className="h-5 w-5 text-purple-400" />
                Learned Lessons (Feedback Loop)
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {lessons.map((lesson) => (
                    <Card key={lesson.id} className="bg-card border-white/5">
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between mb-2">
                                <Badge variant="secondary" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                                    {lesson.category.toUpperCase()}
                                </Badge>
                                <Badge className={getSeverityColor(lesson.severity)}>
                                    {lesson.severity.toUpperCase()}
                                </Badge>
                            </div>
                            <CardTitle className="text-base font-medium leading-tight">
                                {lesson.action_type} Failure
                            </CardTitle>
                            <CardDescription className="text-xs">
                                Agent: {lesson.agent_name}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div>
                                    <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-1">Root Cause</h4>
                                    <p className="text-sm text-white/90">{lesson.root_cause}</p>
                                </div>
                                <div>
                                    <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-1">Prevention Strategy</h4>
                                    <p className="text-sm text-green-400/90 italic">"{lesson.prevention_strategy}"</p>
                                </div>
                                <div className="flex items-center justify-between pt-2 border-t border-white/5">
                                    <span className="text-xs text-muted-foreground">Effectiveness</span>
                                    <span className="text-xs font-mono text-blue-400">
                                        {lesson.effectiveness_rate.toFixed(0)}% ({lesson.occurrence_count} occurrences)
                                    </span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
                {lessons.length === 0 && !loading && !error && (
                    <div className="col-span-full text-center py-12 text-muted-foreground border border-dashed border-white/10 rounded-lg">
                        No lessons learned yet. The Learning Engine is active and waiting for anomalies.
                    </div>
                )}
            </div>
        </div>
    )
}
