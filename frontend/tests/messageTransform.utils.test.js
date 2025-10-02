import { describe, it, expect } from 'vitest'
import { transformMessagesForContext } from '@/utils/messageTransform.js'

describe('transformMessagesForContext', () => {
  it('returns empty array for empty input', () => {
    expect(transformMessagesForContext([])).toEqual([])
  })

  it('returns empty array for null input', () => {
    expect(transformMessagesForContext(null)).toEqual([])
  })

  it('returns empty array for undefined input', () => {
    expect(transformMessagesForContext(undefined)).toEqual([])
  })

  it('extracts type and content from messages', () => {
    const messages = [
      { type: 'user', content: 'Hello', timestamp: 1, corrections: [] },
      { type: 'user', content: 'How are you?', timestamp: 2, tokens_used: 50 },
    ]

    const result = transformMessagesForContext(messages, 20)

    expect(result).toEqual([
      { type: 'user', content: 'Hello' },
      { type: 'user', content: 'How are you?' },
    ])
  })

  it('removes extra fields from messages', () => {
    const messages = [
      {
        type: 'user',
        content: 'Hello',
        timestamp: 123,
        corrections: [],
        tokens_used: 50,
        isStartMessage: true,
      },
    ]

    const result = transformMessagesForContext(messages, 20)

    expect(result).toEqual([{ type: 'user', content: 'Hello' }])
    expect(result[0]).not.toHaveProperty('timestamp')
    expect(result[0]).not.toHaveProperty('corrections')
    expect(result[0]).not.toHaveProperty('tokens_used')
    expect(result[0]).not.toHaveProperty('isStartMessage')
  })

  it('uses next_phrase for AI messages', () => {
    const messages = [
      {
        type: 'ai',
        ai_response: 'Technical explanation',
        next_phrase: 'Conversational response',
        timestamp: 1,
      },
    ]

    const result = transformMessagesForContext(messages, 20)

    expect(result).toEqual([{ type: 'ai', content: 'Conversational response' }])
  })

  it('falls back to content if next_phrase not available', () => {
    const messages = [{ type: 'user', content: 'User message', timestamp: 2 }]

    const result = transformMessagesForContext(messages, 20)

    expect(result).toEqual([{ type: 'user', content: 'User message' }])
  })

  it('respects limit parameter', () => {
    const messages = Array.from({ length: 50 }, (_, i) => ({
      type: 'user',
      content: `Message ${i}`,
      timestamp: i,
    }))

    const result = transformMessagesForContext(messages, 10)

    expect(result.length).toBeLessThanOrEqual(10)
    expect(result[0].content).toContain('Message')
  })

  it('handles empty content strings', () => {
    const messages = [
      { type: 'user', content: '', timestamp: 1 },
      { type: 'user', content: '   ', timestamp: 2 },
      { type: 'user', content: 'Valid', timestamp: 3 },
    ]

    const result = transformMessagesForContext(messages, 20)

    expect(result).toHaveLength(1)
    expect(result[0].content).toBe('Valid')
  })

  it('handles messages with both next_phrase and content', () => {
    const messages = [
      {
        type: 'ai',
        content: 'Fallback content',
        next_phrase: 'Primary content',
        ai_response: 'Technical response',
        timestamp: 1,
      },
    ]

    const result = transformMessagesForContext(messages, 20)

    expect(result).toHaveLength(1)
    expect(result[0].content).toBe('Primary content')
  })

  it('handles mixed user and AI messages', () => {
    const messages = [
      { type: 'user', content: 'Hello', timestamp: 1 },
      {
        type: 'ai',
        next_phrase: 'Hi there!',
        ai_response: 'Greeting response',
        timestamp: 2,
      },
      { type: 'user', content: 'How are you?', timestamp: 3 },
    ]

    const result = transformMessagesForContext(messages, 20)

    expect(result).toHaveLength(3)
    expect(result[0]).toEqual({ type: 'user', content: 'Hello' })
    expect(result[1]).toEqual({ type: 'ai', content: 'Hi there!' })
    expect(result[2]).toEqual({ type: 'user', content: 'How are you?' })
  })
})
