import { emotionColor, formatEmotion } from "@/lib/utils";
import type { WSPersonData } from "@/types";

interface EmotionOverlayProps {
  persons: WSPersonData[];
}

export function EmotionOverlay({ persons }: EmotionOverlayProps) {
  if (persons.length === 0) return null;

  return (
    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-3 py-2">
      <div className="flex flex-wrap gap-1.5">
        {persons.slice(0, 4).map((person, i) => (
          <div
            key={person.person_id || i}
            className="flex items-center gap-1.5"
          >
            <div
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: emotionColor(person.dominant_emotion) }}
            />
            <span className="text-[10px] text-zinc-300">
              {formatEmotion(person.dominant_emotion)}
            </span>
          </div>
        ))}
        {persons.length > 4 && (
          <span className="text-[10px] text-zinc-500">
            +{persons.length - 4}
          </span>
        )}
      </div>
    </div>
  );
}
