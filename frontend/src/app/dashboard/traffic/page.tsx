"use client"

import { useState, useEffect } from "react"
import { Activity, RefreshCw, Loader2, Ghost } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { trafficApi, TrafficItem } from "@/lib/api/client"

export default function TrafficPage() {
    const [items, setItems] = useState<TrafficItem[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [filterSrc, setFilterSrc] = useState("")
    const [filterDst, setFilterDst] = useState("")
    const [limit] = useState(100)
    const [offset, setOffset] = useState(0)

    useEffect(() => {
        loadTraffic()
    }, [offset, filterSrc, filterDst])

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
                        <Ghost className="w-8 h-8 text-purple-500" />
                        Trafik / Paket logları
                    </h1>
                    <p className="text-muted-foreground">Stealth (tshark) yakalama kayıtları</p>
                </div>
                <Button variant="outline" onClick={loadTraffic} disabled={loading} className="gap-2">
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    Yenile
                </Button>
            </div>

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
