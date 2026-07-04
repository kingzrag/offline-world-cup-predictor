import React, { useEffect, useRef } from 'react';
import { CursorEngine } from './cursor/CursorEngine';
import { GlowEngine } from './cursor/GlowEngine';
import { EnergyEngine } from './cursor/EnergyEngine';
import { CursorTrail } from './cursor/CursorTrail';

type CursorTheme = 'upcoming' | 'live' | 'finished';

interface CustomCursorProps {
  theme?: CursorTheme;
}

const THEME_COLORS = {
  upcoming: {
    primary: '#3B82F6',
    secondary: '#60A5FA',
    glow: 'rgba(59, 130, 246, 0.4)',
  },
  live: {
    primary: '#EF4444',
    secondary: '#F87171',
    glow: 'rgba(239, 68, 68, 0.4)',
  },
  finished: {
    primary: '#A855F7',
    secondary: '#C084FC',
    glow: 'rgba(168, 85, 247, 0.4)',
  },
};

const isTouchDevice = (): boolean => {
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    // @ts-ignore
    navigator.msMaxTouchPoints > 0
  );
};

const prefersReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

export const CustomCursor: React.FC<CustomCursorProps> = ({ theme = 'upcoming' }) => {
  const cursorRef = useRef<HTMLDivElement>(null);
  const glowInnerRef = useRef<HTMLDivElement>(null);
  const glowMediumRef = useRef<HTMLDivElement>(null);
  const glowOuterRef = useRef<HTMLDivElement>(null);
  const energyBorderRef = useRef<HTMLDivElement>(null);
  const trailRef = useRef<HTMLDivElement>(null);
  const clickPulseRef = useRef<HTMLDivElement>(null);

  const enginesRef = useRef<{
    cursor: CursorEngine | null;
    glow: GlowEngine | null;
    energy: EnergyEngine | null;
    trail: CursorTrail | null;
  }>({ cursor: null, glow: null, energy: null, trail: null });

  const mouseXRef = useRef(0);
  const mouseYRef = useRef(0);
  const prevMouseXRef = useRef(0);
  const prevMouseYRef = useRef(0);
  const velocityRef = useRef(0);
  const isHoveringRef = useRef(false);
  const isTabActiveRef = useRef(true);
  const animationFrameRef = useRef<number | undefined>(undefined);

  const currentColors = THEME_COLORS[theme];

  useEffect(() => {
    if (isTouchDevice() || prefersReducedMotion()) {
      return;
    }

    // Initialize engines when DOM elements are ready
    const initEngines = () => {
      if (cursorRef.current && glowInnerRef.current && glowMediumRef.current && glowOuterRef.current && energyBorderRef.current && trailRef.current) {
        enginesRef.current.cursor = new CursorEngine(cursorRef.current);
        enginesRef.current.glow = new GlowEngine(glowInnerRef.current, glowMediumRef.current, glowOuterRef.current);
        enginesRef.current.energy = new EnergyEngine(energyBorderRef.current);
        enginesRef.current.trail = new CursorTrail(trailRef.current);

        // Set colors
        enginesRef.current.energy?.setColors(currentColors.primary, currentColors.secondary);
      }
    };

    initEngines();

    const handleMouseMove = (e: MouseEvent) => {
      mouseXRef.current = e.clientX;
      mouseYRef.current = e.clientY;
    };

    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const interactive = target.closest('button, a, [role="button"], .cursor-pointer, .group, .match-card, .nav-item');
      isHoveringRef.current = !!interactive;
    };

    const handleVisibilityChange = () => {
      isTabActiveRef.current = document.visibilityState === 'visible';
    };

    const handleClick = () => {
      if (!clickPulseRef.current) return;
      const x = mouseXRef.current;
      const y = mouseYRef.current;
      
      clickPulseRef.current.style.transform = `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%) scale(0.5)`;
      clickPulseRef.current.style.opacity = '1';
      
      const animation = clickPulseRef.current.animate(
        [
          { transform: `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%) scale(0.5)`, opacity: 1 },
          { transform: `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%) scale(2)`, opacity: 0 },
        ],
        { duration: 150, easing: 'ease-out' }
      );
      
      animation.onfinish = () => {
        if (clickPulseRef.current) {
          clickPulseRef.current.style.opacity = '0';
        }
      };
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseover', handleMouseOver);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('click', handleClick);

    const animate = (timestamp: number) => {
      if (!isTabActiveRef.current) {
        animationFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      // Calculate velocity
      const dx = mouseXRef.current - prevMouseXRef.current;
      const dy = mouseYRef.current - prevMouseYRef.current;
      const distance = Math.sqrt(dx * dx + dy * dy);
      velocityRef.current = distance;
      prevMouseXRef.current = mouseXRef.current;
      prevMouseYRef.current = mouseYRef.current;

      const velocity = velocityRef.current;
      const angle = Math.atan2(dy, dx);

      // Update all engines
      enginesRef.current.cursor?.setPosition(mouseXRef.current, mouseYRef.current);
      enginesRef.current.cursor?.setHovering(isHoveringRef.current);
      enginesRef.current.cursor?.update();

      enginesRef.current.glow?.setPosition(mouseXRef.current, mouseYRef.current);
      enginesRef.current.glow?.setVelocity(velocity);
      enginesRef.current.glow?.setHovering(isHoveringRef.current);
      enginesRef.current.glow?.update();

      enginesRef.current.energy?.setPosition(mouseXRef.current, mouseYRef.current);
      enginesRef.current.energy?.setVelocity(velocity);
      enginesRef.current.energy?.setHovering(isHoveringRef.current);
      enginesRef.current.energy?.update(timestamp);

      enginesRef.current.trail?.setPosition(mouseXRef.current, mouseYRef.current);
      enginesRef.current.trail?.setVelocity(velocity);
      enginesRef.current.trail?.setAngle(angle);
      enginesRef.current.trail?.update(timestamp);

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseover', handleMouseOver);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('click', handleClick);

      if (animationFrameRef.current !== undefined) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      enginesRef.current.cursor?.destroy();
      enginesRef.current.glow?.destroy();
      enginesRef.current.energy?.destroy();
      enginesRef.current.trail?.destroy();
    };
  }, [currentColors]);

  if (isTouchDevice() || prefersReducedMotion()) {
    return null;
  }

  return (
    <>
      {/* Layer 1: White cursor arrow - direct positioning */}
      <div
        ref={cursorRef}
        className="fixed top-0 left-0 pointer-events-none z-[999999] hidden md:block"
        style={{ width: '24px', height: '24px', willChange: 'transform' }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path
            d="M5.5 3.21V20.8c0 .45.54.67.85.35l4.86-4.86a.5.5 0 0 1 .35-.15h6.87a.5.5 0 0 0 .35-.85L6.35 2.86a.5.5 0 0 0-.85.35Z"
            fill="#FFFFFF"
            stroke={currentColors.primary}
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {/* Layer 3: Living energy border */}
      <div
        ref={energyBorderRef}
        className="fixed top-0 left-0 pointer-events-none z-[999998] hidden md:block"
        style={{ width: '32px', height: '32px', willChange: 'transform, opacity', mixBlendMode: 'screen', opacity: 0.2 }}
      />

      {/* Layer 2: Multi-layer glow */}
      <div
        ref={glowInnerRef}
        className="fixed top-0 left-0 pointer-events-none z-[999997] hidden md:block rounded-full"
        style={{
          width: '18px',
          height: '18px',
          background: `radial-gradient(circle, ${currentColors.glow} 0%, transparent 60%)`,
          filter: 'blur(3px)',
          mixBlendMode: 'screen',
          willChange: 'transform, opacity',
          transition: 'opacity 0.15s ease-out',
          opacity: 0.15,
        }}
      />
      <div
        ref={glowMediumRef}
        className="fixed top-0 left-0 pointer-events-none z-[999996] hidden md:block rounded-full"
        style={{
          width: '24px',
          height: '24px',
          background: `radial-gradient(circle, ${currentColors.glow} 0%, transparent 70%)`,
          filter: 'blur(6px)',
          mixBlendMode: 'screen',
          willChange: 'transform, opacity, width, height',
          transition: 'opacity 0.2s ease-out, width 0.2s ease-out, height 0.2s ease-out',
          opacity: 0.1,
        }}
      />
      <div
        ref={glowOuterRef}
        className="fixed top-0 left-0 pointer-events-none z-[999995] hidden md:block rounded-full"
        style={{
          width: '36px',
          height: '36px',
          background: `radial-gradient(circle, ${currentColors.glow} 0%, transparent 80%)`,
          filter: 'blur(12px)',
          mixBlendMode: 'screen',
          willChange: 'transform, opacity, width, height',
          transition: 'opacity 0.25s ease-out, width 0.25s ease-out, height 0.25s ease-out',
          opacity: 0.06,
        }}
      />

      {/* Layer 5: Subtle trail */}
      <div
        ref={trailRef}
        className="fixed top-0 left-0 pointer-events-none z-[999994] hidden md:block"
        style={{
          width: '0px',
          height: '3px',
          background: `linear-gradient(90deg, transparent 0%, ${currentColors.primary} 30%, ${currentColors.secondary} 50%, ${currentColors.primary} 70%, transparent 100%)`,
          filter: 'blur(2px)',
          mixBlendMode: 'screen',
          willChange: 'transform, opacity, width',
          transition: 'opacity 0.08s ease-out',
          opacity: 0,
          borderRadius: '2px',
        }}
      />

      {/* Click pulse */}
      <div
        ref={clickPulseRef}
        className="fixed top-0 left-0 pointer-events-none z-[999993] hidden md:block rounded-full"
        style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${currentColors.primary} 0%, transparent 70%)`,
          opacity: 0,
          pointerEvents: 'none',
          mixBlendMode: 'screen',
          willChange: 'transform, opacity',
        }}
      />

      <style>{`
        @media (pointer: fine) {
          body, a, button, [role="button"], .cursor-pointer {
            cursor: none !important;
          }
        }
        @media (pointer: coarse) {
          body {
            cursor: auto !important;
          }
        }
      `}</style>
    </>
  );
};

export default CustomCursor;
