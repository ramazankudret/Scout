"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"
import api from "@/services/api"
import { modulesApi } from "@/services/modules"

const MIN_WIDTH = 320
const MIN_HEIGHT = 300
const MAX_WIDTH_PCT = 90
const MAX_HEIGHT_PCT = 80
const DEFAULT_WIDTH = 380
const DEFAULT_HEIGHT = 420
const FAB_SIZE = 56

const IP_OR_CIDR_REGEX = /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:\/\d{1,2})?/
const SCAN_KEYWORDS = /\b(tara|scan|tarama|hunter)\b/i

function parseHunterScanIntent(text: string): string | null {
    const lower = text.toLowerCase().trim()
    if (!SCAN_KEYWORDS.test(lower)) return null
    const match = text.match(IP_OR_CIDR_REGEX)
    return match ? match[0] : null
}

type Message = { role: "user" | "assistant"; content: string; agent?: string }

export function ScoutChatWidget() {
    const [open, setOpen] = useState(false)
    const [width, setWidth] = useState(DEFAULT_WIDTH)
    const [height, setHeight] = useState(DEFAULT_HEIGHT)
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState("")
    const [loading, setLoading] = useState(false)
    const [models, setModels] = useState<string[]>([])
    const [selectedModel, setSelectedModel] = useState<string>("")
    const [modelsLoaded, setModelsLoaded] = useState(false)
    const [includeContext, setIncludeContext] = useState(false)
    const [chatMode, setChatMode] = useState<"normal" | "agent">("normal")
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const panelRef = useRef<HTMLDivElement>(null)
    const resizeStartRef = useRef<{ x: number; y: number; w: number; h: number } | null>(null)

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [])

    useEffect(() => {
        if (open && messages.length) scrollToBottom()
    }, [open, messages, scrollToBottom])

    useEffect(() => {
        if (!open) return
        let cancelled = false
        ;(async () => {
            try {
                const { data } = await api.get("/llm/health")
                if (cancelled) return
                const list = (data?.available_models as string[]) ?? []
                setModels(list)
                if (list.length && !selectedModel) setSelectedModel(list[0])
                setModelsLoaded(true)
            } catch {
                if (!cancelled) setModelsLoaded(true)
            }
        })()
        return () => { cancelled = true }
    }, [open])

    const send = useCallback(async () => {
        const text = input.trim()
        if (!text || loading) return
        setInput("")
        setMessages((m) => [...m, { role: "user", content: text }])
        setLoading(true)
        try {
            if (chatMode === "agent") {
                const { data } = await api.post("/agent/chat", { message: text }, { timeoutMs: 60000 })
                const response = (data?.response as string) ?? "No response."
                const currentAgent = (data?.current_agent as string) ?? "end"
                const agentLabel = currentAgent === "end" ? "Orchestrator" : currentAgent.charAt(0).toUpperCase() + currentAgent.slice(1)
                setMessages((m) => [...m, { role: "assistant", content: response, agent: agentLabel }])
                setLoading(false)
                return
            }
            const scanTarget = parseHunterScanIntent(text)
            if (scanTarget) {
                const result = await modulesApi.execute("hunter", "active", { target: scanTarget })
                if (result?.data?.error) {
                    setMessages((m) => [...m, { role: "assistant", content: `Tarama başlatıldı ancak hata: ${result.data.error}` }])
                } else {
                    const openPorts = result?.data?.open_ports?.length ?? 0
                    const scanResults = result?.data?.scan_results?.length
                    let summary = `Tarama başlatıldı: ${scanTarget}. `
                    if (scanResults != null && scanResults > 0) {
                        summary += `${scanResults} host taranan toplu tarama. Sonuçları Hunter sayfasından görebilirsiniz.`
                    } else if (openPorts > 0) {
                        summary += `${openPorts} açık port bulundu. Hunter sayfasından detaylara bakabilirsiniz.`
                    } else {
                        summary += "Sonuçları Hunter sayfasından görebilirsiniz."
                    }
                    setMessages((m) => [...m, { role: "assistant", content: summary }])
                }
                setLoading(false)
                return
            }
            const { data } = await api.post("/llm/chat", {
                message: text,
                model: selectedModel || undefined,
                task_hint: includeContext ? "analysis" : undefined,
            }, { timeoutMs: 120000 })
            const reply = (data?.response as string) ?? "No response."
            setMessages((m) => [...m, { role: "assistant", content: reply }])
        } catch (e) {
            const err = e instanceof Error ? e.message : "Request failed"
            setMessages((m) => [...m, { role: "assistant", content: `Error: ${err}` }])
        } finally {
            setLoading(false)
        }
    }, [input, loading, selectedModel, includeContext, chatMode])

    const handleResizeStart = useCallback(
        (e: React.MouseEvent) => {
            e.preventDefault()
            resizeStartRef.current = { x: e.clientX, y: e.clientY, w: width, h: height }
        },
        [width, height]
    )

    useEffect(() => {
        if (!resizeStartRef.current) return
        const onMove = (e: MouseEvent) => {
            const start = resizeStartRef.current
            if (!start) return
            const dx = e.clientX - start.x
            const dy = e.clientY - start.y
            const maxW = Math.min(window.innerWidth * (MAX_WIDTH_PCT / 100), 1200)
            const maxH = Math.min(window.innerHeight * (MAX_HEIGHT_PCT / 100), 900)
            setWidth((w) => Math.min(maxW, Math.max(MIN_WIDTH, start.w + dx)))
            setHeight((h) => Math.min(maxH, Math.max(MIN_HEIGHT, start.h + dy)))
        }
        const onUp = () => { resizeStartRef.current = null }
        window.addEventListener("mousemove", onMove)
        window.addEventListener("mouseup", onUp)
        return () => {
            window.removeEventListener("mousemove", onMove)
            window.removeEventListener("mouseup", onUp)
        }
    }, [])

    if (!open) {
        return (
            <button
                type="button"
                onClick={() => setOpen(true)}
                className={cn(
                    "fixed z-50 flex items-center justify-center rounded-lg shadow-lg border border-border bg-card text-card-foreground hover:bg-accent/80 transition-colors",
                    "right-4 bottom-4"
                )}
                style={{ width: FAB_SIZE, height: FAB_SIZE }}
                aria-label="Open Scout AI chat"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z" />
                </svg>
            </button>
        )
    }

    return (
        <div
            ref={panelRef}
            className="fixed z-50 flex flex-col rounded-lg border border-border bg-card text-card-foreground shadow-xl right-4 bottom-4"
            style={{
                width: `${width}px`,
                height: `${height}px`,
                minWidth: MIN_WIDTH,
                minHeight: MIN_HEIGHT,
                maxWidth: "90vw",
                maxHeight: "80vh",
            }}
        >
            {/* Header */}
            <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-border shrink-0">
                <span className="font-semibold text-sm truncate">Scout AI</span>
                <div className="flex items-center gap-2 min-w-0">
                    <select
                        value={chatMode}
                        onChange={(e) => setChatMode(e.target.value as "normal" | "agent")}
                        className="h-8 min-w-0 max-w-[100px] rounded border border-input bg-background px-2 text-xs"
                        title="Chat mode"
                    >
                        <option value="normal">LLM</option>
                        <option value="agent">Ajan</option>
                    </select>
                    {chatMode === "normal" && (
                        <select
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            className="h-8 min-w-0 max-w-[140px] rounded border border-input bg-background px-2 text-xs"
                            title="Model"
                        >
                            {!modelsLoaded && <option value="">Loading...</option>}
                            {models.length === 0 && modelsLoaded && <option value="">No models</option>}
                            {models.map((m) => (
                                <option key={m} value={m}>{m}</option>
                            ))}
                        </select>
                    )}
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 shrink-0"
                        onClick={() => setOpen(false)}
                        aria-label="Close chat"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12" /></svg>
                    </Button>
                </div>
            </div>

            {/* Analiz modu: verileri dahil et (sadece LLM modunda) */}
            {chatMode === "normal" && (
                <div className="flex items-center gap-2 px-3 py-2 border-b border-border shrink-0">
                    <Switch
                        id="chat-include-context"
                        checked={includeContext}
                        onCheckedChange={setIncludeContext}
                    />
                    <label htmlFor="chat-include-context" className="text-xs text-muted-foreground cursor-pointer">
                        Verileri dahil et (trafik / tarama / asset özeti)
                    </label>
                </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm">
                {messages.length === 0 && (
                    <p className="text-muted-foreground text-center py-4">
                        {chatMode === "agent"
                            ? "Ajan modu: Orchestrator, Hunter, Stealth veya Defense ile konuşun."
                            : "Ask Scout anything. Choose a model above."}
                    </p>
                )}
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={cn(
                            "rounded-lg px-3 py-2 max-w-[85%]",
                            msg.role === "user"
                                ? "ml-auto bg-primary text-primary-foreground"
                                : "mr-auto bg-muted"
                        )}
                    >
                        <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                        {msg.role === "assistant" && msg.agent && (
                            <div className="text-[10px] text-muted-foreground mt-1">— {msg.agent}</div>
                        )}
                    </div>
                ))}
                {loading && (
                    <div className="mr-auto rounded-lg px-3 py-2 bg-muted max-w-[85%]">
                        <span className="animate-pulse">...</span>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="flex gap-2 p-2 border-t border-border shrink-0">
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())}
                    placeholder="Message..."
                    disabled={loading}
                    className="min-w-0"
                />
                <Button type="button" onClick={send} disabled={loading || !input.trim()} size="sm">
                    Send
                </Button>
            </div>

            {/* Resize handle */}
            <div
                role="separator"
                className="absolute right-0 bottom-0 w-4 h-4 cursor-se-resize"
                style={{ margin: "-2px -2px 0 0" }}
                onMouseDown={handleResizeStart}
            >
                <svg className="absolute right-1 bottom-1 w-3 h-3 text-muted-foreground/60" viewBox="0 0 24 24" fill="currentColor"><path d="M16 16v-4h4v4h-4zm-6 0v-4h4v4h-4zm-6 0v-4h4v4H4z" /></svg>
            </div>
        </div>
    )
}
