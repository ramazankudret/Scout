"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Target, Search, AlertCircle, CheckCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { modulesApi } from "@/services/modules"
import { getBaseUrl } from "@/services/api"

export default function HunterPage() {
    const [target, setTarget] = useState("127.0.0.1")
    const [scanning, setScanning] = useState(false)
    const [results, setResults] = useState<any>(null)
    const [error, setError] = useState<string | null>(null)
    const [backendOk, setBackendOk] = useState<boolean | null>(null)

    useEffect(() => {
        const check = async () => {
            try {
                const res = await fetch(`${getBaseUrl()}/health`, { method: "GET" })
                setBackendOk(res.ok)
            } catch {
                setBackendOk(false)
            }
        }
        check()
    }, [])

    const handleScan = async () => {
        try {
            setScanning(true)
            setResults(null)
            setError(null)
            const result = await modulesApi.execute("hunter", "active", { target })
            if (result?.data?.error) {
                setError(result.data.error)
                setResults(null)
            } else {
                setResults(result?.data ?? null)
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Scan failed"
            setError(msg)
            setResults(null)
            console.error("Scan failed:", err)
        } finally {
            setScanning(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-2">
                        <Target className="w-8 h-8 text-red-500" />
                        Hunter Mode
                    </h1>
                    <p className="text-muted-foreground">Proactive Vulnerability Scanning & Pentesting</p>
                    {backendOk === false && (
                        <p className="text-amber-500 text-sm mt-1">Backend bağlı değil. Backend&apos;i başlatın (port 8000).</p>
                    )}
                    {backendOk === true && (
                        <p className="text-green-600 text-sm mt-1">Backend bağlı</p>
                    )}
                </div>
                <div className="flex gap-2 items-center">
                    <Input
                        value={target}
                        onChange={(e: any) => setTarget(e.target.value)}
                        placeholder="Target IP (e.g., 192.168.1.5)"
                        className="bg-black/50 border-white/10 w-64"
                    />
                    <Button
                        onClick={handleScan}
                        disabled={scanning}
                        className="bg-red-600 hover:bg-red-700 text-white gap-2 min-w-[120px]"
                    >
                        {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                        {scanning ? "Scanning..." : "Start Scan"}
                    </Button>
                </div>
            </div>

            {/* Error */}
            {error && (
                <Card className="border-destructive/50 bg-destructive/10">
                    <CardContent className="pt-6">
                        <p className="text-destructive">{error}</p>
                    </CardContent>
                </Card>
            )}

            {/* Results Section */}
            {results && !results.error && (
                <Card className="border-red-500/20 bg-black/40">
                    <CardHeader>
                        <CardTitle>Scan Results: {results.target ?? target}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-4 md:grid-cols-2">
                            <div>
                                <h3 className="font-bold mb-2">Open Ports</h3>
                                <ul className="space-y-1">
                                    {results.open_ports?.map((port: any) => (
                                        <li key={port} className="text-sm bg-red-500/10 text-red-400 px-2 py-1 rounded inline-block mr-2">
                                            Port {port}
                                        </li>
                                    ))}
                                    {(!results.open_ports || results.open_ports.length === 0) && <li className="text-muted-foreground">No open ports found</li>}
                                </ul>
                            </div>
                            <div>
                                <h3 className="font-bold mb-2">Services</h3>
                                <ul className="space-y-1">
                                    {results.services?.map((svc: string, i: number) => (
                                        <li key={i} className="text-sm text-gray-300">• {svc}</li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            <div className="grid gap-6 md:grid-cols-3">
                {/* Action Cards */}
                <Card className="bg-gradient-to-br from-red-950/30 to-black border-red-500/20 hover:border-red-500/50 transition-colors cursor-pointer group">
                    <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4">
                        <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center group-hover:bg-red-500/20 transition-colors">
                            <Target className="w-8 h-8 text-red-500" />
                        </div>
                        <h3 className="font-bold text-white text-lg">Quick Port Scan</h3>
                        <p className="text-sm text-muted-foreground">Scan top 1000 ports on local network</p>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-orange-950/30 to-black border-orange-500/20 hover:border-orange-500/50 transition-colors cursor-pointer group">
                    <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4">
                        <div className="w-16 h-16 rounded-full bg-orange-500/10 flex items-center justify-center group-hover:bg-orange-500/20 transition-colors">
                            <AlertCircle className="w-8 h-8 text-orange-500" />
                        </div>
                        <h3 className="font-bold text-white text-lg">Vulnerability Check</h3>
                        <p className="text-sm text-muted-foreground">Check for known CVEs on discovered assets</p>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-green-950/30 to-black border-green-500/20 hover:border-green-500/50 transition-colors cursor-pointer group">
                    <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4">
                        <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center group-hover:bg-green-500/20 transition-colors">
                            <CheckCircle className="w-8 h-8 text-green-500" />
                        </div>
                        <h3 className="font-bold text-white text-lg">Compliance Audit</h3>
                        <p className="text-sm text-muted-foreground">Verify security config against best practices</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
