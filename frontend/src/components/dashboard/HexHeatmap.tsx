"use client"

import { useMemo } from "react"

/** UTC ISO string'i yerel saate çevirir; timezone yoksa Z ekleyerek UTC kabul eder. */
function formatUtcToLocal(iso: string | null | undefined): string {
  if (!iso || typeof iso !== "string") return ""
  const utcString = /Z$|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : iso + "Z"
  try {
    return new Date(utcString).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" })
  } catch {
    return iso
  }
}

/** Color scale: dark gray (low) -> red -> orange -> bright yellow (high). Matches reference heatmap spec. */
function colorForValue(t: number): string {
  if (t <= 0) return "rgb(55, 65, 81)" // gray-700
  if (t <= 0.33) {
    const s = t / 0.33
    return `rgb(${55 + (185 - 55) * s}, ${65 + (28 - 65) * s}, ${81 + (28 - 81) * s})` // gray -> red-700
  }
  if (t <= 0.66) {
    const s = (t - 0.33) / 0.33
    return `rgb(${185 + (234 - 185) * s}, ${28 + (88 - 28) * s}, ${28 + (32 - 28) * s})` // red -> orange
  }
  const s = (t - 0.66) / 0.34
  return `rgb(${234 + (234 - 234) * s}, ${88 + (179 - 88) * s}, ${32 + (8 - 32) * s})` // orange -> yellow
}

/** Flat-top hexagon: radius r, center (cx, cy). Returns path d. */
function hexPath(cx: number, cy: number, r: number): string {
  const points: [number, number][] = []
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 3) * i
    points.push([cx + r * Math.cos(a), cy + r * Math.sin(a)])
  }
  return `M ${points.map(([x, y]) => `${x},${y}`).join(" L ")} Z`
}

export interface HexHeatmapProps {
  /** Row labels (e.g. IPs or user ids) */
  rows: string[]
  /** Column labels (e.g. time bucket strings) */
  columns: string[]
  /** Get cell value for (rowKey, columnKey) */
  getValue: (rowKey: string, columnKey: string) => number
  /** Optional max value for scale; defaults to max cell value */
  maxValue?: number
  /** Hex radius in pixels */
  hexRadius?: number
  /** Class name for container */
  className?: string
  /** Show row labels on the left */
  showRowLabels?: boolean
  /** Show column labels on top */
  showColumnLabels?: boolean
}

export function HexHeatmap({
  rows,
  columns,
  getValue,
  maxValue: maxValProp,
  hexRadius = 10,
  className = "",
  showRowLabels = true,
  showColumnLabels = true,
}: HexHeatmapProps) {
  const { width, height, cells, maxValue, rowHeight } = useMemo(() => {
    const r = hexRadius
    const w = 2 * r
    const h = Math.sqrt(3) * r
    const colWidth = w * 0.75
    const rowH = h
    const cols = columns.length
    const rowsCount = rows.length
    const pad = 2
    const cells: { row: number; col: number; cx: number; cy: number; value: number; t: number }[] = []
    let maxValue = 0
    for (let i = 0; i < rowsCount; i++) {
      for (let j = 0; j < cols; j++) {
        const value = getValue(rows[i], columns[j])
        if (value > maxValue) maxValue = value
        const cx = pad + r + j * colWidth
        const cy = pad + r + i * rowH + (j % 2) * (rowH / 2)
        cells.push({ row: i, col: j, cx, cy, value, t: 0 })
      }
    }
    const max = maxValProp ?? Math.max(maxValue, 1)
    cells.forEach((c) => {
      c.t = max ? c.value / max : 0
    })
    const width = pad * 2 + (cols > 0 ? (cols - 1) * colWidth + w : 0)
    const height = pad * 2 + (rowsCount > 0 ? (rowsCount - 1) * rowH + h + (cols > 1 ? rowH / 2 : 0) : 0)
    return { width, height, cells, maxValue: max, rowHeight: rowH }
  }, [rows, columns, getValue, hexRadius, maxValProp])

  if (rows.length === 0 || columns.length === 0) {
    return (
      <div className={`flex items-center justify-center text-muted-foreground py-8 ${className}`}>
        Veri yok
      </div>
    )
  }

  const labelWidth = showRowLabels ? 100 : 0
  const labelHeight = showColumnLabels ? 24 : 0

  return (
    <div className={`overflow-x-auto overflow-y-auto ${className}`}>
      {showColumnLabels && (
        <div className="flex gap-0.5 pl-[100px] pb-1 text-xs text-muted-foreground">
          {columns.slice(0, 24).map((b, j) => (
            <div key={b} className="w-5 text-center truncate" title={b}>
              {formatUtcToLocal(b)}
            </div>
          ))}
        </div>
      )}
      <div className="flex">
        {showRowLabels && (
          <div className="shrink-0 w-[100px] pr-2 text-xs text-muted-foreground font-mono flex flex-col">
            {rows.slice(0, 20).map((ip, i) => (
              <div
                key={ip}
                className="truncate flex items-center"
                style={{ height: rowHeight }}
                title={ip}
              >
                {ip}
              </div>
            ))}
          </div>
        )}
        <svg
          width={width}
          height={height}
          className="shrink-0"
          style={{ minWidth: width, minHeight: height }}
        >
          {cells.map((cell, idx) => (
            <path
              key={idx}
              d={hexPath(cell.cx, cell.cy, hexRadius - 0.5)}
              fill={colorForValue(cell.t)}
              stroke="rgba(0,0,0,0.2)"
              strokeWidth="0.5"
            >
              <title>{`${rows[cell.row]} @ ${columns[cell.col]}: ${cell.value}`}</title>
            </path>
          ))}
        </svg>
      </div>
    </div>
  )
}
