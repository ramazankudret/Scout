"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useQuery } from "@tanstack/react-query"
import { analyticsApi, type LlmUsageBucket } from "@/lib/api/client"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    LineChart,
    Line,
} from "recharts"
import { Loader2, Shield, Server, AlertTriangle, Bot, Zap } from "lucide-react"

const CHART_COLORS = ["#00ffc8", "#58a6ff", "#d29922", "#f85149", "#bc13fe", "#39d353"]

export default function ChartsPage() {
    const overview = useQuery({
        queryKey: ["analytics", "overview"],
        queryFn: () => analyticsApi.getOverview(),
    })
    const bySeverity = useQuery({
        queryKey: ["analytics", "incidents-by-severity"],
        queryFn: () => analyticsApi.getIncidentsBySeverity(),
    })
    const byTime = useQuery({
        queryKey: ["analytics", "incidents-by-time"],
        queryFn: () => analyticsApi.getIncidentsByTime("day"),
    })
    const agentsActivity = useQuery({
        queryKey: ["analytics", "agents-activity"],
        queryFn: () => analyticsApi.getAgentsActivity(),
    })
    const llmUsage = useQuery({
        queryKey: ["analytics", "llm-usage"],
        queryFn: () => analyticsApi.getLlmUsage(),
    })

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-mono font-bold text-foreground tracking-tight">Grafikler</h1>
                <p className="text-muted-foreground text-sm mt-1">Veritabanı verileriyle özet ve grafikler</p>
            </div>

            {/* KPI cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {overview.isLoading ? (
                    <div className="col-span-full flex justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin text-scout-primary" />
                    </div>
                ) : overview.data ? (
                    <>
                        <KpiCard
                            title="Toplam Incident"
                            value={overview.data.incidents_total}
                            icon={AlertTriangle}
                            color="text-scout-warning"
                        />
                        <KpiCard
                            title="Açık Incident"
                            value={overview.data.incidents_open}
                            icon={Shield}
                            color="text-scout-danger"
                        />
                        <KpiCard
                            title="Asset"
                            value={overview.data.assets_total}
                            icon={Server}
                            color="text-scout-accent"
                        />
                        <KpiCard
                            title="Açık Zafiyet"
                            value={overview.data.vulnerabilities_open}
                            icon={AlertTriangle}
                            color="text-scout-warning"
                        />
                        <KpiCard
                            title="Agent Run"
                            value={overview.data.agent_runs_total}
                            icon={Bot}
                            color="text-scout-primary"
                        />
                        <KpiCard
                            title="Başarılı Run"
                            value={overview.data.agent_runs_success}
                            icon={Zap}
                            color="text-scout-success"
                        />
                    </>
                ) : null}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Incidents by severity */}
                <Card className="bg-card border-scout-border">
                    <CardHeader>
                        <CardTitle className="text-base font-mono text-foreground">Incident / Severity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {bySeverity.isLoading ? (
                            <div className="h-64 flex items-center justify-center">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : bySeverity.data?.length ? (
                            <ResponsiveContainer width="100%" height={260}>
                                <BarChart data={bySeverity.data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                                    <XAxis dataKey="severity" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                                        labelStyle={{ color: "hsl(var(--foreground))" }}
                                    />
                                    <Bar dataKey="count" fill="#00ffc8" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">Veri yok</div>
                        )}
                    </CardContent>
                </Card>

                {/* Incidents over time */}
                <Card className="bg-card border-scout-border">
                    <CardHeader>
                        <CardTitle className="text-base font-mono text-foreground">Incident / Zaman</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {byTime.isLoading ? (
                            <div className="h-64 flex items-center justify-center">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : byTime.data?.length ? (
                            <ResponsiveContainer width="100%" height={260}>
                                <LineChart data={byTime.data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                                    <XAxis
                                        dataKey="bucket"
                                        stroke="hsl(var(--muted-foreground))"
                                        fontSize={10}
                                        tickFormatter={(v) => (v && v.slice(0, 10)) || ""}
                                    />
                                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                                    />
                                    <Line type="monotone" dataKey="count" stroke="#00ffc8" strokeWidth={2} dot={{ fill: "#00ffc8" }} />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">Veri yok</div>
                        )}
                    </CardContent>
                </Card>

                {/* Agents activity */}
                <Card className="bg-card border-scout-border">
                    <CardHeader>
                        <CardTitle className="text-base font-mono text-foreground">Agent Aktivitesi</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {agentsActivity.isLoading ? (
                            <div className="h-64 flex items-center justify-center">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : agentsActivity.data?.length ? (
                            <ResponsiveContainer width="100%" height={260}>
                                <BarChart
                                    data={agentsActivity.data}
                                    layout="vertical"
                                    margin={{ top: 8, right: 8, left: 80, bottom: 0 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                                    <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                                    <YAxis type="category" dataKey="agent_name" stroke="hsl(var(--muted-foreground))" fontSize={11} width={70} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                                    />
                                    <Bar dataKey="total_executions" name="Çalıştırma" fill="#58a6ff" radius={[0, 4, 4, 0]} />
                                    <Bar dataKey="success_rate" name="Başarı %" fill="#39d353" radius={[0, 4, 4, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">Veri yok</div>
                        )}
                    </CardContent>
                </Card>

                {/* LLM usage */}
                <Card className="bg-card border-scout-border">
                    <CardHeader>
                        <CardTitle className="text-base font-mono text-foreground">LLM Kullanımı</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {llmUsage.isLoading ? (
                            <div className="h-64 flex items-center justify-center">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : llmUsage.data?.length ? (
                            <ResponsiveContainer width="100%" height={260}>
                                <PieChart>
                                    <Pie
                                        data={llmUsage.data}
                                        dataKey="request_count"
                                        nameKey="model"
                                        cx="50%"
                                        cy="50%"
                                        outerRadius={80}
                                        label={({ model, request_count }) => `${model}: ${request_count}`}
                                    >
                                        {llmUsage.data.map((_, i) => (
                                            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                                        formatter={(value: number, _name: string, props: { payload: LlmUsageBucket }) =>
                                            `${value} istek · ${props.payload.total_tokens} token · $${(props.payload.total_cost_usd ?? 0).toFixed(4)}`
                                        }
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">Veri yok</div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

function KpiCard({
    title,
    value,
    icon: Icon,
    color,
}: {
    title: string
    value: number
    icon: React.ElementType
    color: string
}) {
    return (
        <Card className="bg-card border-scout-border">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground">{title}</CardTitle>
                <Icon className={`h-4 w-4 ${color}`} />
            </CardHeader>
            <CardContent>
                <div className="text-xl font-bold text-foreground">{value}</div>
            </CardContent>
        </Card>
    )
}
