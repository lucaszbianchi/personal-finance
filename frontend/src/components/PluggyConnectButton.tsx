import { useState } from 'react'
import { PluggyConnect } from 'react-pluggy-connect'
import api from '@/services/api'

type Item = {
  id: string
  connector?: { name?: string; imageUrl?: string }
  [key: string]: unknown
}

type Props = {
  onSuccess: (item: Item) => void
  disabled?: boolean
}

export function PluggyConnectButton({ onSuccess, disabled = false }: Props) {
  const [connectToken, setConnectToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleOpen() {
    setError(null)
    setLoading(true)
    try {
      const response = await api.post<{ accessToken: string }>('/pluggy/connect-token')
      setConnectToken(response.data.accessToken)
    } catch {
      setError('Não foi possível iniciar a conexão. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  function handleSuccess(data: { item: Item }) {
    setConnectToken(null)
    onSuccess(data.item)
  }

  function handleClose() {
    setConnectToken(null)
  }

  return (
    <>
      <button
        onClick={handleOpen}
        disabled={disabled || loading}
        className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? 'Aguardando...' : 'Conectar conta bancária'}
      </button>

      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}

      {connectToken && (
        <PluggyConnect
          connectToken={connectToken}
          includeSandbox={false}
          onSuccess={handleSuccess}
          onClose={handleClose}
          onError={({ message }) => {
            setConnectToken(null)
            setError(`Erro na conexão: ${message}`)
          }}
        />
      )}
    </>
  )
}
