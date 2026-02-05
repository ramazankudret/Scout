"use client"

import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls, Line, Html, Stars } from "@react-three/drei"
import { EffectComposer, Bloom } from "@react-three/postprocessing"
import { useRef, useMemo, useState } from "react"
import * as THREE from "three"

// --- Subnet-Based Node Generation ---
const generateMockNodes = () => {
  const nodes: Array<{
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
  }> = []

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
  node: ReturnType<typeof generateMockNodes>[0],
  isSelected: boolean,
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
        <sphereGeometry args={[node.isAnomaly ? 0.18 : 0.08, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isSelected ? 5 : (hovered ? 3 : (node.isAnomaly ? 2 : 0.5))}
          toneMapped={false}
        />
      </mesh>

      {(hovered || isSelected) && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.25, 0.3, 32]} />
          <meshBasicMaterial color={color} transparent opacity={0.5} side={THREE.DoubleSide} />
        </mesh>
      )}

      {hovered && !isSelected && (
        <Html center distanceFactor={8} style={{ pointerEvents: 'none' }}>
          <div className="bg-black/80 border border-scout-neon/50 px-2 py-1 rounded text-xs text-scout-neon font-mono whitespace-nowrap backdrop-blur-sm">
            {node.data.hostname} ({node.data.subnet}.x)
          </div>
        </Html>
      )}
    </group>
  )
}

// --- Core Sphere ---
function CoreSphere() {
  const meshRef = useRef<THREE.Mesh>(null)
  const glowRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.15
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.1
    }
    if (glowRef.current) {
      const pulse = 1 + Math.sin(state.clock.elapsedTime * 0.8) * 0.1
      glowRef.current.scale.setScalar(pulse)
    }
  })

  return (
    <group>
      <mesh ref={meshRef}>
        <icosahedronGeometry args={[0.8, 2]} />
        <meshBasicMaterial color="#00f3ff" wireframe transparent opacity={0.2} />
      </mesh>
      <mesh ref={glowRef}>
        <sphereGeometry args={[0.5, 32, 32]} />
        <meshStandardMaterial
          color="#00f3ff"
          emissive="#00f3ff"
          emissiveIntensity={3}
          transparent
          opacity={0.8}
        />
      </mesh>
      <mesh>
        <sphereGeometry args={[1.5, 32, 32]} />
        <meshBasicMaterial color="#00f3ff" transparent opacity={0.03} />
      </mesh>
    </group>
  )
}

