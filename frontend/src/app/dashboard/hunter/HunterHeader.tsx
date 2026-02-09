"use client"

import { Target } from "lucide-react"

export function HunterHeader({
    backendOk,
    target,
}: {
    backendOk: boolean | null
    target: string
}) {
    return (
        <div>
            <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-2">
                <Target className="w-8 h-8 text-red-500" />
                Hunter Mode
            </h1>
            <p className="text-muted-foreground">Proactive Vulnerability Scanning & Pentesting</p>
            {backendOk === false && (
                <p className="text-amber-500 text-sm mt-1">Backend bağlı değil. Backend&apos;i başlatın (port 8000).</p>
            )}
            {backendOk === true && (
                <p className="text-green-600 text-sm mt-1">Backend bağlı</p>
            )}
            {target.includes("/") && (
                <p className="text-amber-500/90 text-xs mt-1 max-w-xl">
                    Subnet taraması: Backend Docker içindeyse yerel ağa (192.168.x) erişemez. Çözüm: proje kökünde <code className="bg-black/30 px-1 rounded">.\scripts\backend-scan-mode.ps1</code> çalıştırın (backend host ağına alınır).
                </p>
            )}
        </div>
    )
}
