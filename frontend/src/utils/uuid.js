/**
 * Cross-browser UUID v4 generator with Safari fallback support
 *
 * Provides compatibility for:
 * - Modern browsers: crypto.randomUUID()
 * - Safari 11+/iOS 11+: crypto.getRandomValues()
 * - Legacy browsers: Math.random() fallback
 */

/**
 * Generate a UUID v4 string with cross-browser compatibility
 * @returns {string} UUID v4 formatted string
 */
export function generateUUID() {
  // Modern browsers (Chrome 92+, Firefox 95+, Safari 15.4+)
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }

  // Fallback for Safari 11+ using crypto.getRandomValues()
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(
      /[xy]/g,
      function (c) {
        const r = crypto.getRandomValues(new Uint8Array(1))[0] % 16
        const v = c === 'x' ? r : (r & 0x3) | 0x8
        return v.toString(16)
      }
    )
  }

  // Last resort fallback for ancient browsers (less secure)
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}
