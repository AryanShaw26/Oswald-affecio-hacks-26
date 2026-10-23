/**
 * SafetyAlert -- colored alert strip matching the 3 trust states.
 *
 * Accepts an optional `detectedTypes` array (from V5 privacy checker) and
 * an optional `recommendation` string to display as actionable guidance.
 */
export default function SafetyAlert({ level = 'safe', message, action, detectedTypes, recommendation }) {
  const styles = {
    safe: {
      bg: 'bg-green-50 border-green-200',
      icon: '✓',
      iconColor: 'text-[#16A34A]',
      text: 'text-green-800',
    },
    caution: {
      bg: 'bg-amber-50 border-amber-200',
      icon: '!',
      iconColor: 'text-[#D97706]',
      text: 'text-amber-800',
    },
    risk: {
      bg: 'bg-red-50 border-red-200',
      icon: '⚠',
      iconColor: 'text-[#DC2626]',
      text: 'text-red-800',
    },
  };
  const s = styles[level] || styles.safe;

  return (
    <div
      role="alert"
      className={`flex items-start gap-3 border rounded-xl px-4 py-3 ${s.bg}`}
    >
      <span className={`text-lg font-bold leading-none mt-0.5 ${s.iconColor}`} aria-hidden="true">
        {s.icon}
      </span>
      <div className="flex-1">
        <p className={`text-sm font-medium ${s.text}`}>{message}</p>

        {detectedTypes && detectedTypes.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {detectedTypes.map((type) => (
              <span
                key={type}
                className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                  level === 'risk'
                    ? 'bg-red-100 text-red-700'
                    : level === 'caution'
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-green-100 text-green-700'
                }`}
              >
                {type}
              </span>
            ))}
          </div>
        )}

        {recommendation && (
          <p className={`text-xs mt-1.5 ${s.text} opacity-80`}>💡 {recommendation}</p>
        )}

        {action && (
          <button className={`text-xs mt-1 underline font-semibold ${s.text}`}>{action}</button>
        )}
      </div>
    </div>
  );
}
