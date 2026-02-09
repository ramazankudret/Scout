"use client"

import { useState, useEffect, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Eye, Activity, Database, Download, Loader2, BarChart3, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { modulesApi } from "@/services/modules"
import { trafficApi } from "@/lib/api/client"
import { TrafficFlowGraph } from "@/components/dashboard/TrafficFlowGraph"
import { HexHeatmap } from "@/components/dashboard/HexHeatmap"
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts"

const SINCE_OPTIONS = [60, 60 * 6, 60 * 24] as const
const INTERVAL_OPTIONS = [5, 15, 60] as const

/** API'den gelen UTC ISO string'i yerel saate çevirir. Timezone yoksa UTC kabul eder (Z eklenir). */
function formatUtcToLocal(
  iso: string | null | undefined,
  options: Intl.DateTimeFormatOptions = { hour: "2-digit", minute: "2-digit" }
): string {
  if (!iso || typeof iso !== "string") return ""
  const utcString = /Z$|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : iso + "Z"
  try {
    return new Date(utcString).toLocaleTimeString("tr-TR", options)
  } catch {
    return iso
  }
}

export default function StealthPage() {
    const [capturing, setCapturing] = useState(false)
    const [results, setResults] = useState<any>(null)
    const [captureBackend, setCaptureBackend] = useState<"tshark" | "scapy">("tshark")
    const [interfaceName, setInterfaceName] = useState("eth0")
    const [duration, setDuration] = useState(5)
    const [packetCount, setPacketCount] = useState(50)
    const [aggregates, setAggregates] = useState<{
        time_series: { bucket_start: string | null; packet_count: number; byte_count: number }[]
        heatmap_data: { bucket_start: string | null; ip: string; packet_count: number }[]
    } | null>(null)
    const [aggregatesLoading, setAggregatesLoading] = useState(false)
    const [sinceMinutes, setSinceMinutes] = useState(60 * 24)
    const [intervalMinutes, setIntervalMinutes] = useState(15)

    useEffect(() => {
        let cancelled = false
        async function load() {
            setAggregatesLoading(true)
            try {
                const data = await trafficApi.getAggregates({
                    since_minutes: sinceMinutes,
                    interval_minutes: intervalMinutes,
                })
                if (!cancelled) setAggregates(data)
            } catch {
                if (!cancelled) setAggregates(null)
            } finally {
                if (!cancelled) setAggregatesLoading(false)
            }
        }
        load()
        return () => { cancelled = true }
    }, [sinceMinutes, intervalMinutes])

    const chartData = useMemo(() => {
        if (!aggregates?.time_series?.length) return []
        return aggregates.time_series.map((b) => ({
            time: formatUtcToLocal(b.bucket_start, { hour: "2-digit", minute: "2-digit" }),
            packet_count: b.packet_count,
            byte_count: b.byte_count,
        }))
    }, [aggregates])

    const heatmapGrid = useMemo(() => {
        if (!aggregates?.heatmap_data?.length) return { ips: [] as string[], buckets: [] as string[], cells: new Map<string, number>() }
        const ips = Array.from(new Set(aggregates.heatmap_data.map((d) => d.ip).filter(Boolean))).sort()
        const buckets = Array.from(new Set(aggregates.heatmap_data.map((d) => d.bucket_start ?? "").filter(Boolean))).sort()
        const cells = new Map<string, number>()
        for (const d of aggregates.heatmap_data) {
            if (d.bucket_start && d.ip) cells.set(`${d.bucket_start}\t${d.ip}`, d.packet_count)
        }
        return { ips, buckets, cells }
    }, [aggregates])

    const graphDataForFlow = useMemo(() => {
        const r = results
        if (!r) return { nodes: [] as string[], edges: [] as { source: string; destination: string; packet_count: number }[] }
        if (r.graph_nodes?.length || r.graph_edges?.length) {
            return {
                nodes: Array.isArray(r.graph_nodes) ? r.graph_nodes : [],
                edges: Array.isArray(r.graph_edges) ? r.graph_edges : [],
            }
        }
        const packets = r.recent_packets
        if (!Array.isArray(packets) || packets.length === 0) return { nodes: [], edges: [] }
        const nodeSet = new Set<string>()
        const edgeCounts = new Map<string, number>()
        for (const p of packets) {
            const src = (p.source ?? "").toString().trim()
            const dst = (p.destination ?? "").toString().trim()
            if (src) nodeSet.add(src)
            if (dst) nodeSet.add(dst)
            if (src && dst && src !== dst) {
                const key = `${src}\t${dst}`
                edgeCounts.set(key, (edgeCounts.get(key) ?? 0) + 1)
            }
        }
        const edges = Array.from(edgeCounts.entries()).map(([key, packet_count]) => {
            const [source, destination] = key.split("\t")
            return { source, destination, packet_count }
        })
        return { nodes: Array.from(nodeSet), edges }
    }, [results])

    const handleCapture = async () => {
        setResults(null)
        setCapturing(true)
        try {
            const result = await modulesApi.execute("stealth", "passive", {
                capture_backend: captureBackend,
                interface: interfaceName,
                duration: Number(duration) || 5,
                packet_count: Number(packetCount) || 50,
            })
            setResults(result?.data ?? null)
        } catch (error) {
            console.error("Capture failed:", error)
            setResults({ error: error instanceof Error ? error.message : "Capture failed" })
        } finally {
            setCapturing(false)
        }
    }

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
                </div>

            <Card className="border border-white/[0.08] bg-black/40 shadow-none overflow-hidden">
                <CardHeader>
                    <CardTitle>Capture parametreleri</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-4 items-end">
                    <div>
                        <label className="text-sm text-muted-foreground block mb-1">Backend</label>
                        <select
                            value={captureBackend}
                            onChange={(e) => setCaptureBackend(e.target.value as "tshark" | "scapy")}
                            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                        >
                            <option value="tshark">Tshark</option>
                            <option value="scapy">Scapy</option>
                        </select>
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground block mb-1">Interface</label>
                        <Input
                            value={interfaceName}
                            onChange={(e) => setInterfaceName(e.target.value)}
                            placeholder="eth0, Ethernet veya Wi-Fi"
                            className="w-44"
                            title="Windows: Ethernet veya Wi-Fi; Linux: eth0"
                        />
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground block mb-1">Süre (sn)</label>
                        <Input
                            type="number"
                            min={1}
                            max={120}
                            value={duration}
                            onChange={(e) => setDuration(Number(e.target.value) || 5)}
                            className="w-24"
                        />
                    </div>
                    <div>
                        <label className="text-sm text-muted-foreground block mb-1">Paket sayısı</label>
                        <Input
                            type="number"
                            min={1}
                            max={1000}
                            value={packetCount}
                            onChange={(e) => setPacketCount(Number(e.target.value) || 50)}
                            className="w-28"
                        />
                    </div>
                    <Button
                        onClick={handleCapture}
                        disabled={capturing}
                        className="bg-purple-600 hover:bg-purple-700 text-white gap-2 min-w-[140px]"
                    >
                        {capturing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
                        {capturing ? "Listening..." : "Start Capture"}
                    </Button>
                    <Button variant="outline" className="gap-2">
                        <Download className="w-4 h-4" />
                        Export PCAP
                    </Button>
                </CardContent>
            </Card>

            {results?.error && (
                <Card className="border-red-500/50 bg-red-950/20">
                    <CardContent className="pt-4">
                        <p className="text-sm text-red-400">Hata: {results.error}</p>
                        <p className="text-xs text-muted-foreground mt-1">Windows’ta arayüz adı genelde eth0 değildir; Wi-Fi veya Ethernet kullanın. Tshark/Scapy kurulu olmalı.</p>
                    </CardContent>
                </Card>
            )}
            {results && !results.error && (
                <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">
                        Yakalama tamamlandı: {results.capture_source ?? "—"} · {(results.packets_observed ?? 0)} paket · {(results.protocols?.length ?? 0)} protokol
                    </p>
                    {(results.packets_observed ?? 0) === 0 && (
                        <p className="text-xs text-amber-500/90">
                            0 paket alındı. Tshark veya Scapy kurulu mu? Windows’ta arayüz adı <code className="bg-white/10 px-1 rounded">eth0</code> değildir; yukarıda Interface alanına <strong>Ethernet</strong> veya <strong>Wi-Fi</strong> yazıp tekrar deneyin. Tshark için Wireshark kurulumu gerekir.
                        </p>
                    )}
                </div>
            )}

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {/* Network Traffic Flow (2D force graph) */}
                <Card className="col-span-2 border border-white/[0.08] bg-black/40 shadow-none overflow-hidden">
                    <CardHeader>
                        <CardTitle>Network Traffic Flow (Live)</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px] border-t border-white/5 min-h-[300px] overflow-hidden">
                        <TrafficFlowGraph
                            nodes={graphDataForFlow.nodes}
                            edges={graphDataForFlow.edges}
                            height={280}
                        />
                    </CardContent>
                </Card>

                {/* Protocol Distribution (real counts when protocol_counts available) */}
                <Card className="border border-white/[0.08] bg-black/40 shadow-none overflow-hidden">
                    <CardHeader>
                        <CardTitle>Protocol Distribution</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px] flex items-center justify-center border-t border-white/5">
                        <div className="space-y-4 w-full">
                            {capturing ? (
                                <p className="text-muted-foreground flex items-center gap-2">
                                    <Loader2 className="w-4 h-4 animate-spin" /> Yakalanıyor...
                                </p>
                            ) : results?.error ? (
                                <p className="text-sm text-red-400">{results.error}</p>
                            ) : results?.protocol_counts && Object.keys(results.protocol_counts).length > 0 ? (
                                (() => {
                                    const counts = results.protocol_counts as Record<string, number>
                                    const total = Object.values(counts).reduce((a, b) => a + b, 0)
                                    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8)
                                    return entries.map(([p, count]) => (
                                        <div key={p} className="flex items-center justify-between text-sm gap-2">
                                            <span className="text-white shrink-0">{p}</span>
                                            <div className="flex-1 min-w-0 h-2 bg-white/10 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-purple-500 rounded-full"
                                                    style={{ width: `${total ? (count / total) * 100 : 0}%` }}
                                                />
                                            </div>
                                            <span className="text-muted-foreground shrink-0">{total ? Math.round((count / total) * 100) : 0}%</span>
                                        </div>
                                    ))
                                })()
                            ) : results?.protocols && results.protocols.length > 0 ? (
                                results.protocols.slice(0, 5).map((p: string) => (
                                    <div key={p} className="flex items-center justify-between text-sm">
                                        <span className="text-white">{p}</span>
                                        <div className="w-2/3 h-2 bg-white/10 rounded-full overflow-hidden">
                                            <div className="h-full bg-purple-500" style={{ width: "80%" }} />
                                        </div>
                                    </div>
                                ))
                            ) : results !== null ? (
                                <p className="text-muted-foreground">Veri yok</p>
                            ) : (
                                ["TCP", "TLS", "DNS", "HTTP", "UDP"].map((p, i) => (
                                    <div key={p} className="flex items-center justify-between text-sm">
                                        <span className="text-white">{p}</span>
                                        <div className="w-2/3 h-2 bg-white/10 rounded-full overflow-hidden">
                                            <div className="h-full bg-purple-500" style={{ width: `${80 - (i * 15)}%` }} />
                                        </div>
                                        <span className="text-muted-foreground">{80 - (i * 15)}%</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Son 24 saat – veritabanı (timeline + hex heatmap) */}
            <Card className="border border-white/[0.08] bg-black/40 shadow-none overflow-hidden">
                <CardHeader className="pb-2">
                    <CardTitle className="text-white flex items-center gap-2 text-lg">
                        <BarChart3 className="w-5 h-5" />
                        Son 24 saat – veritabanı
                    </CardTitle>
                    <div className="flex flex-wrap gap-4 items-center text-sm">
                        <span className="text-muted-foreground">Son</span>
                        {SINCE_OPTIONS.map((m) => (
                            <Button
                                key={m}
                                variant={sinceMinutes === m ? "default" : "outline"}
                                size="sm"
                                onClick={() => setSinceMinutes(m)}
                            >
                                {m === 60 ? "1h" : m === 360 ? "6h" : "24h"}
                            </Button>
                        ))}
                        <span className="text-muted-foreground ml-2">Aralık (dk)</span>
                        {INTERVAL_OPTIONS.map((m) => (
                            <Button
                                key={m}
                                variant={intervalMinutes === m ? "default" : "outline"}
                                size="sm"
                                onClick={() => setIntervalMinutes(m)}
                            >
                                {m}
                            </Button>
                        ))}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                                setAggregatesLoading(true)
                                trafficApi.getAggregates({ since_minutes: sinceMinutes, interval_minutes: intervalMinutes }).then((data) => {
                                    setAggregates(data)
                                    setAggregatesLoading(false)
                                }).catch(() => setAggregatesLoading(false))
                            }}
                            disabled={aggregatesLoading}
                        >
                            {aggregatesLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {aggregatesLoading ? (
                        <div className="h-64 flex items-center justify-center text-muted-foreground">
                            <Loader2 className="w-8 h-8 animate-spin" />
                        </div>
                    ) : chartData.length === 0 ? (
                        <p className="text-muted-foreground py-8 text-center">Veri yok. Önce Stealth ile yakalama yapın.</p>
                    ) : (
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" className="stroke-white/10" />
                                    <XAxis dataKey="time" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                                    <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                                    <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }} />
                                    <Area type="monotone" dataKey="packet_count" stroke="hsl(263 70% 50%)" fill="hsl(263 70% 50% / 0.3)" name="Paket" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                    {heatmapGrid.ips.length > 0 && heatmapGrid.buckets.length > 0 && (
                        <div>
                            <h4 className="text-sm font-medium text-white mb-2">Heatmap (IP × zaman) – altıgen</h4>
                            <div className="max-h-64 overflow-auto">
                                <HexHeatmap
                                    rows={heatmapGrid.ips.slice(0, 20)}
                                    columns={heatmapGrid.buckets.slice(0, 24)}
                                    getValue={(ip, bucket) => heatmapGrid.cells.get(`${bucket}\t${ip}`) ?? 0}
                                    hexRadius={8}
                                    showRowLabels
                                    showColumnLabels
                                />
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Packet Log */}
            <Card className="border border-white/[0.08] bg-black/40 shadow-none overflow-hidden">
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
                                    <th className="px-4 py-3">Length</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {results?.recent_packets && results.recent_packets.length > 0 ? (
                                    results.recent_packets.map((pkt: any, i: number) => (
                                        <tr key={i} className="hover:bg-white/5 transition-colors">
                                            <td className="px-4 py-3 text-white/60">{formatUtcToLocal(pkt.time, { hour: "2-digit", minute: "2-digit", second: "2-digit" }) || "—"}</td>
                                            <td className="px-4 py-3 text-purple-400">{pkt.source}</td>
                                            <td className="px-4 py-3 text-white">{pkt.destination}</td>
                                            <td className="px-4 py-3"><span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 text-xs">{pkt.protocol}</span></td>
                                            <td className="px-4 py-3 text-muted-foreground">{pkt.length}</td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                                            Click "Start Capture" to listen for packets...
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
