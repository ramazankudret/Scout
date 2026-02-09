"use client"

import { useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

/** Build heatmap data: rows = hosts, columns = ports, value = open (true) or closed (false). */
function buildHeatmapData(
    results: {
        target?: string
        open_ports?: number[]
        scan_results?: Array<{ target?: string; open_ports?: number[] }>
    } | null
): { hosts: string[]; ports: number[]; openSet: Set<string> } {
    if (!results) return { hosts: [], ports: [], openSet: new Set() }

    const openSet = new Set<string>() // "host:port"
    const hostSet = new Set<string>()
    const portSet = new Set<number>()

    if (results.scan_results && results.scan_results.length > 0) {
        for (const row of results.scan_results) {
            const host = row.target ?? "?"
            hostSet.add(host)
            for (const p of row.open_ports ?? []) {
                portSet.add(p)
                openSet.add(`${host}:${p}`)
            }
        }
    } else if (results.target && (results.open_ports?.length ?? 0) > 0) {
        hostSet.add(results.target)
        for (const p of results.open_ports ?? []) {
            portSet.add(p)
            openSet.add(`${results.target}:${p}`)
        }
    }

    const hosts = Array.from(hostSet).sort()
    const ports = Array.from(portSet).sort((a, b) => a - b)
    return { hosts, ports, openSet }
}

export function HunterHeatmap({
    results,
}: {
    results: {
        target?: string
        open_ports?: number[]
        scan_results?: Array<{ target?: string; open_ports?: number[] }>
    } | null
}) {
    const { hosts, ports, openSet } = useMemo(() => buildHeatmapData(results), [results])

    if (hosts.length === 0 || ports.length === 0) return null

    const cellSize = 24
    const maxPorts = 30
    const showPorts = ports.slice(0, maxPorts)
    const truncated = ports.length > maxPorts

    return (
        <Card className="border-red-500/20 bg-black/40">
            <CardHeader>
                <CardTitle>Port heatmap (host × port)</CardTitle>
                <p className="text-sm text-muted-foreground">
                    {hosts.length} host(s), {ports.length} port(s). Green = open, gray = closed.
                    {truncated && ` Showing first ${maxPorts} ports.`}
                </p>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto overflow-y-auto max-h-[400px]">
                    <div className="inline-block min-w-0">
                        <table className="border-collapse text-xs">
                            <thead>
                                <tr>
                                    <th className="sticky left-0 z-10 bg-card border border-border p-1 text-left font-mono">Host</th>
                                    {showPorts.map((p) => (
                                        <th key={p} className="border border-border p-1 text-center font-mono w-8" title={`Port ${p}`}>
                                            {p}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {hosts.map((host) => (
                                    <tr key={host}>
                                        <td className="sticky left-0 z-10 bg-card border border-border p-1 font-mono whitespace-nowrap">
                                            {host}
                                        </td>
                                        {showPorts.map((port) => {
                                            const isOpen = openSet.has(`${host}:${port}`)
                                            return (
                                                <td
                                                    key={`${host}-${port}`}
                                                    className="border border-border p-0"
                                                    style={{ width: cellSize, height: cellSize }}
                                                    title={`${host} port ${port}: ${isOpen ? "open" : "closed"}`}
                                                >
                                                    <span
                                                        className="block w-full h-full"
                                                        style={{
                                                            backgroundColor: isOpen ? "rgba(34, 197, 94, 0.6)" : "rgba(255,255,255,0.08)",
                                                        }}
                                                    />
                                                </td>
                                            )
                                        })}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
