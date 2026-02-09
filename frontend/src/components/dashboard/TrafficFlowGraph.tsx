"use client"

import { useMemo, useRef, useState, useEffect } from "react"
import dynamic from "next/dynamic"

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false })

export interface TrafficFlowEdge {
  source: string
  destination: string
  packet_count?: number
}

interface TrafficFlowGraphProps {
  nodes: string[]
  edges: TrafficFlowEdge[]
  className?: string
  height?: number
}

export function TrafficFlowGraph({ nodes, edges, className = "", height = 280 }: TrafficFlowGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 400, height })

  useEffect(() => {
    setDimensions((d) => ({ ...d, height }))
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver((entries) => {
      const { width } = entries[0]?.contentRect ?? {}
      if (width) setDimensions((prev) => ({ ...prev, width }))
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [height])

  const graphData = useMemo(() => {
    const nodeIds = new Set<string>(nodes)
    edges.forEach((e) => {
      nodeIds.add(e.source)
      nodeIds.add(e.destination)
    })
    const nodeList = Array.from(nodeIds).map((id) => ({ id, label: id }))
    const linkList = edges.map((e) => ({
      source: e.source,
      target: e.destination,
      value: e.packet_count ?? 1,
    }))
    return { nodes: nodeList, links: linkList }
  }, [nodes, edges])

  const maxCount = edges.length ? Math.max(...edges.map((e) => e.packet_count ?? 1), 1) : 1
  const sortedByValue = useMemo(
    () => [...graphData.links].sort((a, b) => (b.value ?? 0) - (a.value ?? 0)),
    [graphData.links]
  )
  const redThresholdIndex = Math.max(0, Math.floor(sortedByValue.length * 0.15))
  const redThresholdValue = sortedByValue[redThresholdIndex]?.value ?? maxCount
  const isRedLink = (link: { value?: number }) => (link.value ?? 0) >= redThresholdValue && redThresholdValue > 0

  if (graphData.nodes.length === 0) {
    return (
      <div
        className={`flex items-center justify-center text-muted-foreground ${className}`}
        style={{ height }}
      >
        Start Capture to see flow
      </div>
    )
  }

  return (
    <div ref={containerRef} className={`[&_canvas]:border-0 [&_canvas]:outline-none ${className}`} style={{ height }}>
      <ForceGraph2D
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="transparent"
        nodeLabel="label"
        nodeColor={() => "rgba(255, 255, 255, 0.98)"}
        nodeVal={(n: { id?: string }) => {
          const out = edges.filter((e) => e.source === (n as { id: string }).id).length
          const in_ = edges.filter((e) => e.destination === (n as { id: string }).id).length
          return 2 + Math.min(8, (out + in_) * 2)
        }}
        linkCurvature={0.35}
        linkColor={(link: { value?: number }) => {
          const v = link.value ?? 0
          const t = maxCount ? v / maxCount : 0
          if (isRedLink(link)) return `rgba(239, 68, 68, ${0.6 + t * 0.35})`
          return `rgba(255, 255, 255, ${0.25 + t * 0.65})`
        }}
        linkWidth={(link: { value?: number }) => {
          const t = maxCount ? (link.value ?? 0) / maxCount : 0
          return Math.max(0.6, 1 + t * 3.5)
        }}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.015}
        linkDirectionalParticleWidth={(link: { value?: number }) => (maxCount ? 0.8 + ((link.value ?? 0) / maxCount) * 1.2 : 1)}
        linkDirectionalParticleColor={(link: { value?: number }) => (isRedLink(link) ? "rgba(239, 68, 68, 0.7)" : "rgba(255, 255, 255, 0.5)")}
      />
    </div>
  )
}
