/**
 * GlowEngine - Multi-layer bloom system
 * Three independent glow layers that react to movement speed
 */

export interface GlowState {
  x: number;
  y: number;
  velocity: number;
  isHovering: boolean;
}

export class GlowEngine {
  private innerGlow: HTMLElement | null = null;
  private mediumGlow: HTMLElement | null = null;
  private outerGlow: HTMLElement | null = null;
  private state: GlowState = { x: 0, y: 0, velocity: 0, isHovering: false };
  private targetX: number = 0;
  private targetY: number = 0;
  private animationFrameId: number | undefined;

  constructor(
    innerGlow: HTMLElement,
    mediumGlow: HTMLElement,
    outerGlow: HTMLElement
  ) {
    this.innerGlow = innerGlow;
    this.mediumGlow = mediumGlow;
    this.outerGlow = outerGlow;
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

  update(): void {
    if (!this.innerGlow || !this.mediumGlow || !this.outerGlow) return;

    // Small interpolation for smooth glow following
    const smoothing = 0.15;
    this.state.x += (this.targetX - this.state.x) * smoothing;
    this.state.y += (this.targetY - this.state.y) * smoothing;

    const velocityFactor = Math.min(this.state.velocity / 30, 1);
    const baseIntensity = 0.15 + (velocityFactor * 0.2);
    const hoverIntensity = this.state.isHovering ? 0.12 : 0;

    // Inner crisp glow
    this.innerGlow.style.transform = `translate3d(${this.state.x}px, ${this.state.y}px, 0)`;
    this.innerGlow.style.opacity = (baseIntensity + hoverIntensity).toString();

    // Medium soft bloom - expands with speed
    const mediumSize = 24 + (velocityFactor * 8);
    this.mediumGlow.style.transform = `translate3d(${this.state.x}px, ${this.state.y}px, 0)`;
    this.mediumGlow.style.width = `${mediumSize}px`;
    this.mediumGlow.style.height = `${mediumSize}px`;
    this.mediumGlow.style.opacity = (baseIntensity * 0.7 + hoverIntensity * 0.8).toString();

    // Large atmospheric aura - expands more with speed
    const outerSize = 36 + (velocityFactor * 12);
    this.outerGlow.style.transform = `translate3d(${this.state.x}px, ${this.state.y}px, 0)`;
    this.outerGlow.style.width = `${outerSize}px`;
    this.outerGlow.style.height = `${outerSize}px`;
    this.outerGlow.style.opacity = (baseIntensity * 0.4 + hoverIntensity * 0.5).toString();
  }

  destroy(): void {
    if (this.animationFrameId !== undefined) {
      cancelAnimationFrame(this.animationFrameId);
    }
    this.innerGlow = null;
    this.mediumGlow = null;
    this.outerGlow = null;
  }
}
