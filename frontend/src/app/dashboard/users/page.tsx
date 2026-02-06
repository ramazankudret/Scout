"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { adminApi, type AdminUser } from "@/lib/api/client"
import { Loader2, Search, UserCheck, UserX, Shield, ShieldOff } from "lucide-react"
import { useState } from "react"

const PAGE_SIZE = 20

export default function UsersPage() {
    const [skip, setSkip] = useState(0)
    const [q, setQ] = useState("")
    const [searchInput, setSearchInput] = useState("")
    const queryClient = useQueryClient()

    const { data, isLoading, error, isError } = useQuery({
        queryKey: ["admin", "users", skip, q],
        queryFn: () => adminApi.listUsers({ skip, limit: PAGE_SIZE, q: q || undefined }),
    })

    const updateUser = useMutation({
        mutationFn: ({ id, data }: { id: string; data: { is_active?: boolean; is_superuser?: boolean } }) =>
            adminApi.updateUser(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin", "users"] })
        },
    })

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        setQ(searchInput.trim())
        setSkip(0)
    }

    const total = data?.total ?? 0
    const hasMore = skip + (data?.items?.length ?? 0) < total
    const hasPrev = skip > 0

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-mono font-bold text-foreground tracking-tight">Kullanıcı Yönetimi</h1>
                <p className="text-muted-foreground text-sm mt-1">Sisteme kayıtlı kullanıcılar (sadece superuser)</p>
            </div>

            <Card className="bg-card border-scout-border">
                <CardHeader className="pb-4">
                    <form onSubmit={handleSearch} className="flex gap-2 flex-wrap">
                        <div className="relative flex-1 min-w-[200px]">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="E-posta veya kullanıcı adı ara..."
                                value={searchInput}
                                onChange={(e) => setSearchInput(e.target.value)}
                                className="pl-9 bg-background border-scout-border"
                            />
                        </div>
                        <Button type="submit" variant="secondary" className="border-scout-border">
                            Ara
                        </Button>
                    </form>
                </CardHeader>
                <CardContent>
                    {isError && (
                        <div className="py-6 text-center text-scout-danger text-sm">
                            {error instanceof Error ? error.message : "Yetkisiz veya sunucu hatası. (403 = Superuser değilsiniz)"}
                        </div>
                    )}
                    {isLoading && (
                        <div className="py-12 flex justify-center">
                            <Loader2 className="h-8 w-8 animate-spin text-scout-primary" />
                        </div>
                    )}
                    {!isLoading && !isError && data?.items && (
                        <>
                            <div className="overflow-x-auto rounded-lg border border-scout-border">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-scout-border bg-muted/30">
                                            <th className="text-left p-3 font-medium text-foreground">E-posta</th>
                                            <th className="text-left p-3 font-medium text-foreground">Kullanıcı adı</th>
                                            <th className="text-left p-3 font-medium text-foreground">Durum</th>
                                            <th className="text-left p-3 font-medium text-foreground">Superuser</th>
                                            <th className="text-left p-3 font-medium text-foreground">Son giriş</th>
                                            <th className="text-right p-3 font-medium text-foreground">İşlem</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.items.map((user) => (
                                            <tr
                                                key={user.id}
                                                className="border-b border-scout-border/50 hover:bg-white/5 transition-colors"
                                            >
                                                <td className="p-3 text-foreground">{user.email}</td>
                                                <td className="p-3 text-muted-foreground">{user.username ?? "—"}</td>
                                                <td className="p-3">
                                                    <span
                                                        className={
                                                            user.is_active
                                                                ? "text-scout-success"
                                                                : "text-muted-foreground"
                                                        }
                                                    >
                                                        {user.is_active ? "Aktif" : "Pasif"}
                                                    </span>
                                                </td>
                                                <td className="p-3">
                                                    {user.is_superuser ? (
                                                        <Shield className="h-4 w-4 text-scout-warning inline" />
                                                    ) : (
                                                        <ShieldOff className="h-4 w-4 text-muted-foreground inline" />
                                                    )}
                                                </td>
                                                <td className="p-3 text-muted-foreground">
                                                    {user.last_login_at
                                                        ? new Date(user.last_login_at).toLocaleString("tr-TR")
                                                        : "—"}
                                                </td>
                                                <td className="p-3 text-right">
                                                    <div className="flex gap-2 justify-end">
                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            className="border-scout-border text-xs"
                                                            onClick={() =>
                                                                updateUser.mutate({
                                                                    id: user.id,
                                                                    data: { is_active: !user.is_active },
                                                                })
                                                            }
                                                            disabled={updateUser.isPending}
                                                        >
                                                            {user.is_active ? (
                                                                <>
                                                                    <UserX className="h-3 w-3 mr-1" />
                                                                    Pasif yap
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <UserCheck className="h-3 w-3 mr-1" />
                                                                    Aktif yap
                                                                </>
                                                            )}
                                                        </Button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div className="flex items-center justify-between mt-4">
                                <p className="text-muted-foreground text-sm">
                                    Toplam {total} kullanıcı · {skip + 1}–{Math.min(skip + PAGE_SIZE, total)} gösteriliyor
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="border-scout-border"
                                        disabled={!hasPrev}
                                        onClick={() => setSkip((s) => Math.max(0, s - PAGE_SIZE))}
                                    >
                                        Önceki
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="border-scout-border"
                                        disabled={!hasMore}
                                        onClick={() => setSkip((s) => s + PAGE_SIZE)}
                                    >
                                        Sonraki
                                    </Button>
                                </div>
                            </div>
                        </>
                    )}
                    {!isLoading && !isError && data?.items?.length === 0 && (
                        <div className="py-12 text-center text-muted-foreground text-sm">Kayıt bulunamadı.</div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
