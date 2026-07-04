/**
 * CursorTrail - Subtle volumetric light streak
 * Almost invisible, disappears within 80ms
 * Smoothness is more important than the trail itself
 */

export interface TrailState {
  x: number;
  y: number;
  velocity: number;
  angle: number;
}

export class CursorTrail {
  private element: HTMLElement | null = null;
  private state: TrailState = { x: 0, y: 0, velocity: 0, angle: 0 };
  private animationFrameId: number | undefined;
  private lastUpdate: number = 0;
  private isActive: boolean = false;

  constructor(element: HTMLElement) {
    this.element = element;
  }

  setPosition(x: number, y: number): void {
    this.state.x = x;
    this.state.y = y;
  }

  setVelocity(velocity: number): void {
    this.state.velocity = velocity;
  }

  setAngle(angle: number): void {
    this.state.angle = angle;
  }

  update(timestamp: number): void {
    if (!this.element) return;

    // Only show trail when moving fast enough
    if (this.state.velocity < 4) {
      this.element.style.opacity = '0';
      this.isActive = false;
      return;
    }

    this.isActive = true;

    // Calculate trail properties
    const trailOpacity = Math.min(this.state.velocity / 30, 0.4);
    const trailLength = Math.min(this.state.velocity * 1.2, 22);

    // Update trail
    this.element.style.transform = `translate3d(${this.state.x}px, ${this.state.y}px, 0) rotate(${this.state.angle}rad)`;
    this.element.style.width = `${trailLength}px`;
    this.element.style.opacity = trailOpacity.toString();

    // Auto-fade after 80ms
    const now = timestamp;
    if (now - this.lastUpdate > 80) {
      this.element.style.opacity = '0';
      this.isActive = false;
    }
    this.lastUpdate = now;
  }

  destroy(): void {
    if (this.animationFrameId !== undefined) {
      cancelAnimationFrame(this.animationFrameId);
    }
    this.element = null;
  }
}
