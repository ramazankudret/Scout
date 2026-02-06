import { Sidebar } from "@/components/layout/Sidebar"
import ProtectedRoute from "@/components/auth/ProtectedRoute"
import { QueryProvider } from "@/components/providers/QueryProvider"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <ProtectedRoute>
            <QueryProvider>
            <div className="flex h-screen bg-background overflow-hidden">
                <Sidebar />
                <main className="flex-1 overflow-y-auto relative">
                    <div className="absolute inset-0 bg-dot-pattern opacity-40 pointer-events-none" />
                    <div className="relative z-10 p-6 md:p-8 max-w-7xl mx-auto w-full">
                        {children}
                    </div>
                </main>
            </div>
            </QueryProvider>
        </ProtectedRoute>
    )
}
