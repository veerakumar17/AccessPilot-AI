import React from 'react';

interface SkeletonProps {
  className?: string;
  count?: number;
}

const Skeleton: React.FC<SkeletonProps> = ({ className = 'h-4 w-full', count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`bg-navy-700/50 rounded animate-pulse ${className} ${i < count - 1 ? 'mb-3' : ''}`}
        />
      ))}
    </>
  );
};

export const CardSkeleton: React.FC = () => (
  <div className="bg-navy-800 border border-navy-600 rounded-xl p-6">
    <Skeleton className="h-3 w-24 mb-4" />
    <Skeleton className="h-8 w-16 mb-2" />
    <Skeleton className="h-3 w-32" />
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="space-y-3">
    <div className="flex gap-4 pb-3 border-b border-navy-600">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-24" />
      ))}
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex gap-4 py-2">
        {Array.from({ length: 4 }).map((_, j) => (
          <Skeleton key={j} className="h-4 w-24" />
        ))}
      </div>
    ))}
  </div>
);

export default Skeleton;