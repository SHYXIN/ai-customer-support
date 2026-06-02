import { useState } from "react";
import { ChevronDown, ChevronUp, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Reference {
  id: string;
  content: string;
  response: string;
  category: string;
  score: number;
}

interface ReferencesProps {
  references: Reference[];
}

export function References({ references }: ReferencesProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (references.length === 0) return null;

  return (
    <div className="mt-2 border-t border-border/50 pt-2">
      <button
        className="flex items-center gap-2 text-xs text-muted-foreground transition-colors hover:text-foreground"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )}
        <FileText className="h-3 w-3" />
        <span>
          参考来源（{references.length} 条）
        </span>
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {references.map((ref) => (
            <div
              key={ref.id}
              className="rounded-md border bg-muted/30 p-3 text-xs"
            >
              <div className="mb-1 flex items-center justify-between">
                <span className="font-medium text-foreground">{ref.content}</span>
                <span
                  className={cn(
                    "rounded px-1.5 py-0.5 text-[10px]",
                    "bg-primary/10 text-primary"
                  )}
                >
                  {ref.category}
                </span>
              </div>
              <p className="text-muted-foreground line-clamp-2">{ref.response}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
