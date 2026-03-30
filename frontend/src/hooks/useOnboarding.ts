import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { onboardingService, type OnboardingStatus, type FullSyncResponse } from '@/services/api';

export function useOnboardingStatus() {
  return useQuery<OnboardingStatus>({
    queryKey: ['onboarding', 'status'],
    queryFn: () => onboardingService.getStatus(),
    staleTime: 0,
    retry: 1,
  });
}

export function useSaveCredentials() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      client_id: string;
      client_secret: string;
    }) => onboardingService.saveCredentials(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'status'] });
    },
  });
}

export function useFullSync() {
  const queryClient = useQueryClient();

  return useMutation<FullSyncResponse, Error>({
    mutationFn: () => onboardingService.fullSync(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'status'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['investments'] });
      localStorage.setItem('lastSyncTime', new Date().toISOString());
    },
  });
}

export function useRestartOnboarding() {
  const queryClient = useQueryClient();

  return useMutation<OnboardingStatus, Error>({
    mutationFn: () => onboardingService.restart(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'status'] });
    },
  });
}
