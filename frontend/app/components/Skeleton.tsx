'use client';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'card';
  width?: string | number;
  height?: string | number;
  count?: number;
}

export default function Skeleton({
  className = '',
  variant = 'text',
  width,
  height,
  count = 1,
}: SkeletonProps) {
  const baseClasses = 'animate-pulse bg-gray-700';

  const variantClasses = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
    card: 'rounded-xl',
  };

  const style: React.CSSProperties = {
    width: width ?? (variant === 'text' ? '100%' : undefined),
    height: height ?? (variant === 'text' ? '1em' : variant === 'circular' ? '40px' : '20px'),
  };

  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <>
      {items.map(i => (
        <div
          key={i}
          className={`${baseClasses} ${variantClasses[variant]} ${className}`}
          style={style}
          aria-hidden="true"
        />
      ))}
    </>
  );
}

// Convenience components for common loading states
export function GameCardSkeleton() {
  return (
    <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-5">
      <div className="flex justify-between items-center">
        <div className="flex-1">
          <Skeleton variant="text" width={200} height={24} className="mb-2" />
          <Skeleton variant="text" width={150} height={16} className="mb-2" />
          <div className="flex-4">
            gap <Skeleton variant="text" width={60} height={14} />
            <Skeleton variant="text" width={80} height={14} />
            <Skeleton variant="text" width={60} height={14} />
            <Skeleton variant="text" width={50} height={14} />
          </div>
        </div>
        <Skeleton variant="circular" width={24} height={24} />
      </div>
    </div>
  );
}

export function ScenarioCardSkeleton() {
  return (
    <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-6">
      <div className="flex justify-between items-start mb-3">
        <Skeleton variant="text" width={150} height={24} />
        <Skeleton variant="rectangular" width={50} height={22} />
      </div>
      <Skeleton variant="text" width="100%" height={16} className="mb-2" />
      <Skeleton variant="text" width="80%" height={16} className="mb-4" />
      <Skeleton variant="text" width={100} height={12} />
    </div>
  );
}

export function GameDetailSkeleton() {
  return (
    <div className="min-h-screen bg-gray-900">
      <div className="bg-gray-800/90 border-b border-gray-700/50 px-6 py-4">
        <Skeleton variant="text" width={250} height={32} />
      </div>
      <div className="p-6">
        <div className="bg-gray-800/80 border border-gray-700/50 rounded-xl p-4 mb-6">
          <Skeleton variant="text" width={150} height={20} className="mb-3" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Skeleton variant="text" width={80} height={16} />
            <Skeleton variant="text" width={100} height={16} />
            <Skeleton variant="text" width={70} height={16} />
            <Skeleton variant="text" width={90} height={16} />
          </div>
        </div>
        <Skeleton variant="rectangular" width="100%" height={400} className="mb-6" />
        <Skeleton variant="rectangular" width="100%" height={200} />
      </div>
    </div>
  );
}
