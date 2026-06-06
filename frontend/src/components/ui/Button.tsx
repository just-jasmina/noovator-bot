import { type ButtonHTMLAttributes } from 'react'
import clsx from 'clsx'
import { Spinner } from './Spinner'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  fullWidth?: boolean
}

export function Button({
  variant = 'primary', size = 'md', loading, fullWidth,
  children, className, disabled, ...props
}: ButtonProps) {
  const base = 'inline-flex items-center justify-center gap-2 font-semibold rounded-xl transition-all duration-150 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed select-none'
  const variants = {
    primary: 'bg-primary-600 text-white shadow-sm hover:bg-primary-700',
    secondary: 'bg-gray-100 text-gray-800 hover:bg-gray-200',
    ghost: 'text-primary-600 hover:bg-primary-50',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  }
  const sizes = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-sm',
    lg: 'px-8 py-4 text-base',
  }
  return (
    <button
      className={clsx(base, variants[variant], sizes[size], fullWidth && 'w-full', className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  )
}
