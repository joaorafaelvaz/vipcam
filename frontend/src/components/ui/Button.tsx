import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
}

const variants = {
  primary:
    "bg-amber-500 text-zinc-900 hover:bg-amber-400 font-semibold shadow-md shadow-amber-500/20",
  secondary: "bg-zinc-800 text-zinc-200 hover:bg-zinc-700 border border-zinc-700",
  danger: "bg-red-600 text-white hover:bg-red-500",
  ghost: "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
