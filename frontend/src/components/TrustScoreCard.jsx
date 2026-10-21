/**
 * TrustScoreCard -- displays a circular 0-100 trust score ring
 * with risk-level label and factor summary.
 */
export default function TrustScoreCard({ score = 0, riskLevel = 'safe', factors = [] }) {
  const colorMap = {
    safe: '#16A34A',
    caution: '#D97706',
    risk: '#DC2626',
  };
  const labelMap = {
    safe: '✓  Verified -- Low Risk',
    caution: '!  One or More Signals',
    risk: '⚠  High Risk Detected',
  };
  const ringColor = colorMap[riskLevel] || colorMap.safe;
  const circumference = 2 * Math.PI * 40; // r=40
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="bg-white rounded-2xl shadow-md p-6 flex flex-col items-center gap-4 w-full max-w-xs">
      {/* Circular score ring */}
      <div className="relative w-28 h-28">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#FCE7F3" strokeWidth="10" />
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke={ringColor}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-700"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-3xl font-bold text-neutral-charcoal">{score}</span>
        </div>
      </div>

      <p className="text-sm font-medium" style={{ color: ringColor }}>
        {labelMap[riskLevel]}
      </p>

      {factors.length > 0 && (
        <ul className="w-full space-y-1">
          {factors.map((f, i) => (
            <li key={i} className="text-xs text-neutral-muted flex items-start gap-1">
              <span>•</span> {f}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
