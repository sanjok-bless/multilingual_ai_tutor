import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createStore } from 'vuex'
import LanguageSelector from '@/components/LanguageSelector.vue'
import state from '@/store/state.js'
import getters from '@/store/getters.js'
import mutations from '@/store/mutations.js'
// Session Management Actions
import * as sessionActions from '@/store/actions.session.js'

// Chat Workflow Actions
import * as chatActions from '@/store/actions.chat.js'

// Initialization Orchestration Actions
import * as initializationActions from '@/store/actions.initialization.js'

const actions = {
  // Session Actions
  ...sessionActions,

  // Chat Actions
  ...chatActions,

  // Initialization Actions
  ...initializationActions,
}

describe('LanguageSelector Component', () => {
  let wrapper
  let store

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks()
  })

  const createTestStore = storeState => {
    const testState = state()
    // Override state with test data
    testState.user.selectedLanguage = storeState.currentLanguage
    testState.user.availableLanguages = storeState.availableLanguages
    testState.chat.isLoading = false
    testState.app.isConnected = storeState.isConnected

    const testActions = {
      ...actions,
      selectLanguage: vi.fn(),
      initializeSessionWithLock: vi.fn(),
    }

    return createStore({
      state: () => testState,
      getters,
      mutations,
      actions: testActions,
    })
  }

  const mountComponent = storeState => {
    store = createTestStore(storeState)
    return mount(LanguageSelector, {
      global: {
        plugins: [store],
      },
    })
  }

  describe('Online Mode (Backend Connected)', () => {
    it('should show all languages as active when multiple languages available', async () => {
      wrapper = mountComponent({
        currentLanguage: 'english',
        availableLanguages: ['english', 'ukrainian', 'polish', 'german'],
        isConnected: true,
      })

      const buttons = wrapper.findAll('button')
      expect(buttons).toHaveLength(4)

      // All buttons should be active (not disabled)
      buttons.forEach(button => {
        expect(button.attributes('disabled')).toBeFalsy()
        expect(button.classes()).not.toContain('cursor-not-allowed')
      })
    })
  })

  describe('Offline Mode (Backend Disconnected)', () => {
    it('should show English as inactive when currentLanguage is null', async () => {
      wrapper = mountComponent({
        currentLanguage: null, // No language selected in offline mode
        availableLanguages: ['english'], // Only English available
        isConnected: false,
      })

      const englishButton = wrapper.find('button')

      // The button should exist
      expect(englishButton.exists()).toBe(true)
      expect(englishButton.text()).toContain('English')

      // The button should be disabled and have inactive styling
      expect(englishButton.attributes('disabled')).toBeDefined()
      expect(englishButton.classes()).toContain('cursor-not-allowed')
      expect(englishButton.classes()).toContain('bg-gray-200')
      expect(englishButton.classes()).toContain('text-gray-500')

      // Should NOT have brand primary or secondary styling (should be inactive)
      expect(englishButton.classes()).not.toContain('bg-brand-primary')
      expect(englishButton.classes()).not.toContain('bg-brand-secondary')
    })

    it('should not allow clicking inactive English button in offline mode', async () => {
      wrapper = mountComponent({
        currentLanguage: null,
        availableLanguages: ['english'],
        isConnected: false,
      })

      const englishButton = wrapper.find('button')

      // The button should be disabled, so clicking should not trigger any action
      expect(englishButton.attributes('disabled')).toBeDefined()

      // Since the button is disabled, we don't need to test the click behavior
      // The disabled attribute prevents the click handler from executing
    })
  })

  describe('isLanguageActive function logic', () => {
    it('should return false for English when in offline mode (currentLanguage null)', () => {
      wrapper = mountComponent({
        currentLanguage: null, // This is the key - no language selected in offline mode
        availableLanguages: ['english'],
        isConnected: false,
      })

      // Access the component instance to test the isLanguageActive function directly
      const vm = wrapper.vm

      // In offline mode with null currentLanguage, English should NOT be active
      // This test verifies the correct behavior
      expect(vm.isLanguageActive('english')).toBe(false)
    })

    it('SHOULD FAIL: demonstrates the bug where selected English shows as active in offline mode', () => {
      // This test demonstrates the problematic scenario that you mentioned
      // Let's create a scenario where English IS selected but backend is offline
      wrapper = mountComponent({
        currentLanguage: 'english', // English is selected
        availableLanguages: ['english'], // Only English available (offline)
        isConnected: false,
      })

      const vm = wrapper.vm

      // This will currently return TRUE due to the bug in isLanguageActive
      // The bug is: currentLanguage.value === language (english === english = true)
      // But in offline mode, we want NO languages to be active
      expect(vm.isLanguageActive('english')).toBe(false) // This should FAIL
    })

    it('should return true for all languages when online', () => {
      wrapper = mountComponent({
        currentLanguage: 'english',
        availableLanguages: ['english', 'ukrainian', 'polish', 'german'],
        isConnected: true,
      })

      const vm = wrapper.vm

      expect(vm.isLanguageActive('english')).toBe(true)
      expect(vm.isLanguageActive('ukrainian')).toBe(true)
      expect(vm.isLanguageActive('polish')).toBe(true)
      expect(vm.isLanguageActive('german')).toBe(true)
    })
  })
})
