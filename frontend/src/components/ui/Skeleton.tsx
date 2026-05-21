interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={`skeleton-shimmer rounded-md bg-slate-100${className ? ` ${className}` : ""}`}
    />
  );
}
