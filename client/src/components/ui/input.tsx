import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'outlined' | 'filled'
  error?: boolean
  fullWidth?: boolean
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, variant = 'default', error, fullWidth, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "h-10 rounded-md px-3 py-2 text-sm transition-all duration-200",
          "placeholder:text-neutral-400",
          "focus:outline-none focus:ring-2 focus:ring-offset-1",
          "disabled:cursor-not-allowed disabled:opacity-50",
          variant === 'default' && [
            "border border-neutral-200 bg-white",
            "hover:border-neutral-300",
            "focus:border-primary-300 focus:ring-primary-200",
          ],
          variant === 'outlined' && [
            "border-2 border-neutral-200 bg-white",
            "hover:border-neutral-300",
            "focus:border-primary-300 focus:ring-primary-200",
          ],
          variant === 'filled' && [
            "border border-transparent bg-neutral-100",
            "hover:bg-neutral-200",
            "focus:bg-white focus:border-primary-300 focus:ring-primary-200",
          ],
          error && [
            "border-danger-300 bg-danger-50",
            "hover:border-danger-400",
            "focus:border-danger-400 focus:ring-danger-200",
          ],
          fullWidth && "w-full",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }