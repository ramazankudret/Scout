"use client"

import { Activity, Shield, Target, LogOut, Settings, Eye, FileText, Bot, Lock, Brain, Server, CheckSquare, ShieldCheck } from "lucide-react"
import Link from "next/link"
import { useRouter, usePathname } from "next/navigation"

import { cn } from "@/lib/utils"

const mainItems = [
  {
    title: "Command Center",
    href: "/dashboard",
    icon: Activity,
    color: "text-scout-neon",
  },
  {
    title: "Pending Approvals",
    href: "/dashboard/approvals",
    icon: CheckSquare,
    color: "text-orange-500",
  },
  {
    title: "Assets Inventory",
    href: "/dashboard/assets",
    icon: Server,
    color: "text-yellow-500",
  },
  {
    title: "Security Incidents",
    href: "/dashboard/incidents",
    icon: Shield,
    color: "text-red-500",
  },
  {
    title: "Stealth Mode",
    href: "/dashboard/stealth",
    icon: Eye,
    color: "text-purple-500",
  },
  {
    title: "Defense Mode",
    href: "/dashboard/defense",
    icon: Shield,
    color: "text-blue-500",
  },
  {
    title: "Hunter Mode",
    href: "/dashboard/hunter",
    icon: Target,
    color: "text-red-500",
  },
]

const systemItems = [
  {
    title: "Supervisor & Health",
    href: "/dashboard/supervisor",
    icon: ShieldCheck,
    color: "text-blue-400",
  },
  {
    title: "System Logs",
    href: "/dashboard/logs",
    icon: FileText,
    color: "text-orange-400",
  },
  {
    title: "Agent Monitor",
    href: "/dashboard/agents",
    icon: Bot,
    color: "text-cyan-400",
  },
  {
    title: "Security",
    href: "/dashboard/security",
    icon: Lock,
    color: "text-green-400",
  },
  {
    title: "AI Security",
    href: "/dashboard/ai-security",
    icon: Brain,
    color: "text-pink-400",
  },
  {
    title: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
    color: "text-gray-400",
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = () => {
    localStorage.removeItem("token")
    router.push("/login")
  }

  return (
    <div className="flex flex-col h-full bg-black/50 backdrop-blur-xl border-r border-white/10 w-64">
      {/* Header */}
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-scout-neon/20 flex items-center justify-center ring-1 ring-scout-neon">
          <Shield className="w-4 h-4 text-scout-neon" />
        </div>
        <span className="font-bold text-xl tracking-wider text-white">SCOUT</span>
      </div>

      {/* Navigation */}
      <div className="flex-1 py-6 flex flex-col gap-1 px-4 overflow-y-auto">
        {/* Main Items */}
        {mainItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-sm font-medium",
              pathname === item.href
                ? "bg-white/10 text-white shadow-[0_0_10px_rgba(255,255,255,0.1)] border border-white/5"
                : "text-muted-foreground hover:bg-white/5 hover:text-white"
            )}
          >
            <item.icon className={cn("w-5 h-5", item.color)} />
            {item.title}
          </Link>
        ))}

        {/* Divider */}
        <div className="my-3 border-t border-white/10" />

        {/* System Items */}
        {systemItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-sm font-medium",
              pathname === item.href
                ? "bg-white/10 text-white shadow-[0_0_10px_rgba(255,255,255,0.1)] border border-white/5"
                : "text-muted-foreground hover:bg-white/5 hover:text-white"
            )}
          >
            <item.icon className={cn("w-5 h-5", item.color)} />
            {item.title}
          </Link>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/10">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors text-sm font-medium"
        >
          <LogOut className="w-5 h-5" />
          Sign Out
        </button>
      </div>
    </div>
  )
}
