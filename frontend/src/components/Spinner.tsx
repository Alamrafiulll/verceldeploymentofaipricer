
export default function Spinner({
  className = '',
  size = 'md',
  color = 'dark',
}: {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  color?: 'light' | 'dark';
}) {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-[3px]',
    lg: 'h-12 w-12 border-4',
  };

  const colorClasses = {
    light: 'border-white/30 border-t-white',
    dark: 'border-slate-200 border-t-slate-800',
  };

  return (
    <div className={`flex justify-center ${className}`}>
      <div
        className={`animate-spin rounded-full ${colorClasses[color]} ${sizeClasses[size]}`}
      />
    </div>
  );
}
