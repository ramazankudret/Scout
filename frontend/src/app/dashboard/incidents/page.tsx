"use client"

import { useState, useEffect } from "react"
import { AlertCircle, Plus, Search, ShieldAlert, CheckCircle, Clock, Filter, RefreshCw, XCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { incidentsApi, Incident, CreateIncidentData, IncidentStats } from "@/lib/api/client"

export default function IncidentsPage() {
    const [incidents, setIncidents] = useState<Incident[]>([])
    const [stats, setStats] = useState<IncidentStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [refreshing, setRefreshing] = useState(false)

    // Create Modal state
    const [isCreateOpen, setIsCreateOpen] = useState(false)
    const [newIncident, setNewIncident] = useState<CreateIncidentData>({
        title: "",
        description: "",
        severity: "medium",
        threat_type: "other",
        source_ip: ""
    })

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        try {
            setLoading(true)
            const [incidentsRes, statsRes] = await Promise.all([
                incidentsApi.list({ limit: 50, status: 'new' }), // Load open incidents by default
                incidentsApi.getStats()
            ])
            setIncidents(incidentsRes.items)
            setStats(statsRes)
            setError(null)
        } catch (err) {
            console.error("Failed to load incidents:", err)
            setError("Failed to load incidents. Please check backend connection.")
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    const handleCreate = async () => {
        try {
            if (!newIncident.title) return

            await incidentsApi.create(newIncident)
            setIsCreateOpen(false)
            setNewIncident({
                title: "",
                description: "",
                severity: "medium",
                threat_type: "other",
                source_ip: ""
            })
            loadData()
        } catch (err) {
            console.error("Failed to create incident:", err)
            alert("Failed to create incident. Check console for details.")
        }
    }

    const handleClose = async (id: string) => {
        if (!confirm("Are you sure you want to close this incident?")) return
        try {
            await incidentsApi.close(id, "manual_closure")
            loadData()
        } catch (err) {
            console.error("Failed to close incident:", err)
        }
    }

    const getSeverityColor = (level: string) => {
        switch (level) {
            case 'critical': return 'text-red-500 border-red-500/50 bg-red-500/10';
            case 'high': return 'text-orange-500 border-orange-500/50 bg-orange-500/10';
            case 'medium': return 'text-yellow-500 border-yellow-500/50 bg-yellow-500/10';
            default: return 'text-blue-500 border-blue-500/50 bg-blue-500/10';
        }
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'new': return <ShieldAlert className="w-5 h-5 text-red-500" />;
            case 'investigating': return <Search className="w-5 h-5 text-yellow-500" />;
            case 'contained': return <CheckCircle className="w-5 h-5 text-orange-500" />;
            case 'closed': return <XCircle className="w-5 h-5 text-green-500" />;
            default: return <Clock className="w-5 h-5 text-gray-500" />;
        }
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row gap-4 md:items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-2">
                        <ShieldAlert className="w-8 h-8 text-red-500" />
                        Security Incidents
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Track and respond to security threats
                    </p>
                </div>

                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        className="border-white/10 hover:bg-white/5"
                        onClick={() => {
                            setRefreshing(true)
                            loadData()
                        }}
                        disabled={refreshing}
                    >
                        <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                    <Button
                        className="bg-red-600 text-white hover:bg-red-700"
                        onClick={() => setIsCreateOpen(!isCreateOpen)}
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Report Incident
                    </Button>
                </div>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card className="p-4 bg-white/5 border-white/10">
                        <div className="text-muted-foreground text-sm">Total Incidents</div>
                        <div className="text-2xl font-bold text-white mt-1">{stats.total}</div>
                    </Card>
                    <Card className="p-4 bg-white/5 border-white/10">
                        <div className="text-muted-foreground text-sm">Active Threats</div>
                        <div className="text-2xl font-bold text-red-500 mt-1">
                            {(stats.by_status['new'] || 0) + (stats.by_status['investigating'] || 0)}
                        </div>
                    </Card>
                    <Card className="p-4 bg-white/5 border-white/10">
                        <div className="text-muted-foreground text-sm">Critical Severity</div>
                        <div className="text-2xl font-bold text-orange-500 mt-1">
                            {stats.by_severity['critical'] || 0}
                        </div>
                    </Card>
                    <Card className="p-4 bg-white/5 border-white/10">
                        <div className="text-muted-foreground text-sm">Resolved</div>
                        <div className="text-2xl font-bold text-green-500 mt-1">
                            {stats.by_status['closed'] || 0}
                        </div>
                    </Card>
                </div>
            )}

            {/* Create Form */}
            {isCreateOpen && (
                <Card className="p-6 bg-white/5 border-white/10 animate-in fade-in slide-in-from-top-4">
                    <h3 className="text-lg font-semibold text-white mb-4">Report New Incident</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="col-span-2 space-y-2">
                            <label className="text-sm text-muted-foreground">Title</label>
                            <Input
                                value={newIncident.title}
                                onChange={e => setNewIncident({ ...newIncident, title: e.target.value })}
                                placeholder="e.g. Suspicious SSH Activity"
                                className="bg-black/50 border-white/10"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Description</label>
                            <Input
                                value={newIncident.description || ''}
                                onChange={e => setNewIncident({ ...newIncident, description: e.target.value })}
                                placeholder="Details about the incident"
                                className="bg-black/50 border-white/10"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Severity</label>
                            <select
                                className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-white"
                                value={newIncident.severity}
                                onChange={e => setNewIncident({ ...newIncident, severity: e.target.value })}
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Threat Type</label>
                            <Input
                                value={newIncident.threat_type || ''}
                                onChange={e => setNewIncident({ ...newIncident, threat_type: e.target.value })}
                                placeholder="e.g. brute_force"
                                className="bg-black/50 border-white/10"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Source IP</label>
                            <Input
                                value={newIncident.source_ip || ''}
                                onChange={e => setNewIncident({ ...newIncident, source_ip: e.target.value })}
                                placeholder="e.g. 1.2.3.4"
                                className="bg-black/50 border-white/10"
                            />
                        </div>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button variant="ghost" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                        <Button className="bg-red-600 text-white hover:bg-red-700" onClick={handleCreate}>Create Incident</Button>
                    </div>
                </Card>
            )}

            {/* List */}
            <div className="grid grid-cols-1 gap-4">
                {loading ? (
                    <div className="text-center py-20 text-muted-foreground">Loading incidents...</div>
                ) : error ? (
                    <div className="text-center py-10 text-red-400">{error}</div>
                ) : incidents.length === 0 ? (
                    <div className="text-center py-20 border border-dashed border-white/10 rounded-lg">
                        <ShieldAlert className="w-12 h-12 text-white/20 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-white">No active incidents</h3>
                        <p className="text-muted-foreground mt-1">System is secure. No threats detected.</p>
                    </div>
                ) : (
                    incidents.map((incident) => (
                        <Card key={incident.id} className="p-4 bg-white/5 border-white/10 hover:bg-white/[0.07] transition-colors">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-white/5`}>
                                        {getStatusIcon(incident.status)}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-medium text-white">{incident.title}</h3>
                                            <Badge variant="outline" className={getSeverityColor(incident.severity)}>
                                                {incident.severity}
                                            </Badge>
                                            <span className="text-xs text-muted-foreground bg-white/5 px-2 py-0.5 rounded">
                                                {incident.incident_number}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                                            <span>
                                                Detected: {new Date(incident.detected_at).toLocaleString()}
                                            </span>
                                            {incident.source_ip && (
                                                <span className="text-red-400">
                                                    Source: {incident.source_ip}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4">
                                    <div className="text-right hidden md:block">
                                        <div className="text-sm text-muted-foreground">Status</div>
                                        <div className="font-medium text-white capitalize">{incident.status}</div>
                                    </div>
                                    {incident.status !== 'closed' && (
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            className="border-green-500/20 text-green-400 hover:bg-green-500/10 hover:text-green-300"
                                            onClick={() => handleClose(incident.id)}
                                        >
                                            <CheckCircle className="w-4 h-4 mr-1" />
                                            Close
                                        </Button>
                                    )}
                                    <Button variant="ghost" size="sm" className="hover:bg-white/10">
                                        Details
                                    </Button>
                                </div>
                            </div>
                        </Card>
                    ))
                )}
            </div>
        </div>
    )
}
