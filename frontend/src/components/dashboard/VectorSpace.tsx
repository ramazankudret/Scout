"use client"

import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls, Line, Html, Stars } from "@react-three/drei"
import { EffectComposer, Bloom, Vignette } from "@react-three/postprocessing"
import { BlendFunction } from "postprocessing"
import { useRef, useMemo, useState, useLayoutEffect } from "react"
import * as THREE from "three"
import { useQuery } from "@tanstack/react-query"
import { assetsApi, topologyApi, type Asset, type TopologyNode, type TopologyEdge, type TopologyThreat } from "@/lib/api/client"

export type NetworkNode = {
  id: string
  position: THREE.Vector3
  isAnomaly: boolean
  category: string
  data: {
    ip: string
    hostname: string
    deviceType: string
    status: string
    os: string
    lastSeen: string
    openPorts: number
    threatLevel: string
    subnet: string
  }
}

// Zone layout by asset type (category)
const ASSET_ZONES: Record<string, { x: number; y: number; z: number; radius: number }> = {
  server: { x: 5, y: 0, z: 0, radius: 2.5 },
  workstation: { x: -5, y: 0, z: 0, radius: 2.5 },
  host: { x: 0, y: 0, z: 2, radius: 2 },
  ip: { x: 0, y: 0, z: 0, radius: 2 },
  network: { x: 0, y: 0, z: 0, radius: 1.5 },
  router: { x: 0, y: 0, z: 0, radius: 0.8 },
  firewall: { x: 0, y: 1.5, z: 0, radius: 0.8 },
  database: { x: 0, y: -4, z: 0, radius: 1.5 },
  iot: { x: 0, y: 4, z: 4, radius: 2 },
  default: { x: 0, y: 0, z: 0, radius: 2 },
}

function parseSubnet(value: string): string {
  const ipMatch = value.match(/(\d{1,3}\.\d{1,3}\.\d{1,3})\.?\d*/)
  if (ipMatch) return ipMatch[1]
  return "0.0.0"
}

function hashId(id: string): number {
  let h = 0
  for (let i = 0; i < id.length; i++) h = ((h << 5) - h) + id.charCodeAt(i) | 0
  return Math.abs(h) / 2147483647
}

function assetsToNodes(assets: Asset[]): NetworkNode[] {
  const byType: Record<string, number> = {}
  return assets.map((asset, index) => {
    const category = (asset.asset_type || "default").toLowerCase()
    const zone = ASSET_ZONES[category] ?? ASSET_ZONES.default
    byType[category] = (byType[category] ?? 0) + 1
    const i = byType[category] - 1
    const count = byType[category]
    const angle = (i / Math.max(1, count)) * Math.PI * 2 + hashId(asset.id) * 0.5
    const dist = zone.radius * (0.4 + (index % 3) * 0.2)
    const x = zone.x + Math.cos(angle) * dist
    const y = zone.y + (hashId(asset.id + "y") - 0.5) * 1
    const z = zone.z + Math.sin(angle) * dist

    const subnet = parseSubnet(asset.value)
    const isAnomaly = asset.risk_score >= 70 || asset.status === "critical" || asset.vulnerability_count > 0
    const threatLevel = asset.risk_score >= 80 ? "HIGH" : asset.risk_score >= 50 ? "MEDIUM" : "LOW"

    return {
      id: asset.id,
      position: new THREE.Vector3(x, y, z),
      isAnomaly,
      category: asset.asset_type || "Asset",
      data: {
        ip: asset.value,
        hostname: asset.label || asset.value,
        deviceType: asset.asset_type || "host",
        status: asset.status || "unknown",
        os: asset.environment || "—",
        lastSeen: "—",
        openPorts: asset.open_ports?.length ?? 0,
        threatLevel,
        subnet,
      },
    }
  })
}

const SCOUT_ONLY_NODES: NetworkNode[] = [
  {
    id: "scout",
    position: new THREE.Vector3(0, 0, 0),
    isAnomaly: false,
    category: "Scout",
    data: {
      ip: "",
      hostname: "Scout",
      deviceType: "Scout",
      status: "online",
      os: "—",
      lastSeen: "—",
      openPorts: 0,
      threatLevel: "LOW",
      subnet: "0.0.0",
    },
  },
]

