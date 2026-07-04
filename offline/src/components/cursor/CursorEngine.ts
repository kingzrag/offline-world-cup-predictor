/**
 * CursorEngine - Direct arrow positioning with zero lag
 * The white arrow stays exactly under the real mouse at all times
 */

export interface CursorState {
  x: number;
  y: number;
  isHovering: boolean;
}

export class CursorEngine {
  private element: HTMLElement | null = null;
  private state: CursorState = { x: 0, y: 0, isHovering: false };
  private animationFrameId: number | undefined;

  constructor(element: HTMLElement) {
    this.element = element;
  }

  setPosition(x: number, y: number): void {
    this.state.x = x;
    this.state.y = y;
  }

  setHovering(isHovering: boolean): void {
    this.state.isHovering = isHovering;
  }

  update(): void {
    if (!this.element) return;

    // Direct positioning - no interpolation, no lag
    this.element.style.transform = `translate3d(${this.state.x}px, ${this.state.y}px, 0)`;
  }

  destroy(): void {
    if (this.animationFrameId !== undefined) {
      cancelAnimationFrame(this.animationFrameId);
    }
    this.element = null;
  }
}
