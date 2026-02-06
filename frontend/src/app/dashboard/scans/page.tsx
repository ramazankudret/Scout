"use client"

import { useState, useEffect } from "react"
import { Search, RefreshCw, Loader2, Crosshair, ExternalLink } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { scansApi, ScanResultItem } from "@/lib/api/client"

export default function ScansPage() {
    const [scans, setScans] = useState<ScanResultItem[]>([])
    const [total, setTotal] = useState(0)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [filterTarget, setFilterTarget] = useState("")
    const [filterScanType, setFilterScanType] = useState("")
    const [limit] = useState(50)
    const [offset, setOffset] = useState(0)

    useEffect(() => {
        loadScans()
    }, [offset, filterTarget, filterScanType])

    const loadScans = async () => {
        try {
            setLoading(true)
            const res = await scansApi.list({
                limit,
                offset,
                target: filterTarget || undefined,
                scan_type: filterScanType || undefined,
            })
            setScans(res.items)
            setTotal(res.total)
            setError(null)
        } catch (err) {
            console.error("Failed to load scans:", err)
            setError("Tarama geçmişi yüklenemedi. Giriş yaptığınızdan emin olun.")
        } finally {
            setLoading(false)
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

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-2">
                        <Crosshair className="w-8 h-8 text-scout-danger" />
                        Tarama Geçmişi
                    </h1>
                    <p className="text-muted-foreground">Nmap ve diğer tarama araçlarından kayıtlar</p>
                </div>
                <Button variant="outline" onClick={loadScans} disabled={loading} className="gap-2">
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    Yenile
                </Button>
            </div>

            <Card className="border-white/10 bg-black/40">
                <CardHeader className="pb-4">
                    <CardTitle className="text-white flex items-center gap-2">
                        <Search className="w-5 h-5" />
                        Filtreler
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-4">
                    <Input
                        placeholder="Hedef (IP veya host)"
                        value={filterTarget}
                        onChange={(e) => setFilterTarget(e.target.value)}
                        className="bg-black/50 border-white/10 w-48"
                    />
                    <select
                        value={filterScanType}
                        onChange={(e) => setFilterScanType(e.target.value)}
                        className="bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white w-40"
                    >
                        <option value="">Tüm tipler</option>
                        <option value="nmap">nmap</option>
                        <option value="masscan">masscan</option>
                    </select>
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
                    <CardTitle className="text-white">Kayıtlar ({total})</CardTitle>
                </CardHeader>
                <CardContent>
                    {loading && offset === 0 ? (
                        <div className="flex items-center justify-center py-12 gap-2 text-muted-foreground">
                            <Loader2 className="w-6 h-6 animate-spin" />
                            Yükleniyor...
                        </div>
                    ) : scans.length === 0 ? (
                        <p className="text-muted-foreground py-8 text-center">
                            Henüz tarama kaydı yok. Hunter sayfasından tarama başlatın.
                        </p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-white/10 text-left text-muted-foreground">
                                        <th className="pb-3 pr-4">Tarih</th>
                                        <th className="pb-3 pr-4">Hedef</th>
                                        <th className="pb-3 pr-4">Tarama tipi</th>
                                        <th className="pb-3 pr-4">Durum</th>
                                        <th className="pb-3 pr-4">Açık port</th>
                                        <th className="pb-3 pr-4">Süre</th>
                                        <th className="pb-3"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {scans.map((s) => (
                                        <tr key={s.id} className="border-b border-white/5 hover:bg-white/5">
                                            <td className="py-3 pr-4 text-muted-foreground">{formatDate(s.created_at)}</td>
                                            <td className="py-3 pr-4 font-mono text-white">{s.target}</td>
                                            <td className="py-3 pr-4">
                                                <Badge variant="outline" className="border-red-500/30 text-red-400">
                                                    {s.scanner_used || s.scan_type}
                                                </Badge>
                                            </td>
                                            <td className="py-3 pr-4">
                                                <Badge className={s.status === "completed" ? "bg-green-600" : "bg-amber-600"}>
                                                    {s.status}
                                                </Badge>
                                            </td>
                                            <td className="py-3 pr-4 text-white">{s.open_ports_count ?? 0}</td>
                                            <td className="py-3 pr-4 text-muted-foreground">
                                                {s.duration_seconds != null ? `${s.duration_seconds}s` : "-"}
                                            </td>
                                            <td className="py-3">
                                                <Link href={`/dashboard/scans/${s.id}`}>
                                                    <Button variant="ghost" size="sm" className="gap-1 text-muted-foreground hover:text-white">
                                                        <ExternalLink className="w-4 h-4" />
                                                        Detay
                                                    </Button>
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                    {total > limit && (
                        <div className="flex justify-between items-center mt-4 pt-4 border-t border-white/10">
                            <p className="text-muted-foreground text-sm">
                                {offset + 1}-{Math.min(offset + scans.length, total)} / {total}
                            </p>
                            <div className="flex gap-2">
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
                                    disabled={offset + scans.length >= total}
                                    onClick={() => setOffset((o) => o + limit)}
                                >
                                    Sonraki
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
