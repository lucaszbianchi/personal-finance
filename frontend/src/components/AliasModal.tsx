import React from 'react';

interface AliasModalProps {
  alias: string;
  onChange: (value: string) => void;
  onSave: (alias: string) => void;
}

export const AliasModal: React.FC<AliasModalProps> = ({ alias, onChange, onSave }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4 space-y-4">
      <h3 className="text-lg font-semibold text-gray-800">Conta conectada!</h3>
      <p className="text-sm text-gray-600">
        Como você quer chamar essa conexão? Um nome facilita identificar de qual conta são as transações.
      </p>
      <input
        className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
        placeholder="Ex: Conta Corrente, Cartão Nubank..."
        value={alias}
        onChange={e => onChange(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') onSave(alias); }}
        autoFocus
      />
      <div className="flex justify-end gap-3 pt-1">
        <button
          onClick={() => onSave('')}
          className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Pular
        </button>
        <button
          onClick={() => onSave(alias)}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Salvar
        </button>
      </div>
    </div>
  </div>
);
