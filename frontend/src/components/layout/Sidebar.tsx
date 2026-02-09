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
    <div className="flex flex-col h-full bg-scout-panel/95 backdrop-blur-xl border-r border-scout-border w-56 shrink-0">
      <div className="px-4 py-4 flex items-center gap-2.5 border-b border-scout-border/80">
        <div className="w-7 h-7 rounded-md bg-scout-primary/15 flex items-center justify-center ring-1 ring-scout-primary/40">
          <Shield className="w-3.5 h-3.5 text-scout-primary" />
        </div>
        <span className="font-mono font-bold text-sm tracking-widest text-foreground">SCOUT</span>
      </div>

      <div className="flex-1 py-3 flex flex-col gap-0 px-2 overflow-y-auto">
        {navGroups.map((group) => {
          const isOpen = openGroups[group.label] ?? false
          const GroupIcon = group.icon
          return (
            <div key={group.label} className="mb-1">
              <button
                type="button"
                onClick={() => toggleGroup(group.label)}
                className={cn(
                  "flex items-center gap-2 w-full px-2.5 py-2 rounded-md text-left text-xs font-medium transition-colors",
                  "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                )}
              >
                {isOpen ? (
                  <ChevronDown className="w-3.5 h-3.5 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5 flex-shrink-0" />
                )}
                <GroupIcon className="w-3.5 h-3.5 flex-shrink-0 text-scout-primary/80" />
                <span>{group.label}</span>
              </button>
              {isOpen && (
                <div className="ml-3 mt-0.5 space-y-0.5 border-l border-scout-border/80 pl-2">
                  {group.items.map((item) => (
                    <Link
                      key={item.href + item.title}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-2.5 px-2.5 py-1.5 rounded-md transition-all text-xs font-medium",
                        pathname === item.href
                          ? "bg-scout-primary/10 text-foreground border border-scout-primary/30"
                          : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                      )}
                    >
                      <item.icon className={cn("w-3.5 h-3.5 flex-shrink-0", item.color)} />
                      {item.title}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="p-3 border-t border-scout-border/80">
        <button
          onClick={handleLogout}
          className="flex items-center gap-2.5 px-3 py-2.5 w-full rounded-md text-scout-danger hover:bg-scout-danger/10 transition-colors text-xs font-medium"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </div>
  )
}
