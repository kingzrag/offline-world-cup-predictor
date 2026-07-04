import React, { useEffect, useRef, useCallback } from 'react';

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
  const glowRef = useRef<HTMLDivElement>(null);
  const auraRef = useRef<HTMLDivElement>(null);
  const pulseRef = useRef<HTMLDivElement>(null);
  const clickGlowRef = useRef<HTMLDivElement>(null);
  const rippleRef = useRef<HTMLDivElement>(null);
  
  const mouseXRef = useRef(0);
  const mouseYRef = useRef(0);
  const cursorXRef = useRef(0);
  const cursorYRef = useRef(0);
  const isHoveringRef = useRef(false);
  const isClickingRef = useRef(false);
  const isTabActiveRef = useRef(true);
  
  const animationFrameRef = useRef<number | undefined>(undefined);
  
  // Get current theme colors
  const currentColors = THEME_COLORS[theme];

  // Direct cursor update with minimal smoothing
  const updateCursor = useCallback(() => {
    if (!cursorRef.current) return;
    
    // Very slight smoothing for premium feel, but nearly imperceptible lag
    const smoothing = 0.3;
    cursorXRef.current += (mouseXRef.current - cursorXRef.current) * smoothing;
    cursorYRef.current += (mouseYRef.current - cursorYRef.current) * smoothing;
    
    const x = cursorXRef.current;
    const y = cursorYRef.current;
    
    cursorRef.current.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    
    // Update glow elements
    if (glowRef.current) {
      glowRef.current.style.transform = `translate3d(${x}px, ${y}px, 0) scale(${isHoveringRef.current ? 1.2 : 1})`;
      glowRef.current.style.opacity = isHoveringRef.current ? '0.6' : '0.4';
    }
    
    if (auraRef.current) {
      auraRef.current.style.transform = `translate3d(${x}px, ${y}px, 0) scale(${isHoveringRef.current ? 1.5 : 1.3})`;
    }
    
    if (pulseRef.current) {
      pulseRef.current.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      pulseRef.current.style.display = isHoveringRef.current ? 'block' : 'none';
    }
    
    if (clickGlowRef.current) {
      clickGlowRef.current.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      clickGlowRef.current.style.opacity = isClickingRef.current ? '0.8' : '0';
    }
  }, []);

  // Main animation loop
  const animate = useCallback(() => {
    if (!isTabActiveRef.current) {
      animationFrameRef.current = requestAnimationFrame(animate);
      return;
    }

    updateCursor();
    animationFrameRef.current = requestAnimationFrame(animate);
  }, [updateCursor]);

  // Mouse move handler
  const handleMouseMove = useCallback((e: MouseEvent) => {
    mouseXRef.current = e.clientX;
    mouseYRef.current = e.clientY;
  }, []);

  // Click handler
  const handleClick = useCallback(() => {
    isClickingRef.current = true;
    setTimeout(() => {
      isClickingRef.current = false;
    }, 120);
  }, []);

  // Hover state detection
  const handleMouseOver = useCallback((e: MouseEvent) => {
    const target = e.target as HTMLElement;
    const interactiveElements = target.closest(
      'button, a, [role="button"], .cursor-pointer, .group, .match-card, .nav-item'
    );
    isHoveringRef.current = !!interactiveElements;
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
    document.addEventListener('click', handleClick);
    document.addEventListener('mouseover', handleMouseOver);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Start animation loop
    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('click', handleClick);
      document.removeEventListener('mouseover', handleMouseOver);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      
      if (animationFrameRef.current !== undefined) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [handleMouseMove, handleClick, handleMouseOver, handleVisibilityChange, animate]);

  // Handle click ripple animation
  useEffect(() => {
    const handleRipple = () => {
      if (!rippleRef.current) return;
      
      const x = cursorXRef.current;
      const y = cursorYRef.current;
      
      rippleRef.current.style.transform = `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%) scale(0)`;
      rippleRef.current.style.opacity = '1';
      
      const animation = rippleRef.current.animate(
        [
          { transform: `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%) scale(0)`, opacity: 1 },
          { transform: `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%) scale(2)`, opacity: 0 },
        ],
        {
          duration: 400,
          easing: 'ease-out',
        }
      );
      
      animation.onfinish = () => {
        if (rippleRef.current) {
          rippleRef.current.style.opacity = '0';
        }
      };
    };
    
    document.addEventListener('click', handleRipple);
    
    return () => {
      document.removeEventListener('click', handleRipple);
    };
  }, []);

  // Skip rendering on touch devices or if reduced motion is preferred
  if (isTouchDevice() || prefersReducedMotion()) {
    return null;
  }

  return (
    <>
      {/* Custom Cursor */}
      <div
        ref={cursorRef}
        className="fixed top-0 left-0 pointer-events-none z-[999999] hidden md:block"
        style={{
          width: '24px',
          height: '24px',
          willChange: 'transform',
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
          />
        </svg>
      </div>

      {/* Neon blue outer glow */}
      <div
        ref={glowRef}
        className="fixed top-0 left-0 pointer-events-none z-[999998] hidden md:block rounded-full"
        style={{
          width: '24px',
          height: '24px',
          background: `radial-gradient(circle, ${currentColors.glow} 0%, transparent 70%)`,
          opacity: 0.4,
          filter: 'blur(4px)',
          mixBlendMode: 'screen',
          willChange: 'transform, opacity',
          transition: 'opacity 0.2s ease, background 0.3s ease',
        }}
      />

      {/* Soft blurred blue aura */}
      <div
        ref={auraRef}
        className="fixed top-0 left-0 pointer-events-none z-[999997] hidden md:block rounded-full"
        style={{
          width: '24px',
          height: '24px',
          background: currentColors.aura,
          filter: 'blur(8px)',
          mixBlendMode: 'screen',
          willChange: 'transform',
        }}
      />

      {/* Electric pulse on hover */}
      <div
        ref={pulseRef}
        className="fixed top-0 left-0 pointer-events-none z-[999996] hidden md:block rounded-full"
        style={{
          width: '24px',
          height: '24px',
          background: currentColors.glow,
          animation: 'pulse 0.6s ease-in-out infinite',
          filter: 'blur(2px)',
          mixBlendMode: 'screen',
          willChange: 'transform',
          display: 'none',
        }}
      />

      {/* Click brightness increase */}
      <div
        ref={clickGlowRef}
        className="fixed top-0 left-0 pointer-events-none z-[999995] hidden md:block rounded-full"
        style={{
          width: '24px',
          height: '24px',
          background: currentColors.glow,
          opacity: 0,
          filter: 'blur(3px)',
          mixBlendMode: 'screen',
          willChange: 'transform, opacity',
          transition: 'opacity 0.1s ease',
        }}
      />

      {/* Click Ripple */}
      <div
        ref={rippleRef}
        className="fixed top-0 left-0 pointer-events-none z-[999994] hidden md:block rounded-full"
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${currentColors.ripple} 0%, transparent 70%)`,
          opacity: 0,
          pointerEvents: 'none',
          mixBlendMode: 'screen',
          willChange: 'transform, opacity',
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
