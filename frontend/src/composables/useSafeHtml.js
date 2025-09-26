import DOMPurify from 'dompurify'

export function useSafeHtml() {
  const sanitizeAndFormat = content => {
    if (!content) return ''

    // Configure DOMPurify to allow only specific formatting tags
    const purifyConfig = {
      ALLOWED_TAGS: ['strong', 'em', 'br'],
      ALLOWED_ATTR: [],
      KEEP_CONTENT: true,
      RETURN_DOM: false,
      RETURN_DOM_FRAGMENT: false,
      RETURN_TRUSTED_TYPE: false,
    }

    // Convert markdown-style formatting to HTML
    const formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>')

    // DOMPurify handles all XSS prevention including HTML escaping
    return DOMPurify.sanitize(formatted, purifyConfig)
  }

  const sanitizeAndFormatCorrected = correctedText => {
    if (!correctedText) return ''

    // Configure DOMPurify for correction display (allows colored strong tags)
    const purifyConfig = {
      ALLOWED_TAGS: ['strong', 'em'],
      ALLOWED_ATTR: ['class'],
      KEEP_CONTENT: true,
      RETURN_DOM: false,
      RETURN_DOM_FRAGMENT: false,
      RETURN_TRUSTED_TYPE: false,
    }

    // Convert markdown-style formatting with correction styling
    const formatted = correctedText
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-green-600">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')

    // DOMPurify handles all XSS prevention including HTML escaping
    return DOMPurify.sanitize(formatted, purifyConfig)
  }

  return {
    sanitizeAndFormat,
    sanitizeAndFormatCorrected,
  }
}
