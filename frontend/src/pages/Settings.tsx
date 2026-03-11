import React, { useEffect, useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query'
import { Trash2 } from 'lucide-react'
import api, { databaseService } from '@/services/api'
import { PluggyConnectButton } from '@/components/PluggyConnectButton'
import { useCategoryLanguage } from '@/contexts/CategoryLanguageContext'

type PluggyItem = {
  item_id: string
  connector_name: string | null
  status: string | null
  created_at: string
}

type ItemStatus = 'UPDATED' | 'UPDATING' | 'LOGIN_ERROR' | 'OUTDATED' | 'WAITING_USER_INPUT'

type LiveItem = {
  id: string
  status: ItemStatus
  connector: { name: string; imageUrl?: string }
  lastUpdatedAt?: string
}

const STATUS_BADGE: Record<ItemStatus, { label: string; className: string }> = {
  UPDATED:             { label: 'Atualizado',       className: 'bg-green-100 text-green-800' },
  UPDATING:            { label: 'Atualizando...',   className: 'bg-blue-100 text-blue-800' },
  LOGIN_ERROR:         { label: 'Erro de login',    className: 'bg-red-100 text-red-800' },
  OUTDATED:            { label: 'Desatualizado',    className: 'bg-orange-100 text-orange-800' },
  WAITING_USER_INPUT:  { label: 'Aguardando ação',  className: 'bg-yellow-100 text-yellow-800' },
}

function formatRelativeDate(isoString?: string): string {
  if (!isoString) return ''
  return formatDistanceToNow(new Date(isoString), { addSuffix: true, locale: ptBR })
}

type MealAllowanceSettings = {
  active: boolean
  value: number
}

type CreditCardSettings = {
  closing_day: number
  due_day: number
}

export const Settings: React.FC = () => {
  const queryClient = useQueryClient()
  const { categoryLanguage, setCategoryLanguage } = useCategoryLanguage()

  const [updateModalOpen, setUpdateModalOpen] = useState(false)
  const [resetModalOpen, setResetModalOpen] = useState(false)
  const [resetLoading, setResetLoading] = useState(false)
  const [resetMessage, setResetMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  async function handleConfirmReset() {
    setResetLoading(true)
    setResetMessage(null)
    try {
      await databaseService.reset()
      setResetMessage({ type: 'success', text: 'Banco de dados resetado com sucesso.' })
      queryClient.invalidateQueries()
    } catch {
      setResetMessage({ type: 'error', text: 'Erro ao resetar o banco de dados.' })
    } finally {
      setResetLoading(false)
      setResetModalOpen(false)
    }
  }

  // --- Pluggy items (lista local) ---
  const { data: items = [], isLoading: itemsLoading } = useQuery({
    queryKey: ['pluggy-items'],
    queryFn: () => api.get<PluggyItem[]>('/pluggy/items').then(r => r.data),
  })

  // Status ao vivo de cada item (chamadas paralelas à Pluggy API)
  const liveQueries = useQueries({
    queries: items.map(item => ({
      queryKey: ['pluggy-item-live', item.item_id],
      queryFn: () => api.get<LiveItem>(`/pluggy/items/${item.item_id}`).then(r => r.data),
      retry: false,
    })),
  })

  const liveByItemId = Object.fromEntries(
    items.map((item, i) => [item.item_id, liveQueries[i]?.data])
  )

  const addItem = useMutation({
    mutationFn: (payload: { item_id: string; connector_name?: string }) =>
      api.post('/pluggy/items', payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pluggy-items'] }),
  })

  const deleteItem = useMutation({
    mutationFn: (itemId: string) => api.delete(`/pluggy/items/${itemId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pluggy-items'] }),
  })

  // --- Meal allowance ---
  const { data: mealData } = useQuery({
    queryKey: ['settings-meal-allowance'],
    queryFn: () => api.get<MealAllowanceSettings>('/settings/meal-allowance').then(r => r.data),
  })

  const [mealActive, setMealActive] = useState(false)
  const [mealValue, setMealValue] = useState('')

  useEffect(() => {
    if (mealData) {
      setMealActive(mealData.active)
      setMealValue(String(mealData.value))
    }
  }, [mealData])

  const saveMeal = useMutation({
    mutationFn: () =>
      api.post('/settings/meal-allowance', { active: mealActive, value: parseFloat(mealValue) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings-meal-allowance'] }),
  })

  // --- Credit card ---
  const { data: creditData } = useQuery({
    queryKey: ['settings-credit-card'],
    queryFn: () => api.get<CreditCardSettings>('/settings/credit-card').then(r => r.data),
  })

  const [closingDay, setClosingDay] = useState('')
  const [dueDay, setDueDay] = useState('')

  useEffect(() => {
    if (creditData) {
      setClosingDay(String(creditData.closing_day))
      setDueDay(String(creditData.due_day))
    }
  }, [creditData])

  const saveCredit = useMutation({
    mutationFn: () =>
      api.post('/settings/credit-card', {
        closing_day: parseInt(closingDay),
        due_day: parseInt(dueDay),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings-credit-card'] }),
  })

  return (
    <div className="max-w-2xl mx-auto py-10 px-4 space-y-10">
      <h1 className="text-3xl font-bold text-gray-800">Configurações</h1>

      {/* Contas Bancárias */}
      <section className="bg-white rounded-lg shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Contas Bancárias Conectadas</h2>

        {itemsLoading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-gray-500">Nenhuma conta conectada.</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {items.map(item => {
              const live = liveByItemId[item.item_id]
              const status = live?.status
              const badge = status ? STATUS_BADGE[status] : null
              const connectorName = live?.connector?.name ?? item.connector_name ?? 'Conta desconhecida'

              return (
                <li key={item.item_id} className="flex items-center justify-between py-3 gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-gray-800">{connectorName}</p>
                      {badge && (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.className}`}>
                          {badge.label}
                        </span>
                      )}
                    </div>
                    {live?.lastUpdatedAt && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        Última atualização: {formatRelativeDate(live.lastUpdatedAt)}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => deleteItem.mutate(item.item_id)}
                    disabled={deleteItem.isPending}
                    className="text-red-500 hover:text-red-700 disabled:opacity-50 flex-shrink-0"
                    title="Remover conta"
                  >
                    <Trash2 size={16} />
                  </button>
                </li>
              )
            })}
          </ul>
        )}

        <div className="flex items-center gap-3 flex-wrap">
          <PluggyConnectButton
            onSuccess={item => {
              addItem.mutate({
                item_id: item.id,
                connector_name: item.connector?.name,
              })
            }}
          />
          <button
            onClick={() => setUpdateModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-md border border-blue-600 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50"
          >
            Atualizar conexões
          </button>
        </div>
      </section>

      {/* Modal: Atualizar conexões */}
      {updateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4 space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Atualizar conexões bancárias</h3>
            <p className="text-sm text-gray-600">
              Algumas situações exigem que você atualize manualmente a conexão com sua instituição:
            </p>
            <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
              <li>Credenciais expiradas ou alteradas (erro de login)</li>
              <li>Instituição que exige autenticação extra (MFA)</li>
              <li>Conexão desatualizada há muito tempo</li>
            </ul>
            <p className="text-sm text-gray-600">
              Acesse o portal da Pluggy para reconectar suas contas:
            </p>
            <a
              href="https://meu.pluggy.ai/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Acessar meu.pluggy.ai ↗
            </a>
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setUpdateModalOpen(false)}
                className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Vale Refeição */}
      <section className="bg-white rounded-lg shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Vale Refeição</h2>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={mealActive}
              onChange={e => setMealActive(e.target.checked)}
              className="w-4 h-4 accent-blue-600"
            />
            Ativo
          </label>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-700 w-24">Valor (R$)</label>
          <input
            type="number"
            value={mealValue}
            onChange={e => setMealValue(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={() => saveMeal.mutate()}
          disabled={saveMeal.isPending}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saveMeal.isPending ? 'Salvando...' : 'Salvar'}
        </button>
        {saveMeal.isSuccess && (
          <p className="text-sm text-green-600">Configuração salva!</p>
        )}
      </section>

      {/* Exibição de Categorias */}
      <section className="bg-white rounded-lg shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Exibição de Categorias</h2>
        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="radio"
              name="categoryLanguage"
              value="en"
              checked={categoryLanguage === 'en'}
              onChange={() => setCategoryLanguage('en')}
              className="w-4 h-4 accent-blue-600"
            />
            Inglês (original)
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="radio"
              name="categoryLanguage"
              value="pt"
              checked={categoryLanguage === 'pt'}
              onChange={() => setCategoryLanguage('pt')}
              className="w-4 h-4 accent-blue-600"
            />
            Português (traduzido)
          </label>
        </div>
        <p className="text-xs text-gray-500">
          Altera o idioma exibido para os nomes de categorias em toda a aplicação.
        </p>
      </section>

      {/* Cartão de Crédito */}
      <section className="bg-white rounded-lg shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Cartão de Crédito</h2>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-700 w-32">Dia de fechamento</label>
          <input
            type="number"
            min={1}
            max={31}
            value={closingDay}
            onChange={e => setClosingDay(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm w-20 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-700 w-32">Dia de vencimento</label>
          <input
            type="number"
            min={1}
            max={31}
            value={dueDay}
            onChange={e => setDueDay(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm w-20 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={() => saveCredit.mutate()}
          disabled={saveCredit.isPending}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saveCredit.isPending ? 'Salvando...' : 'Salvar'}
        </button>
        {saveCredit.isSuccess && (
          <p className="text-sm text-green-600">Configuração salva!</p>
        )}
      </section>

      {/* Zona de Perigo */}
      <section className="bg-white rounded-lg shadow p-6 space-y-4 border border-red-200">
        <h2 className="text-lg font-semibold text-red-700">Zona de Perigo</h2>
        <hr className="border-red-200" />
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-gray-800">Resetar banco de dados</p>
            <p className="text-xs text-gray-500 mt-1">
              Apaga todos os dados e recria as tabelas do zero. Use o import histórico após o reset para repopular.
            </p>
          </div>
          <button
            onClick={() => { setResetMessage(null); setResetModalOpen(true) }}
            className="flex-shrink-0 rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Resetar
          </button>
        </div>
        {resetMessage && (
          <p className={`text-sm ${resetMessage.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
            {resetMessage.text}
          </p>
        )}
      </section>

      {/* Modal de confirmação de reset */}
      {resetModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4 space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">⚠ Confirmar reset</h3>
            <p className="text-sm text-gray-600">
              Esta ação é <strong>irreversível</strong>. Todos os dados serão apagados e as tabelas recriadas vazias.
              Você precisará rodar o import histórico manualmente para repopular.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setResetModalOpen(false)}
                disabled={resetLoading}
                className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirmReset}
                disabled={resetLoading}
                className="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {resetLoading ? 'Resetando...' : 'Confirmar Reset'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Settings