function topologyNodesToNetworkNodes(topologyNodes: TopologyNode[]): NetworkNode[] {
  const byType: Record<string, number> = {}
  const origin = new THREE.Vector3(0, 0, 0)

  return topologyNodes.map((n, index) => {
    if (n.is_scout) {
      return {
        id: "scout",
        position: origin.clone(),
        isAnomaly: false,
        category: "Scout",
        data: {
          ip: "",
          hostname: "Scout",
          deviceType: "Scout",
          status: "online",
          os: "—",
          lastSeen: "—",
          openPorts: 0,
          threatLevel: "LOW",
          subnet: "0.0.0",
        },
      }
    }

    const category = (n.asset_type || "ip").toLowerCase()
    const zone = ASSET_ZONES[category] ?? ASSET_ZONES.default
    byType[category] = (byType[category] ?? 0) + 1
    const i = byType[category] - 1
    const count = byType[category]
    const angle = (i / Math.max(1, count)) * Math.PI * 2 + hashId(n.id) * 0.5
    const dist = zone.radius * (0.4 + (index % 3) * 0.2)
    const x = zone.x + Math.cos(angle) * dist
    const y = zone.y + (hashId(n.id + "y") - 0.5) * 1
    const z = zone.z + Math.sin(angle) * dist

    const subnet = parseSubnet(n.value)
    const isAnomaly = n.risk_score >= 70 || n.status === "critical" || (n.open_ports?.length ?? 0) > 0
    const threatLevel = n.risk_score >= 80 ? "HIGH" : n.risk_score >= 50 ? "MEDIUM" : "LOW"

    return {
      id: n.id,
      position: new THREE.Vector3(x, y, z),
      isAnomaly,
      category: n.asset_type || "Asset",
      data: {
        ip: n.value,
        hostname: n.label || n.value,
        deviceType: n.asset_type || "host",
        status: n.status || "unknown",
        os: "—",
        lastSeen: "—",
        openPorts: n.open_ports?.length ?? 0,
        threatLevel,
        subnet,
      },
    }
  })
}

// --- Fallback mock nodes when no assets ---
const generateMockNodes = (): NetworkNode[] => {
  const nodes: NetworkNode[] = []

  // Define network zones (subnets) - spread wider with fewer nodes
  const categories = [
    { name: "Server", subnet: "192.168.10", count: 8, zone: { x: 5, y: 0, z: 0 }, radius: 2.5, os: ["Ubuntu 22.04", "Windows Server 2022", "RHEL 8"] },
    { name: "Workstation", subnet: "192.168.20", count: 8, zone: { x: -5, y: 0, z: 0 }, radius: 2.5, os: ["Windows 11", "macOS 14", "Ubuntu Desktop"] },
    { name: "Router", subnet: "192.168.1", count: 3, zone: { x: 0, y: 0, z: 0 }, radius: 0.8, os: ["Cisco IOS", "pfSense"] },
    { name: "Firewall", subnet: "192.168.1", count: 2, zone: { x: 0, y: 1.5, z: 0 }, radius: 0.8, os: ["pfSense", "Fortinet"] },
    { name: "IoT Device", subnet: "192.168.30", count: 6, zone: { x: 0, y: 4, z: 4 }, radius: 2, os: ["Embedded Linux", "Custom"] },
    { name: "Database", subnet: "192.168.50", count: 3, zone: { x: 0, y: -4, z: 0 }, radius: 1.5, os: ["PostgreSQL", "MySQL", "MongoDB"] },
  ]

  let nodeIndex = 0

  categories.forEach(cat => {
    for (let i = 0; i < cat.count; i++) {
      const angle = (i / cat.count) * Math.PI * 2 + Math.random() * 0.3
      const dist = cat.radius * (0.5 + Math.random() * 0.5)

      const x = cat.zone.x + Math.cos(angle) * dist
      const y = cat.zone.y + (Math.random() - 0.5) * 1
      const z = cat.zone.z + Math.sin(angle) * dist

      const isAnomaly = Math.random() < 0.08

      nodes.push({
        id: `node-${nodeIndex}`,
        position: new THREE.Vector3(x, y, z),
        isAnomaly,
        category: cat.name,
        data: {
          ip: `${cat.subnet}.${10 + i}`,
          hostname: `${cat.name.toLowerCase()}-${String(i + 1).padStart(2, '0')}`,
          deviceType: cat.name,
          status: isAnomaly ? (Math.random() > 0.5 ? "Critical" : "Warning") : "Online",
          os: cat.os[Math.floor(Math.random() * cat.os.length)],
          lastSeen: `${Math.floor(Math.random() * 60)}s ago`,
          openPorts: cat.name === "Server" ? Math.floor(Math.random() * 15) + 5 : Math.floor(Math.random() * 5) + 1,
          threatLevel: isAnomaly ? (Math.random() > 0.5 ? "HIGH" : "MEDIUM") : "LOW",
          subnet: cat.subnet,
        }
      })
      nodeIndex++
    }
  })

  return nodes
}

