"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Eye, Activity, Database, Download } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function StealthPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-2">
                        <Eye className="w-8 h-8 text-purple-500" />
                        Stealth Mode
                    </h1>
                    <p className="text-muted-foreground">Passive Network Analysis & Baseline Learning</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" className="gap-2">
                        <Download className="w-4 h-4" />
                        Export PCAP
                    </Button>
                    <Button className="bg-purple-600 hover:bg-purple-700 text-white gap-2">
                        <Activity className="w-4 h-4" />
                        Start Capture
                    </Button>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {/* Traffic Source Chart Placeholder */}
                <Card className="col-span-2 border-purple-500/20 bg-black/40">
                    <CardHeader>
                        <CardTitle>Network Traffic Flow (Live)</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px] flex items-center justify-center border-t border-white/5">
                        <p className="text-muted-foreground">Sankey Diagram Placeholder</p>
                    </CardContent>
                </Card>

                {/* Protocols */}
                <Card className="border-purple-500/20 bg-black/40">
                    <CardHeader>
                        <CardTitle>Protocol Distribution</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px] flex items-center justify-center border-t border-white/5">
                        <div className="space-y-4 w-full">
                            {['HTTP', 'HTTPS', 'DNS', 'SSH', 'FTP'].map((p, i) => (
                                <div key={p} className="flex items-center justify-between text-sm">
                                    <span className="text-white">{p}</span>
                                    <div className="w-2/3 h-2 bg-white/10 rounded-full overflow-hidden">
                                        <div className="h-full bg-purple-500" style={{ width: `${80 - (i * 15)}%` }} />
                                    </div>
                                    <span className="text-muted-foreground">{80 - (i * 15)}%</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Packet Log */}
            <Card className="border-purple-500/20">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Database className="w-4 h-4" />
                        Captured Packets
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border border-white/10 overflow-hidden">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-white/5 text-muted-foreground uppercase text-xs">
                                <tr>
                                    <th className="px-4 py-3">Time</th>
                                    <th className="px-4 py-3">Source IP</th>
                                    <th className="px-4 py-3">Dest IP</th>
                                    <th className="px-4 py-3">Protocol</th>
                                    <th className="px-4 py-3">Size</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {[1, 2, 3, 4, 5].map((i) => (
                                    <tr key={i} className="hover:bg-white/5 transition-colors">
                                        <td className="px-4 py-3 text-white/60">14:2{i}:05</td>
                                        <td className="px-4 py-3 text-purple-400">192.168.1.105</td>
                                        <td className="px-4 py-3 text-white">10.0.0.5</td>
                                        <td className="px-4 py-3"><span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 text-xs">TCP</span></td>
                                        <td className="px-4 py-3 text-muted-foreground">64 B</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
