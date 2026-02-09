"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { HunterHeader } from "./HunterHeader"
import { HunterScanForm } from "./HunterScanForm"
import { HunterExecution } from "./HunterExecution"
import { HunterResults } from "./HunterResults"
import { HunterActionCards } from "./HunterActionCards"
import { HunterHeatmap } from "./HunterHeatmap"
import { modulesApi } from "@/services/modules"
import { getBaseUrl } from "@/services/api"

export default function HunterPage() {
    const [target, setTarget] = useState("127.0.0.1")
    const [detailed, setDetailed] = useState(false)
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

    const handleScan = async (opts?: { scan_discovered?: boolean }) => {
        try {
            setScanning(true)
            setResults(null)
            setError(null)
            const payload: Record<string, unknown> = { target }
            if (opts?.scan_discovered) payload.scan_discovered = true
            if (detailed) payload.detailed = true
            const result = await modulesApi.execute("hunter", "active", payload)
            if (result?.data?.error) {
                setError(result.data.error)
                setResults(null)
            } else {
                const data = result?.data ?? null
                setResults(data)
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Scan failed"
            const isTimeout = msg.includes("zaman aşımı") || msg.includes("5 dk")
            const isConnectionLost = msg.includes("Backend'e bağlanılamadı") || msg.includes("Failed to fetch") || msg.includes("yanıt alamadı")
            const isSubnet = target.includes("/")
            let finalMsg = msg
            if (backendOk === true && (isTimeout || isConnectionLost)) {
                if (isSubnet) {
                    finalMsg = "Subnet taraması başarısız: Docker içindeki backend yerel ağa (192.168.x) erişemiyor. Çözüm: Proje kökünde PowerShell'de tek komut çalıştırın: .\\scripts\\backend-scan-mode.ps1 — ardından taramayı tekrar deneyin."
                } else {
                    finalMsg = "Tarama isteği yanıt alamadı. Backend loglarına bakın; Nmap kurulu mu? Subnet tarıyorsanız docker-compose.scan.yml kullanın."
                }
            }
            setError(finalMsg)
            setResults(null)
            console.error("Scan failed:", err)
        } finally {
            setScanning(false)
        }
    }

    const handleScanDiscovered = () => {
        handleScan({ scan_discovered: true })
    }

    const handleQuickPortScan = () => {
        setTarget((t) => t || "127.0.0.1")
        if (target.includes("/")) handleScan({ scan_discovered: true })
        else handleScan()
    }

    const handleVulnerabilityCheck = () => {
        window.location.href = "/dashboard/assets"
    }

    const handleComplianceAudit = () => {
        // Placeholder per plan A4
        alert("Compliance Audit — yakında eklenecek.")
    }

    const hasExecution = results && !results.error && (results.steps?.length || results.command)
    const hasResults = results && !results.error

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <HunterHeader backendOk={backendOk} target={target} />
                <HunterScanForm
                    target={target}
                    onTargetChange={setTarget}
                    detailed={detailed}
                    onDetailedChange={setDetailed}
                    onScan={() => handleScan()}
                    scanning={scanning}
                    scanDiscoveredDisabled={!target.includes("/")}
                    onScanDiscovered={target.includes("/") ? handleScanDiscovered : undefined}
                />
            </div>

            {error && (
                <Card className="border-destructive/50 bg-destructive/10">
                    <CardContent className="pt-6">
                        <p className="text-destructive">{error}</p>
                    </CardContent>
                </Card>
            )}

            {hasExecution && (
                <HunterExecution
                    steps={results.steps}
                    command={results.command}
                    process_output={results.process_output}
                />
            )}

            {hasResults && (
                <HunterResults
                    target={results.target}
                    open_ports={results.open_ports}
                    services={results.services}
                    scan_results={results.scan_results}
                    discovered_hosts={results.discovered_hosts}
                />
            )}

            {hasResults && (
                <HunterHeatmap results={results} />
            )}

            <HunterActionCards
                onQuickPortScan={handleQuickPortScan}
                onVulnerabilityCheck={handleVulnerabilityCheck}
                onComplianceAudit={handleComplianceAudit}
            />
        </div>
    )
}
