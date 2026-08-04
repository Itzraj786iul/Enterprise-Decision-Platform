"use client";

import { useQuery } from "@tanstack/react-query";
import {
  financeApi,
  financeQueryKeys,
  type FinanceQueryParams,
} from "@/services/finance";

const RETRY = 2;
const STALE = 60_000;

export function useFinanceOverview(filters: FinanceQueryParams) {
  return useQuery({
    queryKey: financeQueryKeys.overview(filters),
    queryFn: () => financeApi.overview(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useProfitability(filters: FinanceQueryParams) {
  return useQuery({
    queryKey: financeQueryKeys.profitability(filters),
    queryFn: () => financeApi.profitability(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useCostBreakdown(filters: FinanceQueryParams) {
  return useQuery({
    queryKey: financeQueryKeys.costs(filters),
    queryFn: () => financeApi.costBreakdown(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useCashflow(filters: FinanceQueryParams) {
  return useQuery({
    queryKey: financeQueryKeys.cashflow(filters),
    queryFn: () => financeApi.cashflow(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useFinancialRisks(filters: FinanceQueryParams) {
  return useQuery({
    queryKey: financeQueryKeys.risks(filters),
    queryFn: () => financeApi.financialRisks(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useBudgetVariance(filters: FinanceQueryParams) {
  return useQuery({
    queryKey: financeQueryKeys.budget(filters),
    queryFn: () => financeApi.budgetVariance(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}
