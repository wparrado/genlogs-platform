module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'import'],
  rules: {
    // Protect frontend layer boundaries (AT-012, AT-013, AT-014)
    'import/no-restricted-paths': [
      'error',
      {
        zones: [
          {
            target: './src/services',
            from: './src/components',
            message: 'services must not import from components',
          },
          {
            target: './src/services',
            from: './src/features',
            message: 'services must not import from features',
          },
          {
            target: './src/components',
            from: './src/features',
            message: 'components must not import from features',
          },
        ],
      },
    ],
  },
}
