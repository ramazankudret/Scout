"use client"

import { Search, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"

export function HunterScanForm({
    target,
    onTargetChange,
    detailed,
    onDetailedChange,
    onScan,
    scanning,
    scanDiscoveredDisabled,
    onScanDiscovered,
}: {
    target: string
    onTargetChange: (v: string) => void
    detailed?: boolean
    onDetailedChange?: (v: boolean) => void
    onScan: () => void
    scanning: boolean
    scanDiscoveredDisabled?: boolean
    onScanDiscovered?: () => void
}) {
    return (
        <div className="flex flex-col gap-3">
            <div className="flex gap-2 items-center flex-wrap">
                <Input
                    value={target}
                    onChange={(e) => onTargetChange(e.target.value)}
                    placeholder="IP veya subnet (örn. 192.168.1.0/24)"
                    className="bg-black/50 border-white/10 w-64"
                />
                <Button
                    onClick={onScan}
                    disabled={scanning}
                    className="bg-red-600 hover:bg-red-700 text-white gap-2 min-w-[120px]"
                >
                    {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                    {scanning ? "Scanning..." : "Start Scan"}
                </Button>
                {onScanDiscovered != null && (
                    <Button
                        onClick={onScanDiscovered}
                        disabled={scanning || scanDiscoveredDisabled}
                        variant="outline"
                        className="gap-2"
                    >
                        Keşfedilenleri tara
                    </Button>
                )}
            </div>
            {onDetailedChange != null && (
                <div className="flex items-center gap-2">
                    <Switch
                        id="hunter-detailed"
                        checked={detailed ?? false}
                        onCheckedChange={onDetailedChange}
                    />
                    <label htmlFor="hunter-detailed" className="text-sm text-muted-foreground cursor-pointer">
                        Detaylı tarama (-sV -O, servis/OS, ~180s)
                    </label>
                </div>
            )}
        </div>
    )
}
