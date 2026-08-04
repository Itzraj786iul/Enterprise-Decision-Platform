"use client";

import { useQuery } from "@tanstack/react-query";
import {
  customersApi,
  customersQueryKeys,
  type CustomerQueryParams,
} from "@/services/customers";

const RETRY = 2;
const STALE = 60_000;

export function useCustomerOverview(filters: CustomerQueryParams) {
  return useQuery({
    queryKey: customersQueryKeys.overview(filters),
    queryFn: () => customersApi.overview(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useRfmSegments(filters: CustomerQueryParams) {
  return useQuery({
    queryKey: customersQueryKeys.rfm(filters),
    queryFn: () => customersApi.rfmSegments(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useCustomerCohorts(filters: CustomerQueryParams) {
  return useQuery({
    queryKey: customersQueryKeys.cohorts(filters),
    queryFn: () => customersApi.cohorts(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useCustomerDistribution(filters: CustomerQueryParams) {
  return useQuery({
    queryKey: customersQueryKeys.distribution(filters),
    queryFn: () => customersApi.distribution(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useTopCustomersDetail(
  filters: CustomerQueryParams & { page?: number; pageSize?: number },
) {
  return useQuery({
    queryKey: customersQueryKeys.top(filters),
    queryFn: () => customersApi.topCustomers(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}

export function useChurnRisk(filters: CustomerQueryParams) {
  return useQuery({
    queryKey: customersQueryKeys.churn(filters),
    queryFn: () => customersApi.churnRisk(filters),
    retry: RETRY,
    staleTime: STALE,
  });
}
