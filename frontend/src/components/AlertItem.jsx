import { riskToLevel } from '../utils/riskUtils';

/**
 * AlertItem — renders a single safety alert in the alerts list.
 *
 * Props:
 *   alert   object — { id, alert_type, severity, message, is_read, created_at, related_report_id, related_block_id }
 *   onMarkRead (alertId) => void
 */

const SEVERITY_COLORS = {
  low: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  high: 'bg-red-100 text-red-800 border-red-200',
};
/*Now next is ALERT_TYPE_LABELS which is a mapping of alert types to their corresponding labels. This will be used to display a user-friendly label for each alert type in the UI.*/

const ALERT_TYPE_LABELS = {
  report_created: 'Report Submitted',
  block_applied: 'User Blocked',
  high_risk_conversation: 'High-Risk Conversation',
  privacy_breach: 'Privacy Breach',
  system_notification: 'System Notification',
};

export default function AlertItem({ alert, onMarkRead }) {
  const severityClass = SEVERITY_COLORS[alert.severity] || SEVERITY_COLORS.medium;
  const typeLabel = ALERT_TYPE_LABELS[alert.alert_type] || alert.alert_type.replace('_', ' ');
  const riskLevel = alert.severity === 'high' ? 'risk' : alert.severity === 'medium' ? 'caution' : 'safe';

  const formattedTime = alert.created_at
    ? new Date(alert.created_at).toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  return (
    <div
      className={`rounded-2xl p-4 border transition-all ${
        alert.is_read
          ? 'bg-white border-pink-200'
          : alert.severity === 'high'
            ? 'bg-red-50 border-red-300'
            : alert.severity === 'medium'
              ? 'bg-amber-50 border-amber-300'
              : 'bg-pink-50 border-pink-300'
      }`}
    >
      <div className="flex items-start gap-3">
        <span
          className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border-2 ${severityClass}`}
          aria-label={alert.severity}
        >
          {alert.severity === 'high' ? '⚠' : alert.severity === 'medium' ? '!' : '✓'}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-baseline justify-between gap-2">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${severityClass}`}>
              {typeLabel}
            </span>
            {!alert.is_read && onMarkRead && (
              <button
                onClick={() => onMarkRead(alert.id)}
                className="text-xs text-[#9F7A89] hover:text-[#BE185D] underline font-medium"
                title="Mark as read"
              >
                Mark as read
              </button>
            )}
          </div>

          <p className={`mt-1 text-sm text-[#1F1720] ${!alert.is_read ? 'font-medium' : ''}`}>
            {alert.message}
          </p>

          {alert.related_report_id && (
            <p className="mt-1 text-xs text-[#9F7A89]">
              Related report: #{alert.related_report_id}
            </p>
          )}

          {alert.related_block_id && (
            <p className="mt-1 text-xs text-[#9F7A89]">
              Related block: #{alert.related_block_id}
            </p>
          )}

          {formattedTime && (
            <p className="mt-2 text-xs text-[#9F7A89]">
              {formattedTime}
            </p>
          )}
        </div>

        {!alert.is_read && (
          <div className="flex-shrink-0">
            <span className="w-2 h-2 rounded-full bg-[#E11D48]" title="Unread" />
          </div>
        )}
      </div>
    </div>
  );
}
