"use client";

import { useQuery } from "@tanstack/react-query";
import {
  operationsApi,
  operationsQueryKeys,
  type OperationsQueryParams,
} from "@/services/operations";

const RETRY = 2;
const STALE = 60_000;

export function useOperationsOverview(filters: OperationsQueryParams) {
  return useQuery({
    queryKey: operationsQueryKeys.overview(filters),
    queryFn: () => operationsApi.overview(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useOperationsInventory(
  filters: OperationsQueryParams & { page?: number; pageSize?: number },
) {
  return useQuery({
    queryKey: operationsQueryKeys.inventory(filters),
    queryFn: () => operationsApi.inventory(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useSupplierPerformance(filters: OperationsQueryParams) {
  return useQuery({
    queryKey: operationsQueryKeys.suppliers(filters),
    queryFn: () => operationsApi.supplierPerformance(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useOperationsReturns(filters: OperationsQueryParams) {
  return useQuery({
    queryKey: operationsQueryKeys.returns(filters),
    queryFn: () => operationsApi.returns(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useWarehousePerformance(filters: OperationsQueryParams) {
  return useQuery({
    queryKey: operationsQueryKeys.warehouse(filters),
    queryFn: () => operationsApi.warehousePerformance(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useOperationalRisks(filters: OperationsQueryParams) {
  return useQuery({
    queryKey: operationsQueryKeys.risks(filters),
    queryFn: () => operationsApi.operationalRisks(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}
