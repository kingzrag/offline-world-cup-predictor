import React, { useEffect, useRef, useState, useCallback } from 'react';

interface CursorPosition {
  x: number;
  y: number;
}

interface TrailPoint {
  x: number;
  y: number;
  timestamp: number;
}

type CursorTheme = 'upcoming' | 'live' | 'finished';

interface CustomCursorProps {
  theme?: CursorTheme;
}

// Theme color configurations
const THEME_COLORS = {
  upcoming: {
    glow: '#3B82F6', // Electric Blue
    aura: 'rgba(59, 130, 246, 0.3)',
    ripple: 'rgba(59, 130, 246, 0.6)',
  },
  live: {
    glow: '#EF4444', // Neon Red
    aura: 'rgba(239, 68, 68, 0.3)',
    ripple: 'rgba(239, 68, 68, 0.6)',
  },
  finished: {
    glow: '#A855F7', // Purple
    aura: 'rgba(168, 85, 247, 0.3)',
    ripple: 'rgba(168, 85, 247, 0.6)',
  },
};

// Lerp function for smooth interpolation
const lerp = (start: number, end: number, factor: number): number => {
  return start + (end - start) * factor;
};

// Check if device is touch-enabled
const isTouchDevice = (): boolean => {
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    // @ts-ignore
    navigator.msMaxTouchPoints > 0
  );
};

// Check if user prefers reduced motion
const prefersReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

