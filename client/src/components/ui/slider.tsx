import * as React from "react"

import { cn } from "@/lib/utils"

export interface SliderProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
  min: number
  max: number
  step: number
  value: number[]
  onValueChange: (value: number[]) => void
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, min, max, step, value, onValueChange, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onValueChange([parseFloat(e.target.value)])
    }

    return (
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value[0]}
        onChange={handleChange}
        className={cn(
          "w-full h-2 appearance-none cursor-pointer bg-neutral-200 rounded-full",
          "[&::-webkit-slider-thumb]:appearance-none",
          "[&::-webkit-slider-thumb]:w-4",
          "[&::-webkit-slider-thumb]:h-4",
          "[&::-webkit-slider-thumb]:bg-white",
          "[&::-webkit-slider-thumb]:border-2",
          "[&::-webkit-slider-thumb]:border-primary-500",
          "[&::-webkit-slider-thumb]:rounded-full",
          "[&::-webkit-slider-thumb]:shadow-soft",
          "[&::-webkit-slider-thumb]:transition-all",
          "[&::-webkit-slider-thumb]:hover:shadow-soft-md",
          "[&::-webkit-slider-thumb]:active:scale-95",
          "[&::-moz-range-thumb]:appearance-none",
          "[&::-moz-range-thumb]:w-4",
          "[&::-moz-range-thumb]:h-4",
          "[&::-moz-range-thumb]:bg-white",
          "[&::-moz-range-thumb]:border-2",
          "[&::-moz-range-thumb]:border-primary-500",
          "[&::-moz-range-thumb]:rounded-full",
          "[&::-moz-range-thumb]:shadow-soft",
          "[&::-moz-range-thumb]:transition-all",
          "[&::-moz-range-thumb]:hover:shadow-soft-md",
          "[&::-moz-range-thumb]:active:scale-95",
          "[&::-webkit-slider-runnable-track]:bg-primary-200",
          "[&::-webkit-slider-runnable-track]:rounded-full",
          "[&::-moz-range-track]:bg-primary-200",
          "[&::-moz-range-track]:rounded-full",
          "focus:outline-none",
          "focus-visible:ring-2",
          "focus-visible:ring-primary-400",
          "focus-visible:ring-offset-2",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Slider.displayName = "Slider"

export { Slider }