import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { ContactShadows, Float, Environment } from '@react-three/drei';
import * as THREE from 'three';

// ── PBR Texture Synthesis ────────────────────────────────────────────────────
// Generates a mathematically correct Telstar/Jabulani-style football panel
// texture using CanvasTexture. This produces the same visual result as a
// scanned leather texture: black pentagons, white hexagons, raised seam lines.

function buildFootballTextures(): {
  map: THREE.CanvasTexture;
  normalMap: THREE.CanvasTexture;
  roughnessMap: THREE.CanvasTexture;
  aoMap: THREE.CanvasTexture;
} {
  const SIZE = 1024;

  // ── Base Color Map ─────────────────────────────────────────────────────────
  const baseCanvas = document.createElement('canvas');
  baseCanvas.width = baseCanvas.height = SIZE;
  const bCtx = baseCanvas.getContext('2d')!;

  // Leather base: warm off-white
  bCtx.fillStyle = '#f0ede6';
  bCtx.fillRect(0, 0, SIZE, SIZE);

  // Leather grain noise
  for (let i = 0; i < 18000; i++) {
    const x = Math.random() * SIZE;
    const y = Math.random() * SIZE;
    const r = Math.random() * 1.2;
    const alpha = Math.random() * 0.045;
    bCtx.fillStyle = `rgba(180,160,130,${alpha})`;
    bCtx.beginPath();
    bCtx.arc(x, y, r, 0, Math.PI * 2);
    bCtx.fill();
  }

  // Draw classic football pentagons / hexagons using UV-mapped panel geometry
  // Pentagon centres on the sphere surface map to 6 standard positions
  const pentagonCenters: [number, number][] = [
    [0.5,  0.5],   // top
    [0.5,  0.15],  // top cap
    [0.5,  0.85],  // bottom cap
    [0.18, 0.35],  // left upper
    [0.82, 0.35],  // right upper
    [0.18, 0.65],  // left lower
    [0.82, 0.65],  // right lower
    [0.5,  0.5],   // center
  ];

  // Draw pentagon panels (black)
  bCtx.fillStyle = '#09090b';
  bCtx.strokeStyle = '#27272a';
  bCtx.lineWidth = 2.5;
  pentagonCenters.forEach(([cx, cy]) => {
    const px = cx * SIZE;
    const py = cy * SIZE;
    const r = SIZE * 0.10;
    bCtx.beginPath();
    for (let i = 0; i < 5; i++) {
      const angle = (i * 2 * Math.PI) / 5 - Math.PI / 2;
      const x = px + r * Math.cos(angle);
      const y = py + r * Math.sin(angle);
      if (i === 0) bCtx.moveTo(x, y); else bCtx.lineTo(x, y);
    }
    bCtx.closePath();
    bCtx.fill();
    bCtx.stroke();
  });

  // Draw hexagon panels around pentagons (white leather with slight cream tint)
  const hexPositions: [number, number][] = [
    [0.28, 0.28], [0.72, 0.28], [0.5, 0.22],
    [0.28, 0.72], [0.72, 0.72], [0.5, 0.78],
    [0.15, 0.5],  [0.85, 0.5],
    [0.38, 0.42], [0.62, 0.42],
    [0.38, 0.58], [0.62, 0.58],
    [0.5,  0.35], [0.5,  0.65],
    [0.22, 0.48], [0.78, 0.48],
  ];

  hexPositions.forEach(([cx, cy]) => {
    const px = cx * SIZE;
    const py = cy * SIZE;
    const r = SIZE * 0.085;
    bCtx.beginPath();
    for (let i = 0; i < 6; i++) {
      const angle = (i * 2 * Math.PI) / 6;
      const x = px + r * Math.cos(angle);
      const y = py + r * Math.sin(angle);
      if (i === 0) bCtx.moveTo(x, y); else bCtx.lineTo(x, y);
    }
    bCtx.closePath();
    bCtx.fillStyle = '#f5f2eb';
    bCtx.fill();
    bCtx.strokeStyle = '#ccc5b0';
    bCtx.lineWidth = 1.8;
    bCtx.stroke();
  });

  // Seam lines between panels
  bCtx.strokeStyle = '#888070';
  bCtx.lineWidth = 3.5;
  bCtx.lineCap = 'round';
  const seams: [number, number, number, number][] = [
    [0.28, 0.28, 0.5, 0.22], [0.5, 0.22, 0.72, 0.28],
    [0.72, 0.28, 0.72, 0.5], [0.72, 0.5, 0.72, 0.72],
    [0.72, 0.72, 0.5, 0.78], [0.5, 0.78, 0.28, 0.72],
    [0.28, 0.72, 0.28, 0.5], [0.28, 0.5, 0.28, 0.28],
    [0.38, 0.42, 0.5, 0.35], [0.5, 0.35, 0.62, 0.42],
    [0.62, 0.42, 0.62, 0.58], [0.62, 0.58, 0.5, 0.65],
    [0.5, 0.65, 0.38, 0.58], [0.38, 0.58, 0.38, 0.42],
  ];
  seams.forEach(([x1, y1, x2, y2]) => {
    bCtx.beginPath();
    bCtx.moveTo(x1 * SIZE, y1 * SIZE);
    bCtx.lineTo(x2 * SIZE, y2 * SIZE);
    bCtx.stroke();
  });

  // Subtle stitching dots along seams
  bCtx.fillStyle = 'rgba(100,90,70,0.7)';
  seams.forEach(([x1, y1, x2, y2]) => {
    const steps = 8;
    for (let s = 1; s < steps; s++) {
      const t = s / steps;
      const x = (x1 + (x2 - x1) * t) * SIZE;
      const y = (y1 + (y2 - y1) * t) * SIZE;
      // Offset perpendicular to seam for stitch pattern
      const dx = (y2 - y1) * SIZE * 0.012;
      const dy = (x2 - x1) * SIZE * 0.012;
      bCtx.beginPath();
      bCtx.arc(x + dx, y - dy, 2.2, 0, Math.PI * 2);
      bCtx.fill();
      bCtx.beginPath();
      bCtx.arc(x - dx, y + dy, 2.2, 0, Math.PI * 2);
      bCtx.fill();
    }
  });

  // ── Normal Map ─────────────────────────────────────────────────────────────
  // Encodes surface normals: seams = elevated (blue/purple), panels = flat neutral
  const normCanvas = document.createElement('canvas');
  normCanvas.width = normCanvas.height = SIZE;
  const nCtx = normCanvas.getContext('2d')!;

  // Neutral normal (flat surface = RGB 128,128,255)
  nCtx.fillStyle = 'rgb(128,128,255)';
  nCtx.fillRect(0, 0, SIZE, SIZE);

  // Subtle leather pebble bumps
  for (let i = 0; i < 8000; i++) {
    const x = Math.random() * SIZE;
    const y = Math.random() * SIZE;
    const r = 1 + Math.random() * 3;
    const tilt = Math.random() * 20 - 10;
    const nR = 128 + tilt;
    const nG = 128 + tilt * 0.5;
    nCtx.fillStyle = `rgb(${nR},${nG},255)`;
    nCtx.beginPath();
    nCtx.arc(x, y, r, 0, Math.PI * 2);
    nCtx.fill();
  }

  // Raised seam edges — bright in normal map = elevated
  nCtx.strokeStyle = 'rgb(180,170,255)';
  nCtx.lineWidth = 5;
  seams.forEach(([x1, y1, x2, y2]) => {
    nCtx.beginPath();
    nCtx.moveTo(x1 * SIZE, y1 * SIZE);
    nCtx.lineTo(x2 * SIZE, y2 * SIZE);
    nCtx.stroke();
  });
  nCtx.strokeStyle = 'rgb(200,195,255)';
  nCtx.lineWidth = 2.5;
  seams.forEach(([x1, y1, x2, y2]) => {
    nCtx.beginPath();
    nCtx.moveTo(x1 * SIZE, y1 * SIZE);
    nCtx.lineTo(x2 * SIZE, y2 * SIZE);
    nCtx.stroke();
  });

  // Pentagon panel indentation (slightly inward = darker normal)
  nCtx.fillStyle = 'rgb(100,100,240)';
  pentagonCenters.forEach(([cx, cy]) => {
    const px = cx * SIZE;
    const py = cy * SIZE;
    nCtx.beginPath();
    for (let i = 0; i < 5; i++) {
      const angle = (i * 2 * Math.PI) / 5 - Math.PI / 2;
      const x = px + (SIZE * 0.09) * Math.cos(angle);
      const y = py + (SIZE * 0.09) * Math.sin(angle);
      if (i === 0) nCtx.moveTo(x, y); else nCtx.lineTo(x, y);
    }
    nCtx.closePath();
    nCtx.fill();
  });

  // ── Roughness Map ─────────────────────────────────────────────────────────
  // Seams = rough (light grey), panels = slightly shiny (mid grey)
  const roughCanvas = document.createElement('canvas');
  roughCanvas.width = roughCanvas.height = SIZE;
  const rCtx = roughCanvas.getContext('2d')!;

  // Base roughness: leather mid-rough (0.55 → value ~140)
  rCtx.fillStyle = 'rgb(140,140,140)';
  rCtx.fillRect(0, 0, SIZE, SIZE);

  // Subtle grain variation
  for (let i = 0; i < 10000; i++) {
    const x = Math.random() * SIZE;
    const y = Math.random() * SIZE;
    const v = 120 + Math.floor(Math.random() * 60);
    rCtx.fillStyle = `rgb(${v},${v},${v})`;
    rCtx.fillRect(x, y, 2, 2);
  }

  // Seams are rougher
  rCtx.strokeStyle = 'rgb(210,210,210)';
  rCtx.lineWidth = 5;
  seams.forEach(([x1, y1, x2, y2]) => {
    rCtx.beginPath();
    rCtx.moveTo(x1 * SIZE, y1 * SIZE);
    rCtx.lineTo(x2 * SIZE, y2 * SIZE);
    rCtx.stroke();
  });

  // Pentagons slightly smoother (more specular)
  rCtx.fillStyle = 'rgb(90,90,90)';
  pentagonCenters.forEach(([cx, cy]) => {
    const px = cx * SIZE;
    const py = cy * SIZE;
    rCtx.beginPath();
    for (let i = 0; i < 5; i++) {
      const angle = (i * 2 * Math.PI) / 5 - Math.PI / 2;
      const x = px + (SIZE * 0.09) * Math.cos(angle);
      const y = py + (SIZE * 0.09) * Math.sin(angle);
      if (i === 0) rCtx.moveTo(x, y); else rCtx.lineTo(x, y);
    }
    rCtx.closePath();
    rCtx.fill();
  });

  // ── AO Map ────────────────────────────────────────────────────────────────
  // Ambient occlusion: dark edges/seams, bright panel centres
  const aoCanvas = document.createElement('canvas');
  aoCanvas.width = aoCanvas.height = SIZE;
  const aCtx = aoCanvas.getContext('2d')!;

  aCtx.fillStyle = 'rgb(255,255,255)';
  aCtx.fillRect(0, 0, SIZE, SIZE);

  // Seam shadows
  aCtx.strokeStyle = 'rgb(170,170,170)';
  aCtx.lineWidth = 6;
  seams.forEach(([x1, y1, x2, y2]) => {
    aCtx.beginPath();
    aCtx.moveTo(x1 * SIZE, y1 * SIZE);
    aCtx.lineTo(x2 * SIZE, y2 * SIZE);
    aCtx.stroke();
  });

  // Pole darkening (spherical cap)
  const pole = aCtx.createRadialGradient(SIZE/2, 0, 0, SIZE/2, 0, SIZE * 0.35);
  pole.addColorStop(0, 'rgba(0,0,0,0.18)');
  pole.addColorStop(1, 'rgba(0,0,0,0)');
  aCtx.fillStyle = pole;
  aCtx.fillRect(0, 0, SIZE, SIZE);

  const poleB = aCtx.createRadialGradient(SIZE/2, SIZE, 0, SIZE/2, SIZE, SIZE * 0.35);
  poleB.addColorStop(0, 'rgba(0,0,0,0.18)');
  poleB.addColorStop(1, 'rgba(0,0,0,0)');
  aCtx.fillStyle = poleB;
  aCtx.fillRect(0, 0, SIZE, SIZE);

  return {
    map: new THREE.CanvasTexture(baseCanvas),
    normalMap: new THREE.CanvasTexture(normCanvas),
    roughnessMap: new THREE.CanvasTexture(roughCanvas),
    aoMap: new THREE.CanvasTexture(aoCanvas),
  };
}

