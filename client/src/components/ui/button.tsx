import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default: "bg-primary text-white shadow-soft hover:bg-primary-600 hover:shadow-soft-md",
        secondary: "bg-success text-white shadow-soft hover:bg-success-600 hover:shadow-soft-md",
        outline: "border-2 border-neutral-200 bg-white text-neutral-700 hover:border-primary hover:bg-primary-50 hover:text-primary-600",
        ghost: "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-800",
        warning: "bg-warning text-white shadow-soft hover:bg-warning-600 hover:shadow-soft-md",
        danger: "bg-danger text-white shadow-soft hover:bg-danger-600 hover:shadow-soft-md",
        link: "text-primary-600 underline-offset-4 hover:underline hover:text-primary-700",
      },
      size: {
        xs: "h-7 rounded px-2 text-xs",
        sm: "h-8 rounded-md px-3 text-sm",
        default: "h-10 px-4 py-2",
        lg: "h-11 rounded-md px-6 text-base",
        xl: "h-12 rounded-lg px-8 text-base",
        icon: "h-10 w-10 rounded-full p-2",
      },
      fullWidth: {
        true: "w-full",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
      fullWidth: false,
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
  VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }