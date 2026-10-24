/**
 * DashboardSkeleton — loading placeholders for the dashboard.
 * Reuses the TrustMatch pink/wine color scheme.
 */
export default function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="animate-pulse flex items-center gap-4 mb-6">
        <div className="w-12 h-12 rounded-full bg-pink-200" />
        <div>
          <div className="h-7 w-48 bg-pink-200 rounded mb-1" />
          <div className="h-5 w-64 bg-pink-200 rounded" />
        </div>
      </div>

      {/* Trust Score card */}
      <div className="bg-white rounded-2xl shadow-md p-6 animate-pulse">
        <div className="h-4 w-32 bg-pink-200 rounded mb-4" />
        <div className="w-28 h-28 rounded-full bg-pink-200 mx-auto" />
      </div>

      {/* Stat cards grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-2xl shadow-md p-4 animate-pulse">
            <div className="h-4 w-20 bg-pink-200 rounded mb-2" />
            <div className="h-8 w-full bg-pink-200 rounded" />
          </div>
        ))}
      </div>

      {/* Section skeletons */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white rounded-2xl shadow-md p-6 animate-pulse">
          <div className="h-5 w-40 bg-pink-200 rounded mb-4" />
          <div className="h-4 w-full bg-pink-200 rounded mb-2" />
          <div className="h-4 w-full bg-pink-200 rounded mb-2" />
          <div className="h-4 w-3/4 bg-pink-200 rounded" />
        </div>
      ))}
    </div>
  );
}
