"use client";

import { useEffect } from "react";

import { useRealtimeStore } from "@/stores/useRealtimeStore";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const connect = useRealtimeStore((s) => s.connect);

  useEffect(() => {
    connect();
  }, [connect]);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <Sidebar />
      <main className="ml-64">{children}</main>
    </div>
  );
}
