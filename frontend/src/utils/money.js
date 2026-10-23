// Purpose: Utility functions for sen to RM conversions and monetary formatting.
// Security: Ensures integer sen arithmetic on frontend; prevents floating-point corruption.

/**
 * Convert integer sen to Malaysian Ringgit display string (e.g. 1250 -> "RM 12.50").
 * @param {number} sen - Amount in sen
 * @returns {string} Formatted RM string
 */
export function formatRm(sen) {
  if (sen === null || sen === undefined || isNaN(sen)) {
    return "RM 0.00";
  }
  const rm = (sen / 100).toFixed(2);
  return `RM ${rm}`;
}

/**
 * Convert integer sen to decimal string for numeric input fields (e.g. 1250 -> "12.50").
 * @param {number} sen
 * @returns {string}
 */
export function senToRmInput(sen) {
  if (sen === null || sen === undefined || isNaN(sen)) {
    return "";
  }
  return (sen / 100).toFixed(2);
}

/**
 * Convert RM input string or number to integer sen (e.g. "12.50" -> 1250, "12" -> 1200).
 * @param {string|number} rmValue
 * @returns {number} Integer sen
 */
export function rmToSen(rmValue) {
  if (!rmValue && rmValue !== 0) return 0;
  const cleaned = String(rmValue).trim().replace(/,/g, "");
  const num = parseFloat(cleaned);
  if (isNaN(num)) return 0;
  return Math.round(num * 100);
}
