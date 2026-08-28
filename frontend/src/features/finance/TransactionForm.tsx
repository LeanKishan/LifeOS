import { useState, type FormEvent } from "react";

import * as fin from "@/features/finance/api";
import type { Account, Category, TransactionKind } from "@/features/finance/api";
import { useFinanceMutation } from "@/features/finance/queries";
import { parseAmountToCents } from "@/features/finance/money";
import { toDateInput } from "@/features/calendar/dateUtils";

const inputClass =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none " +
  "focus:border-emerald-500 dark:border-slate-700 dark:bg-slate-900";

export function TransactionForm({
  accounts,
  categories,
  onDone,
}: {
  accounts: Account[];
  categories: Category[];
  onDone: () => void;
}) {
  const create = useFinanceMutation(fin.createTransaction);

  const [accountId, setAccountId] = useState(accounts[0]?.id ?? 0);
  const [kind, setKind] = useState<TransactionKind>("expense");
  const [amount, setAmount] = useState("");
  const [occurredOn, setOccurredOn] = useState(toDateInput(new Date()));
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  const relevantCategories = categories.filter((category) => category.kind === kind);

  function submit(event: FormEvent): void {
    event.preventDefault();
    const cents = parseAmountToCents(amount);
    if (cents === null) {
      setError("Enter a positive amount.");
      return;
    }
    if (!accountId) {
      setError("Pick an account.");
      return;
    }
    create.mutate(
      {
        account_id: accountId,
        kind,
        amount_cents: cents,
        occurred_on: occurredOn,
        category_id: categoryId === "" ? null : categoryId,
        description: description.trim() || null,
      },
      { onSuccess: onDone, onError: () => setError("Could not save the transaction.") },
    );
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      {error && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
          {error}
        </p>
      )}
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="mb-1 block text-xs text-slate-500">Account</span>
          <select
            className={inputClass}
            value={accountId}
            onChange={(e) => setAccountId(Number(e.target.value))}
          >
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-1 block text-xs text-slate-500">Type</span>
          <select
            className={inputClass}
            value={kind}
            onChange={(e) => {
              setKind(e.target.value as TransactionKind);
              setCategoryId("");
            }}
          >
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
        </label>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="mb-1 block text-xs text-slate-500">Amount</span>
          <input
            className={inputClass}
            placeholder="0.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs text-slate-500">Date</span>
          <input
            type="date"
            className={inputClass}
            value={occurredOn}
            onChange={(e) => setOccurredOn(e.target.value)}
          />
        </label>
      </div>
      <label className="block">
        <span className="mb-1 block text-xs text-slate-500">Category</span>
        <select
          className={inputClass}
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value === "" ? "" : Number(e.target.value))}
        >
          <option value="">Uncategorized</option>
          {relevantCategories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </label>
      <input
        className={inputClass}
        placeholder="Description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <button
        type="submit"
        disabled={create.isPending}
        className="w-full rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
      >
        {create.isPending ? "Saving…" : "Add transaction"}
      </button>
    </form>
  );
}