// --- Smart Network Connections ---
function NetworkConnections({ nodes }: { nodes: ReturnType<typeof generateMockNodes> }) {
  const connections = useMemo(() => {
    const conns: [THREE.Vector3, THREE.Vector3, boolean, string][] = []

    // Find hubs (routers/firewalls)
    const hubs = nodes.filter(n => n.category === "Router" || n.category === "Firewall")

    // 1. Same subnet connections
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const sameSubnet = nodes[i].data.subnet === nodes[j].data.subnet
        const dist = nodes[i].position.distanceTo(nodes[j].position)

        if (sameSubnet && dist < 2.5 && Math.random() < 0.4) {
          conns.push([nodes[i].position, nodes[j].position, nodes[i].isAnomaly || nodes[j].isAnomaly, "subnet"])
        }
      }
    }

    // 2. Hub connections (routers connect everything)
    hubs.forEach(hub => {
      nodes.forEach(node => {
        if (hub.id !== node.id && Math.random() < 0.12) {
          conns.push([hub.position, node.position, hub.isAnomaly || node.isAnomaly, "hub"])
        }
      })
    })

    // 3. Database connections
    const databases = nodes.filter(n => n.category === "Database")
    const servers = nodes.filter(n => n.category === "Server")

    databases.forEach(db => {
      servers.forEach(server => {
        if (Math.random() < 0.2) {
          conns.push([server.position, db.position, db.isAnomaly || server.isAnomaly, "db"])
        }
      })
    })

    // 4. Core router connections
    hubs.forEach(hub => {
      if (Math.random() < 0.7) {
        conns.push([hub.position, new THREE.Vector3(0, 0, 0), hub.isAnomaly, "core"])
      }
    })

    return conns
  }, [nodes])

  return (
    <group>
      {connections.map((conn, i) => {
        const [start, end, isAnomaly, type] = conn
        const lineWidth = type === "db" ? 0.6 : (type === "hub" ? 0.4 : 0.3)
        const opacity = isAnomaly ? 0.15 : (type === "core" ? 0.08 : 0.1)
        const color = isAnomaly ? "#ff0055" : (type === "db" ? "#bc13fe" : "#00f3ff")

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

// --- Data Streams ---
function DataStreams() {
  const count = 30
  const particles = useRef<THREE.InstancedMesh>(null)

  const data = useMemo(() => {
    return new Array(count).fill(0).map(() => ({
      pos: new THREE.Vector3((Math.random() - 0.5) * 12, -6, (Math.random() - 0.5) * 12),
      speed: 0.02 + Math.random() * 0.04
    }))
  }, [])

  useFrame(() => {
    if (!particles.current) return

    data.forEach((p, i) => {
      p.pos.y += p.speed
      if (p.pos.y > 6) p.pos.y = -6

      const matrix = new THREE.Matrix4()
      matrix.setPosition(p.pos)
      particles.current!.setMatrixAt(i, matrix)
    })
    particles.current.instanceMatrix.needsUpdate = true
  })

  return (
    <instancedMesh ref={particles} args={[undefined, undefined, count]}>
      <boxGeometry args={[0.015, 0.3, 0.015]} />
      <meshBasicMaterial color="#00f3ff" transparent opacity={0.4} />
    </instancedMesh>
  )
}

// --- Main Component ---
export default function VectorSpace() {
  const [selectedNode, setSelectedNode] = useState<ReturnType<typeof generateMockNodes>[0] | null>(null)

  const nodes = useMemo(() => generateMockNodes(), [])
  const anomalyCount = useMemo(() => nodes.filter(n => n.isAnomaly).length, [nodes])

  return (
    <div className="w-full h-full min-h-[500px] relative bg-gradient-to-b from-[#050a14] to-[#0a1525] rounded-xl overflow-hidden border border-white/5">
      <Canvas
        camera={{ position: [0, 3, 12], fov: 50 }}
        gl={{ antialias: true }}
        onClick={() => setSelectedNode(null)}
      >
        <color attach="background" args={["#050a14"]} />
        <fog attach="fog" args={["#050a14", 8, 25]} />

        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={0.5} color="#00f3ff" />
        <pointLight position={[-10, -10, -10]} intensity={0.3} color="#bc13fe" />

        <Stars radius={80} depth={50} count={2000} factor={3} saturation={0} fade speed={0.3} />

        <group>
          <CoreSphere />
          <NetworkConnections nodes={nodes} />
          {nodes.map((node) => (
            <NetworkNode
              key={node.id}
              node={node}
              isSelected={selectedNode?.id === node.id}
              onClick={() => setSelectedNode(node)}
            />
          ))}
          <DataStreams />
        </group>

        <EffectComposer>
          <Bloom luminanceThreshold={1} mipmapBlur={false} intensity={0.3} radius={0.2} />
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
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 text-right font-mono text-xs space-y-1">
        <div className="text-scout-neon/70">TOTAL NODES: <span className="text-scout-neon">{nodes.length}</span></div>
        <div className="text-green-400/70">ONLINE: <span className="text-green-400">{nodes.length - anomalyCount}</span></div>
        <div className="text-red-400/70">THREATS: <span className="text-red-400 font-bold">{anomalyCount}</span></div>
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
      <div className="absolute bottom-4 right-4 pointer-events-none space-y-1">
        <div className="flex items-center gap-2 justify-end">
          <span className="text-[10px] text-scout-neon/60 font-mono">HEALTHY</span>
          <div className="w-2 h-2 rounded-full bg-scout-neon" />
        </div>
        <div className="flex items-center gap-2 justify-end">
          <span className="text-[10px] text-yellow-400/60 font-mono">WARNING</span>
          <div className="w-2 h-2 rounded-full bg-yellow-400" />
        </div>
        <div className="flex items-center gap-2 justify-end">
          <span className="text-[10px] text-red-400/60 font-mono">THREAT</span>
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        </div>
      </div>
    </div>
  )
}
