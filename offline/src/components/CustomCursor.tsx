import React, { useEffect, useRef } from 'react';

type CursorTheme = 'upcoming' | 'live' | 'finished';

interface CustomCursorProps {
  theme?: CursorTheme;
}

const THEME_COLORS = {
  upcoming: { primary: '#3B82F6', glow: 'rgba(59, 130, 246, 0.3)' },
  live: { primary: '#EF4444', glow: 'rgba(239, 68, 68, 0.3)' },
  finished: { primary: '#A855F7', glow: 'rgba(168, 85, 247, 0.3)' },
};

const isTouchDevice = (): boolean => {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
};

const prefersReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

export const CursorFX: React.FC<CustomCursorProps> = ({ theme = 'upcoming' }) => {
  const glowRef = useRef<HTMLDivElement>(null);
  const rippleContainerRef = useRef<HTMLDivElement>(null);
  const mouseXRef = useRef(0);
  const mouseYRef = useRef(0);
  const isTabActiveRef = useRef(true);
  const animationFrameRef = useRef<number | undefined>(undefined);
  const magneticTargetRef = useRef<HTMLElement | null>(null);
  const magneticOffsetRef = useRef({ x: 0, y: 0 });

  const currentColors = THEME_COLORS[theme];

  useEffect(() => {
    if (isTouchDevice() || prefersReducedMotion()) return;

    const handleMouseMove = (e: MouseEvent) => {
      mouseXRef.current = e.clientX;
      mouseYRef.current = e.clientY;

      // Check for magnetic target
      const target = e.target as HTMLElement;
      const button = target.closest('button, a, [role="button"]');
      magneticTargetRef.current = button as HTMLElement | null;
    };

    const handleMouseLeave = () => {
      magneticTargetRef.current = null;
      magneticOffsetRef.current = { x: 0, y: 0 };
    };

    const handleVisibilityChange = () => {
      isTabActiveRef.current = document.visibilityState === 'visible';
    };

    const handleClick = (e: MouseEvent) => {
      if (!rippleContainerRef.current) return;
      
      const ripple = document.createElement('div');
      ripple.style.cssText = `
        position: fixed;
        left: ${e.clientX}px;
        top: ${e.clientY}px;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: radial-gradient(circle, ${currentColors.primary} 0%, transparent 70%);
        pointer-events: none;
        transform: translate(-50%, -50%) scale(0);
        animation: rippleExpand 250ms ease-out forwards;
      `;
      
      rippleContainerRef.current.appendChild(ripple);
      
      ripple.addEventListener('animationend', () => {
        ripple.remove();
      });
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('click', handleClick);

    const animate = () => {
      if (!isTabActiveRef.current) {
        animationFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      if (glowRef.current) {
        // Calculate magnetic offset
        let offsetX = 0;
        let offsetY = 0;
        
        if (magneticTargetRef.current) {
          const rect = magneticTargetRef.current.getBoundingClientRect();
          const centerX = rect.left + rect.width / 2;
          const centerY = rect.top + rect.height / 2;
          
          const dx = centerX - mouseXRef.current;
          const dy = centerY - mouseYRef.current;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < 100) {
            const strength = (100 - distance) / 100;
            offsetX = dx * strength * 0.3;
            offsetY = dy * strength * 0.3;
          }
        }
        
        magneticOffsetRef.current = { x: offsetX, y: offsetY };
        
        // Single transform update per frame
        glowRef.current.style.transform = `translate3d(${mouseXRef.current + offsetX}px, ${mouseYRef.current + offsetY}px, 0)`;
      }

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('click', handleClick);
      if (animationFrameRef.current !== undefined) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [currentColors]);

  if (isTouchDevice() || prefersReducedMotion()) return null;

  return (
    <>
      {/* Cursor FX Glow - follows native cursor */}
      <div
        ref={glowRef}
        className="fixed top-0 left-0 pointer-events-none z-[999999] hidden md:block"
        style={{
          width: '16px',
          height: '16px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${currentColors.glow} 0%, transparent 70%)`,
          filter: 'blur(6px)',
          mixBlendMode: 'screen',
          opacity: 0.4,
          willChange: 'transform',
          transition: 'opacity 0.2s ease-out',
        }}
      />

      {/* Ripple container for click effects */}
      <div ref={rippleContainerRef} className="fixed top-0 left-0 pointer-events-none z-[999998] hidden md:block" />

      <style>{`
        @keyframes rippleExpand {
          0% {
            transform: translate(-50%, -50%) scale(0);
            opacity: 0.6;
          }
          100% {
            transform: translate(-50%, -50%) scale(4);
            opacity: 0;
          }
        }

        /* Button hover effects */
        button:hover, a:hover, [role="button"]:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3), 0 0 20px rgba(59, 130, 246, 0.2);
          border-color: rgba(59, 130, 246, 0.5);
          transition: all 0.2s ease-out;
        }

        /* Prediction card hover effects */
        .match-card:hover {
          transform: translateY(-3px);
          border-color: rgba(59, 130, 246, 0.6);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 30px rgba(59, 130, 246, 0.15);
          background: rgba(20, 20, 20, 0.95);
          transition: all 0.25s ease-out;
        }

        /* Navigation hover effects */
        .nav-item {
          position: relative;
        }
        .nav-item::after {
          content: '';
          position: absolute;
          bottom: -2px;
          left: 0;
          width: 0;
          height: 2px;
          background: linear-gradient(90deg, #3B82F6, #60A5FA);
          transition: width 0.3s ease-out;
        }
        .nav-item:hover::after {
          width: 100%;
        }
        .nav-item:hover {
          text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
          transition: all 0.2s ease-out;
        }
      `}</style>
    </>
  );
};

export default CursorFX;
