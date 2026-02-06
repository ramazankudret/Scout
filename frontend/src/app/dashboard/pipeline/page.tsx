"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import PipelineViz from "@/components/dashboard/PipelineViz"
import Link from "next/link"

export default function PipelinePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Pipeline</h1>
          <p className="text-muted-foreground">
            Agent workflow: Orchestrator → Hunter, Stealth, Defense
          </p>
        </div>
        <Link
          href="/dashboard"
          className="text-sm text-scout-neon hover:underline"
        >
          Back to Dashboard
        </Link>
      </div>

      <Card className="border-white/10 bg-black/40">
        <CardHeader>
          <CardTitle>Pipeline Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="min-h-[280px] flex items-center justify-center">
            <div className="w-full max-w-2xl">
              <PipelineViz />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
