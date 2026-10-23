/**
 * riskUtils — shared helpers for translating V4 Conversation-Safety
 * risk levels into the three-color SafetyAlert levels used throughout
 * the TrustMatch AI UI.
 *
 * V4 /safety/analyze returns:  { risk_level: "low" | "moderate" | "high" }
 * SafetyAlert expects:          level  : "safe" | "caution" | "risk"
 */

/** Map a V4 `risk_level` → SafetyAlert `level`. */
export const RISK_LEVEL_MAP = {
  low: 'safe',
  moderate: 'caution',
  high: 'risk',
};

/** Default risk level returned by the backend when none is given. */
export const DEFAULT_RISK_LEVEL = 'low';

/** Default SafetyAlert level used as a fallback. */
export const DEFAULT_ALERT_LEVEL = 'safe';

/**
 * Convert a V4 `risk_level` string ("low" | "moderate" | "high") into the
 * corresponding SafetyAlert level ("safe" | "caution" | "risk").
 *
 * Returns "safe" for unknown / missing values so the UI never breaks.
 *
 * @param {string} [riskLevel] — the risk level from the backend
 * @returns {"safe" | "caution" | "risk"}
 */
export const riskToLevel = (riskLevel) => {
  if (!riskLevel) return DEFAULT_ALERT_LEVEL;
  return RISK_LEVEL_MAP[riskLevel] || DEFAULT_ALERT_LEVEL;
};

/**
 * Reverse lookup: SafetyAlert level → V4 risk_level.
 * Useful when you need to send a user-selected level back to the API.
 */
export const ALERT_LEVEL_MAP = {
  safe: 'low',
  caution: 'moderate',
  risk: 'high',
};

/**
 * @param {"safe" | "caution" | "risk"} [level]
 * @returns {"low" | "moderate" | "high"}
 */
export const levelToRisk = (level) => {
  if (!level) return DEFAULT_RISK_LEVEL;
  return ALERT_LEVEL_MAP[level] || DEFAULT_RISK_LEVEL;
};

/** Human-readable labels for display. */
export const RISK_LABELS = {
  low: 'Low Risk',
  moderate: 'Moderate Risk',
  high: 'High Risk',
};

/**
 * @param {string} [riskLevel]
 * @returns {string} e.g. "Low Risk", "Moderate Risk", "High Risk"
 */
export const riskLabel = (riskLevel) => {
  if (!riskLevel) return RISK_LABELS[DEFAULT_RISK_LEVEL];
  return RISK_LABELS[riskLevel] || RISK_LABELS[DEFAULT_RISK_LEVEL];
};

/**
 * Numerical severity used for sorting arrays of results.
 *   low = 1, moderate = 2, high = 3
 */
export const RISK_SEVERITY = {
  low: 1,
  moderate: 2,
  high: 3,
};

/**
 * Sort an array of safety / privacy results by risk severity (ascending).
 *
 * Each item is expected to have a `risk_level` field.  Items with unknown
 * risk levels are treated as `low` so they sort first.
 *
 * @param {Array} items
 * @returns {Array} a new, sorted array (does not mutate the input)
 */
export const sortByRisk = (items) => {
  if (!Array.isArray(items)) return [];
  return [...items].sort((a, b) => {
    const sa = RISK_SEVERITY[a?.risk_level] ?? RISK_SEVERITY[DEFAULT_RISK_LEVEL];
    const sb = RISK_SEVERITY[b?.risk_level] ?? RISK_SEVERITY[DEFAULT_RISK_LEVEL];
    return sa - sb;
  });
};

export default {
  RISK_LEVEL_MAP,
  DEFAULT_RISK_LEVEL,
  DEFAULT_ALERT_LEVEL,
  riskToLevel,
  ALERT_LEVEL_MAP,
  levelToRisk,
  RISK_LABELS,
  riskLabel,
  RISK_SEVERITY,
  sortByRisk,
};