// --- Single Clickable Node ---
function NetworkNode({ node, isSelected, onClick }: {
  node: NetworkNode
  isSelected: boolean
  onClick: () => void
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [hovered, setHovered] = useState(false)

  useFrame((state) => {
    if (meshRef.current) {
      if (node.isAnomaly) {
        const scale = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.2
        meshRef.current.scale.setScalar(scale)
      }
      if (hovered || isSelected) {
        meshRef.current.scale.lerp(new THREE.Vector3(1.5, 1.5, 1.5), 0.1)
      } else if (!node.isAnomaly) {
        meshRef.current.scale.lerp(new THREE.Vector3(1, 1, 1), 0.1)
      }
    }
  })

  const color = useMemo(() => {
    if (node.isAnomaly) return "#ff0055"
    if (node.data.status === "Warning") return "#ffaa00"
    return "#00f3ff"
  }, [node])

  return (
    <group position={node.position}>
      <mesh
        ref={meshRef}
        onClick={(e) => { e.stopPropagation(); onClick() }}
        onPointerOver={(e) => { e.stopPropagation(); setHovered(true); document.body.style.cursor = 'pointer' }}
        onPointerOut={() => { setHovered(false); document.body.style.cursor = 'auto' }}
      >
        <sphereGeometry args={[node.isAnomaly ? 0.18 : 0.08, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isSelected ? 6 : (hovered ? 3.5 : (node.isAnomaly ? 2.2 : 0.6))}
          metalness={0.15}
          roughness={0.7}
          toneMapped={false}
        />
      </mesh>

      {(hovered || isSelected) && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.28, 0.34, 32]} />
          <meshBasicMaterial color={color} transparent opacity={hovered || isSelected ? 0.7 : 0.5} side={THREE.DoubleSide} />
        </mesh>
      )}

      {hovered && !isSelected && (
        <Html center distanceFactor={8} style={{ pointerEvents: 'none' }}>
          <div className="bg-black/90 border border-scout-neon/50 px-2 py-1.5 rounded text-xs text-scout-neon font-mono whitespace-nowrap backdrop-blur-sm shadow-lg">
            <div className="font-semibold">{node.data.hostname || node.data.ip}</div>
            {node.data.ip && <div className="text-scout-neon/70 text-[10px]">{node.data.ip}</div>}
            <div className="text-scout-neon/60 text-[10px]">{node.data.deviceType} · {node.data.status}</div>
          </div>
        </Html>
      )}
    </group>
  )
}

