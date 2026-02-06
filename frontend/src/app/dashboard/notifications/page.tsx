"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { notificationsApi } from "@/lib/api/client"
import { Loader2, Bell, CheckCheck } from "lucide-react"

export default function NotificationsPage() {
    const queryClient = useQueryClient()
    const { data: list, isLoading, error } = useQuery({
        queryKey: ["notifications"],
        queryFn: () => notificationsApi.list({ limit: 100 }),
    })
    const markAllRead = useMutation({
        mutationFn: () => notificationsApi.markAllRead(),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
    })

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-mono font-bold text-foreground tracking-tight">Bildirimler</h1>
                    <p className="text-muted-foreground text-sm mt-1">Tüm bildirimleriniz</p>
                </div>
                {list && list.length > 0 && (
                    <Button
                        variant="outline"
                        size="sm"
                        className="border-scout-border"
                        onClick={() => markAllRead.mutate()}
                        disabled={markAllRead.isPending}
                    >
                        <CheckCheck className="h-4 w-4 mr-2" />
                        Tümünü okundu işaretle
                    </Button>
                )}
            </div>

            <Card className="bg-card border-scout-border">
                <CardContent className="py-6">
                    {isLoading && (
                        <div className="flex justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-scout-primary" />
                        </div>
                    )}
                    {error && (
                        <p className="text-center text-scout-danger text-sm py-4">
                            {error instanceof Error ? error.message : "Yüklenemedi."}
                        </p>
                    )}
                    {!isLoading && !error && (!list || list.length === 0) && (
                        <div className="flex flex-col items-center gap-3 py-12 text-muted-foreground">
                            <Bell className="h-12 w-12 opacity-50" />
                            <p>Bildirim yok.</p>
                        </div>
                    )}
                    {!isLoading && !error && list && list.length > 0 && (
                        <ul className="divide-y divide-scout-border">
                            {list.map((n) => (
                                <li
                                    key={n.id}
                                    className={`py-4 first:pt-0 ${!n.is_read ? "bg-scout-primary/5 border-l-2 border-scout-primary pl-4 -ml-4" : ""}`}
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <div>
                                            <p className="font-medium text-foreground">{n.title}</p>
                                            {n.message && <p className="text-sm text-muted-foreground mt-1">{n.message}</p>}
                                            <p className="text-xs text-muted-foreground mt-2">
                                                {n.created_at ? new Date(n.created_at).toLocaleString("tr-TR") : ""} · {n.severity}
                                            </p>
                                        </div>
                                        {!n.is_read && (
                                            <MarkReadButton notificationId={n.id} />
                                        )}
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}

function MarkReadButton({ notificationId }: { notificationId: string }) {
    const queryClient = useQueryClient()
    const mutation = useMutation({
        mutationFn: () => notificationsApi.markRead(notificationId),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
    })
    return (
        <Button
            variant="ghost"
            size="sm"
            className="text-scout-primary"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
        >
            Okundu
        </Button>
    )
}
