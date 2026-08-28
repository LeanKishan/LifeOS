import { useState } from "react";

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
    <div className="relative h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800">
      <div
        className={`absolute inset-y-0 left-0 rounded-full ${over ? "bg-rose-500" : "bg-emerald-500"}`}
        style={{ width: `${spentPct}%` }}
      />
      {budgetPct != null && (
        <div
          className="absolute inset-y-[-2px] w-0.5 bg-slate-500"
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

  const expenseCategories = categories.filter((category) => category.kind === "expense");
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
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <h3 className="mb-3 text-sm font-medium text-slate-500">Spending vs budget</h3>

      {rows.length === 0 && (
        <p className="text-sm text-slate-400">No expense categories yet.</p>
      )}

      <ul className="space-y-3">
        {rows.map(({ category, spent, budget, over }) => (
          <li key={category.id}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span className="flex items-center gap-1.5">
                <span
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: category.color }}
                />
                {category.name}
              </span>
              <span className={over ? "font-medium text-rose-600" : "text-slate-500"}>
                {formatCents(spent)}
                {budget != null && ` / ${formatCents(budget)}`}
              </span>
            </div>
            <Bar spent={spent} budget={budget} />
            <input
              value={drafts[category.id] ?? (budget != null ? String(budget / 100) : "")}
              onChange={(e) => setDrafts((d) => ({ ...d, [category.id]: e.target.value }))}
              onBlur={() => saveBudget(category.id)}
              placeholder="set budget"
              className="mt-1 w-28 rounded border border-slate-200 px-2 py-0.5 text-xs outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900"
            />
          </li>
        ))}
      </ul>

      <form
        className="mt-4 flex gap-2"
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
        <input
          value={newCategory}
          onChange={(e) => setNewCategory(e.target.value)}
          placeholder="+ expense category"
          className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900"
        />
        <button
          type="submit"
          className="rounded-md bg-slate-100 px-3 py-1 text-sm font-medium hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700"
        >
          Add
        </button>
      </form>
    </div>
  );
}
