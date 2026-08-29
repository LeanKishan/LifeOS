import { useRef, useState } from "react";

import { Icon } from "@/components/icons";
import { Modal } from "@/components/Modal";
import { Button, Card, CardHeader, Input, PageHeader, Select, StatTile } from "@/components/ui";
import * as fin from "@/features/finance/api";
import type { TransactionKind } from "@/features/finance/api";
import { BudgetPanel } from "@/features/finance/BudgetPanel";
import { currentMonth, formatCents } from "@/features/finance/money";
import {
  useAccounts,
  useCategories,
  useFinanceMutation,
  useSummary,
  useTransactions,
} from "@/features/finance/queries";
import { TransactionForm } from "@/features/finance/TransactionForm";
import { pushToast } from "@/features/notifications/toasts";

const pct = (v: number) => `${Math.round(v * 100)}%`;

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

  async function downloadReport(): Promise<void> {
    try {
      await fin.requestReport(month);
      const blob = await fin.fetchReport(month);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `finance-${month}.pdf`;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch {
      pushToast({
        message: "Report is generating — you'll get a notification when it's ready.",
      });
    }
  }

  const categoryName = (id: number | null): string =>
    id === null ? "—" : (categories.find((c) => c.id === id)?.name ?? "—");

  return (
    <div>
      <PageHeader
        title="Finance"
        subtitle={
          <span className="inline-flex items-center gap-2">
            Money in, money out —
            <input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="field-input h-7 w-[8.5rem] px-2 py-0 text-xs"
            />
          </span>
        }
        actions={
          <>
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
            <Button variant="ghost" icon="download" onClick={() => fileInput.current?.click()}>
              Import CSV
            </Button>
            <Button variant="secondary" icon="download" onClick={() => void downloadReport()}>
              Report PDF
            </Button>
            <Button
              variant="primary"
              icon="plus"
              disabled={accounts.length === 0}
              onClick={() => setAdding(true)}
            >
              Transaction
            </Button>
          </>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Income" value={summary ? formatCents(summary.income_cents) : "–"} icon="wallet" />
        <StatTile
          label="Expenses"
          value={summary ? formatCents(summary.expense_cents) : "–"}
          icon="arrowRight"
          tone="rose"
        />
        <StatTile
          label="Net"
          value={summary ? formatCents(summary.net_cents) : "–"}
          icon="chart"
          tone="violet"
        />
        <StatTile
          label="Savings rate"
          value={summary ? pct(summary.savings_rate) : "–"}
          icon="target"
          tone="amber"
        />
      </div>

      {importCsv.data && (
        <p className="mb-4 text-sm text-muted">
          Imported {importCsv.data.imported} row{importCsv.data.imported === 1 ? "" : "s"}
          {importCsv.data.errors.length > 0 && `, ${importCsv.data.errors.length} skipped`}.
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <BudgetPanel month={month} byCategory={summary?.by_category ?? []} />

        <Card>
          <CardHeader title="Accounts" />
          <ul className="space-y-2 text-sm">
            {accounts.map((account) => (
              <li
                key={account.id}
                className="flex justify-between rounded-lg px-2 py-1.5 hover:bg-line/[0.04]"
              >
                <span className="text-content">{account.name}</span>
                <span className="font-semibold tabular-nums text-content">
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
            <Input name="name" placeholder="New account name" className="flex-1" />
            <Button type="submit" variant="secondary" icon="plus" size="sm">
              Add
            </Button>
          </form>
        </Card>
      </div>

      <div className="mt-6">
        <div className="mb-3 flex items-center gap-3">
          <h3 className="label-eyebrow">Transactions</h3>
          <Select
            value={kindFilter}
            onChange={(e) => setKindFilter(e.target.value as TransactionKind | "")}
            className="h-7 w-28 py-0 text-xs"
          >
            <option value="">All</option>
            <option value="expense">Expenses</option>
            <option value="income">Income</option>
          </Select>
        </div>
        <div className="surface-card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line/[0.08] text-xs uppercase tracking-wide text-faint">
                <th className="px-4 py-3 font-semibold">Date</th>
                <th className="px-4 py-3 font-semibold">Description</th>
                <th className="px-4 py-3 font-semibold">Category</th>
                <th className="px-4 py-3 text-right font-semibold">Amount</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => (
                <tr
                  key={txn.id}
                  className="group border-b border-line/[0.05] last:border-0 hover:bg-line/[0.03]"
                >
                  <td className="px-4 py-2.5 tabular-nums text-faint">{txn.occurred_on}</td>
                  <td className="px-4 py-2.5 text-content">{txn.description ?? "—"}</td>
                  <td className="px-4 py-2.5 text-muted">{categoryName(txn.category_id)}</td>
                  <td
                    className={`px-4 py-2.5 text-right font-semibold tabular-nums ${
                      txn.kind === "income" ? "text-brand-hi" : "text-content"
                    }`}
                  >
                    {txn.kind === "income" ? "+" : "−"}
                    {formatCents(txn.amount_cents)}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <button
                      type="button"
                      onClick={() => removeTxn.mutate(txn.id)}
                      className="text-faint opacity-0 transition hover:text-rose-400 group-hover:opacity-100"
                      aria-label="Delete transaction"
                    >
                      <Icon name="trash" size={15} />
                    </button>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-sm text-faint">
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
