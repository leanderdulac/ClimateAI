import * as React from "react"
import { cn } from "@/lib/utils"

interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'default' | 'lg' | 'xl' | 'full'
  gutter?: boolean
}

const Container = React.forwardRef<HTMLDivElement, ContainerProps>(
  ({ className, size = 'default', gutter = true, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "mx-auto w-full",
          {
            'sm:max-w-screen-sm': size === 'sm',
            'lg:max-w-screen-lg': size === 'default',
            'xl:max-w-screen-xl': size === 'lg',
            '2xl:max-w-screen-2xl': size === 'xl',
            'max-w-none': size === 'full',
          },
          gutter && 'px-4 sm:px-6 lg:px-8',
          className
        )}
        {...props}
      />
    )
  }
)
Container.displayName = "Container"

export { Container }