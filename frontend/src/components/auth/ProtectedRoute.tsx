"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { Loader2 } from "lucide-react"

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const router = useRouter()
    const pathname = usePathname()
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        // Check for token
        const token = localStorage.getItem('token')

        if (!token) {
            // Redirect to login if no token found
            // Save the current path to redirect back after login (optional future improvement)
            router.push(`/login?from=${encodeURIComponent(pathname)}`)
        } else {
            setIsLoading(false)
        }
    }, [router, pathname])

    if (isLoading) {
        return (
            <div className="min-h-screen bg-black flex items-center justify-center">
                <div className="flex flex-col items-center gap-4 text-scout-neon">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <p className="text-sm font-mono tracking-wider">VERIFYING ACCESS...</p>
                </div>
            </div>
        )
    }

    return <>{children}</>
}
