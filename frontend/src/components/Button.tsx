import React from 'react'

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & { children?: React.ReactNode }

export default function Button(props: Props): React.ReactElement {
  const { children, ...rest } = props
  return (
    <button {...rest}>{children}</button>
  )
}
