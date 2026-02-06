"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Bell, Shield, User, Lock, Save, Key, Loader2, Copy, Trash2 } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { authApi, apiKeysApi, type ApiKeyEntry, type ApiKeyCreateResult } from "@/lib/api/client"
import { useState, useEffect } from "react"

export default function SettingsPage() {
    return (
        <div className="space-y-6 max-w-4xl">
            <div>
                <h1 className="text-2xl font-mono font-bold tracking-tight text-foreground">Ayarlar</h1>
                <p className="text-muted-foreground text-sm mt-1">Profil, API anahtarları ve tercihler</p>
            </div>

            <ProfileCard />
            <ApiKeysCard />
            <Card className="bg-card border-scout-border">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-foreground">
                        <Shield className="w-5 h-5 text-scout-primary" />
                        Güvenlik modülleri
                    </CardTitle>
                    <CardDescription>Güvenlik ajanlarını aç/kapat</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="font-medium text-foreground">Stealth (otomatik başlat)</p>
                            <p className="text-sm text-muted-foreground">Pasif izleme</p>
                        </div>
                        <Switch />
                    </div>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="font-medium text-foreground">Defense (aktif engelleme)</p>
                            <p className="text-sm text-muted-foreground">Onay olmadan IP engelleme</p>
                        </div>
                        <Switch />
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-card border-scout-border">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-foreground">
                        <Bell className="w-5 h-5 text-scout-warning" />
                        Bildirim tercihleri
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-2">
                        <label className="text-sm font-medium text-foreground">Uyarı e-postası</label>
                        <Input placeholder="guvenlik@sirket.com" className="bg-background border-scout-border" />
                    </div>
                    <div className="flex items-center justify-between pt-2">
                        <div>
                            <p className="font-medium text-foreground">Sadece kritik uyarılar</p>
                            <p className="text-sm text-muted-foreground">Düşük öncelikli bildirimleri azalt</p>
                        </div>
                        <Switch defaultChecked />
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

function ProfileCard() {
    const queryClient = useQueryClient()
    const { data: me, isLoading } = useQuery({ queryKey: ["auth", "me"], queryFn: () => authApi.getMe() })
    const [fullName, setFullName] = useState("")
    const [timezone, setTimezone] = useState("")
    const [locale, setLocale] = useState("")
    const [saved, setSaved] = useState(false)

    const updateMe = useMutation({
        mutationFn: (data: { full_name?: string; timezone?: string; locale?: string }) => authApi.updateMe(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["auth", "me"] })
            setSaved(true)
            setTimeout(() => setSaved(false), 2000)
        },
    })

    useEffect(() => {
        if (me) {
            setFullName(me.full_name ?? "")
            setTimezone(me.timezone ?? "Europe/Istanbul")
            setLocale(me.locale ?? "tr")
        }
    }, [me])

    return (
        <Card className="bg-card border-scout-border">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-foreground">
                    <User className="w-5 h-5 text-scout-primary" />
                    Profil
                </CardTitle>
                <CardDescription>Ad, dil ve saat dilimi</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                {isLoading ? (
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                    <>
                        <div className="grid gap-2">
                            <label className="text-sm font-medium text-foreground">E-posta</label>
                            <Input value={me?.email ?? ""} disabled className="bg-muted border-scout-border" />
                        </div>
                        <div className="grid gap-2">
                            <label className="text-sm font-medium text-foreground">Ad Soyad</label>
                            <Input
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                placeholder="Ad Soyad"
                                className="bg-background border-scout-border"
                            />
                        </div>
                        <div className="grid gap-2">
                            <label className="text-sm font-medium text-foreground">Saat dilimi</label>
                            <Input
                                value={timezone}
                                onChange={(e) => setTimezone(e.target.value)}
                                placeholder="Europe/Istanbul"
                                className="bg-background border-scout-border"
                            />
                        </div>
                        <div className="grid gap-2">
                            <label className="text-sm font-medium text-foreground">Dil (locale)</label>
                            <Input
                                value={locale}
                                onChange={(e) => setLocale(e.target.value)}
                                placeholder="tr"
                                className="bg-background border-scout-border"
                            />
                        </div>
                        <Button
                            className="bg-scout-primary text-black font-bold gap-2"
                            onClick={() => updateMe.mutate({ full_name: fullName || undefined, timezone: timezone || undefined, locale: locale || undefined })}
                            disabled={updateMe.isPending}
                        >
                            <Save className="w-4 h-4" />
                            {saved ? "Kaydedildi" : "Kaydet"}
                        </Button>
                    </>
                )}
            </CardContent>
        </Card>
    )
}

function ApiKeysCard() {
    const queryClient = useQueryClient()
    const { data: keys, isLoading } = useQuery({ queryKey: ["api-keys"], queryFn: () => apiKeysApi.list() })
    const [newName, setNewName] = useState("")
    const [createdKey, setCreatedKey] = useState<ApiKeyCreateResult | null>(null)

    const createKey = useMutation({
        mutationFn: (name: string) => apiKeysApi.create(name),
        onSuccess: (data) => {
            setCreatedKey(data)
            setNewName("")
            queryClient.invalidateQueries({ queryKey: ["api-keys"] })
        },
    })
    const deleteKey = useMutation({
        mutationFn: (id: string) => apiKeysApi.delete(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
    })

    return (
        <Card className="bg-card border-scout-border">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-foreground">
                    <Key className="w-5 h-5 text-scout-primary" />
                    API Anahtarları
                </CardTitle>
                <CardDescription>API erişimi için anahtar oluştur; anahtar yalnızca bir kez gösterilir.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                {createdKey && (
                    <div className="rounded-lg bg-scout-primary/10 border border-scout-primary/30 p-4 space-y-2">
                        <p className="text-sm font-medium text-scout-primary">Yeni anahtar (bir kez gösterilir)</p>
                        <p className="font-mono text-sm break-all">{createdKey.key}</p>
                        <Button size="sm" variant="outline" className="border-scout-border" onClick={() => navigator.clipboard.writeText(createdKey.key)}>
                            <Copy className="w-3 h-3 mr-1" /> Kopyala
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setCreatedKey(null)}>Kapat</Button>
                    </div>
                )}
                <div className="flex gap-2">
                    <Input
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        placeholder="Anahtar adı"
                        className="bg-background border-scout-border flex-1"
                    />
                    <Button
                        className="bg-scout-primary text-black"
                        onClick={() => newName.trim() && createKey.mutate(newName.trim())}
                        disabled={createKey.isPending || !newName.trim()}
                    >
                        Oluştur
                    </Button>
                </div>
                {isLoading ? (
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                ) : (
                    <ul className="space-y-2">
                        {(keys ?? []).map((k: ApiKeyEntry) => (
                            <li key={k.id} className="flex items-center justify-between py-2 border-b border-scout-border/50">
                                <span className="font-mono text-sm text-foreground">{k.name}</span>
                                <span className="text-muted-foreground text-xs">{k.key_prefix ?? "—"}</span>
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    className="text-scout-danger hover:bg-scout-danger/10"
                                    onClick={() => deleteKey.mutate(k.id)}
                                    disabled={deleteKey.isPending}
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            </li>
                        ))}
                        {(!keys || keys.length === 0) && !createdKey && <p className="text-muted-foreground text-sm">Henüz anahtar yok.</p>}
                    </ul>
                )}
            </CardContent>
        </Card>
    )
}
