"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, Ban, Globe, AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function DefensePage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-2">
                        <Shield className="w-8 h-8 text-blue-500" />
                        Defense Mode
                    </h1>
                    <p className="text-muted-foreground">Active Protection & Threat Mitigation</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="destructive" className="gap-2">
                        <Ban className="w-4 h-4" />
                        Block IP Range
                    </Button>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                {/* World Map Placeholder */}
                <Card className="col-span-2 border-blue-500/20 bg-black/40">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Globe className="w-4 h-4 text-blue-400" />
                            Global Threat Map
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[400px] flex items-center justify-center border-t border-white/5 relative overflow-hidden">
                        {/* Simulated Map Dots */}
                        <div className="absolute inset-0 opacity-30 bg-[url('https://upload.wikimedia.org/wikipedia/commons/8/80/World_map_-_low_resolution.svg')] bg-contain bg-no-repeat bg-center opacity-20" />
                        <div className="relative z-10 text-center">
                            <p className="text-blue-400 animate-pulse">MONITORING GLOBAL TRAFFIC...</p>
                        </div>
                    </CardContent>
                </Card>

                {/* Blocked List */}
                <Card className="border-blue-500/20 bg-black/40">
                    <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                            <span>Blocked Entities</span>
                            <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">12 Active</span>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[
                                { ip: "45.12.55.12", country: "CN", reason: "Brute Force" },
                                { ip: "185.22.1.5", country: "RU", reason: "Port Scan" },
                                { ip: "92.11.55.2", country: "US", reason: "Malware Signature" },
                            ].map((item, i) => (
                                <div key={i} className="flex items-center justify-between p-3 rounded bg-white/5 border border-white/5">
                                    <div>
                                        <p className="text-white font-mono text-sm">{item.ip}</p>
                                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                                            <span className="w-3 h-3 rounded-full bg-white/10 text-[8px] flex items-center justify-center">{item.country}</span>
                                            {item.reason}
                                        </p>
                                    </div>
                                    <Button variant="ghost" size="sm" className="h-6 text-xs text-muted-foreground hover:text-white">Unblock</Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
