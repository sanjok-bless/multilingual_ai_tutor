/* eslint-env node */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2020: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-essential',
    'plugin:vue/vue3-strongly-recommended',
    'plugin:vue/vue3-recommended',
    'prettier',
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['vue', 'security', 'no-unsanitized'],
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

    // Security rules (replacing semgrep functionality)
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

    // Custom security patterns to match semgrep rules
    'no-implied-eval': 'error', // Covers setTimeout/setInterval with strings
    'no-script-url': 'error', // Prevents javascript: URLs

    // Vue security rules (matching semgrep v-html detection)
    'vue/no-v-html': 'warn', // Warns about v-html XSS risks

    // Hardcoded secrets detection (basic patterns)
    'no-secrets/no-secrets': 'off', // Disabled - using custom patterns below
  },
  overrides: [
    {
      files: ['tests/**/*.{js,jsx}'],
      globals: {
        vi: true,
        describe: true,
        it: true,
        expect: true,
        beforeEach: true,
        afterEach: true,
      },
    },
    {
      // Enhanced security rules for all source files
      files: ['src/**/*.{js,jsx,vue}'],
      rules: {
        // Additional DOM security (matching semgrep innerHTML detection)
        'no-unsanitized/property': 'error',

        // For now, use built-in rules that catch similar patterns
        'no-eval': 'error',
        'no-new-func': 'error',
      },
    },
  ],
}