export const CustomCursor: React.FC<CustomCursorProps> = ({ theme = 'upcoming' }) => {
  const cursorRef = useRef<HTMLDivElement>(null);
  const trailRef = useRef<HTMLDivElement>(null);
  const rippleRef = useRef<HTMLDivElement>(null);
  
  const [mousePosition, setMousePosition] = useState<CursorPosition>({ x: 0, y: 0 });
  const [cursorPosition, setCursorPosition] = useState<CursorPosition>({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const [isClicking, setIsClicking] = useState(false);
  const [isHidden, setIsHidden] = useState(true);
  const [trailPoints, setTrailPoints] = useState<TrailPoint[]>([]);
  
  const animationFrameRef = useRef<number | undefined>(undefined);
  const lastTimestampRef = useRef<number>(0);
  const isTabActiveRef = useRef<boolean>(true);
  
  // Get current theme colors
  const currentColors = THEME_COLORS[theme];

  // Smooth cursor movement with lerp
  const updateCursorPosition = useCallback(() => {
    setCursorPosition((prev) => ({
      x: lerp(prev.x, mousePosition.x, 0.15),
      y: lerp(prev.y, mousePosition.y, 0.15),
    }));
  }, [mousePosition]);

  // Update trail points
  const updateTrail = useCallback(() => {
    const now = Date.now();
    const maxTrailAge = 350; // 350ms
    
    // Add new trail point
    setTrailPoints((prev) => {
      const newPoints = [...prev, { x: cursorPosition.x, y: cursorPosition.y, timestamp: now }];
      // Remove old points
      return newPoints.filter((point) => now - point.timestamp < maxTrailAge);
    });
  }, [cursorPosition]);

  // Main animation loop
  const animate = useCallback((_timestamp: number) => {
    if (!isTabActiveRef.current) {
      animationFrameRef.current = requestAnimationFrame(animate);
      return;
    }

    // Limit to ~60 FPS
    const now = Date.now();
    const elapsed = now - lastTimestampRef.current;
    if (elapsed < 16.67) {
      animationFrameRef.current = requestAnimationFrame(animate);
      return;
    }
    lastTimestampRef.current = now;

    updateCursorPosition();
    updateTrail();

    animationFrameRef.current = requestAnimationFrame(animate);
  }, [updateCursorPosition, updateTrail]);

  // Mouse move handler
  const handleMouseMove = useCallback((e: MouseEvent) => {
    setMousePosition({ x: e.clientX, y: e.clientY });
    setIsHidden(false);
  }, []);

  // Mouse enter/leave handlers
  const handleMouseEnter = useCallback(() => setIsHidden(false), []);
  const handleMouseLeave = useCallback(() => setIsHidden(true), []);

  // Click handler
  const handleClick = useCallback(() => {
    setIsClicking(true);
    setTimeout(() => setIsClicking(false), 120);
  }, []);

  // Hover state detection
  const handleMouseOver = useCallback((e: MouseEvent) => {
    const target = e.target as HTMLElement;
    const interactiveElements = target.closest(
      'button, a, [role="button"], .cursor-pointer, .group, .match-card, .nav-item'
    );
    setIsHovering(!!interactiveElements);
  }, []);

  // Tab visibility change handler
  const handleVisibilityChange = useCallback(() => {
    isTabActiveRef.current = document.visibilityState === 'visible';
  }, []);

  // Setup event listeners
  useEffect(() => {
    // Skip on touch devices or if reduced motion is preferred
    if (isTouchDevice() || prefersReducedMotion()) {
      return;
    }

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseenter', handleMouseEnter);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('click', handleClick);
    document.addEventListener('mouseover', handleMouseOver);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Start animation loop
    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseenter', handleMouseEnter);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('click', handleClick);
      document.removeEventListener('mouseover', handleMouseOver);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [handleMouseMove, handleMouseEnter, handleMouseLeave, handleClick, handleMouseOver, handleVisibilityChange, animate]);

  // Update cursor DOM position
  useEffect(() => {
    if (cursorRef.current) {
      cursorRef.current.style.transform = `translate3d(${cursorPosition.x}px, ${cursorPosition.y}px, 0)`;
    }
  }, [cursorPosition]);

  // Update trail DOM
  useEffect(() => {
    if (!trailRef.current || trailPoints.length === 0) return;

    // Clear previous trail
    trailRef.current.innerHTML = '';

    // Create trail points
    trailPoints.forEach((point, index) => {
      const now = performance.now();
      const age = now - point.timestamp;
      const maxAge = 350;
      const opacity = 1 - age / maxAge;
      const scale = 0.5 + (opacity * 0.5);

      const trailDot = document.createElement('div');
      trailDot.style.cssText = `
        position: absolute;
        left: ${point.x}px;
        top: ${point.y}px;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: ${currentColors.glow};
        opacity: ${opacity * 0.4};
        transform: translate(-50%, -50%) scale(${scale});
        pointer-events: none;
        mix-blend-mode: screen;
        filter: blur(2px);
      `;
      trailRef.current.appendChild(trailDot);
    });
  }, [trailPoints, currentColors.glow]);

  // Handle click ripple animation
  useEffect(() => {
    if (!rippleRef.current || !isClicking) return;

    const ripple = rippleRef.current;
    ripple.style.transform = `translate3d(${cursorPosition.x}px, ${cursorPosition.y}px, 0) scale(0)`;
    ripple.style.opacity = '1';

    const animation = ripple.animate(
      [
        { transform: `translate3d(${cursorPosition.x}px, ${cursorPosition.y}px, 0) scale(0)`, opacity: 1 },
        { transform: `translate3d(${cursorPosition.x}px, ${cursorPosition.y}px, 0) scale(2)`, opacity: 0 },
      ],
      {
        duration: 400,
        easing: 'ease-out',
      }
    );

    return () => animation.cancel();
  }, [isClicking, cursorPosition, currentColors.ripple]);

  // Skip rendering on touch devices or if reduced motion is preferred
  if (isTouchDevice() || prefersReducedMotion()) {
    return null;
  }

  return (
    <>
      {/* Custom Cursor */}
      <div
        ref={cursorRef}
        className="fixed top-0 left-0 pointer-events-none z-[9999] hidden md:block"
        style={{
          width: '24px',
          height: '24px',
          transition: 'transform 0.1s ease-out',
        }}
      >
        {/* White arrow body */}
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          style={{
            filter: 'drop-shadow(0 0 4px rgba(0, 0, 0, 0.3))',
          }}
        >
          <path
            d="M5.5 3.21V20.8c0 .45.54.67.85.35l4.86-4.86a.5.5 0 0 1 .35-.15h6.87a.5.5 0 0 0 .35-.85L6.35 2.86a.5.5 0 0 0-.85.35Z"
            fill="#FFFFFF"
            style={{
              transition: 'fill 0.3s ease',
            }}
          />
        </svg>

        {/* Neon blue outer glow */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: `radial-gradient(circle, ${currentColors.glow} 0%, transparent 70%)`,
            opacity: isHovering ? 0.6 : 0.4,
            transform: `scale(${isHovering ? 1.2 : 1})`,
            transition: 'opacity 0.2s ease, transform 0.2s ease, background 0.3s ease',
            filter: 'blur(4px)',
            mixBlendMode: 'screen',
          }}
        />

        {/* Soft blurred blue aura */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: currentColors.aura,
            transform: `scale(${isHovering ? 1.5 : 1.3})`,
            transition: 'transform 0.2s ease, background 0.3s ease',
            filter: 'blur(8px)',
            mixBlendMode: 'screen',
          }}
        />

        {/* Electric pulse on hover */}
        {isHovering && (
          <div
            className="absolute inset-0 rounded-full"
            style={{
              background: currentColors.glow,
              animation: 'pulse 0.6s ease-in-out infinite',
              filter: 'blur(2px)',
              mixBlendMode: 'screen',
            }}
          />
        )}

        {/* Click brightness increase */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: currentColors.glow,
            opacity: isClicking ? 0.8 : 0,
            transition: 'opacity 0.1s ease',
            filter: 'blur(3px)',
            mixBlendMode: 'screen',
          }}
        />
      </div>

      {/* Motion Trail Container */}
      <div
        ref={trailRef}
        className="fixed top-0 left-0 pointer-events-none z-[9998] hidden md:block"
        style={{ mixBlendMode: 'screen' }}
      />

      {/* Click Ripple */}
      <div
        ref={rippleRef}
        className="fixed top-0 left-0 pointer-events-none z-[9997] hidden md:block"
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${currentColors.ripple} 0%, transparent 70%)`,
          transform: `translate3d(${cursorPosition.x}px, ${cursorPosition.y}px, 0) translate(-50%, -50%)`,
          opacity: 0,
          pointerEvents: 'none',
          mixBlendMode: 'screen',
        }}
      />

      {/* Global styles for animations */}
      <style>{`
        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
            opacity: 0.3;
          }
          50% {
            transform: scale(1.1);
            opacity: 0.6;
          }
        }

        /* Hide default cursor on desktop */
        @media (pointer: fine) {
          body {
            cursor: none !important;
          }

          a, button, [role="button"], .cursor-pointer {
            cursor: none !important;
          }
        }

        /* Show default cursor on touch devices */
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
