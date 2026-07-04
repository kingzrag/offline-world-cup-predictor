/**
 * EnergyEngine - Organic flowing energy border
 * Creates liquid neon that continuously changes shape and brightness
 * Never repeats the exact same animation - feels alive
 */

export interface EnergyState {
  x: number;
  y: number;
  velocity: number;
  isHovering: boolean;
}

export class EnergyEngine {
  private element: HTMLElement | null = null;
  private state: EnergyState = { x: 0, y: 0, velocity: 0, isHovering: false };
  private targetX: number = 0;
  private targetY: number = 0;
  private phase: number = 0;
  private animationFrameId: number | undefined;
  private svgElement: SVGSVGElement | null = null;
  private pathElement: SVGPathElement | null = null;

  constructor(element: HTMLElement) {
    this.element = element;
    this.initializeSVG();
  }

  private initializeSVG(): void {
    if (!this.element) return;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '32');
    svg.setAttribute('height', '32');
    svg.setAttribute('viewBox', '0 0 32 32');
    svg.style.overflow = 'visible';
    svg.style.position = 'absolute';
    svg.style.top = '-4px';
    svg.style.left = '-4px';

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round');
    
    svg.appendChild(path);
    this.element.appendChild(svg);

    this.svgElement = svg;
    this.pathElement = path;
  }

  setPosition(x: number, y: number): void {
    this.targetX = x;
    this.targetY = y;
  }

  setVelocity(velocity: number): void {
    this.state.velocity = velocity;
  }

  setHovering(isHovering: boolean): void {
    this.state.isHovering = isHovering;
  }

  setColors(primary: string, secondary: string): void {
    if (!this.pathElement) return;
    this.pathElement.setAttribute('stroke', primary);
  }

  private generateOrganicPath(time: number): string {
    // Generate organic flowing shape using sine waves with varying frequencies
    // This creates a border that never repeats exactly
    const points: string[] = [];
    const segments = 32;
    const baseRadius = 11;
    
    for (let i = 0; i <= segments; i++) {
      const angle = (i / segments) * Math.PI * 2;
      
      // Multiple sine waves for organic variation
      const wave1 = Math.sin(angle * 3 + time * 0.002) * 0.8;
      const wave2 = Math.sin(angle * 5 - time * 0.003) * 0.5;
      const wave3 = Math.sin(angle * 7 + time * 0.001) * 0.3;
      
      const radius = baseRadius + wave1 + wave2 + wave3;
      const x = 16 + Math.cos(angle) * radius;
      const y = 16 + Math.sin(angle) * radius;
      
      points.push(`${x.toFixed(2)},${y.toFixed(2)}`);
    }
    
    return `M ${points[0]} L ${points.slice(1).join(' L ')} Z`;
  }

  update(timestamp: number): void {
    if (!this.element || !this.pathElement) return;

    // Small interpolation for smooth following
    const smoothing = 0.12;
    this.state.x += (this.targetX - this.state.x) * smoothing;
    this.state.y += (this.targetY - this.state.y) * smoothing;

    const velocityFactor = Math.min(this.state.velocity / 30, 1);
    const glowIntensity = 0.2 + (velocityFactor * 0.2) + (this.state.isHovering ? 0.1 : 0);
    const scale = 1 + (velocityFactor * 0.08) + (this.state.isHovering ? 0.04 : 0);

    // Update position
    this.element.style.transform = `translate3d(${this.state.x}px, ${this.state.y}px, 0) scale(${scale})`;
    this.element.style.opacity = glowIntensity.toString();

    // Update organic path
    this.phase += 1;
    const organicPath = this.generateOrganicPath(timestamp);
    this.pathElement.setAttribute('d', organicPath);
    this.pathElement.setAttribute('stroke-width', (1.5 + velocityFactor * 0.5).toString());
  }

  destroy(): void {
    if (this.animationFrameId !== undefined) {
      cancelAnimationFrame(this.animationFrameId);
    }
    if (this.svgElement && this.element) {
      this.element.removeChild(this.svgElement);
    }
    this.element = null;
    this.svgElement = null;
    this.pathElement = null;
  }
}
