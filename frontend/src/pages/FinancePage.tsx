import { useRef, useState } from "react";

import { Modal } from "@/components/Modal";
import * as fin from "@/features/finance/api";
import type { TransactionKind } from "@/features/finance/api";
import { BudgetPanel } from "@/features/finance/BudgetPanel";
import { TransactionForm } from "@/features/finance/TransactionForm";
import { currentMonth, formatCents } from "@/features/finance/money";
import {
  useAccounts,
  useCategories,
  useFinanceMutation,
  useSummary,
  useTransactions,
} from "@/features/finance/queries";

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export default function FinancePage() {
  const [month, setMonth] = useState(currentMonth());
  const [adding, setAdding] = useState(false);
  const [kindFilter, setKindFilter] = useState<TransactionKind | "">("");
  const fileInput = useRef<HTMLInputElement>(null);

  const { data: summary } = useSummary(month);
  const { data: accounts = [] } = useAccounts();
  const { data: categories = [] } = useCategories();
  const { data: transactions = [] } = useTransactions({
    from: `${month}-01`,
    to: `${month}-31`,
    kind: kindFilter || undefined,
    limit: 200,
  });

  const importCsv = useFinanceMutation(fin.importTransactions);
  const removeTxn = useFinanceMutation(fin.deleteTransaction);
  const createAccount = useFinanceMutation(fin.createAccount);

  const categoryName = (id: number | null): string =>
    id === null ? "—" : (categories.find((c) => c.id === id)?.name ?? "—");

  const cards = [
    { label: "Income", value: summary ? formatCents(summary.income_cents) : "–" },
    { label: "Expenses", value: summary ? formatCents(summary.expense_cents) : "–" },
    { label: "Net", value: summary ? formatCents(summary.net_cents) : "–" },
    { label: "Savings rate", value: summary ? pct(summary.savings_rate) : "–" },
  ];

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold">Finance</h2>
          <input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="rounded-md border border-slate-300 px-2 py-1 text-sm outline-none focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900"
          />
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={fileInput}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) importCsv.mutate(file);
              e.target.value = "";
            }}
          />
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Import CSV
          </button>
          <button
            type="button"
            onClick={() => setAdding(true)}
            disabled={accounts.length === 0}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            + Transaction
          </button>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {cards.map((card) => (
          <div
            key={card.label}
            className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="text-xl font-bold tabular-nums">{card.value}</div>
            <div className="text-xs text-slate-500">{card.label}</div>
          </div>
        ))}
      </div>

      {importCsv.data && (
        <p className="mb-4 text-sm text-slate-500">
          Imported {importCsv.data.imported} row{importCsv.data.imported === 1 ? "" : "s"}
          {importCsv.data.errors.length > 0 && `, ${importCsv.data.errors.length} skipped`}.
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <BudgetPanel month={month} byCategory={summary?.by_category ?? []} />

        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="mb-3 text-sm font-medium text-slate-500">Accounts</h3>
          <ul className="space-y-2 text-sm">
            {accounts.map((account) => (
              <li key={account.id} className="flex justify-between">
                <span>{account.name}</span>
                <span className="tabular-nums font-medium">
                  {formatCents(account.balance_cents, account.currency)}
                </span>
              </li>
            ))}
          </ul>
          <form
            className="mt-3 flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              const data = new FormData(event.currentTarget);
              const name = String(data.get("name") ?? "").trim();
              if (name) {
                createAccount.mutate({ name });
                event.currentTarget.reset();
              }
            }}
          >
            <input
              name="name"
              placeholder="+ account"
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
      </div>

      <div className="mt-6">
        <div className="mb-2 flex items-center gap-2">
          <h3 className="text-sm font-medium text-slate-500">Transactions</h3>
          <select
            value={kindFilter}
            onChange={(e) => setKindFilter(e.target.value as TransactionKind | "")}
            className="rounded border border-slate-300 px-1.5 py-0.5 text-xs outline-none dark:border-slate-700 dark:bg-slate-900"
          >
            <option value="">All</option>
            <option value="expense">Expenses</option>
            <option value="income">Income</option>
          </select>
        </div>
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-900">
              <tr>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Description</th>
                <th className="px-3 py-2">Category</th>
                <th className="px-3 py-2 text-right">Amount</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => (
                <tr key={txn.id} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="px-3 py-2 tabular-nums text-slate-500">{txn.occurred_on}</td>
                  <td className="px-3 py-2">{txn.description ?? "—"}</td>
                  <td className="px-3 py-2 text-slate-500">{categoryName(txn.category_id)}</td>
                  <td
                    className={`px-3 py-2 text-right tabular-nums ${
                      txn.kind === "income" ? "text-emerald-600" : ""
                    }`}
                  >
                    {txn.kind === "income" ? "+" : "−"}
                    {formatCents(txn.amount_cents)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <button
                      type="button"
                      onClick={() => removeTxn.mutate(txn.id)}
                      className="text-slate-300 hover:text-rose-500"
                      aria-label="Delete transaction"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-sm text-slate-400">
                    No transactions this month.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {adding && (
        <Modal title="New transaction" onClose={() => setAdding(false)}>
          <TransactionForm
            accounts={accounts}
            categories={categories}
            onDone={() => setAdding(false)}
          />
        </Modal>
      )}
    </div>
  );
}
