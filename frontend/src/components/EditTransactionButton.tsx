import React from 'react';
import { Edit } from 'lucide-react';

interface EditTransactionButtonProps {
  onClick: () => void;
  className?: string;
  disabled?: boolean;
}

export const EditTransactionButton: React.FC<EditTransactionButtonProps> = ({
  onClick,
  className = '',
  disabled = false
}) => {
  return (
    <button
      onClick={onClick}
      className={`text-blue-600 hover:text-blue-800 ${className}`}
      title="Editar transação"
      disabled={disabled}
    >
      <Edit className="w-4 h-4" />
    </button>
  );
};