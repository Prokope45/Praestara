import * as React from "react"
import { Button, ButtonProps } from "@mui/material"

export interface LinkButtonProps extends Omit<ButtonProps, 'href'> {
  href?: string
}

export const LinkButton = React.forwardRef<HTMLAnchorElement, LinkButtonProps>(
  function LinkButton(props, ref) {
    const { href, ...rest } = props
    
    return (
      <Button
        component="a"
        href={href}
        ref={ref}
        {...rest}
      />
    )
  }
)
