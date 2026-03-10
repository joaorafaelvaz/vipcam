import Link from "next/link";
import { User } from "lucide-react";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatTimeAgo, satisfactionLevel } from "@/lib/utils";
import type { Person } from "@/types";

interface PersonCardProps {
  person: Person;
}

export function PersonCard({ person }: PersonCardProps) {
  const satisfaction = satisfactionLevel(person.avg_satisfaction);
  const typeLabels: Record<string, string> = {
    client: "Cliente",
    employee: "Funcionario",
    unknown: "Desconhecido",
  };
  const typeVariants: Record<string, "info" | "success" | "default"> = {
    client: "info",
    employee: "success",
    unknown: "default",
  };

  return (
    <Link href={`/people/${person.id}`}>
      <Card className="hover:border-zinc-700/80 transition-all duration-200 cursor-pointer group">
        <div className="p-4 flex items-start gap-3">
          {/* Avatar */}
          <div className="h-12 w-12 rounded-full bg-zinc-800 flex items-center justify-center shrink-0 overflow-hidden">
            {person.thumbnail_path ? (
              <img
                src={`/api/persons/${person.id}/thumbnail`}
                alt=""
                className="h-full w-full object-cover"
              />
            ) : (
              <User className="h-5 w-5 text-zinc-600" />
            )}
          </div>

          {/* Info */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-zinc-200 truncate group-hover:text-amber-400 transition-colors">
                {person.display_name || `Pessoa #${person.id.slice(0, 6)}`}
              </h3>
              <Badge variant={typeVariants[person.person_type]}>
                {typeLabels[person.person_type]}
              </Badge>
            </div>

            <div className="mt-1 flex items-center gap-3 text-[11px] text-zinc-500">
              <span>{person.total_visits} visitas</span>
              <span>Visto {formatTimeAgo(person.last_seen_at)}</span>
            </div>

            {person.avg_satisfaction !== null && (
              <div className="mt-1.5 flex items-center gap-1.5">
                <div
                  className="h-1.5 w-1.5 rounded-full"
                  style={{ backgroundColor: satisfaction.color }}
                />
                <span className="text-[11px]" style={{ color: satisfaction.color }}>
                  Satisfacao: {person.avg_satisfaction.toFixed(1)}/10
                </span>
              </div>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}
