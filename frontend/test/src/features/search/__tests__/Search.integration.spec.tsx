import { get } from '../../../../../src/services/apiClient'

describe('API client integration (scaffold)', () => {
  beforeEach(() => {
    // reset fetch mock
    // @ts-ignore
    global.fetch = jest.fn()
  })

  test('get throws on non-OK response', async () => {
    // @ts-ignore
    global.fetch = jest.fn(() => Promise.resolve({ ok: false, status: 500 }))
    await expect(get('/test')).rejects.toThrow(/failed with status/)
  })
})
