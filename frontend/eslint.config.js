import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import security from 'eslint-plugin-security'
import noUnsanitized from 'eslint-plugin-no-unsanitized'
import prettierConfig from 'eslint-config-prettier'

export default [
  // Ignore patterns (migrated from .eslintignore)
  {
    ignores: [
      'node_modules/',
      'dist/',
      'coverage/',
      '*.log',
      '.env*',
      'package-lock.json',
      'yarn.lock',
      'pnpm-lock.yaml',
    ],
  },

  // Base JavaScript recommended rules
  js.configs.recommended,

  // Vue 3 essential rules
  ...vue.configs['flat/essential'],
  ...vue.configs['flat/strongly-recommended'],
  ...vue.configs['flat/recommended'],

  // Prettier config (disables conflicting rules)
  prettierConfig,

  // Global configuration
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        // Browser environment
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        console: 'readonly',
        // Node environment (for config files)
        process: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        require: 'readonly',
        module: 'readonly',
        exports: 'readonly',
      },
    },
    plugins: {
      vue,
      security,
      'no-unsanitized': noUnsanitized,
    },
    rules: {
      // Vue-specific rules
      'vue/multi-word-component-names': 'off',
      'vue/no-reserved-component-names': 'off',
      'vue/component-tags-order': [
        'error',
        {
          order: [['script', 'template'], 'style'],
        },
      ],

      // General rules
      'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'prefer-const': 'error',
      'no-var': 'error',

      // Import/export rules
      'no-duplicate-imports': 'error',

      // Security rules
      'security/detect-eval-with-expression': 'error',
      'security/detect-non-literal-fs-filename': 'error',
      'security/detect-non-literal-require': 'error',
      'security/detect-unsafe-regex': 'error',
      'security/detect-buffer-noassert': 'error',
      'security/detect-child-process': 'error',
      'security/detect-disable-mustache-escape': 'error',
      'security/detect-no-csrf-before-method-override': 'error',
      'security/detect-non-literal-regexp': 'error',
      'security/detect-possible-timing-attacks': 'error',
      'security/detect-pseudoRandomBytes': 'error',

      // Custom security patterns
      'no-implied-eval': 'error',
      'no-script-url': 'error',
      'no-eval': 'error',
      'no-new-func': 'error',

      // Vue security rules
      'vue/no-v-html': 'error',
    },
  },

  // Test files configuration
  {
    files: ['tests/**/*.{js,jsx}'],
    languageOptions: {
      globals: {
        vi: 'readonly',
        describe: 'readonly',
        it: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        global: 'writable',
      },
    },
  },

  // Enhanced security rules for source files
  {
    files: ['src/**/*.{js,jsx,vue}'],
    rules: {
      'no-unsanitized/property': 'error',
    },
  },
]
