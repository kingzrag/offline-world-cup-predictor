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

// Duration of the scroll animation (ms)
const ANIMATION_DURATION = 800;
// Extra cooldown after animation to absorb trackpad momentum inertia (ms)
const MOMENTUM_COOLDOWN = 250;
// Minimum wheel delta to count as an intentional gesture
const INTENT_THRESHOLD = 35;

export function useViewportSnap({
  activeTab,
  sectionIds = DEFAULT_SECTIONS,
  enabled = true,
}: UseViewportSnapOptions) {
  const activeIndexRef = useRef(0);
  const isLockedRef = useRef(false);

  useEffect(() => {
    if (!enabled || activeTab !== 'home' || typeof window === 'undefined') return;

    // Only enable on desktop non-touch screens
    const isDesktop = window.innerWidth >= 768;
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (!isDesktop || isTouch) return;

    // -------------------------------------------------------------------
    // Helper: resolve chapter elements in document order
    // -------------------------------------------------------------------
    const getElements = (): Array<HTMLElement | null> =>
      sectionIds.map((id) => document.getElementById(id));

    // -------------------------------------------------------------------
    // Helper: find which chapter is closest to viewport top right now
    // -------------------------------------------------------------------
    const syncActiveIndex = () => {
      const els = getElements();
      let bestIdx = 0;
      let bestDist = Infinity;
      els.forEach((el, i) => {
        if (!el) return;
        const dist = Math.abs(el.getBoundingClientRect().top);
        if (dist < bestDist) {
          bestDist = dist;
          bestIdx = i;
        }
      });
      activeIndexRef.current = bestIdx;
    };

    // -------------------------------------------------------------------
    // Helper: smoothly scroll to chapter at index and engage lock
    // -------------------------------------------------------------------
    const goToChapter = (idx: number) => {
      const els = getElements();
      const target = els[idx];
      if (!target) return;

      const targetTop = window.scrollY + target.getBoundingClientRect().top;

      isLockedRef.current = true;
      activeIndexRef.current = idx;

      window.scrollTo({ top: targetTop, behavior: 'smooth' });

      // Unlock after animation + momentum cooldown
      setTimeout(() => {
        isLockedRef.current = false;
        // Sync index in case user manually scrolled mid-animation
        syncActiveIndex();
      }, ANIMATION_DURATION + MOMENTUM_COOLDOWN);
    };

    // -------------------------------------------------------------------
    // Wheel handler: detect intent and transition
    // -------------------------------------------------------------------
    const handleWheel = (e: WheelEvent) => {
      // Ignore horizontal scrolls (trackpad two-finger side swipe)
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;

      const delta = e.deltaY;

      // Ignore tiny accidental movements
      if (Math.abs(delta) < INTENT_THRESHOLD) return;

      // Block if currently animating
      if (isLockedRef.current) {
        e.preventDefault();
        return;
      }

      const current = activeIndexRef.current;
      const maxIdx = sectionIds.length - 1;

      const nextIdx = delta > 0
        ? Math.min(current + 1, maxIdx)   // scroll down → next chapter
        : Math.max(current - 1, 0);       // scroll up   → previous chapter

      // Already at edge — let browser handle naturally
      if (nextIdx === current) return;

      // Intercept and drive the transition
      e.preventDefault();
      goToChapter(nextIdx);
    };

    // -------------------------------------------------------------------
    // Sync on resize so index stays accurate
    // -------------------------------------------------------------------
    const handleResize = () => syncActiveIndex();

    // Initial sync to whatever chapter is visible on mount
    syncActiveIndex();

    // Use { capture: true } so we receive the event before browser default
    window.addEventListener('wheel', handleWheel, { passive: false, capture: true });
    window.addEventListener('resize', handleResize, { passive: true });

    return () => {
      window.removeEventListener('wheel', handleWheel, { capture: true });
      window.removeEventListener('resize', handleResize);
    };
  }, [activeTab, sectionIds, enabled]);
}
