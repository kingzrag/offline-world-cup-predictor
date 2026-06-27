import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Mesh, SphereGeometry, MeshStandardMaterial } from 'three';

export function Football3D() {
  const meshRef = useRef<Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      // Slow rotation: one full rotation every 8-10 seconds
      meshRef.current.rotation.y += 0.001;
      meshRef.current.rotation.x += 0.0005;
      
      // Subtle floating animation (3-6px vertical movement)
      meshRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.8) * 0.006;
    }
  });

  return (
    <mesh ref={meshRef} castShadow receiveShadow>
      <sphereGeometry args={[1, 64, 64]} />
      <meshStandardMaterial
        color="#ffffff"
        roughness={0.4}
        metalness={0.1}
        envMapIntensity={0.8}
      />
    </mesh>
  );
}
