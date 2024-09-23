import { Options } from '@popperjs/core'

export function popperOptionsWithAutoOffset(
  config: Partial<Options>
): Partial<Options> {
  const windowWidth = window?.innerWidth
  if (windowWidth < 400) {
    const dropdownElement: HTMLElement = this['_nativeElement'] // method is scoped, 'this' is NgbDropdown
    config.modifiers.push({
      name: 'offset',
      options: {
        offset: ({ popper, reference, placement }) => {
          const rightOverflow =
            windowWidth - 10 - (dropdownElement.offsetLeft + popper.width)
          return [rightOverflow < 0 ? rightOverflow : 0, 0]
        },
      },
    })
  }
  return config
}
