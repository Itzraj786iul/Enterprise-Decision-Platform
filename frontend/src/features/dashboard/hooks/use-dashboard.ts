"use client";

import { useQuery } from "@tanstack/react-query";
import {
  dashboardApi,
  dashboardQueryKeys,
} from "@/services/dashboard";

const RETRY = 2;

export function useDashboardOverview(days = 30) {
  return useQuery({
    queryKey: dashboardQueryKeys.overview(days),
    queryFn: () => dashboardApi.overview(days),
    retry: RETRY,
    staleTime: 60_000,
  });
}

export function useDashboardTrends(days = 90) {
  return useQuery({
    queryKey: dashboardQueryKeys.trends(days),
    queryFn: () => dashboardApi.trends(days),
    retry: RETRY,
    staleTime: 60_000,
  });
}

export function useRegionalPerformance(days = 30) {
  return useQuery({
    queryKey: dashboardQueryKeys.regional(days),
    queryFn: () => dashboardApi.regionalPerformance(days),
    retry: RETRY,
    staleTime: 60_000,
  });
}

export function useTopRisks(limit = 10) {
  return useQuery({
    queryKey: dashboardQueryKeys.risks(limit),
    queryFn: () => dashboardApi.topRisks(limit),
    retry: RETRY,
    staleTime: 60_000,
  });
}

export function useOpportunities(limit = 10) {
  return useQuery({
    queryKey: dashboardQueryKeys.opportunities(limit),
    queryFn: () => dashboardApi.opportunities(limit),
    retry: RETRY,
    staleTime: 60_000,
  });
}
