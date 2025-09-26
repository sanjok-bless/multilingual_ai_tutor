/**
 * Timezone-aware date utilities for session management
 * Following YAGNI principle - only what's needed for daily session checking
 */

/**
 * Check if a timestamp is from today in user's local timezone
 * @param {number} timestamp - UTC timestamp in milliseconds
 * @returns {boolean} - true if timestamp is from today
 */
export function isToday(timestamp) {
  const today = new Date()
  const compareDate = new Date(timestamp)

  return (
    today.getFullYear() === compareDate.getFullYear() &&
    today.getMonth() === compareDate.getMonth() &&
    today.getDate() === compareDate.getDate()
  )
}

/**
 * Check if session needs a daily start message
 * @param {Object} session - Session object with lastActivity timestamp
 * @returns {boolean} - true if session needs fresh start message
 */
export function needsDailyStart(session) {
  if (!session?.lastActivity) return true
  return !isToday(session.lastActivity)
}
