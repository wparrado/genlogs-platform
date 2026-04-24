import { post } from '../src/services/apiClient'

describe('Error handling (scaffold)', () => {
  beforeEach(() => {
    // @ts-ignore
    global.fetch = jest.fn()
  })

  test('post throws on non-OK response', async () => {
    // @ts-ignore
    global.fetch = jest.fn(() => Promise.resolve({ ok: false, status: 400 }))
    await expect(post('/search', { from: 'A', to: 'B' })).rejects.toThrow(/failed with status/) 
  })
})
