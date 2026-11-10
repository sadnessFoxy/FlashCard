// Minimal shared tokens for F2 screens. A full design system is still in the backlog.
export const colors = {
  primary: "#2563eb",
  primaryPressed: "#1d4ed8",
  onPrimary: "#ffffff",
  text: "#111827",
  textMuted: "#6b7280",
  border: "#d1d5db",
  surface: "#ffffff",
  background: "#f9fafb",
  danger: "#b91c1c",
  dangerBg: "#fee2e2",
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = { sm: 6, md: 10, lg: 14 } as const;

export const fontSize = { sm: 13, md: 15, lg: 17, xl: 24 } as const;
