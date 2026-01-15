import {
  Radio as MuiRadio,
  RadioGroup as MuiRadioGroup,
  FormControlLabel,
  RadioGroupProps,
  RadioProps as MuiRadioProps,
} from '@mui/material';
import * as React from 'react';

export interface RadioProps extends MuiRadioProps {
  children?: React.ReactNode;
}

export const Radio = React.forwardRef<HTMLButtonElement, RadioProps>(
  function Radio({ children, ...props }, ref) {
    if (children) {
      return (
        <FormControlLabel
          control={<MuiRadio ref={ref} {...props} />}
          label={children}
        />
      );
    }
    return <MuiRadio ref={ref} {...props} />;
  }
);

interface RadioGroupPropsExtended extends RadioGroupProps {
  onValueChange?: (value: string) => void;
}

export const RadioGroup = React.forwardRef<HTMLDivElement, RadioGroupPropsExtended>(
  function RadioGroup({ onValueChange, onChange, ...props }, ref) {
    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (onValueChange) {
        onValueChange(event.target.value);
      }
      if (onChange) {
        onChange(event, event.target.value);
      }
    };

    return <MuiRadioGroup ref={ref} onChange={handleChange} {...props} />;
  }
);
