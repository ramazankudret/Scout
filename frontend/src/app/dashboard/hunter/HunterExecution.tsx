"use client"

import ProcessOutputBlock from "@/components/dashboard/ProcessOutputBlock"

type Step = { command?: string; output?: string; status?: string }

export function HunterExecution({
    steps,
    command,
    process_output,
}: {
    steps?: Step[]
    command?: string
    process_output?: string
}) {
    if (!steps?.length && !command) return null
    return (
        <ProcessOutputBlock
            title="Execution"
            steps={steps ?? []}
            command={command ?? ""}
            output={process_output}
        />
    )
}
