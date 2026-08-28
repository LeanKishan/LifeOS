import { api } from "@/lib/api";

export type TransactionKind = "income" | "expense";

export interface Account {
  id: number;
  name: string;
  kind: string;
  currency: string;
  starting_balance_cents: number;
  balance_cents: number;
  archived: boolean;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  kind: TransactionKind;
  color: string;
}

export interface Transaction {
  id: number;
  account_id: number;
  category_id: number | null;
  kind: TransactionKind;
  amount_cents: number;
  occurred_on: string;
  description: string | null;
  created_at: string;
}

export interface Budget {
  id: number;
  category_id: number;
  month: string;
  limit_cents: number;
}

export interface CategorySpend {
  category_id: number;
  name: string;
  color: string;
  spent_cents: number;
  budget_cents: number | null;
  over: boolean;
}

export interface FinanceSummary {
  month: string;
  income_cents: number;
  expense_cents: number;
  net_cents: number;
  savings_rate: number;
  uncategorized_cents: number;
  upcoming_bills_cents: number;
  by_category: CategorySpend[];
}

export interface ImportResult {
  imported: number;
  errors: { row: number; message: string }[];
}

export interface TransactionFilters {
  account_id?: number;
  category_id?: number;
  kind?: TransactionKind;
  from?: string;
  to?: string;
  limit?: number;
}

const BASE = "/finance";

export async function listAccounts(): Promise<Account[]> {
  return (await api.get<Account[]>(`${BASE}/accounts`)).data;
}

export async function createAccount(input: {
  name: string;
  kind?: string;
  starting_balance_cents?: number;
}): Promise<Account> {
  return (await api.post<Account>(`${BASE}/accounts`, input)).data;
}

export async function listCategories(): Promise<Category[]> {
  return (await api.get<Category[]>(`${BASE}/categories`)).data;
}

export async function createCategory(input: {
  name: string;
  kind: TransactionKind;
  color?: string;
}): Promise<Category> {
  return (await api.post<Category>(`${BASE}/categories`, input)).data;
}

export async function listTransactions(filters: TransactionFilters = {}): Promise<Transaction[]> {
  return (await api.get<Transaction[]>(`${BASE}/transactions`, { params: filters })).data;
}

export async function createTransaction(input: {
  account_id: number;
  category_id?: number | null;
  kind: TransactionKind;
  amount_cents: number;
  occurred_on: string;
  description?: string | null;
}): Promise<Transaction> {
  return (await api.post<Transaction>(`${BASE}/transactions`, input)).data;
}

export async function deleteTransaction(id: number): Promise<void> {
  await api.delete(`${BASE}/transactions/${id}`);
}

export async function importTransactions(file: File): Promise<ImportResult> {
  const form = new FormData();
  form.append("file", file);
  return (
    await api.post<ImportResult>(`${BASE}/transactions/import`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  ).data;
}

export async function getSummary(month: string): Promise<FinanceSummary> {
  return (await api.get<FinanceSummary>(`${BASE}/summary`, { params: { month } })).data;
}

export async function listBudgets(month: string): Promise<Budget[]> {
  return (await api.get<Budget[]>(`${BASE}/budgets`, { params: { month } })).data;
}

export async function setBudget(input: {
  category_id: number;
  month: string;
  limit_cents: number;
}): Promise<Budget> {
  return (await api.post<Budget>(`${BASE}/budgets`, input)).data;
}
