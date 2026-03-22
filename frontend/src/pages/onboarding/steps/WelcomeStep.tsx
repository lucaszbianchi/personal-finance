import React from 'react';
import { Wallet } from 'lucide-react';

type Props = { onNext: () => void };

export const WelcomeStep: React.FC<Props> = ({ onNext }) => (
  <div className="text-center">
    <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
      <Wallet size={32} className="text-blue-600" />
    </div>

    <h2 className="text-2xl font-bold text-gray-800 mb-3">
      Bem-vindo ao seu app de financas pessoais
    </h2>

    <p className="text-gray-600 mb-2">
      Vamos configurar tudo para voce em poucos passos:
    </p>

    <ul className="text-left text-gray-600 space-y-2 mb-8 max-w-sm mx-auto">
      <li className="flex items-start gap-2">
        <span className="font-semibold text-blue-600 mt-0.5">1.</span>
        Inserir suas credenciais da Pluggy API
      </li>
      <li className="flex items-start gap-2">
        <span className="font-semibold text-blue-600 mt-0.5">2.</span>
        Conectar sua conta bancaria
      </li>
      <li className="flex items-start gap-2">
        <span className="font-semibold text-blue-600 mt-0.5">3.</span>
        Sincronizar seus dados financeiros
      </li>
    </ul>

    <button
      onClick={onNext}
      className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 transition-colors"
    >
      Comecar
    </button>
  </div>
);
