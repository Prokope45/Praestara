import * as React from "react"
import { TextField, TextFieldProps, InputAdornment } from "@mui/material"

export interface InputGroupProps extends Omit<TextFieldProps, 'startElement' | 'endElement'> {
  startElement?: React.ReactNode
  endElement?: React.ReactNode
  startOffset?: string
  endOffset?: string
}

export const InputGroup = React.forwardRef<HTMLDivElement, InputGroupProps>(
  function InputGroup(props, ref) {
    const {
      startElement,
      endElement,
      startOffset,
      endOffset,
      children,
      ...rest
    } = props

    // If children is provided and is a TextField-like element, use it
    if (children && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement<any>, {
        InputProps: {
          ...(children.props as any).InputProps,
          startAdornment: startElement ? (
            <InputAdornment position="start">{startElement}</InputAdornment>
          ) : undefined,
          endAdornment: endElement ? (
            <InputAdornment position="end">{endElement}</InputAdornment>
          ) : undefined,
        },
      })
    }

    // Otherwise, render as a TextField
    return (
      <TextField
        ref={ref}
        {...rest}
        InputProps={{
          ...rest.InputProps,
          startAdornment: startElement ? (
            <InputAdornment position="start">{startElement}</InputAdornment>
          ) : undefined,
          endAdornment: endElement ? (
            <InputAdornment position="end">{endElement}</InputAdornment>
          ) : undefined,
        }}
      />
    )
  },
)
