<template>
  <div
    class="relative flex size-full min-h-screen flex-col bg-brand-bg font-sans"
  >
    <div class="layout-container flex h-full grow flex-col">
      <!-- App Header -->
      <AppHeader />

      <!-- Main content -->
      <div
        class="px-4 sm:px-8 md:px-16 lg:px-24 xl:px-40 flex flex-1 justify-center py-5"
      >
        <div
          class="layout-content-container flex flex-col max-w-[960px] flex-1"
        >
          <!-- Loading screen for initialization -->
          <div v-if="isInitializing" class="text-center py-16">
            <div class="animate-pulse text-brand-text-muted mb-4">
              <div class="avatar-base avatar-ai w-8 h-8 mx-auto mb-4"></div>
            </div>
            <h1 class="text-xl font-bold text-brand-text mb-2">
              Initializing Chat Session
            </h1>
            <p class="text-brand-text-muted">
              Setting up your multilingual tutoring experience...
            </p>
          </div>

          <!-- Main chat interface -->
          <div v-else class="flex flex-col h-full">
            <!-- Language Selector -->
            <LanguageSelector />

            <!-- Level Selector -->
            <LevelSelector />

            <!-- Chat Container -->
            <ChatContainer />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { useStore } from 'vuex'
import AppHeader from '@/components/AppHeader.vue'
import LanguageSelector from '@/components/LanguageSelector.vue'
import LevelSelector from '@/components/LevelSelector.vue'
import ChatContainer from '@/components/ChatContainer.vue'
import apiService from '@/services/api.js'

export default {
  name: 'ChatView',
  components: {
    AppHeader,
    LanguageSelector,
    LevelSelector,
    ChatContainer,
  },
  setup() {
    const store = useStore()
    const isInitializing = ref(true)

    // Computed properties
    const currentSession = computed(() => store.getters.currentSession)
    const hasAnySessions = computed(() => store.getters.hasAnySessions)

    // Watch for session changes to initialize chat
    watch(
      () => currentSession.value?.sessionId,
      async (newSessionId, oldSessionId) => {
        if (newSessionId && newSessionId !== oldSessionId) {
          // New session created, initialize chat
          await store.dispatch('initializeSessionWithLock')
        }
      },
      { immediate: false }
    )

    // Initialize the application
    const initializeApp = async () => {
      try {
        console.log('Initializing ChatView...')

        // Step 1: Load sessions from localStorage
        await store.dispatch('loadFromLocalStorage')

        // Step 2: Load available languages and select from last active session
        const languageResult = await store.dispatch('loadAvailableLanguages')

        // Step 3: Initialize user defaults (will use last active session if exists)
        await store.dispatch('initializeDefaults')

        // Step 4: Load chat messages for current session
        await store.dispatch('loadSessionMessages')

        // Step 5: Initialize session with daily start message logic ONLY if languages loaded successfully
        if (languageResult.success) {
          await store.dispatch('initializeSessionWithLock')
          console.log('ChatView initialization complete with API integration')
        } else {
          console.log(
            'ChatView initialization complete (offline mode - languages API failed)'
          )
        }
      } catch (error) {
        console.error('Error initializing ChatView:', error)

        // Create fallback session if needed
        if (!currentSession.value) {
          await store.dispatch('createDefaultSession')
        }
      } finally {
        isInitializing.value = false
      }
    }

    // Debug utilities (development only)
    const debugInfo = computed(() => {
      if (!import.meta.env.DEV) return null

      return {
        hasAnySessions: hasAnySessions.value,
        currentSessionKey: store.state.sessions.currentSessionKey,
        currentLanguage: store.getters.currentLanguage,
        currentLevel: store.getters.currentLevel,
        messageCount: currentSession.value?.messages?.length || 0,
        sessionCount: Object.keys(store.getters.allSessions).length,
      }
    })

    // Expose debug info to global scope in development
    if (import.meta.env.DEV) {
      window.chatDebug = {
        store,
        apiService,
        getDebugInfo: () => debugInfo.value,
        getSessions: () => store.getters.allSessions,
        getCurrentSession: () => currentSession.value,
      }
    }

    // Initialize on mount
    onMounted(() => {
      initializeApp()
    })

    return {
      isInitializing,
      currentSession,
      debugInfo,
    }
  },
}
</script>
