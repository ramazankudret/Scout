"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Brain, Shield, Target, AlertTriangle, CheckCircle, Play, Loader2 } from "lucide-react"

// Mock LLM security data
const mockScanHistory = [
    { id: 1, target: "api.example.com/chat", score: 75, vulns: 2, timestamp: "10m ago" },
    { id: 2, target: "chatbot.test.io/v1", score: 95, vulns: 0, timestamp: "1h ago" },
    { id: 3, target: "ai.internal/assistant", score: 60, vulns: 4, timestamp: "2h ago" },
]

const attackTypes = [
    { id: "prompt_injection", name: "Prompt Injection", enabled: true },
    { id: "jailbreak", name: "Jailbreak", enabled: true },
    { id: "data_exfiltration", name: "Data Exfiltration", enabled: true },
    { id: "context_overflow", name: "Context Overflow", enabled: false },
]

export default function AISecurityPage() {
    const [targetUrl, setTargetUrl] = useState("")
    const [isScanning, setIsScanning] = useState(false)
    const [scanHistory] = useState(mockScanHistory)

    const startScan = () => {
        if (!targetUrl) return
        setIsScanning(true)
        // TODO: Call API
        setTimeout(() => setIsScanning(false), 3000)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-white">AI Security</h1>
                <p className="text-slate-400 text-sm">LLM vulnerability scanner and protection</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
                <Card className="bg-scout-neon/10 border-scout-neon/30">
                    <CardContent className="p-4 flex items-center gap-4">
                        <Brain className="w-8 h-8 text-scout-neon" />
                        <div>
                            <p className="text-2xl font-bold text-scout-neon">{scanHistory.length}</p>
                            <p className="text-xs text-scout-neon/70">Scans Completed</p>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-red-500/10 border-red-500/30">
                    <CardContent className="p-4 flex items-center gap-4">
                        <AlertTriangle className="w-8 h-8 text-red-500" />
                        <div>
                            <p className="text-2xl font-bold text-red-500">6</p>
                            <p className="text-xs text-red-400">Vulnerabilities Found</p>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-green-500/10 border-green-500/30">
                    <CardContent className="p-4 flex items-center gap-4">
                        <Shield className="w-8 h-8 text-green-500" />
                        <div>
                            <p className="text-2xl font-bold text-green-500">142</p>
                            <p className="text-xs text-green-400">Threats Blocked (LLM Guard)</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* New Scan */}
            <Card className="bg-slate-900/50 border-white/5">
                <CardHeader>
                    <CardTitle className="text-scout-neon flex items-center gap-2">
                        <Target className="w-4 h-4" /> New AI Pentest
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex gap-2">
                        <Input
                            placeholder="Enter target LLM API endpoint (e.g., https://api.example.com/chat)"
                            value={targetUrl}
                            onChange={(e) => setTargetUrl(e.target.value)}
                            className="bg-black/30 border-white/10"
                        />
                        <Button
                            onClick={startScan}
                            disabled={isScanning || !targetUrl}
                            className="bg-scout-neon text-black hover:bg-scout-neon/80"
                        >
                            {isScanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                            <span className="ml-2">{isScanning ? "Scanning..." : "Start Scan"}</span>
                        </Button>
                    </div>

                    {/* Attack Type Selection */}
                    <div className="flex gap-2 flex-wrap">
                        {attackTypes.map((type) => (
                            <Button
                                key={type.id}
                                variant="outline"
                                size="sm"
                                className={type.enabled ? "border-scout-neon/50 text-scout-neon" : "border-slate-700 text-slate-500"}
                            >
                                {type.name}
                            </Button>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Scan History */}
            <Card className="bg-slate-900/50 border-white/5">
                <CardHeader>
                    <CardTitle className="text-white">Recent Scans</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {scanHistory.map((scan) => (
                            <div
                                key={scan.id}
                                className="flex items-center justify-between p-3 rounded-lg bg-black/30 border border-white/5"
                            >
                                <div className="flex items-center gap-3">
                                    {scan.vulns === 0 ? (
                                        <CheckCircle className="w-5 h-5 text-green-500" />
                                    ) : (
                                        <AlertTriangle className="w-5 h-5 text-yellow-500" />
                                    )}
                                    <div>
                                        <p className="text-sm text-white font-mono">{scan.target}</p>
                                        <p className="text-xs text-slate-500">{scan.timestamp}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="text-right">
                                        <p className={`text-lg font-bold ${scan.score >= 80 ? "text-green-500" : scan.score >= 60 ? "text-yellow-500" : "text-red-500"}`}>
                                            {scan.score}%
                                        </p>
                                        <p className="text-[10px] text-slate-500">Security Score</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-lg font-bold text-red-400">{scan.vulns}</p>
                                        <p className="text-[10px] text-slate-500">Vulns</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
