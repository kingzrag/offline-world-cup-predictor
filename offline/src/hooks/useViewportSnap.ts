import { useEffect, useRef } from 'react';

interface UseViewportSnapOptions {
  activeTab: string;
  sectionIds?: string[];
  enabled?: boolean;
}

const DEFAULT_SECTIONS = [
  'editorial-hero',
  'todays-best-predictions',
  'competition-archive',
  'the-model-section',
  'app-footer',
];

export function useViewportSnap({
  activeTab,
  sectionIds = DEFAULT_SECTIONS,
  enabled = true,
}: UseViewportSnapOptions) {
  const isSnappingRef = useRef(false);
  const lastScrollYRef = useRef(0);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const visibleRatiosRef = useRef<Record<string, number>>({});

  useEffect(() => {
    // Only enable on desktop/tablet viewports (>= 768px) on the home tab
    if (!enabled || activeTab !== 'home' || typeof window === 'undefined') return;

    const isDesktop = window.innerWidth >= 768;
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (!isDesktop || isTouch) return;

    lastScrollYRef.current = window.scrollY;

    // 1. Setup IntersectionObserver to track visibility ratio of each chapter section
    const observerCallback: IntersectionObserverCallback = (entries) => {
      entries.forEach((entry) => {
        if (entry.target.id) {
          visibleRatiosRef.current[entry.target.id] = entry.intersectionRatio;
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, {
      threshold: [0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0],
    });

    const elements: HTMLElement[] = [];
    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) {
        elements.push(el);
        observer.observe(el);
      }
    });

    // 2. Debounced scroll handler to trigger gentle alignment after scrolling settles
    const handleScroll = () => {
      if (isSnappingRef.current) return;

      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }

      scrollTimeoutRef.current = setTimeout(() => {
        const currentScrollY = window.scrollY;
        const delta = Math.abs(currentScrollY - lastScrollYRef.current);

        // Ignore tiny accidental touchpad movements (< 50px)
        if (delta < 50) {
          lastScrollYRef.current = currentScrollY;
          return;
        }

        // Find section with highest visibility or threshold >= 45%
        let bestId: string | null = null;
        let maxRatio = 0;

        sectionIds.forEach((id) => {
          const ratio = visibleRatiosRef.current[id] || 0;
          if (ratio > maxRatio) {
            maxRatio = ratio;
            bestId = id;
          }
        });

        // Trigger gentle alignment if a target section is meaningfully visible (>= 40%)
        if (bestId && maxRatio >= 0.4) {
          const targetEl = document.getElementById(bestId);
          if (targetEl) {
            const rect = targetEl.getBoundingClientRect();
            const targetTop = window.scrollY + rect.top;

            // Only snap if target is not already aligned near top (within 30px)
            if (Math.abs(rect.top) > 30) {
              isSnappingRef.current = true;
              window.scrollTo({
                top: targetTop,
                behavior: 'smooth',
              });

              // Reset snapping lock after smooth animation settles
              setTimeout(() => {
                isSnappingRef.current = false;
                lastScrollYRef.current = window.scrollY;
              }, 750);
              return;
            }
          }
        }

        lastScrollYRef.current = currentScrollY;
      }, 200);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      observer.disconnect();
    };
  }, [activeTab, sectionIds, enabled]);
}
