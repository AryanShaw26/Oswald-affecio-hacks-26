/**
 * SafetyAlert -- colored alert strip matching the 3 trust states.
 */
export default function SafetyAlert({ level = 'safe', message, action }) {
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
        {action && (
          <button className={`text-xs mt-1 underline font-semibold ${s.text}`}>{action}</button>
        )}
      </div>
    </div>
  );
}
