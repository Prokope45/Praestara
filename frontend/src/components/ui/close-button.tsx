import * as React from "react"
import { IconButton, IconButtonProps } from "@mui/material"
import { LuX } from "react-icons/lu"

export type CloseButtonProps = IconButtonProps

export const CloseButton = React.forwardRef<
  HTMLButtonElement,
  CloseButtonProps
>(function CloseButton(props, ref) {
  return (
    <IconButton aria-label="Close" ref={ref} {...props}>
      {props.children ?? <LuX />}
    </IconButton>
  )
})
