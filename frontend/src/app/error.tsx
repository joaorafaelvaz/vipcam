"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="text-center space-y-4">
        <AlertTriangle className="h-12 w-12 text-amber-400 mx-auto" />
        <h2 className="text-lg font-semibold text-zinc-200">
          Algo deu errado
        </h2>
        <p className="text-sm text-zinc-500 max-w-md">
          Ocorreu um erro ao carregar esta pagina. Tente recarregar.
        </p>
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-zinc-900 hover:bg-amber-400 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Tentar novamente
        </button>
      </div>
    </div>
  );
}
