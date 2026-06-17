/**
 * dateTimeUtils.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * Kickoff times are stored and transmitted as ISO-8601 UTC strings.
 * All display and filter helpers convert to the visitor's local timezone
 * using browser Intl APIs (no hardcoded timezone).
 */

/** IANA timezone detected from the browser, e.g. "America/New_York". */
export function getUserTimeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return "UTC";
  }
}

/** Short timezone label, e.g. IST, EDT, BST, JST. */
export function getTimezoneAbbreviation(
  date: Date = new Date(),
  timeZone: string = getUserTimeZone()
): string {
  try {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone,
      timeZoneName: "short",
    }).formatToParts(date);
    return parts.find((p) => p.type === "timeZoneName")?.value ?? "";
  } catch {
    return "";
  }
}

/** Local calendar date as YYYY-MM-DD (for Today/Tomorrow filters). */
export function getLocalDateKey(
  isoStr: string | null | undefined,
  timeZone: string = getUserTimeZone()
): string {
  if (!isoStr) return "";
  try {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date(isoStr));
  } catch {
    return "";
  }
}

export function getTodayLocalDateKey(timeZone: string = getUserTimeZone()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

export function getTomorrowLocalDateKey(timeZone: string = getUserTimeZone()): string {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(tomorrow);
}

export function isKickoffToday(isoStr: string | null | undefined): boolean {
  if (!isoStr) return false;
  return getLocalDateKey(isoStr) === getTodayLocalDateKey();
}

export function isKickoffTomorrow(isoStr: string | null | undefined): boolean {
  if (!isoStr) return false;
  return getLocalDateKey(isoStr) === getTomorrowLocalDateKey();
}

/** Short date for cards, e.g. "Jun 15, 2026". */
export function formatKickoffDateLocal(isoStr: string | null | undefined): string {
  if (!isoStr) return "Unknown Date";
  try {
    return new Date(isoStr).toLocaleDateString("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric",
    });
  } catch {
    return "Unknown Date";
  }
}

/** Time with timezone abbrev, e.g. "12:30 AM IST". */
export function formatKickoffTimeLocal(isoStr: string | null | undefined): string {
  if (!isoStr) return "TBD";
  try {
    const d = new Date(isoStr);
    const time = d.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    const tz = getTimezoneAbbreviation(d);
    return tz ? `${time} ${tz}` : time;
  } catch {
    return "TBD";
  }
}

/** Full kickoff string, e.g. "Sun 15 Jun · 12:30 AM IST". */
export function formatSmartKickoffLocal(isoStr: string | null | undefined): string {
  if (!isoStr) return "TBD";
  try {
    const d = new Date(isoStr);
    const weekday = d.toLocaleDateString("en-US", { weekday: "short" });
    const day = d.toLocaleDateString("en-US", { day: "numeric" });
    const month = d.toLocaleDateString("en-US", { month: "short" });
    const time = d.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    const tz = getTimezoneAbbreviation(d);
    return `${weekday} ${day} ${month} · ${time}${tz ? ` ${tz}` : ""}`.trim();
  } catch {
    return "TBD";
  }
}

/** Date + time for analysis/detail views. */
export function formatKickoffDateTimeLocal(isoStr: string | null | undefined): string {
  if (!isoStr) return "TBD";
  try {
    const d = new Date(isoStr);
    const date = d.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
    const time = d.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    const tz = getTimezoneAbbreviation(d);
    return tz ? `${date} at ${time} ${tz}` : `${date} at ${time}`;
  } catch {
    return "TBD";
  }
}
