<template>
  <div
    class="flex items-center px-4 py-3 gap-3 border-t border-brand-secondary bg-white"
  >
    <!-- User avatar -->
    <div class="avatar-base avatar-user size-10 shrink-0">
      <span class="avatar-user-icon">👤</span>
    </div>

    <!-- Input container -->
    <div class="flex flex-col min-w-40 h-12 flex-1">
      <div class="flex w-full flex-1 items-stretch rounded-lg h-full">
        <input
          ref="messageInput"
          v-model="messageText"
          :placeholder="inputPlaceholder"
          :disabled="disabled"
          class="chat-input rounded-r-none border-r-0 pr-2"
          maxlength="500"
          @keydown.enter="handleEnterKey"
          @input="handleInput"
        />
        <div
          class="flex border-none bg-brand-secondary items-center justify-center pr-4 rounded-r-lg border-l-0 !pr-2"
        >
          <div class="flex items-center gap-4 justify-end">
            <!-- Character counter -->
            <div
              v-if="messageText.length > 400"
              :class="[
                'text-xs',
                messageText.length > 450
                  ? 'text-red-500'
                  : 'text-brand-text-muted',
              ]"
            >
              {{ messageText.length }}/500
            </div>

            <!-- Send button -->
            <button
              :disabled="!canSend"
              :class="[
                'min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-8 px-4 text-sm font-medium leading-normal',
                canSend
                  ? 'bg-brand-primary text-brand-text hover:opacity-90'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed',
              ]"
              @click="sendMessage"
            >
              <span class="truncate">
                {{ disabled ? 'Sending...' : 'Send' }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, nextTick } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'MessageInput',
  props: {
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['send-message'],
  setup(props, { emit }) {
    const store = useStore()
    const messageInput = ref(null)
    const messageText = ref('')

    const currentLanguage = computed(() => store.getters.currentLanguage)

    const inputPlaceholder = computed(() => {
      const placeholders = {
        english: 'Type your message in English...',
        ukrainian: 'Напишіть ваше повідомлення українською...',
        polish: 'Wpisz swoją wiadomość po polsku...',
        german: 'Schreibe deine Nachricht auf Deutsch...',
      }
      return placeholders[currentLanguage.value] || 'Type your message...'
    })

    const canSend = computed(() => {
      return (
        !props.disabled &&
        messageText.value.trim().length > 0 &&
        messageText.value.length <= 500
      )
    })

    const handleInput = () => {
      // Auto-resize could be added here if we switch to textarea
      // For now, input field handles single line well
    }

    const handleEnterKey = event => {
      if (!event.shiftKey && canSend.value) {
        event.preventDefault()
        sendMessage()
      }
    }

    const sendMessage = () => {
      if (!canSend.value) return

      const message = messageText.value.trim()
      if (message) {
        emit('send-message', message)
        messageText.value = ''

        // Focus back to input after sending
        nextTick(() => {
          if (messageInput.value) {
            messageInput.value.focus()
          }
        })
      }
    }

    // Focus input when component is mounted
    nextTick(() => {
      if (messageInput.value) {
        messageInput.value.focus()
      }
    })

    return {
      messageInput,
      messageText,
      inputPlaceholder,
      canSend,
      handleInput,
      handleEnterKey,
      sendMessage,
    }
  },
}
</script>
