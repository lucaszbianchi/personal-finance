import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { automationService } from '@/services/api';
import type { AutomationRule, CreateAutomationRuleRequest } from '@/types';

export const useAutomations = () => {
  return useQuery<AutomationRule[]>({
    queryKey: ['automations'],
    queryFn: async () => {
      const res = await automationService.getAll();
      return res.data;
    },
  });
};

export const useCreateAutomation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateAutomationRuleRequest) =>
      automationService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] });
    },
  });
};

export const useUpdateAutomation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateAutomationRuleRequest> }) =>
      automationService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] });
    },
  });
};

export const useDeleteAutomation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => automationService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] });
    },
  });
};

export const useToggleAutomation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      automationService.toggle(id, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] });
    },
  });
};

export const usePreviewAutomation = () => {
  return useMutation({
    mutationFn: async (conditions: Parameters<typeof automationService.preview>[0]) => {
      const res = await automationService.preview(conditions);
      return res.data;
    },
  });
};

export const useApplyAutomation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const res = await automationService.apply(id);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};
