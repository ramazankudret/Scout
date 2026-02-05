"use client"

import { useState, useEffect } from "react"
import { AlertCircle, Plus, Search, Server, Shield, Globe, Laptop, Database, Filter, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { assetsApi, Asset, CreateAssetData } from "@/lib/api/client"

export default function AssetsPage() {
    const [assets, setAssets] = useState<Asset[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [refreshing, setRefreshing] = useState(false)

    // Create Modal state
    const [isCreateOpen, setIsCreateOpen] = useState(false)
    const [newAsset, setNewAsset] = useState<CreateAssetData>({
        asset_type: "ip",
        value: "",
        label: "",
        criticality: "medium",
        environment: "production"
    })

    useEffect(() => {
        loadAssets()
    }, [])

    const loadAssets = async () => {
        try {
            setLoading(true)
            const response = await assetsApi.list({ limit: 100 })
            setAssets(response.items)
            setError(null)
        } catch (err) {
            console.error("Failed to load assets:", err)
            setError("Failed to load assets. Please check backend connection.")
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    const handleCreate = async () => {
        try {
            if (!newAsset.value) return

            await assetsApi.create(newAsset)
            setIsCreateOpen(false)
            setNewAsset({
                asset_type: "ip",
                value: "",
                label: "",
                criticality: "medium",
                environment: "production"
            })
            loadAssets()
        } catch (err) {
            console.error("Failed to create asset:", err)
            alert("Failed to create asset")
        }
    }

    const getIcon = (type: string) => {
        switch (type) {
            case 'server': return <Server className="w-5 h-5" />;
            case 'domain': return <Globe className="w-5 h-5" />;
            case 'database': return <Database className="w-5 h-5" />;
            case 'laptop': return <Laptop className="w-5 h-5" />;
            default: return <Shield className="w-5 h-5" />;
        }
    }

    const getCriticalityColor = (level: string) => {
        switch (level) {
            case 'critical': return 'text-red-500 border-red-500/50 bg-red-500/10';
            case 'high': return 'text-orange-500 border-orange-500/50 bg-orange-500/10';
            case 'medium': return 'text-yellow-500 border-yellow-500/50 bg-yellow-500/10';
            default: return 'text-blue-500 border-blue-500/50 bg-blue-500/10';
        }
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row gap-4 md:items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-2">
                        <Server className="w-8 h-8 text-scout-neon" />
                        Assets Inventory
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Manage and monitor your digital assets
                    </p>
                </div>

                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        className="border-white/10 hover:bg-white/5"
                        onClick={() => {
                            setRefreshing(true)
                            loadAssets()
                        }}
                        disabled={refreshing}
                    >
                        <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                    <Button
                        className="bg-scout-neon text-black hover:bg-scout-neon/90"
                        onClick={() => setIsCreateOpen(!isCreateOpen)}
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Asset
                    </Button>
                </div>
            </div>

            {/* Stats Cards (Mock for now, could be real stats later) */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="p-4 bg-white/5 border-white/10">
                    <div className="text-muted-foreground text-sm">Total Assets</div>
                    <div className="text-2xl font-bold text-white mt-1">{assets.length}</div>
                </Card>
                <Card className="p-4 bg-white/5 border-white/10">
                    <div className="text-muted-foreground text-sm">Critical</div>
                    <div className="text-2xl font-bold text-red-500 mt-1">
                        {assets.filter(a => a.criticality === 'critical' || a.criticality === 'high').length}
                    </div>
                </Card>
                <Card className="p-4 bg-white/5 border-white/10">
                    <div className="text-muted-foreground text-sm">Vulnerable</div>
                    <div className="text-2xl font-bold text-orange-500 mt-1">
                        {assets.filter(a => a.vulnerability_count > 0).length}
                    </div>
                </Card>
                <Card className="p-4 bg-white/5 border-white/10">
                    <div className="text-muted-foreground text-sm">Active</div>
                    <div className="text-2xl font-bold text-green-500 mt-1">
                        {assets.filter(a => a.status === 'active').length}
                    </div>
                </Card>
            </div>

            {/* Create Form (Simple Collapsible) */}
            {isCreateOpen && (
                <Card className="p-6 bg-white/5 border-white/10 animate-in fade-in slide-in-from-top-4">
                    <h3 className="text-lg font-semibold text-white mb-4">Add New Asset</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Type</label>
                            <select
                                className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-white"
                                value={newAsset.asset_type}
                                onChange={e => setNewAsset({ ...newAsset, asset_type: e.target.value })}
                            >
                                <option value="ip">IP Address</option>
                                <option value="domain">Domain</option>
                                <option value="server">Server</option>
                                <option value="database">Database</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Value (IP/Domain)</label>
                            <Input
                                value={newAsset.value}
                                onChange={e => setNewAsset({ ...newAsset, value: e.target.value })}
                                placeholder="e.g. 192.168.1.100"
                                className="bg-black/50 border-white/10"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Label</label>
                            <Input
                                value={newAsset.label || ''}
                                onChange={e => setNewAsset({ ...newAsset, label: e.target.value })}
                                placeholder="e.g. Web Server"
                                className="bg-black/50 border-white/10"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm text-muted-foreground">Criticality</label>
                            <select
                                className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-white"
                                value={newAsset.criticality}
                                onChange={e => setNewAsset({ ...newAsset, criticality: e.target.value })}
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button variant="ghost" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                        <Button className="bg-scout-neon text-black" onClick={handleCreate}>Create Asset</Button>
                    </div>
                </Card>
            )}

            {/* Filters */}
            <div className="flex gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                        placeholder="Search assets..."
                        className="pl-9 bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                    />
                </div>
                <Button variant="outline" className="border-white/10 gap-2">
                    <Filter className="w-4 h-4" />
                    Filters
                </Button>
            </div>

            {/* Asset List */}
            {loading ? (
                <div className="text-center py-20 text-muted-foreground">
                    Loading assets...
                </div>
            ) : error ? (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                </div>
            ) : assets.length === 0 ? (
                <div className="text-center py-20 border border-dashed border-white/10 rounded-lg">
                    <Server className="w-12 h-12 text-white/20 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-white">No assets found</h3>
                    <p className="text-muted-foreground mt-1">Start by adding your first asset to monitor</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {assets.map((asset) => (
                        <Card key={asset.id} className="p-4 bg-white/5 border-white/10 hover:bg-white/[0.07] transition-colors">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-white/5`}>
                                        {getIcon(asset.asset_type)}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-medium text-white">{asset.label || asset.value}</h3>
                                            <Badge variant="outline" className={getCriticalityColor(asset.criticality)}>
                                                {asset.criticality}
                                            </Badge>
                                        </div>
                                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                                            <span className="flex items-center gap-1">
                                                <Globe className="w-3 h-3" /> {asset.value}
                                            </span>
                                            <span className="flex items-center gap-1">
                                                <div className={`w-2 h-2 rounded-full ${asset.status === 'active' ? 'bg-green-500' : 'bg-gray-500'}`} />
                                                {asset.status}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-8">
                                    <div className="text-right">
                                        <div className="text-sm text-muted-foreground">Risk Score</div>
                                        <div className={`font-mono font-bold ${asset.risk_score > 70 ? 'text-red-500' : 'text-green-500'}`}>
                                            {asset.risk_score}/100
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm text-muted-foreground">Vulns</div>
                                        <div className="font-mono font-bold text-white">
                                            {asset.vulnerability_count}
                                        </div>
                                    </div>
                                    <Button variant="ghost" size="sm" className="hover:bg-white/10">
                                        View
                                    </Button>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    )
}
