/// <reference types="vite/client" />

// Image asset imports
declare module '*.png' {
  const src: string;
  export default src;
}
declare module '*.jpg' {
  const src: string;
  export default src;
}
declare module '*.jpeg' {
  const src: string;
  export default src;
}
declare module '*.webp' {
  const src: string;
  export default src;
}
declare module '*.svg' {
  const src: string;
  export default src;
}

// 3D model asset imports
declare module '*.glb' {
  const src: string;
  export default src;
}
declare module '*.gltf' {
  const src: string;
  export default src;
}

// HDR / EXR environment maps
declare module '*.hdr' {
  const src: string;
  export default src;
}
declare module '*.exr' {
  const src: string;
  export default src;
}
