module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  testPathIgnorePatterns: ['/node_modules/', '/dist/'],
  moduleDirectories: ['node_modules', '<rootDir>/../node_modules'],
  globals: {
    'ts-jest': {
      tsconfig: '<rootDir>/../tsconfig.json',
      isolatedModules: true
    }
  },
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': '<rootDir>/src/__mocks__/styleMock.js'
  }
}
