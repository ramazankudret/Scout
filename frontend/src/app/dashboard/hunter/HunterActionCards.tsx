"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Target, AlertCircle, CheckCircle } from "lucide-react"

export function HunterActionCards({
    onQuickPortScan,
    onVulnerabilityCheck,
    onComplianceAudit,
}: {
    onQuickPortScan?: () => void
    onVulnerabilityCheck?: () => void
    onComplianceAudit?: () => void
}) {
    return (
        <div className="grid gap-6 md:grid-cols-3">
            <Card
                className="bg-gradient-to-br from-red-950/30 to-black border-red-500/20 hover:border-red-500/50 transition-colors cursor-pointer group"
                onClick={onQuickPortScan}
            >
                <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center group-hover:bg-red-500/20 transition-colors">
                        <Target className="w-8 h-8 text-red-500" />
                    </div>
                    <h3 className="font-bold text-white text-lg">Quick Port Scan</h3>
                    <p className="text-sm text-muted-foreground">Scan top 1000 ports on local network</p>
                </CardContent>
            </Card>

            <Card
                className="bg-gradient-to-br from-orange-950/30 to-black border-orange-500/20 hover:border-orange-500/50 transition-colors cursor-pointer group"
                onClick={onVulnerabilityCheck}
            >
                <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-orange-500/10 flex items-center justify-center group-hover:bg-orange-500/20 transition-colors">
                        <AlertCircle className="w-8 h-8 text-orange-500" />
                    </div>
                    <h3 className="font-bold text-white text-lg">Vulnerability Check</h3>
                    <p className="text-sm text-muted-foreground">Check for known CVEs on discovered assets</p>
                </CardContent>
            </Card>

            <Card
                className="bg-gradient-to-br from-green-950/30 to-black border-green-500/20 hover:border-green-500/50 transition-colors cursor-pointer group"
                onClick={onComplianceAudit}
            >
                <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center group-hover:bg-green-500/20 transition-colors">
                        <CheckCircle className="w-8 h-8 text-green-500" />
                    </div>
                    <h3 className="font-bold text-white text-lg">Compliance Audit</h3>
                    <p className="text-sm text-muted-foreground">Verify security config against best practices</p>
                </CardContent>
            </Card>
        </div>
    )
}
