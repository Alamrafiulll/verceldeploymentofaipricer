interface LogoProps {
  collapsed?: boolean;
  className?: string;
}

export default function ChinHinLogo({ collapsed = false, className = '' }: LogoProps) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {/* Geometric chevron mark */}
      <svg
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="h-9 w-9 flex-shrink-0"
      >
        {/* Red chevron stripe */}
        <polygon points="4,38 20,10 26,10 10,38" fill="#E41E2B" />
        {/* Blue chevron stripe 1 */}
        <polygon points="12,38 28,10 34,10 18,38" fill="#1e3a7b" />
        {/* Blue chevron stripe 2 */}
        <polygon points="20,38 36,10 42,10 26,38" fill="#262261" />
        {/* White stripe between */}
        <polygon points="10,38 26,10 28,10 12,38" fill="white" opacity="0.9" />
        <polygon points="18,38 34,10 36,10 20,38" fill="white" opacity="0.9" />
      </svg>

      {!collapsed && (
        <div className="flex flex-col leading-none">
          <span className="text-[17px] font-extrabold tracking-tight text-white">
            CHIN HIN
          </span>
          <span className="text-[8px] font-medium tracking-[0.15em] text-white/60">
            GROUP BERHAD
          </span>
        </div>
      )}
    </div>
  );
}
