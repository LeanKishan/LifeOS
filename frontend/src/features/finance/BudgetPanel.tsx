import { useState } from "react";

import { Button, CardHeader, Input } from "@/components/ui";
import * as fin from "@/features/finance/api";
import type { CategorySpend } from "@/features/finance/api";
import { formatCents, parseAmountToCents } from "@/features/finance/money";
import { useCategories, useFinanceMutation } from "@/features/finance/queries";

function Bar({ spent, budget }: { spent: number; budget: number | null }) {
  const ceiling = Math.max(spent, budget ?? 0, 1);
  const spentPct = (spent / ceiling) * 100;
  const budgetPct = budget ? (budget / ceiling) * 100 : null;
  const over = budget != null && spent > budget;

  return (
    <div className="relative h-2 w-full overflow-hidden rounded-full bg-line/[0.08]">
      <div
        className={`absolute inset-y-0 left-0 rounded-full ${
          over ? "bg-rose-500" : "bg-gradient-to-r from-brand-hi to-brand"
        }`}
        style={{ width: `${Math.min(spentPct, 100)}%` }}
      />
      {budgetPct != null && budgetPct < 100 && (
        <div
          className="absolute inset-y-[-2px] w-0.5 bg-content/60"
          style={{ left: `${budgetPct}%` }}
        />
      )}
    </div>
  );
}

export function BudgetPanel({
  month,
  byCategory,
}: {
  month: string;
  byCategory: CategorySpend[];
}) {
  const { data: categories = [] } = useCategories();
  const setBudget = useFinanceMutation(fin.setBudget);
  const addCategory = useFinanceMutation(fin.createCategory);

  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [newCategory, setNewCategory] = useState("");

  const expenseCategories = categories.filter((c) => c.kind === "expense");
  const rows = expenseCategories.map((category) => {
    const spend = byCategory.find((entry) => entry.category_id === category.id);
    return {
      category,
      spent: spend?.spent_cents ?? 0,
      budget: spend?.budget_cents ?? null,
      over: spend?.over ?? false,
    };
  });

  function saveBudget(categoryId: number): void {
    const raw = drafts[categoryId];
    if (raw === undefined) return;
    const cents = raw.trim() === "" ? 0 : parseAmountToCents(raw);
    if (cents === null) return;
    setBudget.mutate({ category_id: categoryId, month, limit_cents: cents });
  }

  return (
    <div className="surface-card p-5">
      <CardHeader title="Spending vs budget" />

      {rows.length === 0 && <p className="text-sm text-faint">No expense categories yet.</p>}

      <ul className="space-y-4">
        {rows.map(({ category, spent, budget, over }) => (
          <li key={category.id}>
            <div className="mb-1.5 flex items-center justify-between gap-2 text-sm">
              <span className="flex items-center gap-1.5 text-content">
                <span
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: category.color }}
                />
                {category.name}
              </span>
              <span
                className={over ? "font-semibold text-rose-400" : "tabular-nums text-muted"}
              >
                {formatCents(spent)}
                {budget != null && ` / ${formatCents(budget)}`}
              </span>
            </div>
            <Bar spent={spent} budget={budget} />
            <input
              value={drafts[category.id] ?? (budget != null ? String(budget / 100) : "")}
              onChange={(e) => setDrafts((d) => ({ ...d, [category.id]: e.target.value }))}
              onBlur={() => saveBudget(category.id)}
              placeholder="set monthly budget"
              inputMode="decimal"
              className="field-input mt-2 h-8 w-40 px-2.5 py-0 text-xs"
            />
          </li>
        ))}
      </ul>

      <form
        className="mt-5 flex gap-2 border-t border-line/[0.06] pt-4"
        onSubmit={(event) => {
          event.preventDefault();
          const name = newCategory.trim();
          if (name) {
            addCategory.mutate(
              { name, kind: "expense" },
              { onSuccess: () => setNewCategory("") },
            );
          }
        }}
      >
        <Input
          value={newCategory}
          onChange={(e) => setNewCategory(e.target.value)}
          placeholder="New expense category"
          className="flex-1"
        />
        <Button type="submit" variant="secondary" icon="plus" size="sm">
          Add
        </Button>
      </form>
    </div>
  );
}
