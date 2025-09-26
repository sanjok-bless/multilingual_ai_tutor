import axios from 'axios'

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_PREFIX = '/api/v1'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  config => {
    // Add timestamp to prevent caching
    config.headers['X-Request-Time'] = Date.now().toString()

    // Log request in development
    if (import.meta.env.DEV) {
      console.log(
        `API Request: ${config.method?.toUpperCase()} ${config.url}`,
        {
          data: config.data,
          params: config.params,
        }
      )
    }

    return config
  },
  error => {
    console.error('Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  response => {
    // Log response in development
    if (import.meta.env.DEV) {
      console.log(
        `API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`,
        response.data
      )
    }

    return response
  },
  error => {
    // Enhanced error logging
    if (import.meta.env.DEV) {
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      })
    }

    // Handle specific error cases
    if (error.code === 'ECONNABORTED') {
      error.message = 'Please check your internet connection.'
    } else if (error.message === 'Network Error') {
      error.message = 'Unable to connect to the server. Please try again.'
    }

    return Promise.reject(error)
  }
)

// API service class
class ApiService {
  /**
   * Send a chat message to the AI tutor
   */
  async sendChatMessage({ session_id, message, language, level }) {
    try {
      const response = await apiClient.post('/chat', {
        session_id,
        message,
        language,
        level,
      })

      // Validate response structure
      this._validateChatResponse(response.data)

      return response.data
    } catch (error) {
      throw this._enhanceChatError(error)
    }
  }

  /**
   * Request a start message from the AI tutor
   */
  async requestStartMessage({ session_id, language, level }) {
    try {
      const response = await apiClient.post('/start', {
        session_id,
        language,
        level,
      })

      // Validate response structure
      this._validateStartMessageResponse(response.data)

      return response.data
    } catch (error) {
      throw this._enhanceStartMessageError(error)
    }
  }

  /**
   * Get list of supported languages
   */
  async getSupportedLanguages() {
    try {
      const response = await apiClient.get('/languages')
      return response.data
    } catch (error) {
      console.error('Error fetching supported languages:', error)
      throw error
    }
  }

  // Private validation methods
  _validateChatResponse(data) {
    if (!data) {
      throw new Error('Empty response from chat endpoint')
    }

    // Check for required fields based on backend schema
    const requiredFields = ['ai_response']
    const missingFields = requiredFields.filter(field => !data[field])

    if (missingFields.length > 0) {
      console.warn('Chat response missing fields:', missingFields, data)
    }

    // Ensure corrections is an array
    if (data.corrections && !Array.isArray(data.corrections)) {
      console.warn('Corrections field is not an array:', data.corrections)
      data.corrections = []
    }

    return data
  }

  _validateStartMessageResponse(data) {
    if (!data) {
      throw new Error('Empty response from start endpoint')
    }

    if (!data.start_message) {
      console.warn('Start message response missing start_message field:', data)
    }

    return data
  }

  // Private error enhancement methods
  _enhanceChatError(error) {
    if (error.response?.status === 503) {
      error.message =
        'AI service is temporarily unavailable. Please try again in a moment.'
    } else if (error.response?.status === 400) {
      const detail = error.response.data?.detail
      if (detail && typeof detail === 'string') {
        error.message = detail
      } else {
        error.message = 'Invalid message format. Please try again.'
      }
    } else if (error.response?.status === 422) {
      error.message = 'Message validation failed. Please check your input.'
    }

    return error
  }

  _enhanceStartMessageError(error) {
    if (error.response?.status === 503) {
      error.message =
        'Unable to generate greeting. You can start typing to begin the conversation.'
    } else if (error.response?.status === 400) {
      error.message =
        'Invalid session parameters. Please try refreshing the page.'
    }

    return error
  }

  // Utility methods
  getApiUrl() {
    return `${API_BASE_URL}${API_PREFIX}`
  }

  // Debug utilities (development only)
  enableDebugLogging() {
    if (import.meta.env.DEV) {
      localStorage.setItem('api_debug', 'true')
    }
  }

  disableDebugLogging() {
    localStorage.removeItem('api_debug')
  }

  // Request timeout utilities
  async makeRequestWithTimeout(requestFn, timeoutMs = 30000) {
    return Promise.race([
      requestFn(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), timeoutMs)
      ),
    ])
  }
}

// Create and export singleton instance
const apiService = new ApiService()

export default apiService
