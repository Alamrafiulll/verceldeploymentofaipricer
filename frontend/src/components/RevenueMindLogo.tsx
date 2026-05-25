interface LogoProps {
  collapsed?: boolean;
  className?: string;
  imageClassName?: string;
  transparent?: boolean;
}

export default function RevenueMindLogo({
  collapsed = false,
  className = '',
  imageClassName = '',
  transparent = false,
}: LogoProps) {
  const defaultImageSize = collapsed ? 'h-10 w-40' : 'h-20 w-72';

  const containerClasses = transparent
    ? `inline-flex items-center justify-center transition-all duration-300 ${className}`
    : `inline-flex items-center justify-center rounded-xl bg-white/95 backdrop-blur-md border border-slate-100/50 shadow-sm transition-all duration-300 dark:bg-slate-900/60 dark:border-slate-800/40 ${className}`;

  return (
    <div className={containerClasses}>
      <img
        src="/revenuemind-logo-color.svg"
        alt="RevenueMind"
        className={`${defaultImageSize} object-contain transition-all duration-300 dark:hidden ${imageClassName}`}
      />
      <img
        src="/revenuemind-logo-white.svg"
        alt="RevenueMind"
        className={`${defaultImageSize} object-contain transition-all duration-300 hidden dark:block ${imageClassName}`}
      />
    </div>
  );
}
