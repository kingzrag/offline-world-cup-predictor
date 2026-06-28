import { useRef, useMemo, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF, ContactShadows, Float, Environment } from '@react-three/drei';
import * as THREE from 'three';

// ── Football Mesh ────────────────────────────────────────────────────────────
function FootballMesh({ onLoaded }: { onLoaded: () => void }) {
  const groupRef = useRef<THREE.Group>(null);
  const { scene } = useGLTF('/models/football.glb');

  // Clone the scene to avoid modifying the original
  const footballMesh = useMemo(() => {
    const cloned = scene.clone();
    // Enable shadows for all children
    cloned.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        (child as THREE.Mesh).castShadow = true;
        (child as THREE.Mesh).receiveShadow = true;
      }
    });
    // Scale the model appropriately
    cloned.scale.set(6.5, 6.5, 6.5);
    return cloned;
  }, [scene]);

  // Notify parent when model is ready
  useEffect(() => {
    if (footballMesh) {
      onLoaded();
    }
  }, [footballMesh, onLoaded]);

  useFrame(() => {
    if (!groupRef.current) return;
    // Slow rotation (about 8-10 seconds per revolution)
    groupRef.current.rotation.y += 0.0115;
  });

  return (
    <group ref={groupRef}>
      <primitive object={footballMesh} />
    </group>
  );
}

// ── Exported Component ───────────────────────────────────────────────────────
export function Football3D({ onLoaded }: { onLoaded: () => void }) {
  return (
    <>
      {/* HDR-style environment using drei's preset for realistic PBR */}
      <Environment preset="night" />

      {/* Strong key light: white, soft, from above (simulates stadium floods) */}
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
        <FootballMesh onLoaded={onLoaded} />
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

// Preload the model for better performance
useGLTF.preload('/models/football.glb');
