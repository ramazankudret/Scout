"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { ArrowLeft, Loader2 } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { scansApi } from "@/lib/api/client"

export default function ScanDetailPage() {
    const params = useParams()
    const router = useRouter()
    const id = params?.id as string
    const [scan, setScan] = useState<Awaited<ReturnType<typeof scansApi.get>> | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!id) return
        scansApi
            .get(id)
            .then(setScan)
            .catch(() => setError("Tarama bulunamadı."))
            .finally(() => setLoading(false))
    }, [id])

    const formatDate = (iso: string | null) => {
        if (!iso) return "-"
        try {
            return new Date(iso).toLocaleString("tr-TR")
        } catch {
            return iso
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-24 gap-2 text-muted-foreground">
                <Loader2 className="w-6 h-6 animate-spin" />
                Yükleniyor...
            </div>
        )
    }
    if (error || !scan) {
        return (
            <div className="space-y-4">
                <p className="text-destructive">{error || "Tarama bulunamadı."}</p>
                <Link href="/dashboard/scans">
                    <Button variant="outline" className="gap-2">
                        <ArrowLeft className="w-4 h-4" />
                        Listeye dön
                    </Button>
                </Link>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Link href="/dashboard/scans">
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="w-5 h-5" />
                    </Button>
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-white">Tarama detayı</h1>
                    <p className="text-muted-foreground font-mono">{scan.target}</p>
                </div>
            </div>

            <Card className="border-white/10 bg-black/40">
                <CardHeader>
                    <CardTitle className="text-white">Özet</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                    <p><span className="text-muted-foreground">Tarama tipi:</span> <Badge variant="outline">{scan.scanner_used || scan.scan_type}</Badge></p>
                    <p><span className="text-muted-foreground">Durum:</span> <Badge className={scan.status === "completed" ? "bg-green-600" : "bg-amber-600"}>{scan.status}</Badge></p>
                    <p><span className="text-muted-foreground">Başlangıç:</span> {formatDate(scan.started_at)}</p>
                    <p><span className="text-muted-foreground">Bitiş:</span> {formatDate(scan.completed_at)}</p>
                    <p><span className="text-muted-foreground">Süre:</span> {scan.duration_seconds != null ? `${scan.duration_seconds} saniye` : "-"}</p>
                    {scan.error_message && <p className="text-destructive">Hata: {scan.error_message}</p>}
                </CardContent>
            </Card>

            {(scan.open_ports?.length ?? 0) > 0 && (
                <Card className="border-white/10 bg-black/40">
                    <CardHeader>
                        <CardTitle className="text-white">Açık portlar</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex flex-wrap gap-2">
                            {(scan.open_ports || []).map((port) => (
                                <Badge key={port} variant="secondary" className="font-mono">
                                    {port}
                                </Badge>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {(scan.services_found?.length ?? 0) > 0 && (
                <Card className="border-white/10 bg-black/40">
                    <CardHeader>
                        <CardTitle className="text-white">Servisler</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                            {(scan.services_found || []).map((svc, i) => (
                                <li key={i}>{svc}</li>
                            ))}
                        </ul>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
