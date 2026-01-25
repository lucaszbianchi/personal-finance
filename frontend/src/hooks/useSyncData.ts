import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importService, type SyncResponse } from '@/services/api';

export const useSyncData = () => {
  const queryClient = useQueryClient();

  return useMutation<SyncResponse, Error>({
    mutationFn: importService.syncData,
    onSuccess: () => {
      // Invalida queries para refetch automático
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['investments'] });
      
      // Salva timestamp da última sincronização
      localStorage.setItem('lastSyncTime', new Date().toISOString());
    },
    onError: (error) => {
      console.error('Erro ao sincronizar dados:', error);
    },
  });
};
