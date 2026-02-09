"use client"

import { cn } from "@/lib/utils"

export type ProcessStep = {
  command: string
  output?: string
  status?: string
}

type ProcessOutputBlockProps = {
  /** List of steps (command + output). Rendered in order. */
  steps?: ProcessStep[]
  /** Single command (used when steps is empty). */
  command?: string
  /** Single output (used when steps is empty). */
  output?: string
  /** Optional title above the block. */
  title?: string
  className?: string
}

function SingleStep({ step, stepIndex, showStepLabel }: { step: ProcessStep; stepIndex: number; showStepLabel: boolean }) {
  const isSuccess = (step.status ?? "success").toLowerCase() === "success"
  return (
    <div className="flex flex-col gap-1">
      {showStepLabel && (
        <div className="text-[10px] font-semibold uppercase tracking-wider text-scout-neon/70">
          Step {stepIndex + 1}
        </div>
      )}
      <div className="flex items-center gap-2 font-mono text-sm">
        <span className="select-none text-scout-neon">$</span>
        <span className="text-foreground break-all">{step.command}</span>
        {step.status && (
          <span
            className={cn(
              "ml-auto shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium",
              isSuccess ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
            )}
          >
            {step.status}
          </span>
        )}
      </div>
      {step.output != null && step.output !== "" && (
        <pre className="mt-1 whitespace-pre-wrap break-words rounded border border-white/5 bg-black/40 px-3 py-2 font-mono text-xs text-muted-foreground">
          {step.output}
        </pre>
      )}
    </div>
  )
}

export default function ProcessOutputBlock({ steps, command, output, title, className }: ProcessOutputBlockProps) {
  const effectiveSteps: ProcessStep[] =
    steps?.length
      ? steps
      : command != null
        ? [{ command, output: output ?? "", status: "success" }]
        : []

  if (effectiveSteps.length === 0) return null

  const showStepLabels = effectiveSteps.length > 1

  return (
    <div
      className={cn(
        "rounded-lg border border-scout-border bg-scout-dark/80 font-mono text-sm shadow-sm",
        className
      )}
    >
      {title && (
        <div className="border-b border-scout-border px-4 py-2 text-xs font-semibold uppercase tracking-wider text-scout-neon/90">
          {title}
        </div>
      )}
      <div className="space-y-4 p-4">
        {effectiveSteps.map((step, i) => (
          <SingleStep key={i} step={step} stepIndex={i} showStepLabel={showStepLabels} />
        ))}
      </div>
    </div>
  )
}
