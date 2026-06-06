import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react'
import clsx from 'clsx'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, ...props }, ref) => (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <input
        ref={ref}
        className={clsx(
          'input',
          error && 'border-red-400 ring-2 ring-red-200',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-red-500">{error}</p>}
      {hint && !error && <p className="text-xs text-gray-400">{hint}</p>}
    </div>
  )
)
Input.displayName = 'Input'

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  hint?: string
  showWordCount?: boolean
  maxWords?: number
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, showWordCount, maxWords, className, value, onChange, ...props }, ref) => {
    const wordCount = String(value || '').trim().split(/\s+/).filter(Boolean).length
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <div className="flex justify-between">
            <label className="text-sm font-medium text-gray-700">{label}</label>
            {showWordCount && maxWords && (
              <span className={clsx('text-xs', wordCount >= maxWords ? 'text-red-500' : 'text-gray-400')}>
                {wordCount}/{maxWords}
              </span>
            )}
          </div>
        )}
        <textarea
          ref={ref}
          className={clsx(
            'input resize-none min-h-[100px]',
            error && 'border-red-400 ring-2 ring-red-200',
            className
          )}
          value={value}
          onChange={onChange}
          {...props}
        />
        {error && <p className="text-xs text-red-500">{error}</p>}
        {hint && !error && <p className="text-xs text-gray-400">{hint}</p>}
      </div>
    )
  }
)
Textarea.displayName = 'Textarea'

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  options: Array<{ value: string; label: string }>
}

export function Select({ label, error, options, className, ...props }: SelectProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <select
        className={clsx('input appearance-none bg-[url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\'%3E%3Cpath stroke=\'%236b7280\' stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M6 9l6 6 6-6\'/%3E%3C/svg%3E")] bg-no-repeat bg-[right_12px_center] bg-[length:20px]', error && 'border-red-400', className)}
        {...props}
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}
