export function Spinner({ size = 'md', className = '' }: { size?: 'sm' | 'md' | 'lg'; className?: string }) {
  const sizes = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' }
  return (
    <div className={`animate-spin rounded-full border-2 border-gray-200 border-t-primary-600 ${sizes[size]} ${className}`} />
  )
}

export function PageLoader() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-white">
      <div className="relative">
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-600 to-teal-500 flex items-center justify-center shadow-lg">
          <svg className="w-8 h-8 text-white" viewBox="0 0 24 24" fill="none">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="currentColor" opacity="0.2"/>
            <path d="M9 11l3 3L22 4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <Spinner size="lg" className="absolute inset-0 -m-2" />
      </div>
      <p className="mt-4 text-sm text-gray-500 font-medium">Tibbiyot Novatorlari</p>
    </div>
  )
}
