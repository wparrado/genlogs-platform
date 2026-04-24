/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: 'no-services-importing-ui',
      comment: 'services must not import from UI layers (AT-012)',
      severity: 'error',
      from: { path: '^src/services' },
      to: { path: '^src/(components|features)' },
    },
    {
      name: 'no-components-importing-features',
      comment: 'shared components must not import feature internals (AT-013)',
      severity: 'error',
      from: { path: '^src/components' },
      to: { path: '^src/features' },
    },
    {
      name: 'no-circular-dependencies',
      comment: 'circular dependencies are not allowed',
      severity: 'error',
      from: {},
      to: { circular: true },
    },
  ],
  options: {
    doNotFollow: {
      path: 'node_modules',
    },
    tsPreCompilationDeps: true,
    reporterOptions: {
      text: {
        highlightFocused: true,
      },
    },
  },
}
