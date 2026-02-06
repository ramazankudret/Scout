"use client"

import {
  Activity,
  Shield,
  Target,
  LogOut,
  Settings,
  Eye,
  FileText,
  Bot,
  Lock,
  Brain,
  Server,
  CheckSquare,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  Crosshair,
  Ghost,
  ShieldAlert,
  AlertTriangle,
  Workflow,
  BarChart3,
  Users,
  ScrollText,
  Bell,
} from "lucide-react"
import Link from "next/link"
import { useRouter, usePathname } from "next/navigation"
import { useState } from "react"
import { cn } from "@/lib/utils"

type NavItem = {
  title: string
  href: string
  icon: React.ElementType
  color: string
}

type NavGroup = {
  label: string
  icon: React.ElementType
  items: NavItem[]
}

const navGroups: NavGroup[] = [
  {
    label: "Command Center",
    icon: Activity,
    items: [
      { title: "Dashboard", href: "/dashboard", icon: Activity, color: "text-scout-primary" },
      { title: "Grafikler", href: "/dashboard/charts", icon: BarChart3, color: "text-scout-accent" },
    ],
  },
  {
    label: "Operations",
    icon: Target,
    items: [
      { title: "Hunter", href: "/dashboard/hunter", icon: Crosshair, color: "text-scout-danger" },
      { title: "Stealth", href: "/dashboard/stealth", icon: Ghost, color: "text-purple-500" },
      { title: "Defense", href: "/dashboard/defense", icon: ShieldAlert, color: "text-scout-accent" },
      { title: "Approvals", href: "/dashboard/approvals", icon: CheckSquare, color: "text-scout-warning" },
    ],
  },
  {
    label: "Intelligence",
    icon: Eye,
    items: [
      { title: "Assets", href: "/dashboard/assets", icon: Server, color: "text-scout-warning" },
      { title: "Incidents", href: "/dashboard/incidents", icon: Shield, color: "text-scout-danger" },
      { title: "Tarama Geçmişi", href: "/dashboard/scans", icon: Crosshair, color: "text-scout-danger" },
      { title: "Trafik", href: "/dashboard/traffic", icon: Ghost, color: "text-purple-500" },
      { title: "Threats", href: "/dashboard/incidents", icon: AlertTriangle, color: "text-amber-500" },
    ],
  },
  {
    label: "System",
    icon: Bot,
    items: [
      { title: "Supervisor", href: "/dashboard/supervisor", icon: ShieldCheck, color: "text-scout-accent" },
      { title: "Agents", href: "/dashboard/agents", icon: Bot, color: "text-scout-primary" },
      { title: "Pipeline", href: "/dashboard/pipeline", icon: Workflow, color: "text-scout-primary" },
      { title: "Sistem Logları", href: "/dashboard/logs", icon: ScrollText, color: "text-scout-warning" },
      { title: "Bildirimler", href: "/dashboard/notifications", icon: Bell, color: "text-scout-accent" },
      { title: "Kullanıcı Yönetimi", href: "/dashboard/users", icon: Users, color: "text-scout-success" },
      { title: "Security", href: "/dashboard/security", icon: Lock, color: "text-scout-success" },
      { title: "AI Security", href: "/dashboard/ai-security", icon: Brain, color: "text-pink-400" },
      { title: "Settings", href: "/dashboard/settings", icon: Settings, color: "text-scout-muted" },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
    "Command Center": true,
    Operations: true,
    Intelligence: true,
    System: false,
  })

  const toggleGroup = (label: string) => {
    setOpenGroups((prev) => ({ ...prev, [label]: !prev[label] }))
  }

  const handleLogout = () => {
    localStorage.removeItem("token")
    router.push("/login")
  }

  return (
    <div className="flex flex-col h-full bg-scout-panel backdrop-blur-xl border-r border-scout-border w-64">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-scout-primary/15 flex items-center justify-center ring-1 ring-scout-primary/50">
          <Shield className="w-4 h-4 text-scout-primary" />
        </div>
        <span className="font-mono font-bold text-xl tracking-wider text-foreground">SCOUT</span>
      </div>

      <div className="flex-1 py-4 flex flex-col gap-0 px-3 overflow-y-auto">
        {navGroups.map((group) => {
          const isOpen = openGroups[group.label] ?? false
          const GroupIcon = group.icon
          return (
            <div key={group.label} className="mb-1">
              <button
                type="button"
                onClick={() => toggleGroup(group.label)}
                className={cn(
                  "flex items-center gap-2 w-full px-3 py-2.5 rounded-lg text-left text-sm font-medium transition-colors",
                  "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                )}
              >
                {isOpen ? (
                  <ChevronDown className="w-4 h-4 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 flex-shrink-0" />
                )}
                <GroupIcon className="w-4 h-4 flex-shrink-0 text-scout-primary/80" />
                <span>{group.label}</span>
              </button>
              {isOpen && (
                <div className="ml-4 mt-0.5 space-y-0.5 border-l border-scout-border pl-2">
                  {group.items.map((item) => (
                    <Link
                      key={item.href + item.title}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 rounded-md transition-all text-sm font-medium",
                        pathname === item.href
                          ? "bg-scout-primary/10 text-foreground border border-scout-primary/30"
                          : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                      )}
                    >
                      <item.icon className={cn("w-4 h-4 flex-shrink-0", item.color)} />
                      {item.title}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="p-4 border-t border-scout-border">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-scout-danger hover:bg-scout-danger/10 transition-colors text-sm font-medium"
        >
          <LogOut className="w-5 h-5" />
          Sign Out
        </button>
      </div>
    </div>
  )
}
