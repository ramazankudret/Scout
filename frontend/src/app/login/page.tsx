"use client"

import { useState } from "react"
import { Shield, Lock, Mail, ArrowRight, AlertCircle, Loader2 } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"

export default function LoginPage() {
    const router = useRouter()
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const [formData, setFormData] = useState({
        username: "",
        password: ""
    })

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError(null)

        try {
            const formBody = new URLSearchParams()
            formBody.append('username', formData.username)
            formBody.append('password', formData.password)

            const res = await fetch('http://localhost:8000/api/v1/auth/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formBody
            })

            if (!res.ok) {
                throw new Error("Invalid username or password")
            }

            const data = await res.json()
            // Store token
            localStorage.setItem('token', data.access_token)
            // Redirect to dashboard
            router.push('/dashboard')

        } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-black flex flex-col items-center justify-center p-4 relative overflow-hidden">
            {/* Background Grid */}
            <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20 pointer-events-none" />

            {/* Glow Effect */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-scout-neon/20 rounded-full blur-[100px] pointer-events-none" />

            <div className="w-full max-w-md relative z-10 space-y-8">
                {/* Logo */}
                <div className="text-center space-y-2">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-scout-neon/10 ring-1 ring-scout-neon/50 mb-4">
                        <Shield className="w-8 h-8 text-scout-neon" />
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Welcome Back</h1>
                    <p className="text-muted-foreground">Sign in to access your command center</p>
                </div>

                {/* Form */}
                <Card className="p-8 bg-black/50 backdrop-blur-xl border-white/10 shadow-2xl">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="p-3 rounded bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-sm text-red-400">
                                <AlertCircle className="w-4 h-4" />
                                {error}
                            </div>
                        )}

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-muted-foreground">Username</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                    <Input
                                        type="text"
                                        placeholder="Enter your username"
                                        className="pl-9 bg-white/5 border-white/10 text-white placeholder:text-muted-foreground/50 focus:border-scout-neon/50 focus:ring-scout-neon/20"
                                        value={formData.username}
                                        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <label className="text-sm font-medium text-muted-foreground">Password</label>
                                    <Link href="#" className="text-xs text-scout-neon hover:text-scout-neon/80">Forgot password?</Link>
                                </div>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                    <Input
                                        type="password"
                                        placeholder="••••••••"
                                        className="pl-9 bg-white/5 border-white/10 text-white placeholder:text-muted-foreground/50 focus:border-scout-neon/50 focus:ring-scout-neon/20"
                                        value={formData.password}
                                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                        required
                                    />
                                </div>
                            </div>
                        </div>

                        <Button
                            type="submit"
                            className="w-full bg-scout-neon text-black hover:bg-scout-neon/90 font-medium h-11"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Authenticating...
                                </>
                            ) : (
                                <>
                                    Sign In
                                    <ArrowRight className="w-4 h-4 ml-2" />
                                </>
                            )}
                        </Button>
                    </form>
                </Card>

                {/* Footer */}
                <p className="text-center text-sm text-muted-foreground">
                    Don't have an account?{" "}
                    <Link href="/register" className="text-scout-neon hover:text-scout-neon/80 font-medium transition-colors">
                        Create Access Key
                    </Link>
                </p>
            </div>
        </div>
    )
}
