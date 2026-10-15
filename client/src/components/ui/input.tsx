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
          "bg-background text-foreground placeholder:text-muted-foreground",
          "focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-background",
          "disabled:cursor-not-allowed disabled:opacity-50",
          variant === 'default' && [
            "border border-input",
            "hover:border-primary/40",
            "focus:border-primary focus:ring-primary/20",
          ],
          variant === 'outlined' && [
            "border-2 border-input",
            "hover:border-primary/40",
            "focus:border-primary focus:ring-primary/20",
          ],
          variant === 'filled' && [
            "border border-transparent bg-muted",
            "hover:bg-muted/80",
            "focus:bg-background focus:border-primary focus:ring-primary/20",
          ],
          error && [
            "border-destructive bg-destructive/10",
            "hover:border-destructive",
            "focus:border-destructive focus:ring-destructive/20",
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
