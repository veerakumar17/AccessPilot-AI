import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({ children, className = '', onClick }) => {
  return (
    <div
      onClick={onClick}
      className={`bg-navy-800 border border-navy-600 rounded-xl p-6 ${onClick ? 'cursor-pointer hover:border-navy-400 transition-all' : ''} ${className}`}
    >
      {children}
    </div>
  );
};

export default Card;