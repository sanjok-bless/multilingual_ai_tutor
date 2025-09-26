<template>
  <div class="flex flex-col h-full max-h-[600px]">
    <h2
      class="text-brand-text text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5"
    >
      Chat
    </h2>
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto px-4 space-y-1"
      style="scrollbar-width: thin"
    >
      <!-- Loading indicator for initial session -->
      <div
        v-if="isLoading && messages.length === 0"
        class="flex items-center justify-center py-8"
      >
        <div class="text-brand-text-muted">Loading chat...</div>
      </div>

      <!-- Messages -->
      <ChatMessageBubble
        v-for="message in messages"
        :key="`${message.timestamp}-${message.type}`"
        :message="message"
      />

      <!-- Error message (not saved to history) -->
      <ChatErrorMessage
        v-if="hasError"
        :error="currentError"
        @retry="retryMessage"
      />

      <!-- Loading indicator for new messages -->
      <div
        v-if="isLoading && messages.length > 0"
        class="flex items-end gap-3 p-4"
      >
        <div
          class="bg-center bg-no-repeat aspect-square bg-cover rounded-full w-10 shrink-0 bg-gray-300"
        ></div>
        <div class="flex flex-1 flex-col gap-1 items-start">
          <p
            class="text-brand-text-muted text-[13px] font-normal leading-normal max-w-[360px]"
          >
            Tutor
          </p>
          <div class="message-bubble-ai">
            <div class="flex items-center gap-2">
              <div class="animate-pulse">Thinking...</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Message Input -->
    <ChatMessageInput
      :disabled="isLoading || !isInitialized || hasError"
      @send-message="handleSendMessage"
    />
  </div>
</template>

<script>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useStore } from 'vuex'
import ChatMessageBubble from './ChatMessageBubble.vue'
import ChatErrorMessage from './ChatErrorMessage.vue'
import ChatMessageInput from './ChatMessageInput.vue'

export default {
  name: 'ChatContainer',
  components: {
    ChatMessageBubble,
    ChatErrorMessage,
    ChatMessageInput,
  },
  setup() {
    const store = useStore()
    const messagesContainer = ref(null)

    const messages = computed(() => store.getters.allMessages)
    const isLoading = computed(() => store.getters.isLoading)
    const hasError = computed(() => store.getters.hasError)
    const currentError = computed(() => store.getters.currentError)
    const isInitialized = computed(() => store.getters.isInitialized)

    const handleSendMessage = async content => {
      await store.dispatch('sendMessage', { content })
      await scrollToBottom()
    }

    const retryMessage = async () => {
      await store.dispatch('retryConnection')
      await scrollToBottom()
    }

    const scrollToBottom = async () => {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    // Auto-scroll when new messages are added
    watch(
      () => messages.value?.length || 0,
      async () => {
        await scrollToBottom()
      }
    )

    // Auto-scroll when loading state changes
    watch(
      () => isLoading.value,
      async () => {
        await scrollToBottom()
      }
    )

    // Scroll to bottom on component mount (page reload)
    onMounted(async () => {
      await nextTick()
      await scrollToBottom()
    })

    return {
      messagesContainer,
      messages,
      isLoading,
      hasError,
      currentError,
      isInitialized,
      handleSendMessage,
      retryMessage,
    }
  },
}
</script>
