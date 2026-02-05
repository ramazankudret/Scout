"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, Eye, Target, Zap } from "lucide-react"
import dynamic from "next/dynamic"

// VectorSpace bileşenini SSR olmadan yükle (Three.js SSR desteklemiyor)
const VectorSpace = dynamic(() => import("@/components/dashboard/VectorSpace"), {
    ssr: false,
    loading: () => (
        <div className="w-full h-full flex items-center justify-center">
            <div className="text-scout-neon animate-pulse">Loading 3D Space...</div>
        </div>
    ),
})

export default function DashboardPage() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Command Center</h1>
                    <p className="text-muted-foreground">System Status: <span className="text-scout-neon">OPTIMAL</span></p>
                </div>
                <div className="flex items-center gap-4">
                    {/* Status Indicators placeholder */}
                </div>
            </div>

            {/* KPI Stats */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card className="border-scout-neon/20">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Active Threats</CardTitle>
                        <Shield className="h-4 w-4 text-scout-neon" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">0</div>
                        <p className="text-xs text-muted-foreground mt-1">No anomalies detected</p>
                    </CardContent>
                </Card>

                <Card className="border-purple-500/20">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Monitored Assets</CardTitle>
                        <Eye className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">12</div>
                        <p className="text-xs text-muted-foreground mt-1">All systems online</p>
                    </CardContent>
                </Card>

                <Card className="border-blue-500/20">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Network Traffic</CardTitle>
                        <Zap className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">4.2 GB</div>
                        <p className="text-xs text-muted-foreground mt-1">↓ 12% from last hour</p>
                    </CardContent>
                </Card>

                <Card className="border-red-500/20">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Vulnerabilities</CardTitle>
                        <Target className="h-4 w-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">3</div>
                        <p className="text-xs text-muted-foreground mt-1 text-red-400">1 Critical issue found</p>
                    </CardContent>
                </Card>
            </div>


            {/* Main Content Area - 3D Universe */}
            <div className="grid gap-4 md:grid-cols-7 h-[600px]">
                <Card className="col-span-5 relative overflow-hidden flex items-center justify-center border-white/10 bg-black/60 h-full">
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-scout-neon/5 via-black/0 to-black/0 pointer-events-none" />
                    <div className="w-full h-full">
                        <VectorSpace />
                    </div>
                </Card>
                <Card className="col-span-2">
                    <CardHeader>
                        <CardTitle>Recent Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div key={i} className="flex items-center gap-4 text-sm p-2 rounded hover:bg-white/5 transition-colors cursor-pointer group">
                                    <div className="w-2 h-2 rounded-full bg-scout-neon" />
                                    <div>
                                        <p className="text-white group-hover:text-scout-neon transition-colors">Port Scan Detected</p>
                                        <p className="text-xs text-muted-foreground">192.168.1.10{i} • 2m ago</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
