"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { ShieldCheck, Activity, RefreshCw, BrainCircuit, AlertTriangle, RotateCcw, History } from "lucide-react"
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

interface SupervisorEvent {
    id: string
    event_type: string
    target_agent: string | null
    trigger_reason: string | null
    action_taken: string | null
    outcome: string | null
    is_automated: boolean
    timestamp: string
}

export default function SupervisorDashboard() {
    const [agents, setAgents] = useState<AgentStatus[]>([])
    const [lessons, setLessons] = useState<LearnedLesson[]>([])
    const [events, setEvents] = useState<SupervisorEvent[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [restarting, setRestarting] = useState<string | null>(null)

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

    const fetchData = async () => {
        try {
            setLoading(true)
            const [agentsRes, lessonsRes, eventsRes] = await Promise.all([
                fetch(`${baseUrl}/supervisor/status`),
                fetch(`${baseUrl}/supervisor/lessons`),
                fetch(`${baseUrl}/supervisor/events?limit=10`),
            ])

            if (!agentsRes.ok || !lessonsRes.ok) throw new Error("Failed to fetch supervisor data")

            const agentsData = await agentsRes.json()
            const lessonsData = await lessonsRes.json()
            setAgents(agentsData)
            setLessons(lessonsData)
            if (eventsRes.ok) {
                const eventsData = await eventsRes.json()
                setEvents(eventsData)
            } else {
                setEvents([])
            }
            setError(null)
        } catch (err) {
            setError("Unable to connect to Supervisor Agent. Is the backend running?")
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleRestart = async (agentName: string) => {
        setRestarting(agentName)
        try {
            const res = await fetch(`${baseUrl}/supervisor/restart/${encodeURIComponent(agentName)}`, { method: "POST" })
            if (res.ok) await fetchData()
        } finally {
            setRestarting(null)
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

    const formatEventTime = (ts: string) => {
        if (!ts) return ""
        try {
            const d = new Date(ts)
            return d.toLocaleString()
        } catch {
            return ts
        }
    }

    return (
        <div className="p-6 space-y-6 animate-in fade-in duration-500">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-mono font-bold tracking-tight text-foreground flex items-center gap-3">
                        <ShieldCheck className="h-8 w-8 text-scout-primary" />
                        Supervisor Agent
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Self-healing architecture monitor & adaptive learning engine
                    </p>
                </div>
                <Button variant="outline" className="border-scout-border" onClick={fetchData} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                    Refresh
                </Button>
            </div>

            {error && (
                <Alert variant="destructive" className="bg-scout-danger/10 border-scout-danger/30">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Connection Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {/* Agent Health Grid */}
            <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <Activity className="h-5 w-5 text-scout-success" />
                Agent Operations
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
                {agents.map((agent) => (
                    <Card key={agent.agent_name} className="bg-scout-panel border-scout-border overflow-hidden relative">
                        <div className={`absolute top-0 left-0 w-1 h-full ${agent.status === "healthy" ? "bg-scout-success" : agent.status === "failed" ? "bg-scout-danger" : "bg-scout-warning"}`} />
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-lg font-medium text-foreground">{agent.agent_name}</CardTitle>
                                <Badge variant="outline" className={getStatusColor(agent.status)}>
                                    {agent.status.toUpperCase()}
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Success Rate</span>
                                    <span className={`font-mono ${agent.success_rate < 90 ? "text-scout-danger" : "text-scout-success"}`}>
                                        {agent.success_rate.toFixed(1)}%
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Executions</span>
                                    <span className="font-mono text-foreground">{agent.total_executions}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Failures</span>
                                    <span className={`font-mono ${agent.consecutive_failures > 0 ? "text-scout-danger" : "text-muted-foreground"}`}>
                                        {agent.consecutive_failures}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Restarts</span>
                                    <span className="font-mono text-foreground">{agent.restart_count}</span>
                                </div>
                                {agent.last_error && (
                                    <div className="mt-2 text-xs text-scout-danger bg-scout-danger/10 p-2 rounded border border-scout-border">
                                        {agent.last_error}
                                    </div>
                                )}
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="w-full mt-2 border-scout-border text-scout-primary hover:bg-scout-primary/10"
                                    onClick={() => handleRestart(agent.agent_name)}
                                    disabled={restarting === agent.agent_name}
                                >
                                    <RotateCcw className={`h-3 w-3 mr-1 ${restarting === agent.agent_name ? "animate-spin" : ""}`} />
                                    {restarting === agent.agent_name ? "Restarting…" : "Restart"}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                ))}
                {agents.length === 0 && !loading && !error && (
                    <div className="col-span-full text-center py-12 text-muted-foreground border border-dashed border-scout-border rounded-lg bg-scout-panel/50">
                        No agents registered yet. Agents will appear here once they start executing.
                    </div>
                )}
            </div>

            {/* Son Olaylar */}
            <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <History className="h-5 w-5 text-scout-accent" />
                Son Olaylar
            </h2>
            <Card className="bg-scout-panel border-scout-border">
                <CardContent className="pt-4">
                    {events.length === 0 ? (
                        <p className="text-sm text-muted-foreground py-4">Henüz olay yok.</p>
                    ) : (
                        <ul className="space-y-2">
                            {events.map((ev) => (
                                <li key={ev.id} className="flex flex-wrap items-start gap-2 text-sm border-b border-scout-border pb-2 last:border-0">
                                    <Badge variant="outline" className="text-xs border-scout-border">
                                        {ev.event_type}
                                    </Badge>
                                    {ev.target_agent && <span className="text-foreground font-mono">{ev.target_agent}</span>}
                                    <span className="text-muted-foreground">{formatEventTime(ev.timestamp)}</span>
                                    {ev.trigger_reason && (
                                        <span className="w-full text-muted-foreground truncate" title={ev.trigger_reason}>
                                            {ev.trigger_reason}
                                        </span>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </CardContent>
            </Card>

            {/* Learning Engine Insights */}
            <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <BrainCircuit className="h-5 w-5 text-scout-accent" />
                Learned Lessons (Feedback Loop)
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {lessons.map((lesson) => (
                    <Card key={lesson.id} className="bg-scout-panel border-scout-border">
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between mb-2">
                                <Badge variant="secondary" className="bg-scout-accent/10 text-scout-accent border-scout-accent/20">
                                    {lesson.category.toUpperCase()}
                                </Badge>
                                <Badge className={getSeverityColor(lesson.severity)}>
                                    {lesson.severity.toUpperCase()}
                                </Badge>
                            </div>
                            <CardTitle className="text-base font-medium leading-tight text-foreground">
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
                                    <p className="text-sm text-foreground/90">{lesson.root_cause}</p>
                                </div>
                                <div>
                                    <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-1">Prevention Strategy</h4>
                                    <p className="text-sm text-scout-success/90 italic">&quot;{lesson.prevention_strategy}&quot;</p>
                                </div>
                                <div className="flex items-center justify-between pt-2 border-t border-scout-border">
                                    <span className="text-xs text-muted-foreground">Effectiveness</span>
                                    <span className="text-xs font-mono text-scout-accent">
                                        {lesson.effectiveness_rate.toFixed(0)}% ({lesson.occurrence_count} occurrences)
                                    </span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
                {lessons.length === 0 && !loading && !error && (
                    <div className="col-span-full text-center py-12 text-muted-foreground border border-dashed border-scout-border rounded-lg bg-scout-panel/50">
                        No lessons learned yet. The Learning Engine is active and waiting for anomalies.
                    </div>
                )}
            </div>
        </div>
    )
}
