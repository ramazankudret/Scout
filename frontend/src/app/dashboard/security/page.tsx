"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Shield, Lock, Key, Activity, AlertTriangle, CheckCircle, RefreshCw, Server } from "lucide-react"

// Mock endpoint security data
const mockChecks = [
    { id: "file_integrity", name: "File Integrity", status: "ok", message: "All critical files intact", details: "42 files checked" },
    { id: "open_ports", name: "Open Ports", status: "ok", message: "No unexpected open ports", details: "Ports: 22, 80, 443" },
    { id: "processes", name: "Running Processes", status: "ok", message: "No suspicious processes", details: "156 processes" },
    { id: "login_attempts", name: "Login Attempts", status: "warning", message: "3 failed login attempts", details: "From: 192.168.1.105" },
    { id: "updates", name: "System Updates", status: "warning", message: "5 security updates pending", details: "1 critical update" },
    { id: "resources", name: "Resource Usage", status: "ok", message: "Normal usage", details: "CPU: 23%, RAM: 45%" },
]

const statusConfig = {
    ok: { icon: CheckCircle, color: "text-green-500", bg: "bg-green-500/10", border: "border-green-500/30" },
    warning: { icon: AlertTriangle, color: "text-yellow-500", bg: "bg-yellow-500/10", border: "border-yellow-500/30" },
    critical: { icon: AlertTriangle, color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/30" },
}

export default function SecurityPage() {
    const [checks] = useState(mockChecks)
    const [lastScan] = useState("2 minutes ago")

    const okCount = checks.filter(c => c.status === "ok").length
    const warningCount = checks.filter(c => c.status === "warning").length

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Endpoint Security</h1>
                    <p className="text-slate-400 text-sm">Host protection and system health monitoring</p>
                </div>
                <Button variant="outline" size="sm" className="border-scout-neon/30 text-scout-neon">
                    <RefreshCw className="w-4 h-4 mr-2" /> Run Scan
                </Button>
            </div>

            {/* System Info */}
            <Card className="bg-gradient-to-r from-scout-neon/10 to-purple-500/10 border-scout-neon/30">
                <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Server className="w-10 h-10 text-scout-neon" />
                        <div>
                            <p className="text-lg font-bold text-white">DESKTOP-SCOUT</p>
                            <p className="text-sm text-slate-400">Windows 11 Pro • Last scan: {lastScan}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="text-center">
                            <p className="text-2xl font-bold text-green-500">{okCount}</p>
                            <p className="text-xs text-green-400">Passed</p>
                        </div>
                        <div className="text-center">
                            <p className="text-2xl font-bold text-yellow-500">{warningCount}</p>
                            <p className="text-xs text-yellow-400">Warnings</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Security Checks */}
            <div className="grid grid-cols-2 gap-4">
                {checks.map((check) => {
                    const config = statusConfig[check.status as keyof typeof statusConfig]
                    const Icon = config.icon

                    return (
                        <Card key={check.id} className={`${config.bg} ${config.border}`}>
                            <CardContent className="p-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-3">
                                        <Icon className={`w-6 h-6 ${config.color}`} />
                                        <div>
                                            <p className="font-medium text-white">{check.name}</p>
                                            <p className="text-sm text-slate-400">{check.message}</p>
                                            <p className="text-xs text-slate-500 mt-1">{check.details}</p>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )
                })}
            </div>

            {/* Quick Actions */}
            <Card className="bg-slate-900/50 border-white/5">
                <CardHeader>
                    <CardTitle className="text-scout-neon flex items-center gap-2">
                        <Shield className="w-4 h-4" /> Quick Actions
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex gap-3">
                    <Button variant="outline" size="sm" className="border-scout-neon/30 text-scout-neon">
                        <Lock className="w-4 h-4 mr-2" /> Lock System
                    </Button>
                    <Button variant="outline" size="sm" className="border-yellow-500/30 text-yellow-400">
                        <Activity className="w-4 h-4 mr-2" /> View Processes
                    </Button>
                    <Button variant="outline" size="sm" className="border-purple-500/30 text-purple-400">
                        <Key className="w-4 h-4 mr-2" /> Manage Secrets
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}
