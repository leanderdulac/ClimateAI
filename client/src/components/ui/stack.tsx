import * as React from "react"
import { cn } from "@/lib/utils"

interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  direction?: 'row' | 'col'
  spacing?: 'none' | 'sm' | 'default' | 'lg' | 'xl'
  align?: 'start' | 'center' | 'end' | 'stretch'
  justify?: 'start' | 'center' | 'end' | 'between' | 'around'
  wrap?: boolean
}

const Stack = React.forwardRef<HTMLDivElement, StackProps>(
  ({ 
    className, 
    direction = 'col', 
    spacing = 'default', 
    align = 'start',
    justify = 'start',
    wrap = false,
    ...props 
  }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "flex",
          {
            'flex-row': direction === 'row',
            'flex-col': direction === 'col',
            'gap-0': spacing === 'none',
            'gap-3': spacing === 'sm',
            'gap-6': spacing === 'default',
            'gap-8': spacing === 'lg',
            'gap-12': spacing === 'xl',
            'items-start': align === 'start',
            'items-center': align === 'center',
            'items-end': align === 'end',
            'items-stretch': align === 'stretch',
            'justify-start': justify === 'start',
            'justify-center': justify === 'center',
            'justify-end': justify === 'end',
            'justify-between': justify === 'between',
            'justify-around': justify === 'around',
            'flex-wrap': wrap,
            'flex-nowrap': !wrap,
          },
          className
        )}
        {...props}
      />
    )
  }
)
Stack.displayName = "Stack"

export { Stack }