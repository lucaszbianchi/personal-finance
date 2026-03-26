import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importService, type SyncResponse, type ImportType } from '@/services/api';

export type SyncParams = { importType: ImportType; itemId?: string };

export const useSyncData = () => {
  const queryClient = useQueryClient();

  return useMutation<SyncResponse, Error, SyncParams>({
    mutationFn: ({ importType, itemId }) => importService.syncData(importType, itemId),
    onSuccess: () => {
      // Invalida queries para refetch automático
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['investments'] });
      queryClient.invalidateQueries({ queryKey: ['rate-limit-usage'] });

      // Salva timestamp da última sincronização
      localStorage.setItem('lastSyncTime', new Date().toISOString());
    },
    onError: (error) => {
      console.error('Erro ao sincronizar dados:', error);
    },
  });
};
