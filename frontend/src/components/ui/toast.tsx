import * as React from "react"

export type ToastActionElement = React.ReactElement

export interface ToastProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  id?: string
  title?: React.ReactNode
  description?: React.ReactNode
  action?: ToastActionElement
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ id, title, description, action, open, onOpenChange, className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        role="status"
        aria-live="polite"
        className={className}
        {...props}
      >
        {title && <div className="font-semibold">{title}</div>}
        {description && <div className="text-sm opacity-90">{description}</div>}
        {action}
        {children}
      </div>
    )
  }
)

Toast.displayName = "Toast"