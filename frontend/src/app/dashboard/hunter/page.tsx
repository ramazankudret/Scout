"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Target, Search, AlertCircle, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function HunterPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-2">
                        <Target className="w-8 h-8 text-red-500" />
                        Hunter Mode
                    </h1>
                    <p className="text-muted-foreground">Proactive Vulnerability Scanning & Pentesting</p>
                </div>
                <div className="flex gap-2">
                    <Button className="bg-red-600 hover:bg-red-700 text-white gap-2">
                        <Search className="w-4 h-4" />
                        New Scan
                    </Button>
                </div>
            </div>

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

            {/* Recent Findings */}
            <Card className="border-red-500/20">
                <CardHeader>
                    <CardTitle>Recent Findings</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        {[
                            { severity: "CRITICAL", title: "Open SMB Port (445)", host: "192.168.1.50" },
                            { severity: "HIGH", title: "Outdated SSH Version", host: "192.168.1.12" },
                            { severity: "MEDIUM", title: "Default Admin Password", host: "192.168.1.200" },
                        ].map((find, i) => (
                            <div key={i} className="flex items-center gap-4 p-4 rounded bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10">
                                <div className={`px-2 py-1 text-xs font-bold rounded ${find.severity === 'CRITICAL' ? 'bg-red-500 text-black' : find.severity === 'HIGH' ? 'bg-orange-500 text-black' : 'bg-yellow-500 text-black'}`}>
                                    {find.severity}
                                </div>
                                <div className="flex-1">
                                    <h4 className="text-white font-medium">{find.title}</h4>
                                    <p className="text-xs text-muted-foreground">Host: {find.host}</p>
                                </div>
                                <Button variant="ghost" size="sm">Fix This</Button>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
