"use client";

import { useQuery } from "@tanstack/react-query";
import {
  salesApi,
  salesQueryKeys,
  type SalesQueryParams,
} from "@/services/sales";

const RETRY = 2;
const STALE = 60_000;

export function useSalesOverview(filters: SalesQueryParams) {
  return useQuery({
    queryKey: salesQueryKeys.overview(filters),
    queryFn: () => salesApi.overview(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useSalesTrends(
  grain: "daily" | "weekly" | "monthly",
  filters: SalesQueryParams,
) {
  return useQuery({
    queryKey: salesQueryKeys.trends(grain, filters),
    queryFn: () => salesApi.trends(grain, filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useCategoryPerformance(filters: SalesQueryParams) {
  return useQuery({
    queryKey: salesQueryKeys.category(filters),
    queryFn: () => salesApi.categoryPerformance(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useProductPerformance(
  filters: SalesQueryParams & { page?: number; pageSize?: number },
) {
  return useQuery({
    queryKey: salesQueryKeys.products(filters),
    queryFn: () => salesApi.productPerformance(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useRegionalSales(filters: SalesQueryParams) {
  return useQuery({
    queryKey: salesQueryKeys.regional(filters),
    queryFn: () => salesApi.regionalPerformance(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useTopCustomers(limit = 10, search?: string) {
  return useQuery({
    queryKey: salesQueryKeys.customers(limit, search),
    queryFn: () => salesApi.topCustomers(limit, search),
    retry: RETRY,
    staleTime: STALE,
  });
}