// --- Core Sphere (tech wireframe + orbit ring + inner glow) ---
function CoreSphere() {
  const meshRef = useRef<THREE.Mesh>(null)
  const glowRef = useRef<THREE.Mesh>(null)
  const ringRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    const t = state.clock.elapsedTime
    if (meshRef.current) {
      meshRef.current.rotation.y = t * 0.15
      meshRef.current.rotation.x = Math.sin(t * 0.3) * 0.12
    }
    if (glowRef.current) {
      const pulse = 1 + Math.sin(t * 0.8) * 0.12
      glowRef.current.scale.setScalar(pulse)
    }
    if (ringRef.current) {
      ringRef.current.rotation.x = Math.PI / 2
      ringRef.current.rotation.z = t * 0.2
    }
  })

  return (
    <group>
      {/* Outer wireframe sphere */}
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[0.85, 2]} />
        <meshBasicMaterial color="#00f3ff" wireframe transparent opacity={0.25} />
      </mesh>
      {/* Orbit ring */}
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.1, 0.012, 8, 64]} />
        <meshBasicMaterial color="#00f3ff" transparent opacity={0.5} />
      </mesh>
      {/* Inner glow core */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[0.45, 32, 32]} />
        <meshStandardMaterial
          color="#00ffc8"
          emissive="#00ffc8"
          emissiveIntensity={4}
          metalness={0.1}
          roughness={0.2}
          transparent
          opacity={0.9}
          toneMapped={false}
        />
      </mesh>
      {/* Soft outer halo */}
      <mesh>
        <sphereGeometry args={[1.6, 32, 32]} />
        <meshBasicMaterial color="#00f3ff" transparent opacity={0.04} />
      </mesh>
    </group>
  )
}

// --- IP -> position map for edges/threats ---
function ipToPositionMap(nodes: NetworkNode[]): Map<string, THREE.Vector3> {
  const m = new Map<string, THREE.Vector3>()
  nodes.forEach(n => {
    if (n.data.ip) m.set(n.data.ip, n.position)
    if (n.id === "scout") m.set("scout", n.position)
  })
  return m
}

// --- Smart Network Connections (real edges from topology or heuristic fallback) ---
function NetworkConnections({ nodes, edges }: { nodes: NetworkNode[]; edges?: TopologyEdge[] | null }) {
  const connections = useMemo(() => {
    const ipPos = ipToPositionMap(nodes)

    if (edges?.length) {
      const conns: [THREE.Vector3, THREE.Vector3, number][] = []
      for (const e of edges) {
        const start = ipPos.get(e.source_ip)
        const end = ipPos.get(e.destination_ip)
        if (start && end) {
          const weight = e.packet_count ?? 1
          conns.push([start, end, weight])
        }
      }
      return conns.map(([start, end, weight]) => [start, end, false, "traffic", weight] as const)
    }

    // Heuristic fallback when no topology edges
    const conns: [THREE.Vector3, THREE.Vector3, boolean, string, number][] = []
    const hubs = nodes.filter(n => {
      const c = n.category.toLowerCase()
      return c === "router" || c === "firewall" || c === "network"
    })

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const sameSubnet = nodes[i].data.subnet === nodes[j].data.subnet
        const dist = nodes[i].position.distanceTo(nodes[j].position)
        if (sameSubnet && dist < 2.5 && Math.random() < 0.4) {
          conns.push([nodes[i].position, nodes[j].position, nodes[i].isAnomaly || nodes[j].isAnomaly, "subnet", 1])
        }
      }
    }
    hubs.forEach(hub => {
      nodes.forEach(node => {
        if (hub.id !== node.id && Math.random() < 0.12) {
          conns.push([hub.position, node.position, hub.isAnomaly || node.isAnomaly, "hub", 1])
        }
      })
    })
    const databases = nodes.filter(n => n.category.toLowerCase() === "database")
    const servers = nodes.filter(n => n.category.toLowerCase() === "server")
    databases.forEach(db => {
      servers.forEach(server => {
        if (Math.random() < 0.2) {
          conns.push([server.position, db.position, db.isAnomaly || server.isAnomaly, "db", 1])
        }
      })
    })
    hubs.forEach(hub => {
      if (Math.random() < 0.7) {
        conns.push([hub.position, new THREE.Vector3(0, 0, 0), hub.isAnomaly, "core", 1])
      }
    })
    return conns
  }, [nodes, edges])

  return (
    <group>
      {connections.map((conn, i) => {
        const [start, end, isAnomaly, type, weight] = conn
        const lineWidth = type === "traffic" ? 0.25 + Math.min(0.35, (weight ?? 1) / 500) : (type === "db" ? 0.6 : type === "hub" ? 0.4 : 0.3)
        const opacity = type === "traffic" ? 0.08 + Math.min(0.12, (weight ?? 1) / 1000) : (isAnomaly ? 0.15 : type === "core" ? 0.08 : 0.1)
        const color = isAnomaly ? "#ff0055" : type === "traffic" ? "#00f3ff" : (type === "db" ? "#bc13fe" : "#00f3ff")

        return (
          <Line
            key={i}
            points={[start, end]}
            color={color}
            lineWidth={lineWidth}
            transparent
            opacity={opacity}
          />
        )
      })}
    </group>
  )
}

