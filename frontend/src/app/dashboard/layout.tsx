import { Sidebar } from "@/components/layout/Sidebar"
import ProtectedRoute from "@/components/auth/ProtectedRoute"
import { QueryProvider } from "@/components/providers/QueryProvider"
import { ScoutChatWidget } from "@/components/chat/ScoutChatWidget"

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
                    <div className="absolute inset-0 bg-grid-soc opacity-50 pointer-events-none" />
                    <div className="relative z-10 p-6 md:p-8 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                        <div className="min-w-0 col-span-1 lg:col-span-2 xl:col-span-3">
                            {children}
                        </div>
                    </div>
                </main>
                <ScoutChatWidget />
            </div>
            </QueryProvider>
        </ProtectedRoute>
    )
}
