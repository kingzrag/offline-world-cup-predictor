/**
 * src/flagUtils.ts
 * ──────────────────────────────────────────────────────────────────────────────
 * Converts a country/team name into a flag emoji without a hardcoded FLAG_MAP.
 *
 * How it works
 * ─────────────
 * 1. Normalise the name (lowercase, trim).
 * 2. Look it up in ALIAS_MAP — a small hand-curated table for names that don't
 *    match the standard country name used by Intl (e.g. "USA" → "US",
 *    "England" → "GB-ENG", "Bosnia-Herzegovina" → "BA").
 * 3. If no alias, derive the ISO 3166-1 alpha-2 code from the name by querying
 *    the browser's Intl.DisplayNames API (language "en", type "region").
 *    We iterate over a precomputed region→name map and find the match.
 * 4. Build the emoji from the two regional indicator symbols (U+1F1E6 + offset).
 * 5. GB subdivisions (England, Scotland, Wales, Northern Ireland) are returned
 *    as their Unicode tag-flag sequences instead.
 *
 * Complexity: the region→name map is built once (module-level) and cached.
 * All subsequent calls are O(1) alias lookups or O(n) map lookups where n ≤ 250.
 */

// ── Alias map ────────────────────────────────────────────────────────────────
// Maps common alternate team names → ISO 3166-1 alpha-2 codes (or special tags).
// Add entries here whenever the API sends a name that doesn't match the
// standard English country name used by Intl.DisplayNames.

const ALIAS_MAP: Record<string, string> = {
  // United States
  "usa":                        "US",
  "united states":              "US",
  "united states of america":   "US",

  // United Kingdom home nations (use Unicode tag sequences)
  "england":                    "GB-ENG",
  "scotland":                   "GB-SCT",
  "wales":                      "GB-WLS",
  "northern ireland":           "GB-NIR",

  // Common alternate spellings / FIFA names
  "bosnia-herzegovina":         "BA",
  "bosnia & herzegovina":       "BA",
  "bosnia and herzegovina":     "BA",
  "ivory coast":                "CI",
  "côte d'ivoire":              "CI",
  "cote d'ivoire":              "CI",
  "cape verde":                 "CV",
  "cape verde islands":         "CV",
  "curacao":                    "CW",
  "curaçao":                    "CW",
  "north macedonia":            "MK",
  "republic of ireland":        "IE",
  "ireland":                    "IE",
  "trinidad & tobago":          "TT",
  "trinidad and tobago":        "TT",
  "korea republic":             "KR",
  "south korea":                "KR",
  "korea dpr":                  "KP",
  "north korea":                "KP",
  "dr congo":                   "CD",
  "democratic republic of congo":"CD",
  "congo dr":                   "CD",
  "republic of congo":          "CG",
  "congo":                      "CG",
  "guinea-bissau":              "GW",
  "guinea bissau":              "GW",
  "equatorial guinea":          "GQ",
  "central african republic":   "CF",
  "south africa":               "ZA",
  "saint kitts and nevis":      "KN",
  "saint lucia":                "LC",
  "saint vincent and the grenadines": "VC",
  "antigua and barbuda":        "AG",
  "uae":                        "AE",
  "united arab emirates":       "AE",
  "chinese taipei":             "TW",
  "hong kong":                  "HK",
  "new zealand":                "NZ",
  "papua new guinea":           "PG",
  "burkina faso":               "BF",
  "sierra leone":               "SL",
  "the gambia":                 "GM",
  "gambia":                     "GM",
  "kyrgyz republic":            "KG",
  "moldova":                    "MD",
};


// ── Unicode tag-flag sequences for GB subdivisions ───────────────────────────

const GB_SUBDIVISIONS: Record<string, string> = {
  "GB-ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  "GB-SCT": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
  "GB-WLS": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
  "GB-NIR": "🇬🇧", // No standard emoji; fall back to UK flag
};

// ── ISO alpha-2 → display name map (built once) ──────────────────────────────

let _regionNameMap: Map<string, string> | null = null;

function buildRegionNameMap(): Map<string, string> {
  if (_regionNameMap) return _regionNameMap;
  _regionNameMap = new Map();

  try {
    // All ISO 3166-1 alpha-2 codes (A–Z × A–Z, filtered to valid regions)
    const displayNames = new Intl.DisplayNames(["en"], { type: "region" });
    for (let i = 65; i <= 90; i++) {
      for (let j = 65; j <= 90; j++) {
        const code = String.fromCharCode(i) + String.fromCharCode(j);
        try {
          const name = displayNames.of(code);
          if (name && name !== code) {
            // Store normalised lowercase name → code
            _regionNameMap.set(name.toLowerCase(), code);
          }
        } catch {
          // Invalid code — skip
        }
      }
    }
  } catch {
    // Intl.DisplayNames not supported (very old browsers) — map stays empty
  }

  return _regionNameMap;
}

// ── ISO alpha-2 → flag emoji ─────────────────────────────────────────────────

function isoToEmoji(code: string): string {
  // Each letter maps to a Regional Indicator Symbol (U+1F1E6 = A)
  return Array.from(code.toUpperCase())
    .map(c => String.fromCodePoint(0x1f1e6 + c.charCodeAt(0) - 65))
    .join("");
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * getFlag(countryName)
 *
 * Returns a flag emoji for any country / team name string.
 * Falls back to 🏳️ when no match can be found.
 *
 * @example
 *   getFlag("Brazil")           // "🇧🇷"
 *   getFlag("USA")              // "🇺🇸"
 *   getFlag("England")          // "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
 *   getFlag("Bosnia-Herzegovina") // "🇧🇦"
 *   getFlag("Ivory Coast")      // "🇨🇮"
 */
export function getFlag(countryName: string): string {
  if (!countryName) return "🏳️";

  const normalised = countryName.trim().toLowerCase();

  // 1. Check alias map
  const aliasCode = ALIAS_MAP[normalised];
  if (aliasCode) {
    if (aliasCode in GB_SUBDIVISIONS) return GB_SUBDIVISIONS[aliasCode];
    return isoToEmoji(aliasCode);
  }

  // 2. Try exact match in Intl region→name map
  const regionMap = buildRegionNameMap();
  const exactCode = regionMap.get(normalised);
  if (exactCode) return isoToEmoji(exactCode);

  // 3. Try partial / prefix match (handles "Netherlands" vs "Netherlands (the)" etc.)
  for (const [name, code] of regionMap) {
    if (name.startsWith(normalised) || normalised.startsWith(name)) {
      return isoToEmoji(code);
    }
  }

  // 4. No match — return neutral white flag
  return "🏳️";
}
