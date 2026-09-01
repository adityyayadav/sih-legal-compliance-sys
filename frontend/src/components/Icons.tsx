/** Minimal line icons (24×24, currentColor stroke). */
type P = { size?: number; className?: string };

const base = (size: number, className?: string) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  className,
});

export const IconScan = ({ size = 24, className }: P) => (
  <svg {...base(size, className)}>
    <path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3" />
    <path d="M4 12h16" />
  </svg>
);

export const IconDashboard = ({ size = 24, className }: P) => (
  <svg {...base(size, className)}>
    <rect x="3" y="3" width="8" height="10" rx="1" />
    <rect x="13" y="3" width="8" height="6" rx="1" />
    <rect x="13" y="13" width="8" height="8" rx="1" />
    <rect x="3" y="17" width="8" height="4" rx="1" />
  </svg>
);

export const IconBox = ({ size = 24, className }: P) => (
  <svg {...base(size, className)}>
    <path d="M21 8 12 3 3 8v8l9 5 9-5V8Z" />
    <path d="m3 8 9 5 9-5M12 13v8" />
  </svg>
);

export const IconReport = ({ size = 24, className }: P) => (
  <svg {...base(size, className)}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
    <path d="M14 2v6h6M9 13h6M9 17h6M9 9h1" />
  </svg>
);

export const IconRules = ({ size = 24, className }: P) => (
  <svg {...base(size, className)}>
    <path d="M9 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4" />
    <path d="m9 11 3 3 9-9M8 7h4" />
  </svg>
);

export const IconHelp = ({ size = 24, className }: P) => (
  <svg {...base(size, className)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M9.5 9a2.5 2.5 0 0 1 4.5 1.5c0 1.5-2 2-2 3M12 17h.01" />
  </svg>
);

export const IconShield = ({ size = 24, className }: P) => (
  <svg {...base(size, className)}>
    <path d="M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6Z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

export const IconGauge = ({ size = 24, className }: P) => (
  <svg {...base(size, className)}>
    <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
    <path d="M13.5 10.5 17 7M4 20a10 10 0 1 1 16 0" />
  </svg>
);

export const IconUpload = ({ size = 24, className }: P) => (
  <svg {...base(size, className)}>
    <path d="M12 15V3m0 0-4 4m4-4 4 4" />
    <path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4" />
  </svg>
);