// --- Threat vectors (incident source -> target) ---
function ThreatVectors({ nodes, threats }: { nodes: NetworkNode[]; threats?: TopologyThreat[] | null }) {
  const ipPos = ipToPositionMap(nodes)
  const lines = useMemo(() => {
    if (!threats?.length) return []
    const out: { start: THREE.Vector3; end: THREE.Vector3; severity: string; title: string }[] = []
    for (const t of threats) {
      const sip = t.source_ip || null
      const tip = t.target_ip || null
      if (!sip || !tip) continue
      const start = ipPos.get(sip)
      const end = ipPos.get(tip)
      if (start && end) out.push({ start, end, severity: t.severity, title: t.title })
    }
    return out
  }, [nodes, threats])

  if (lines.length === 0) return null

  return (
    <group>
      {lines.map((l, i) => {
        const isHigh = l.severity?.toLowerCase() === "critical" || l.severity?.toLowerCase() === "high"
        const color = isHigh ? "#ff0055" : "#ff6600"
        return (
          <Line
            key={i}
            points={[l.start, l.end]}
            color={color}
            lineWidth={0.6}
            transparent
            opacity={0.8}
          />
        )
      })}
    </group>
  )
}

// --- Data Streams (sphere particles, color variety) ---
const STREAM_COLORS = ["#00f3ff", "#39d353", "#bc13fe"]
function DataStreams() {
  const count = 40
  const particles = useRef<THREE.InstancedMesh>(null)
  const colors = useRef<Float32Array | null>(null)
  if (!colors.current) colors.current = new Float32Array(count * 3)
  const data = useMemo(() => {
    const arr = new Array(count).fill(0).map((_, i) => {
      const c = STREAM_COLORS[i % 3]
      const [r, g, b] = [parseInt(c.slice(1, 3), 16) / 255, parseInt(c.slice(3, 5), 16) / 255, parseInt(c.slice(5, 7), 16) / 255]
      colors.current!.set([r, g, b], i * 3)
      return {
        pos: new THREE.Vector3((Math.random() - 0.5) * 14, -6 - Math.random() * 2, (Math.random() - 0.5) * 14),
        speed: 0.018 + Math.random() * 0.035
      }
    })
    return arr
  }, [])

  useLayoutEffect(() => {
    if (!particles.current || !colors.current) return
    particles.current.instanceColor = new THREE.InstancedBufferAttribute(colors.current, 3)
  }, [])

  useFrame(() => {
    if (!particles.current) return
    data.forEach((p, i) => {
      p.pos.y += p.speed
      if (p.pos.y > 6) p.pos.y = -8
      const matrix = new THREE.Matrix4()
      matrix.setPosition(p.pos)
      particles.current!.setMatrixAt(i, matrix)
    })
    particles.current.instanceMatrix.needsUpdate = true
  })

  return (
    <instancedMesh ref={particles} args={[undefined, undefined, count]}>
      <sphereGeometry args={[0.04, 8, 8]} />
      <meshBasicMaterial transparent opacity={0.55} vertexColors toneMapped={false} />
    </instancedMesh>
  )
}

