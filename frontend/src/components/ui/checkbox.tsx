import * as React from "react"
import {
  Checkbox as MuiCheckbox,
  CheckboxProps as MuiCheckboxProps,
  FormControlLabel,
} from "@mui/material"

export interface CheckboxProps extends Omit<MuiCheckboxProps, 'icon'> {
  icon?: React.ReactNode
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>
  rootRef?: React.Ref<HTMLLabelElement>
  children?: React.ReactNode
}

export const Checkbox = React.forwardRef<HTMLButtonElement, CheckboxProps>(
  function Checkbox(props, ref) {
    const { icon, children, inputProps, rootRef, ...rest } = props
    
    const checkbox = (
      <MuiCheckbox 
        ref={ref} 
        icon={icon}
        inputProps={inputProps}
        {...rest} 
      />
    )

    if (children != null) {
      return (
        <FormControlLabel
          ref={rootRef}
          control={checkbox}
          label={children}
        />
      )
    }

    return checkbox
  },
)
