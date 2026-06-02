import { cn } from "@/lib/utils";

interface QuickQuestionsProps {
  onSelect: (question: string) => void;
  disabled: boolean;
}

const QUESTIONS = [
  { label: "如何取消订单", message: "如何取消订单？" },
  { label: "查询物流", message: "如何查询物流信息？" },
  { label: "申请退款", message: "如何申请退款？" },
  { label: "退换货政策", message: "请问退换货政策是什么？" },
  { label: "支付方式", message: "支持哪些支付方式？" },
  { label: "运费说明", message: "运费如何计算？" },
];

export function QuickQuestions({ onSelect, disabled }: QuickQuestionsProps) {
  return (
    <div className="flex flex-wrap gap-2 px-4 py-2">
      {QUESTIONS.map((q) => (
        <button
          key={q.label}
          className={cn(
            "rounded-full border bg-background px-3 py-1.5 text-xs text-foreground transition-colors",
            "hover:bg-accent hover:text-accent-foreground",
            "disabled:cursor-not-allowed disabled:opacity-50"
          )}
          onClick={() => onSelect(q.message)}
          disabled={disabled}
        >
          {q.label}
        </button>
      ))}
    </div>
  );
}