// --- Main Component ---
export default function VectorSpace() {
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null)
  const {
    data: topologyData,
    isPending: topologyLoading,
    isError: topologyError,
  } = useQuery({
    queryKey: ["topology"],
    queryFn: () => topologyApi.get({ since_minutes: 60 * 24, edges_limit: 500, threats_limit: 100 }),
    retry: 2,
    retryDelay: 1000,
  })
  const { data: assetsData } = useQuery({
    queryKey: ["assets", "list"],
    queryFn: () => assetsApi.list({ limit: 500 }),
  })

  const nodes = useMemo(() => {
    if (topologyData && Array.isArray(topologyData.nodes) && topologyData.nodes.length > 0) {
      return topologyNodesToNetworkNodes(topologyData.nodes)
    }
    if (topologyError || topologyLoading) return SCOUT_ONLY_NODES
    const items = assetsData?.items
    if (items?.length) return assetsToNodes(items)
    return SCOUT_ONLY_NODES
  }, [topologyData, topologyLoading, topologyError, assetsData?.items])
  const anomalyCount = useMemo(() => nodes.filter(n => n.isAnomaly).length, [nodes])
  const threatCount = topologyData?.threats?.length ?? anomalyCount
  const showingScoutOnly = nodes.length === 1 && nodes[0]?.id === "scout"
  const dataSource = topologyData?.nodes?.length
    ? "topology"
    : assetsData?.items?.length
      ? "assets"
      : null

  return (
    <div
      className="w-full h-full min-h-[500px] relative bg-gradient-to-b from-[#030810] via-[#050a14] to-[#0a1525] rounded-xl overflow-hidden border border-scout-border/50"
      data-topology-widget="v2"
    >
      <Canvas
        camera={{ position: [0, 3, 12], fov: 50 }}
        gl={{ antialias: true }}
        onClick={() => setSelectedNode(null)}
      >
        <color attach="background" args={["#030810"]} />
        <fog attach="fog" args={["#030810", 10, 28]} />

        <ambientLight intensity={0.25} />
        <pointLight position={[10, 10, 10]} intensity={0.6} color="#00f3ff" />
        <pointLight position={[-10, -10, -10]} intensity={0.35} color="#bc13fe" />
        <pointLight position={[0, 5, 0]} intensity={0.15} color="#00ffc8" />

        <Stars radius={100} depth={60} count={3000} factor={4} saturation={0} fade speed={0.4} />

        <group>
          <CoreSphere />
          <NetworkConnections nodes={nodes} edges={topologyData?.edges} />
          <ThreatVectors nodes={nodes} threats={topologyData?.threats} />
          {nodes.map((node) =>
            node.id === "scout" ? null : (
              <NetworkNode
                key={node.id}
                node={node}
                isSelected={selectedNode?.id === node.id}
                onClick={() => setSelectedNode(node)}
              />
            )
          )}
          <DataStreams />
        </group>

        <EffectComposer>
          <Bloom luminanceThreshold={0.85} luminanceSmoothing={0.4} mipmapBlur intensity={0.45} radius={0.25} />
          <Vignette offset={0.35} darkness={0.4} blendFunction={BlendFunction.NORMAL} />
        </EffectComposer>

        <OrbitControls
          enablePan={false}
          autoRotate={!selectedNode}
          autoRotateSpeed={0.3}
          minDistance={5}
          maxDistance={20}
        />
      </Canvas>

      {/* Header */}
      <div className="absolute top-4 left-4 pointer-events-none">
        <h3 className="text-lg font-bold text-scout-neon tracking-wider drop-shadow-lg">NETWORK TOPOLOGY</h3>
        <p className="text-[11px] text-scout-neon/60 font-mono">SUBNET-BASED VISUALIZATION</p>
        {topologyError && (
          <p className="text-xs text-amber-400 font-mono mt-1 bg-black/40 px-2 py-1 rounded">
            Topoloji API bağlanamadı — Backend çalışıyor mu? (http://localhost:8000 veya NEXT_PUBLIC_API_URL)
          </p>
        )}
        {showingScoutOnly && !topologyError && !topologyLoading && (
          <p className="text-xs text-scout-neon/80 font-mono mt-1 bg-black/40 px-2 py-1 rounded">
            Cihaz yok — Hunter ile subnet tara veya POST /discovery/scan ile keşfet
          </p>
        )}
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 text-right font-mono text-xs space-y-1 bg-black/50 backdrop-blur-sm border border-white/10 rounded-lg px-3 py-2">
        <div className="text-[10px] font-bold text-scout-neon/90 uppercase tracking-wider border-b border-scout-neon/30 pb-1 mb-1">
          İstatistik
        </div>
        {dataSource && (
          <div className="text-[10px] text-emerald-400 font-medium mb-0.5">
            {dataSource === "topology" ? "Veri: Topoloji API" : "Veri: Assets API"}
          </div>
        )}
        <div className="text-scout-neon/70">Toplam düğüm: <span className="text-scout-neon font-semibold">{nodes.length}</span></div>
        <div className="text-green-400/70">Çevrimiçi: <span className="text-green-400 font-semibold">{nodes.length - anomalyCount}</span></div>
        <div className="text-red-400/70">Tehdit: <span className="text-red-400 font-bold">{threatCount}</span></div>
      </div>

      {/* Selected Node Panel */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 right-4 md:right-auto md:w-80 bg-black/90 backdrop-blur-lg border border-scout-neon/30 rounded-lg p-4 shadow-2xl">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-scout-neon font-bold text-sm tracking-wide">NODE DETAILS</h4>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-scout-neon/60 hover:text-scout-neon text-lg leading-none"
            >
              ×
            </button>
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs font-mono">
            <div className="text-scout-neon/60">HOSTNAME</div>
            <div className="text-white truncate">{selectedNode.data.hostname}</div>

            <div className="text-scout-neon/60">IP ADDRESS</div>
            <div className="text-white">{selectedNode.data.ip}</div>

            <div className="text-scout-neon/60">SUBNET</div>
            <div className="text-white">{selectedNode.data.subnet}.0/24</div>

            <div className="text-scout-neon/60">DEVICE TYPE</div>
            <div className="text-white">{selectedNode.data.deviceType}</div>

            <div className="text-scout-neon/60">OS</div>
            <div className="text-white truncate">{selectedNode.data.os}</div>

            <div className="text-scout-neon/60">STATUS</div>
            <div className={`font-bold ${selectedNode.data.status === "Critical" ? "text-red-500" :
              selectedNode.data.status === "Warning" ? "text-yellow-500" : "text-green-500"
              }`}>
              {selectedNode.data.status.toUpperCase()}
            </div>

            <div className="text-scout-neon/60">THREAT LEVEL</div>
            <div className={`font-bold ${selectedNode.data.threatLevel === "HIGH" ? "text-red-500" :
              selectedNode.data.threatLevel === "MEDIUM" ? "text-yellow-500" : "text-green-500"
              }`}>
              {selectedNode.data.threatLevel}
            </div>

            <div className="text-scout-neon/60">OPEN PORTS</div>
            <div className="text-white">{selectedNode.data.openPorts}</div>

            <div className="text-scout-neon/60">LAST SEEN</div>
            <div className="text-white">{selectedNode.data.lastSeen}</div>
          </div>

          <div className="mt-4 flex gap-2">
            <button className="flex-1 bg-scout-neon/10 hover:bg-scout-neon/20 border border-scout-neon/30 text-scout-neon text-xs py-1.5 rounded transition-colors">
              Deep Scan
            </button>
            {selectedNode.isAnomaly && (
              <button className="flex-1 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 text-xs py-1.5 rounded transition-colors">
                Isolate
              </button>
            )}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 right-4 pointer-events-none bg-black/50 backdrop-blur-sm border border-white/10 rounded-lg px-3 py-2 space-y-2">
        <div className="text-[10px] font-bold text-scout-neon/90 uppercase tracking-wider border-b border-scout-neon/30 pb-1 mb-0.5">
          Lejant
        </div>
        <div className="flex items-center gap-2 justify-end">
          <span className="text-[10px] text-scout-neon/80 font-mono">Bağlantı (trafik)</span>
          <div className="w-4 h-0.5 rounded bg-scout-neon/80" />
        </div>
        <div className="flex items-center gap-2 justify-end">
          <span className="text-[10px] text-red-400/80 font-mono">Tehdit vektörü</span>
          <div className="w-4 h-0.5 rounded bg-red-500" />
        </div>
        <div className="flex items-center gap-2 justify-end">
          <span className="text-[10px] text-scout-neon/80 font-mono">Sağlıklı</span>
          <div className="w-2 h-2 rounded-full bg-scout-neon" />
        </div>
        <div className="flex items-center gap-2 justify-end">
          <span className="text-[10px] text-yellow-400/80 font-mono">Uyarı</span>
          <div className="w-2 h-2 rounded-full bg-yellow-400" />
        </div>
        <div className="flex items-center gap-2 justify-end">
          <span className="text-[10px] text-red-400/80 font-mono">Tehdit</span>
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        </div>
      </div>
    </div>
  )
}
