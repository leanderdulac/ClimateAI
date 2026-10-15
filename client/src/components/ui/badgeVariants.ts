import { cva, type VariantProps } from "class-variance-authority"

export const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-all duration-200",
  {
    variants: {
      variant: {
        default: "bg-primary/15 text-primary border border-primary/20",
        secondary: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30",
        warning: "bg-amber-500/10 text-amber-400 border border-amber-500/30",
        danger: "bg-red-500/10 text-red-400 border border-red-500/30",
        info: "bg-muted text-muted-foreground border border-border/50",
        outline: "border border-border/60 text-foreground",
      },
      size: {
        sm: "px-2 py-0.5 text-xs",
        default: "px-2.5 py-1 text-xs",
        lg: "px-3 py-1.5 text-sm",
      },
      animation: {
        none: "",
        pulse: "animate-pulse",
        bounce: "animate-bounce",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
      animation: "none",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
  VariantProps<typeof badgeVariants> { }
