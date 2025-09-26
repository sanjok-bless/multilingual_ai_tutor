<template>
  <div>
    <h2
      class="text-brand-text text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5"
    >
      Language
    </h2>
    <div class="flex justify-stretch">
      <div class="flex flex-1 gap-3 flex-wrap px-4 py-3 justify-start">
        <button
          v-for="language in availableLanguages"
          :key="language"
          :class="[
            'flex min-w-[84px] max-w-[480px] items-center justify-center overflow-hidden rounded-lg h-10 px-4 text-sm font-bold leading-normal tracking-[0.015em]',
            currentLanguage === language
              ? 'bg-brand-primary text-brand-text cursor-pointer'
              : isLanguageActive(language)
                ? 'bg-brand-secondary text-brand-text cursor-pointer hover:bg-brand-primary/20'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed',
          ]"
          :disabled="isLoading || !isLanguageActive(language)"
          @click="selectLanguage(language)"
        >
          <span class="truncate">{{ formatLanguageName(language) }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'LanguageSelector',
  setup() {
    const store = useStore()

    const availableLanguages = computed(() => store.getters.availableLanguages)
    const currentLanguage = computed(() => store.getters.currentLanguage)
    const isLoading = computed(() => store.getters.isLoading)

    const formatLanguageName = language => {
      return language.charAt(0).toUpperCase() + language.slice(1)
    }

    const isLanguageActive = _language => {
      // Language is active only if connection to /languages was successful (has multiple languages)
      // In offline mode, no languages should be selectable
      return availableLanguages.value.length > 1
    }

    const selectLanguage = async language => {
      // Only allow selection of active languages
      if (
        language !== currentLanguage.value &&
        !isLoading.value &&
        isLanguageActive(language)
      ) {
        await store.dispatch('selectLanguage', language)
        // Initialize session with start message after language selection
        await store.dispatch('initializeSessionWithLock')
      }
    }

    return {
      availableLanguages,
      currentLanguage,
      isLoading,
      formatLanguageName,
      isLanguageActive,
      selectLanguage,
    }
  },
}
</script>
