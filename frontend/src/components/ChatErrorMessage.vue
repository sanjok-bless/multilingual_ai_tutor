<template>
  <div class="flex items-end gap-3 p-4">
    <!-- AI avatar -->
    <div class="avatar-base avatar-ai w-10 shrink-0 opacity-60"></div>

    <!-- Error content -->
    <div class="flex flex-1 flex-col gap-1 items-start">
      <!-- Error message bubble -->
      <div class="message-bubble-error">
        <div class="flex items-start gap-2">
          <!-- Error icon -->
          <svg
            class="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>

          <div class="flex-1">
            <p class="text-sm font-medium text-red-800">{{ error.message }}</p>

            <!-- Action button or message -->
            <div class="mt-3">
              <button
                v-if="shouldShowRetryButton"
                :disabled="isRetrying"
                class="inline-flex items-center px-3 py-1.5 text-xs font-medium text-red-700 bg-red-100 border border-red-300 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                @click="$emit('retry')"
              >
                <svg
                  v-if="isRetrying"
                  class="w-3 h-3 mr-1 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  ></circle>
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <svg
                  v-else
                  class="w-3 h-3 mr-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                {{ isRetrying ? 'Retrying...' : 'Retry' }}
              </button>

              <p
                v-else-if="shouldShowTryLater"
                class="text-xs text-red-600 font-medium"
              >
                Try again later
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'ErrorMessage',
  props: {
    error: {
      type: Object,
      required: true,
    },
  },
  emits: ['retry'],
  setup() {
    const store = useStore()

    const isRetrying = computed(() => store.getters.isRetrying)
    const shouldShowRetryButton = computed(
      () => store.getters.shouldShowRetryButton
    )
    const shouldShowTryLater = computed(() => store.getters.shouldShowTryLater)

    return {
      isRetrying,
      shouldShowRetryButton,
      shouldShowTryLater,
    }
  },
}
</script>
