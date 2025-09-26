<template>
  <div>
    <h2
      class="text-brand-text text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5"
    >
      Level
    </h2>
    <div class="flex justify-stretch">
      <div class="flex flex-1 gap-3 flex-wrap px-4 py-3 justify-start">
        <button
          v-for="level in availableLevels"
          :key="level.key"
          :class="[
            'flex min-w-[84px] max-w-[480px] items-center justify-center overflow-hidden rounded-lg h-10 px-4 text-sm font-bold leading-normal tracking-[0.015em]',
            currentLevel === level.key
              ? 'bg-brand-primary text-brand-text cursor-pointer'
              : isInitialized
                ? 'bg-brand-secondary text-brand-text cursor-pointer hover:bg-brand-primary/20'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed',
          ]"
          :disabled="isLoading || !isInitialized"
          @click="selectLevel(level.key)"
        >
          <span class="truncate">{{ level.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'LevelSelector',
  setup() {
    const store = useStore()

    const availableLevels = computed(() => store.getters.availableLevels)
    const currentLevel = computed(() => store.getters.currentLevel)
    const isLoading = computed(() => store.getters.isLoading)
    const isInitialized = computed(() => store.getters.isInitialized)

    const selectLevel = async level => {
      if (
        level !== currentLevel.value &&
        !isLoading.value &&
        isInitialized.value
      ) {
        await store.dispatch('selectLevel', level)
        // Initialize session with start message after level selection
        await store.dispatch('initializeSessionWithLock')
      }
    }

    return {
      availableLevels,
      currentLevel,
      isLoading,
      isInitialized,
      selectLevel,
    }
  },
}
</script>
