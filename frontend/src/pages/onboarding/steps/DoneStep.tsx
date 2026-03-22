import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';

export const DoneStep: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="text-center">
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
        <CheckCircle size={32} className="text-green-600" />
      </div>

      <h2 className="text-2xl font-bold text-gray-800 mb-3">Tudo pronto!</h2>

      <p className="text-gray-600 mb-8">
        Seus dados financeiros foram importados com sucesso. Agora voce pode
        acompanhar suas financas pelo dashboard.
      </p>

      <button
        onClick={() => navigate('/')}
        className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700 transition-colors"
      >
        Ir para o Dashboard
      </button>
    </div>
  );
};
