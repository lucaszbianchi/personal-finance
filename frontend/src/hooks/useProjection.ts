import { useQuery } from '@tanstack/react-query';
import { projectionService } from '@/services/api';
import type { ProjectionData, ProjectionAssumptions } from '@/types';

export function useProjection(months = 12) {
  return useQuery<ProjectionData>({
    queryKey: ['projection', months],
    queryFn: () => projectionService.getProjection(months).then(r => r.data),
    staleTime: 1000 * 60 * 5,
  });
}

export function useProjectionAssumptions() {
  return useQuery<ProjectionAssumptions>({
    queryKey: ['projection', 'assumptions'],
    queryFn: () => projectionService.getAssumptions().then(r => r.data),
    staleTime: 1000 * 60 * 5,
  });
}