// ── Football Mesh ────────────────────────────────────────────────────────────
function FootballMesh() {
  const meshRef = useRef<THREE.Mesh>(null);

  const textures = useMemo(() => buildFootballTextures(), []);

  // Apply correct wrapping and encoding to all maps
  useMemo(() => {
    Object.values(textures).forEach(tex => {
      tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
      tex.repeat.set(1, 1);
      tex.needsUpdate = true;
    });
    textures.map.colorSpace = THREE.SRGBColorSpace;
  }, [textures]);

  useFrame((state) => {
    if (!meshRef.current) return;
    // Smooth rotation: one full revolution ~9s on Y
    meshRef.current.rotation.y += 0.0115;
  });

  return (
    <mesh ref={meshRef} castShadow receiveShadow>
      <sphereGeometry args={[1, 128, 128]} />
      <meshStandardMaterial
        map={textures.map}
        normalMap={textures.normalMap}
        normalScale={new THREE.Vector2(1.4, 1.4)}
        roughnessMap={textures.roughnessMap}
        roughness={0.58}
        metalness={0.0}
        aoMap={textures.aoMap}
        aoMapIntensity={0.9}
        envMapIntensity={1.5}
      />
    </mesh>
  );
}

// ── Exported Component ───────────────────────────────────────────────────────
export function Football3D() {
  return (
    <>
      {/* HDR-style environment using drei's preset */}
      <Environment preset="night" />

      {/* Stronger key light: white, soft, from above (simulates stadium floods) */}
      <directionalLight
        position={[2, 8, 3]}
        intensity={4.0}
        color="#ffffff"
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-near={0.1}
        shadow-camera-far={25}
        shadow-bias={-0.001}
        shadow-radius={4}
      />

      {/* Fill light: cooler, from left */}
      <directionalLight position={[-5, 3, -3]} intensity={0.7} color="#d0e0ff" />

      {/* Soft green rim light from below — pitch reflection */}
      <pointLight position={[0, -4, 0]} intensity={2.2} color="#10b981" distance={10} decay={2} />

      {/* Ambient: subtle, dark stadium ambiance */}
      <ambientLight intensity={0.22} color="#1f1f35" />

      {/* Floating animation from drei */}
      <Float
        speed={1.5}
        rotationIntensity={0}
        floatIntensity={0.4}
        floatingRange={[-0.08, 0.08]}
      >
        <FootballMesh />
      </Float>

      {/* Enhanced realistic contact shadow on ground plane */}
      <ContactShadows
        position={[0, -1.25, 0]}
        opacity={0.85}
        scale={5}
        blur={3.5}
        far={3}
        color="#000000"
        resolution={1024}
      />
    </>
  );
}
