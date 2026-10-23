import { useState, useEffect } from 'react';
import { getPrivacyAlerts } from '../services/api';
import SafetyAlert from '../components/SafetyAlert';
import useAuth from '../hooks/useAuth';
import { riskToLevel } from '../utils/riskUtils';

/**
 * PrivacyAlerts — shows the history of V5 Privacy-Guardian checks
 * (GET /privacy/alerts).  Each alert is rendered with a SafetyAlert
 * strip so the user can quickly see what was flagged and what to do.
 */
export default function PrivacyAlerts() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const isLoading = loading || refreshing;

  const fetchAlerts = async () => {
    if (!refreshing) setLoading(true);
    setError('');
    try {
      const data = await getPrivacyAlerts();
      setAlerts(Array.isArray(data) ? data : []);
    } catch (err) {
      const status = err.response?.status;
      if (status === 401) {
        setError('Please sign in to view privacy alerts.');
      } else if (status === 403) {
        setError('You do not have permission to view privacy alerts.');
      } else if (status >= 500) {
        setError('Privacy check service is unavailable. Try again in a moment.');
      } else {
        setError('Unable to load privacy alerts. Please try again.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAlerts();
  };

  return (
    <div className="min-h-screen bg-[#FFF1F2] pt-20">
      <div className="max-w-4xl mx-auto px-4 pb-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-[#831843]">
              Privacy Alerts
            </h1>
            <p className="text-sm text-[#9F7A89] mt-1">
              {user ? `Signed in as ${user.email}` : 'Signed out'}
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="px-4 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white hover:brightness-110 active:scale-95 transition-all disabled:opacity-60"
          >
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="text-center py-16 text-[#9F7A89]">
            <div className="text-5xl mb-4">🔒</div>
            <p className="text-lg font-medium text-[#831843]">
              {refreshing ? 'Refreshing…' : 'Loading privacy alerts…'}
            </p>
          </div>
        )}

        {/* Error */}
        {!isLoading && error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-sm text-[#DC2626] flex items-start gap-3">
            <span className="text-lg">⚠</span>
            <p>{error}</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && alerts.length === 0 && (
          <div className="text-center py-16 text-[#9F7A89]">
            <div className="text-5xl mb-4">✅</div>
            <h2 className="text-lg font-semibold text-[#831843] mb-2">
              No Privacy Alerts
            </h2>
            <p className="text-sm">
              No privacy concerns have been detected. Your conversations are clean.
            </p>
          </div>
        )}

        {/* Alerts list */}
        {!isLoading && !error && alerts.length > 0 && (
          <div className="space-y-4">
            {alerts.map((alert, idx) => {
              const level = riskToLevel(alert.risk_level);
              const alertId = alert.id || `alert-${idx}`;

              return (
                <div
                  key={alertId}
                  className="bg-white rounded-2xl shadow-lg border border-pink-200 p-4"
                >
                  <SafetyAlert
                    level={level}
                    message={alert.warning || 'Privacy concern detected'}
                    detectedTypes={alert.detected_types}
                    recommendation={alert.recommendation}
                  />

                  {alert.summary && (
                    <p className="text-xs text-[#9F7A89] mt-2 italic">
                      “{alert.summary}”
                    </p>
                  )}

                  {(alert.created_at || alert.timestamp) && (
                    <p className="text-xs text-[#9F7A89] mt-2">
                      {new Date(alert.created_at || alert.timestamp).toLocaleString()}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
