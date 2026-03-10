"use client";

import { useRealtimeStore } from "@/stores/useRealtimeStore";

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const connected = useRealtimeStore((s) => s.connected);

  return (
    <header className="flex h-16 items-center justify-between border-b border-zinc-800/60 bg-zinc-950/80 px-6 backdrop-blur-sm">
      <div>
        <h2 className="text-lg font-semibold text-zinc-100">{title}</h2>
        {subtitle && (
          <p className="text-xs text-zinc-500">{subtitle}</p>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs">
          <div
            className={`h-2 w-2 rounded-full ${
              connected
                ? "bg-emerald-400 shadow-sm shadow-emerald-400/50"
                : "bg-red-400 shadow-sm shadow-red-400/50"
            }`}
          />
          <span className="text-zinc-500">
            {connected ? "Ao vivo" : "Desconectado"}
          </span>
        </div>
      </div>
    </header>
  );
}
