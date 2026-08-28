import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as fin from "@/features/finance/api";
import type { TransactionFilters } from "@/features/finance/api";

const KEY = ["finance"] as const;

export function useAccounts() {
  return useQuery({ queryKey: [...KEY, "accounts"], queryFn: fin.listAccounts });
}

export function useCategories() {
  return useQuery({ queryKey: [...KEY, "categories"], queryFn: fin.listCategories });
}

export function useTransactions(filters: TransactionFilters) {
  return useQuery({
    queryKey: [...KEY, "transactions", filters],
    queryFn: () => fin.listTransactions(filters),
  });
}

export function useSummary(month: string) {
  return useQuery({
    queryKey: [...KEY, "summary", month],
    queryFn: () => fin.getSummary(month),
    enabled: Boolean(month),
  });
}

export function useBudgets(month: string) {
  return useQuery({
    queryKey: [...KEY, "budgets", month],
    queryFn: () => fin.listBudgets(month),
    enabled: Boolean(month),
  });
}

function useInvalidate() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: KEY });
}

export function useFinanceMutation<TArgs, TResult>(fn: (args: TArgs) => Promise<TResult>) {
  const invalidate = useInvalidate();
  return useMutation({ mutationFn: fn, onSuccess: invalidate });
}
