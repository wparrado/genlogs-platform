import { get } from '../../../../../src/services/apiClient'

describe('API client integration (scaffold)', () => {
  beforeEach(() => {
    // reset fetch mock
    // @ts-ignore
    global.fetch = jest.fn()
  })

  test('get throws on non-OK response', async () => {
    // @ts-ignore
    global.fetch = jest.fn(() => Promise.resolve({
      ok: false,
      status: 500,
      statusText: 'Server Error',
      headers: { get: (_: string) => null },
      json: async () => ({}),
      text: async () => ''
    }))
    try {
      await get('/test')
      throw new Error('Expected get to throw')
    } catch (err: any) {
      if (!String(err).match(/failed with status|Bad|Server Error/)) {
        throw new Error(`Unexpected error: ${String(err)}`)
      }
    }
  })
})
