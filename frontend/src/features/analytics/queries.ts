import { useQuery } from "@tanstack/react-query";

import { getOverview } from "@/features/analytics/api";

export function useOverview(from: string, to: string) {
  return useQuery({
    queryKey: ["analytics", "overview", from, to],
    queryFn: () => getOverview(from, to),
    enabled: Boolean(from && to),
  });
}
