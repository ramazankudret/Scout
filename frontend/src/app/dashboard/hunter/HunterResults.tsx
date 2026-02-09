"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function HunterResults({
    target,
    open_ports,
    services,
    scan_results,
    discovered_hosts,
}: {
    target?: string
    open_ports?: number[]
    services?: string[]
    scan_results?: Array<{ target?: string; open_ports?: number[]; services?: string[] }>
    discovered_hosts?: Array<{ ip?: string; mac?: string; vendor?: string }>
}) {
    const hasSingle = (open_ports?.length ?? 0) > 0 || (services?.length ?? 0) > 0
    const hasBulk = scan_results && scan_results.length > 0
    const hasDiscovery = discovered_hosts && discovered_hosts.length > 0
    const displayTarget = target ?? scan_results?.[0]?.target ?? "—"

    if (!hasSingle && !hasBulk && !hasDiscovery) return null

    const discoveryCard = hasDiscovery ? (
        <Card key="discovery" className="border-red-500/20 bg-black/40">
            <CardHeader>
                <CardTitle>Keşif sonuçları (MAC / Vendor)</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-border">
                                <th className="text-left py-2 pr-4">IP</th>
                                <th className="text-left py-2 pr-4">MAC</th>
                                <th className="text-left py-2">Vendor</th>
                            </tr>
                        </thead>
                        <tbody>
                            {discovered_hosts!.map((row, i) => (
                                <tr key={i} className="border-b border-border/50">
                                    <td className="py-2 pr-4 font-mono">{row.ip ?? "—"}</td>
                                    <td className="py-2 pr-4 font-mono text-muted-foreground">{row.mac || "—"}</td>
                                    <td className="py-2 text-muted-foreground">{row.vendor || "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </CardContent>
        </Card>
    ) : null

    if (hasBulk) {
        return (
            <>
                {discoveryCard}
                <Card className="border-red-500/20 bg-black/40">
                <CardHeader>
                    <CardTitle>Toplu tarama sonuçları</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="text-left py-2 pr-4">Host</th>
                                    <th className="text-left py-2 pr-4">Açık portlar</th>
                                    <th className="text-left py-2">Servisler</th>
                                </tr>
                            </thead>
                            <tbody>
                                {scan_results!.map((row, i) => (
                                    <tr key={i} className="border-b border-border/50">
                                        <td className="py-2 pr-4 font-mono">{row.target ?? "—"}</td>
                                        <td className="py-2 pr-4">
                                            {(row.open_ports ?? []).length
                                                ? (row.open_ports ?? []).map((p) => (
                                                      <span key={p} className="bg-red-500/10 text-red-400 px-2 py-0.5 rounded inline-block mr-1 mb-1">
                                                          {p}
                                                      </span>
                                                  ))
                                                : "—"}
                                        </td>
                                        <td className="py-2 text-muted-foreground">
                                            {(row.services ?? []).slice(0, 3).join(", ") || "—"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
                </Card>
            </>
        )
    }

    return (
        <>
            {discoveryCard}
            <Card className="border-red-500/20 bg-black/40">
                <CardHeader>
                    <CardTitle>Scan Results: {displayTarget}</CardTitle>
                </CardHeader>
            <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                    <div>
                        <h3 className="font-bold mb-2">Open Ports</h3>
                        <ul className="space-y-1">
                            {(open_ports ?? []).map((port) => (
                                <li key={port} className="text-sm bg-red-500/10 text-red-400 px-2 py-1 rounded inline-block mr-2">
                                    Port {port}
                                </li>
                            ))}
                            {(!open_ports || open_ports.length === 0) && <li className="text-muted-foreground">No open ports found</li>}
                        </ul>
                    </div>
                    <div>
                        <h3 className="font-bold mb-2">Services</h3>
                        <ul className="space-y-1">
                            {(services ?? []).map((svc, i) => (
                                <li key={i} className="text-sm text-gray-300">• {svc}</li>
                            ))}
                        </ul>
                    </div>
                </div>
            </CardContent>
            </Card>
        </>
    )
}
