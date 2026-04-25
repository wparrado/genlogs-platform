import { post } from '../../../../../src/services/apiClient'

describe('Error handling (scaffold)', () => {
  beforeEach(() => {
    // @ts-ignore
    global.fetch = jest.fn()
  })

  test('post throws on non-OK response', async () => {
    // @ts-ignore
    global.fetch = jest.fn(() => Promise.resolve({
      ok: false,
      status: 400,
      statusText: 'Bad',
      headers: { get: (_: string) => null },
      json: async () => ({}),
      text: async () => ''
    }))
    try {
      await post('/search', { from: 'A', to: 'B' })
      throw new Error('Expected post to throw')
    } catch (err: any) {
      if (!String(err).match(/failed with status|Bad|Server Error/)) {
        throw new Error(`Unexpected error: ${String(err)}`)
      }
    }
  })
})
