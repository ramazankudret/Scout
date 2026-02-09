"use client"

import { useState, useEffect, useMemo } from "react"
import { Activity, RefreshCw, Loader2, Ghost, BarChart3, Grid3X3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { trafficApi, TrafficItem, TrafficAggregates } from "@/lib/api/client"
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts"
import { HexHeatmap } from "@/components/dashboard/HexHeatmap"

const SINCE_OPTIONS = [60, 60 * 6, 60 * 24] as const
const INTERVAL_OPTIONS = [5, 15, 60] as const

function formatUtcToLocal(iso: string | null | undefined): string {
    if (!iso || typeof iso !== "string") return ""
    const utcString = /Z$|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : iso + "Z"
    try {
        return new Date(utcString).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" })
    } catch {
        return iso
    }
}

export default function TrafficPage() {
    const [items, setItems] = useState<TrafficItem[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [filterSrc, setFilterSrc] = useState("")
    const [filterDst, setFilterDst] = useState("")
    const [limit] = useState(100)
    const [offset, setOffset] = useState(0)
    const [aggregates, setAggregates] = useState<TrafficAggregates | null>(null)
    const [aggregatesLoading, setAggregatesLoading] = useState(false)
    const [sinceMinutes, setSinceMinutes] = useState(60 * 24)
    const [intervalMinutes, setIntervalMinutes] = useState(15)

    useEffect(() => {
        loadTraffic()
    }, [offset, filterSrc, filterDst])

    useEffect(() => {
        loadAggregates()
    }, [sinceMinutes, intervalMinutes])

    const loadTraffic = async () => {
        try {
            setLoading(true)
            const res = await trafficApi.list({
                limit,
                offset,
                source_ip: filterSrc || undefined,
                destination_ip: filterDst || undefined,
            })
            setItems(res.items)
            setError(null)
        } catch (err) {
            console.error("Failed to load traffic:", err)
            setError("Paket logları yüklenemedi. Giriş yaptığınızdan emin olun.")
        } finally {
            setLoading(false)
        }
    }

    const loadAggregates = async () => {
        try {
            setAggregatesLoading(true)
            const data = await trafficApi.getAggregates({
                since_minutes: sinceMinutes,
                interval_minutes: intervalMinutes,
            })
            setAggregates(data)
        } catch (err) {
            console.error("Failed to load aggregates:", err)
            setAggregates(null)
        } finally {
            setAggregatesLoading(false)
        }
    }

    const formatDate = (iso: string | null) => {
        if (!iso) return "-"
        try {
            return new Date(iso).toLocaleString("tr-TR")
        } catch {
            return iso
        }
    }

    const chartData = useMemo(() => {
        if (!aggregates?.time_series?.length) return []
        return aggregates.time_series.map((b) => ({
            time: formatUtcToLocal(b.bucket_start),
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

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-2">
                        <Ghost className="w-8 h-8 text-purple-500" />
                        Trafik / Paket logları
                    </h1>
                    <p className="text-muted-foreground">Stealth (tshark/scapy) yakalama kayıtları</p>
                </div>
                <Button variant="outline" onClick={loadTraffic} disabled={loading} className="gap-2">
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    Yenile
                </Button>
            </div>

            {/* Time series */}
            <Card className="border-white/10 bg-black/40">
                <CardHeader className="pb-2">
                    <CardTitle className="text-white flex items-center gap-2 text-lg">
                        <BarChart3 className="w-5 h-5" />
                        Zaman serisi (paket / byte)
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
                        <Button variant="ghost" size="sm" onClick={loadAggregates} disabled={aggregatesLoading}>
                            {aggregatesLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
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
                </CardContent>
            </Card>

            {/* Heatmap IP × zaman (hex, referans görsel spec: gri→kırmızı→turuncu→sarı) */}
            {heatmapGrid.ips.length > 0 && heatmapGrid.buckets.length > 0 && (
                <Card className="border-white/10 bg-black/40">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2 text-lg">
                            <Grid3X3 className="w-5 h-5" />
                            Heatmap (IP × zaman)
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
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
                    </CardContent>
                </Card>
            )}

            <Card className="border-white/10 bg-black/40">
                <CardHeader className="pb-4">
                    <CardTitle className="text-white flex items-center gap-2">
                        <Activity className="w-5 h-5" />
                        Filtreler
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-4">
                    <Input
                        placeholder="Kaynak IP"
                        value={filterSrc}
                        onChange={(e) => setFilterSrc(e.target.value)}
                        className="bg-black/50 border-white/10 w-40 font-mono"
                    />
                    <Input
                        placeholder="Hedef IP"
                        value={filterDst}
                        onChange={(e) => setFilterDst(e.target.value)}
                        className="bg-black/50 border-white/10 w-40 font-mono"
                    />
                </CardContent>
            </Card>

            {error && (
                <Card className="border-destructive/50 bg-destructive/10">
                    <CardContent className="pt-6">
                        <p className="text-destructive">{error}</p>
                    </CardContent>
                </Card>
            )}

            <Card className="border-white/10 bg-black/40">
                <CardHeader>
                    <CardTitle className="text-white">Son paketler</CardTitle>
                </CardHeader>
                <CardContent>
                    {loading && offset === 0 ? (
                        <div className="flex items-center justify-center py-12 gap-2 text-muted-foreground">
                            <Loader2 className="w-6 h-6 animate-spin" />
                            Yükleniyor...
                        </div>
                    ) : items.length === 0 ? (
                        <p className="text-muted-foreground py-8 text-center">
                            Henüz paket kaydı yok. Stealth sayfasından yakalama başlatın.
                        </p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-white/10 text-left text-muted-foreground">
                                        <th className="pb-3 pr-4">Zaman</th>
                                        <th className="pb-3 pr-4">Kaynak IP</th>
                                        <th className="pb-3 pr-4">Hedef IP</th>
                                        <th className="pb-3 pr-4">Protokol</th>
                                        <th className="pb-3 pr-4">Uzunluk</th>
                                        <th className="pb-3 pr-4">Arayüz</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {items.map((p) => (
                                        <tr key={`${p.timestamp}-${p.id}`} className="border-b border-white/5 hover:bg-white/5">
                                            <td className="py-2 pr-4 text-muted-foreground">{formatDate(p.timestamp)}</td>
                                            <td className="py-2 pr-4 font-mono text-white">{p.source_ip}</td>
                                            <td className="py-2 pr-4 font-mono text-white">{p.destination_ip}</td>
                                            <td className="py-2 pr-4">{p.protocol}</td>
                                            <td className="py-2 pr-4">{p.length}</td>
                                            <td className="py-2 pr-4 text-muted-foreground">{p.interface}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                    {items.length === limit && (
                        <div className="flex justify-between items-center mt-4 pt-4 border-t border-white/10">
                            <Button
                                variant="outline"
                                size="sm"
                                disabled={offset === 0}
                                onClick={() => setOffset((o) => Math.max(0, o - limit))}
                            >
                                Önceki
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setOffset((o) => o + limit)}
                            >
                                Sonraki
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
