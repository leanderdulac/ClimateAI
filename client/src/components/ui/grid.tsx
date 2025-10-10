import * as React from "react"
import { cn } from "@/lib/utils"

interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: 1 | 2 | 3 | 4 | 6 | 12
  gap?: 'none' | 'sm' | 'default' | 'lg' | 'xl'
  flow?: 'row' | 'col'
}

const Grid = React.forwardRef<HTMLDivElement, GridProps>(
  ({ className, cols = 12, gap = 'default', flow = 'row', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "grid",
          {
            'grid-cols-1': cols === 1,
            'grid-cols-2': cols === 2,
            'grid-cols-3': cols === 3,
            'grid-cols-4': cols === 4,
            'grid-cols-6': cols === 6,
            'grid-cols-12': cols === 12,
            'gap-0': gap === 'none',
            'gap-3': gap === 'sm',
            'gap-6': gap === 'default',
            'gap-8': gap === 'lg',
            'gap-12': gap === 'xl',
            'auto-rows-auto': flow === 'row',
            'auto-cols-auto': flow === 'col',
          },
          className
        )}
        {...props}
      />
    )
  }
)
Grid.displayName = "Grid"

interface GridItemProps extends React.HTMLAttributes<HTMLDivElement> {
  span?: number
  start?: number
}

const GridItem = React.forwardRef<HTMLDivElement, GridItemProps>(
  ({ className, span, start, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          {
            'col-span-1': span === 1,
            'col-span-2': span === 2,
            'col-span-3': span === 3,
            'col-span-4': span === 4,
            'col-span-5': span === 5,
            'col-span-6': span === 6,
            'col-span-7': span === 7,
            'col-span-8': span === 8,
            'col-span-9': span === 9,
            'col-span-10': span === 10,
            'col-span-11': span === 11,
            'col-span-12': span === 12,
            'col-start-1': start === 1,
            'col-start-2': start === 2,
            'col-start-3': start === 3,
            'col-start-4': start === 4,
            'col-start-5': start === 5,
            'col-start-6': start === 6,
            'col-start-7': start === 7,
            'col-start-8': start === 8,
            'col-start-9': start === 9,
            'col-start-10': start === 10,
            'col-start-11': start === 11,
            'col-start-12': start === 12,
          },
          className
        )}
        {...props}
      />
    )
  }
)
GridItem.displayName = "GridItem"

export { Grid, GridItem }