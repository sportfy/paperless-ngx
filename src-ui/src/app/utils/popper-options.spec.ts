import { popperOptionsWithAutoOffset } from './popper-options'
import { Options } from '@popperjs/core'

describe('popperOptionsWithAutoOffset', () => {
  let mockDropdownElement

  beforeEach(() => {
    mockDropdownElement = jest.fn() as any
    mockDropdownElement.offsetLeft = 100
  })

  it('should not add offset modifier when window width is 400 or more', () => {
    window.innerWidth = 400
    const config: Partial<Options> = { modifiers: [] }
    const context = { _nativeElement: mockDropdownElement }

    const result = popperOptionsWithAutoOffset.call(context, config)

    expect(result.modifiers).toHaveLength(0)
  })

  it('should calculate the correct offset when there is right overflow', () => {
    window.innerWidth = 300
    const config: Partial<Options> = { modifiers: [] }
    const context = { _nativeElement: mockDropdownElement }

    const result = popperOptionsWithAutoOffset.call(context, config)
    const offsetFunction = result.modifiers[0].options.offset
    const offset = offsetFunction({
      popper: { width: 250 },
      reference: {},
      placement: 'bottom',
    })

    expect(offset).toEqual([-60, 0]) // (300 - 10) - (100 + 250) = -60
  })

  it('should calculate the correct offset when there is no right overflow', () => {
    window.innerWidth = 300
    const config: Partial<Options> = { modifiers: [] }
    const context = { _nativeElement: mockDropdownElement }

    const result = popperOptionsWithAutoOffset.call(context, config)
    const offsetFunction = result.modifiers[0].options.offset
    const offset = offsetFunction({
      popper: { width: 100 },
      reference: {},
      placement: 'bottom',
    })

    expect(offset).toEqual([0, 0]) // No overflow
  })
})
