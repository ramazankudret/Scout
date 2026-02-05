"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Bell, Shield, User, Lock, Save } from "lucide-react"

export default function SettingsPage() {
    return (
        <div className="space-y-6 max-w-4xl">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Settings</h1>
                <p className="text-muted-foreground">Manage system configuration and preferences</p>
            </div>

            <div className="grid gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Shield className="w-5 h-5 text-scout-neon" />
                            Security Modules
                        </CardTitle>
                        <CardDescription>Enable or disable active security agents</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="font-medium text-white">Stealth Mode (Auto-Start)</p>
                                <p className="text-sm text-muted-foreground">Automatically start passive monitoring on boot</p>
                            </div>
                            <Switch />
                        </div>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="font-medium text-white">Defense Mode (Active Blocking)</p>
                                <p className="text-sm text-muted-foreground">Allow agent to block IPs without confirmation</p>
                            </div>
                            <Switch />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Bell className="w-5 h-5 text-yellow-500" />
                            Notifications
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <label className="text-sm font-medium text-white">Email for Alerts</label>
                            <Input placeholder="security@company.com" />
                        </div>
                        <div className="flex items-center justify-between pt-2">
                            <div>
                                <p className="font-medium text-white">Critical Alerts Only</p>
                                <p className="text-sm text-muted-foreground">Suppress low-priority notifications</p>
                            </div>
                            <Switch defaultChecked />
                        </div>
                    </CardContent>
                </Card>

                <div className="flex justify-end gap-4">
                    <Button variant="ghost">Reset Defaults</Button>
                    <Button className="bg-scout-neon text-black font-bold gap-2">
                        <Save className="w-4 h-4" />
                        Save Changes
                    </Button>
                </div>
            </div>
        </div>
    )
}
