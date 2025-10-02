/**
 * Transform messages for API context processing.
 * Extracts messages with minimal payload (type and content only).
 */

/**
 * Transform full message objects to minimal context format.
 * @param {Array} messages - Full message history from store
 * @param {number} limit - Maximum number of messages to include
 * @returns {Array} Transformed messages with {type, content} structure
 */
export function transformMessagesForContext(messages = [], limit = 40) {
  if (!Array.isArray(messages) || messages.length === 0) {
    return []
  }

  // Optimization: Pre-slice to reasonable window to reduce iterations
  const recentMessages = messages.slice(-limit)
  const context = []

  // Process messages in chronological order
  for (let i = 0; i < recentMessages.length; i++) {
    const msg = recentMessages[i]

    const content = msg.next_phrase || msg.content || ''
    if (content.trim()) {
      context.push({
        type: msg.type,
        content: content,
      })
    }
  }

  // Return last N messages from validated context
  return context.slice(-limit)
}
