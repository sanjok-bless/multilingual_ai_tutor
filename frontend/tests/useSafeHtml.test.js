import { describe, it, expect } from 'vitest'
import { useSafeHtml } from '@/composables/useSafeHtml'

describe('useSafeHtml', () => {
  const { sanitizeAndFormat, sanitizeAndFormatCorrected } = useSafeHtml()

  describe('Core Functionality', () => {
    it('should handle null/undefined/empty input', () => {
      expect(sanitizeAndFormat(null)).toBe('')
      expect(sanitizeAndFormat(undefined)).toBe('')
      expect(sanitizeAndFormat('')).toBe('')
      expect(sanitizeAndFormatCorrected(null)).toBe('')
      expect(sanitizeAndFormatCorrected(undefined)).toBe('')
      expect(sanitizeAndFormatCorrected('')).toBe('')
    })

    it('should convert markdown-style bold to HTML strong tags', () => {
      expect(sanitizeAndFormat('**bold text**')).toBe(
        '<strong>bold text</strong>'
      )
      expect(sanitizeAndFormat('This is **bold** text')).toBe(
        'This is <strong>bold</strong> text'
      )
    })

    it('should convert markdown-style italic to HTML em tags', () => {
      expect(sanitizeAndFormat('*italic text*')).toBe('<em>italic text</em>')
      expect(sanitizeAndFormat('This is *italic* text')).toBe(
        'This is <em>italic</em> text'
      )
    })

    it('should convert newlines to br tags', () => {
      expect(sanitizeAndFormat('line1\nline2')).toBe('line1<br>line2')
      expect(sanitizeAndFormat('line1\nline2\nline3')).toBe(
        'line1<br>line2<br>line3'
      )
    })

    it('should handle mixed formatting', () => {
      const input = 'This is **bold** and *italic*\nOn new line'
      const expected =
        'This is <strong>bold</strong> and <em>italic</em><br>On new line'
      expect(sanitizeAndFormat(input)).toBe(expected)
    })

    it('should sanitize dangerous HTML by removing unsafe elements', () => {
      expect(sanitizeAndFormat('<script>alert("xss")</script>')).toBe('')
      expect(sanitizeAndFormat('<img src="x" onerror="alert(1)">')).toBe('')
      expect(sanitizeAndFormat('<div onclick="alert(1)">text</div>')).toBe(
        'text'
      )
    })

    it('should handle nested markdown safely', () => {
      expect(sanitizeAndFormat('***nested***')).toBe(
        '<strong><em>nested</em></strong>'
      )
      expect(sanitizeAndFormat('**bold *and italic* text**')).toBe(
        '<strong>bold <em>and italic</em> text</strong>'
      )
    })

    it('should preserve safe HTML entities', () => {
      expect(sanitizeAndFormat('&amp; &lt; &gt;')).toBe('&amp; &lt; &gt;')
    })

    it('should handle special characters', () => {
      expect(sanitizeAndFormat('text & "quotes" \'apostrophes\'')).toBe(
        'text & "quotes" \'apostrophes\''
      )
    })
  })

  describe('Correction Formatting', () => {
    it('should convert markdown bold to green-colored strong tags', () => {
      expect(sanitizeAndFormatCorrected('**corrected**')).toBe(
        '<strong class="text-green-600">corrected</strong>'
      )
      expect(sanitizeAndFormatCorrected('This is **fixed** text')).toBe(
        'This is <strong class="text-green-600">fixed</strong> text'
      )
    })

    it('should convert markdown italic to em tags', () => {
      expect(sanitizeAndFormatCorrected('*italic*')).toBe('<em>italic</em>')
    })

    it('should sanitize dangerous HTML by removing unsafe elements', () => {
      expect(sanitizeAndFormatCorrected('<script>alert("xss")</script>')).toBe(
        ''
      )
      expect(
        sanitizeAndFormatCorrected('<img src="x" onerror="alert(1)">')
      ).toBe('')
    })

    it('should preserve class attribute on strong tags only', () => {
      const input = '**bold** text'
      const result = sanitizeAndFormatCorrected(input)
      expect(result).toBe('<strong class="text-green-600">bold</strong> text')
    })

    it('should handle mixed formatting', () => {
      const input = 'Fixed **word** and *emphasis*'
      const expected =
        'Fixed <strong class="text-green-600">word</strong> and <em>emphasis</em>'
      expect(sanitizeAndFormatCorrected(input)).toBe(expected)
    })

    it('should handle special characters', () => {
      expect(sanitizeAndFormatCorrected('text & "quotes"')).toBe(
        'text & "quotes"'
      )
    })
  })

  describe('XSS Prevention', () => {
    const coreXssVectors = [
      { name: 'script injection', payload: '<script>alert("xss")</script>' },
      { name: 'event handler', payload: '<img src="x" onerror="alert(1)">' },
      {
        name: 'javascript URL',
        payload: '<iframe src="javascript:alert(1)"></iframe>',
      },
      { name: 'svg onload', payload: '<svg onload="alert(1)">' },
    ]

    coreXssVectors.forEach(({ name, payload }) => {
      it(`should prevent ${name} XSS`, () => {
        const result1 = sanitizeAndFormat(payload)
        const result2 = sanitizeAndFormatCorrected(payload)

        // Should remove dangerous elements entirely
        expect(result1).toBe('')
        expect(result2).toBe('')
      })
    })
  })

  describe('Content Preservation', () => {
    it('should preserve legitimate content', () => {
      const testContent =
        'Hello world! Numbers: 123, Unicode: 你好 🌍 éñ, Special: !@#$%^&*()'
      expect(sanitizeAndFormat(testContent)).toBe(testContent)
      expect(sanitizeAndFormatCorrected(testContent)).toBe(testContent)
    })
  })
})
