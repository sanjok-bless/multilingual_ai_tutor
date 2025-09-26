<template>
  <div
    v-if="message.type === 'user'"
    class="flex items-end gap-3 p-4 justify-end"
  >
    <!-- User message content -->
    <div class="flex flex-1 flex-col gap-1 items-end">
      <!-- Sender label -->
      <p
        class="text-brand-text-muted text-[13px] font-normal leading-normal max-w-[360px] md:max-w-[480px] lg:max-w-[560px] xl:max-w-[600px] text-right"
      >
        {{ getSenderLabel('user') }}
      </p>

      <!-- Message bubble -->

      <!-- eslint-disable vue/no-v-html -- Safe: Content sanitized with DOMPurify -->
      <div
        class="text-base font-normal leading-normal flex max-w-[360px] md:max-w-[480px] lg:max-w-[560px] xl:max-w-[600px] rounded-lg px-4 py-3 message-bubble-user"
        v-html="formatMessageContent(message.content)"
      ></div>
      <!-- eslint-enable vue/no-v-html -->
    </div>

    <!-- User avatar (right side) -->
    <div class="avatar-base avatar-user w-10 shrink-0">
      <span class="avatar-user-icon">👤</span>
    </div>
  </div>

  <!-- AI message(s) - can be multiple bubbles -->
  <div v-else-if="message.type === 'ai'" class="space-y-0">
    <div
      v-for="(bubble, index) in messageBubbles"
      :key="index"
      class="flex items-end gap-3 p-2 justify-start"
    >
      <!-- AI avatar (left side) - only on last bubble -->
      <div
        v-if="bubble.isLast"
        class="avatar-base avatar-ai w-10 shrink-0"
      ></div>
      <!-- Empty space to align with avatar when not showing -->
      <div v-else class="w-10 shrink-0"></div>

      <!-- Message content -->
      <div class="flex flex-1 flex-col gap-1 items-start">
        <!-- Sender label - only on first bubble -->
        <p
          v-if="bubble.isFirst"
          class="text-brand-text-muted text-[13px] font-normal leading-normal max-w-[360px] md:max-w-[480px] lg:max-w-[560px] xl:max-w-[600px] text-left"
        >
          {{ getSenderLabel('ai') }}
        </p>

        <!-- Message bubble -->
        <div
          :class="[
            'text-base font-normal leading-normal flex max-w-[360px] md:max-w-[480px] lg:max-w-[560px] xl:max-w-[600px] rounded-lg px-4 py-3',
            bubble.type === 'corrections'
              ? 'bg-yellow-50 border border-yellow-200 flex-col gap-3'
              : bubble.type === 'ai_response_success'
                ? 'bg-green-50 border border-green-200 flex-col gap-3'
                : 'message-bubble-ai',
          ]"
        >
          <!-- Regular message content -->

          <!-- eslint-disable vue/no-v-html -- Safe: Content sanitized with DOMPurify -->
          <div
            v-if="
              bubble.type !== 'corrections' &&
              bubble.type !== 'ai_response_success'
            "
            v-html="formatMessageContent(bubble.content)"
          ></div>
          <!-- eslint-enable vue/no-v-html -->

          <!-- AI Response Success content (green area when no corrections) -->
          <div v-else-if="bubble.type === 'ai_response_success'">
            <div class="bg-white rounded-lg p-3 border border-green-200">
              <!-- eslint-disable-next-line vue/no-v-html -- Safe: Content sanitized with DOMPurify -->
              <div v-html="formatMessageContent(bubble.content)"></div>
            </div>
          </div>

          <!-- Corrections content -->
          <div v-else>
            <!-- AI Response section (if included with corrections) -->
            <div
              v-if="bubble.ai_response"
              class="bg-white rounded-lg p-3 border border-yellow-200 mb-3"
            >
              <!-- eslint-disable-next-line vue/no-v-html -- Safe: Content sanitized with DOMPurify -->
              <div v-html="formatMessageContent(bubble.ai_response)"></div>
            </div>

            <div class="space-y-3">
              <div
                v-for="(correction, corrIndex) in bubble.content"
                :key="corrIndex"
                class="bg-white rounded-lg p-3 border border-yellow-200"
              >
                <!-- Succinct Layout -->
                <div class="space-y-1">
                  <div class="text-sm">
                    <span
                      :class="[
                        'text-xs font-medium px-1.5 py-0.5 rounded mr-2',
                        getErrorTypeClass(correction.error_type),
                      ]"
                    >
                      {{ formatErrorType(correction.error_type) }}
                    </span>
                    <span class="text-gray-600 line-through"
                      >"{{ correction.original }}"</span
                    >
                    <span class="mx-2 text-gray-400">→</span>

                    <!-- eslint-disable vue/no-v-html -- Safe: Content sanitized with DOMPurify -->
                    <span
                      class="font-medium"
                      v-html="
                        '&quot;' +
                        formatCorrected(correction.corrected) +
                        '&quot;'
                      "
                    ></span>
                    <!-- eslint-enable vue/no-v-html -->
                  </div>
                  <div
                    v-if="
                      correction.explanation &&
                      correction.explanation.length > 0
                    "
                    class="text-xs text-gray-500"
                  >
                    <strong>{{ correction.explanation[0] }}:</strong>
                    {{ correction.explanation[1] }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Token usage (dev info for AI messages) - only on last bubble -->
        <div
          v-if="bubble.isLast && message.tokens_used && showDebugInfo"
          class="text-brand-text-muted text-xs mt-1"
        >
          Tokens: {{ message.tokens_used }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useSafeHtml } from '@/composables/useSafeHtml'

export default {
  name: 'MessageBubble',
  props: {
    message: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    const { sanitizeAndFormat, sanitizeAndFormatCorrected } = useSafeHtml()

    const showDebugInfo = computed(() => {
      return (
        import.meta.env.DEV &&
        localStorage.getItem('show_debug_info') === 'true'
      )
    })

    // Create array of bubbles for AI messages (1-3 bubbles depending on content)
    const messageBubbles = computed(() => {
      if (props.message.type !== 'ai') return []

      const bubbles = []

      // 1. Corrections bubble with ai_response (if corrections exist)
      if (props.message.corrections && props.message.corrections.length > 0) {
        bubbles.push({
          type: 'corrections',
          content: props.message.corrections,
          ai_response: props.message.ai_response, // Include ai_response in corrections bubble
          isFirst: true,
          isLast: false,
        })
      }
      // 2. AI Response bubble in green area (if no corrections)
      else if (props.message.ai_response) {
        bubbles.push({
          type: 'ai_response_success',
          content: props.message.ai_response,
          isFirst: true,
          isLast: false,
        })
      }

      // 3. Next phrase bubble (if exists)
      if (props.message.next_phrase) {
        bubbles.push({
          type: 'next_phrase',
          content: props.message.next_phrase,
          isFirst: bubbles.length === 0,
          isLast: false,
        })
      }

      // Fallback: if no specific content, use message.content
      if (bubbles.length === 0) {
        bubbles.push({
          type: 'fallback',
          content: props.message.content || 'Response received.',
          isFirst: true,
          isLast: false,
        })
      }

      // Mark the last bubble
      if (bubbles.length > 0) {
        bubbles[bubbles.length - 1].isLast = true
      }

      return bubbles
    })

    const getSenderLabel = type => {
      return type === 'user' ? 'You' : 'Tutor'
    }

    const formatMessageContent = content => {
      return sanitizeAndFormat(content)
    }

    // Correction formatting functions
    const formatErrorType = errorType => {
      const types = {
        GRAMMAR: 'Grammar',
        SPELLING: 'Spelling',
        VOCABULARY: 'Vocabulary',
        PUNCTUATION: 'Punctuation',
        STYLE: 'Style',
      }
      return types[errorType] || errorType
    }

    const getErrorTypeClass = errorType => {
      const classes = {
        GRAMMAR: 'text-blue-700 bg-blue-100',
        SPELLING: 'text-red-700 bg-red-100',
        VOCABULARY: 'text-purple-700 bg-purple-100',
        PUNCTUATION: 'text-orange-700 bg-orange-100',
        STYLE: 'text-green-700 bg-green-100',
      }
      return classes[errorType] || 'text-gray-700 bg-gray-100'
    }

    const formatCorrected = correctedText => {
      return sanitizeAndFormatCorrected(correctedText)
    }

    return {
      messageBubbles,
      showDebugInfo,
      getSenderLabel,
      formatMessageContent,
      formatErrorType,
      getErrorTypeClass,
      formatCorrected,
    }
  },
}
</script>
