interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
}

const SIZE_CLASSES = {
  sm: 'h-4 w-4 border-2',
  md: 'h-6 w-6 border-2',
  lg: 'h-8 w-8 border-[3px]',
};

export default function Spinner({ size = 'md' }: SpinnerProps) {
  return (
    <span
      aria-label="Loading"
      role="status"
      className={`inline-block animate-spin rounded-full border-slate-300 border-t-slate-900 ${SIZE_CLASSES[size]}`}
    />
  );
}
