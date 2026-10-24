import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDashboard, markAllAlertsRead } from '../services/api';
import useAuth from '../hooks/useAuth';
import TrustScoreCard from '../components/TrustScoreCard';
import DashboardSkeleton from '../components/DashboardSkeleton';
import AlertItem from '../components/AlertItem';
import { riskToLevel } from '../utils/riskUtils';

/**
 * Dashboard — V6 safety dashboard.
 * Pulls everything from GET /dashboard (backend-aggregated).
 */
export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [markingRead, setMarkingRead] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const dashboard = await getDashboard();
      setData(dashboard);
    } catch (err) {
      const status = err.response?.status;
      if (status === 401) {
        setError('Please sign in to view your dashboard.');
      } else if (status === 403) {
        setError('You do not have permission to view this dashboard.');
      } else if (status === 404) {
        setError('Dashboard data not found. Please complete your profile first.');
      } else if (status >= 500) {
        setError('Safety dashboard is temporarily unavailable. Please try again in a moment.');
      } else {
        setError('Unable to load the safety dashboard. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleMarkAllRead = async () => {
    setMarkingRead(true);
    try {
      await markAllAlertsRead();
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          recent_alerts: prev.recent_alerts.map((a) => ({ ...a, is_read: true })),
          unread_alerts_count: 0,
        };
      });
    } catch {
      // Silently fail — the alert list page has its own error handling
    } finally {
      setMarkingRead(false);
    }
  };

  if (loading) return <DashboardSkeleton />;

  if (error) {
    return (
      <div className="min-h-screen bg-[#FFF1F2] pt-20">
        <div className="max-w-4xl mx-auto px-4 pb-8">
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
            <span className="text-3xl mb-2 block">⚠</span>
            <h2 className="text-xl font-bold text-[#831843] mb-2">Unable to load dashboard</h2>
            <p className="text-sm text-[#9F7A89] mb-4">{error}</p>
            <button
              onClick={fetchData}
              className="px-6 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white hover:brightness-110 transition-all"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  // ── Destructured dashboard data (GET /dashboard → DashboardResponse) ──
  const ts = data.trust_score || {};
  const trustScore = ts.score ?? 0;
  const trustRiskLevel = riskToLevel(ts.risk_level);
  const trustFactors = ts.factors || [];
  const recentAlerts = data.recent_alerts || [];
  const unreadCount = data.unread_alerts_count || 0;
  const blockedCount = data.blocked_count || 0;
  const reportCount = data.report_count || 0;

  return (
    <div className="min-h-screen bg-[#FFF1F2] pt-20">
      <div className="max-w-4xl mx-auto px-4 pb-8">
        {/* ── Header ── */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-[#831843]">Safety Dashboard</h1>
            <p className="text-sm text-[#9F7A89] mt-1">
              {user ? `Signed in as ${user.email}` : 'Signed out'}
            </p>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              disabled={markingRead}
              className="px-4 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white hover:brightness-110 active:scale-95 transition-all disabled:opacity-60 flex items-center gap-2"
            >
              {markingRead ? (
                <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : null}
              {markingRead ? 'Marking…' : 'Mark All Read'}
            </button>
          )}
        </div>

        {/* ── Trust Score Card ── */}
        <div className="mb-8 flex justify-center">
          <TrustScoreCard
            score={trustScore}
            riskLevel={trustRiskLevel}
            factors={trustFactors}
          />
        </div>

        {/* ── Stat Cards ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard icon="🚨" label="Unread Alerts" value={unreadCount} to="/privacy-alerts" />
          <StatCard icon="🚫" label="Blocked Users" value={blockedCount} to="/discover" />
          <StatCard icon="📝" label="Reports Sent" value={reportCount} to="/privacy-alerts" />
          {ts.last_calculated && (
            <StatCard
              icon="🕒"
              label="Score Updated"
              value={new Date(ts.last_calculated).toLocaleDateString([], { month: 'short', day: 'numeric' })}
              to="/discover"
            />
          )}
        </div>

        {/* ── Recent Alerts ── */}
        <div>
          <h2 className="text-lg font-bold text-[#831843] mb-4">Recent Alerts</h2>
          {recentAlerts.length === 0 ? (
            <div className="bg-white rounded-2xl shadow-md border border-pink-200 p-6 text-center">
              <span className="text-3xl mb-2 block">✅</span>
              <p className="text-sm text-[#9F7A89]">No recent alerts. You're all caught up!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentAlerts.map((alert) => (
                <AlertItem key={alert.id} alert={alert} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * StatCard — a small stat tile that links to a route.
 */
function StatCard({ icon, label, value, subtitle, to }) {
  return (
    <Link
      to={to}
      className="bg-white rounded-2xl shadow-lg border border-pink-200 p-4 text-center hover:shadow-xl hover:-translate-y-0.5 transition-all"
    >
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-2xl font-bold text-[#831843]">{value}</div>
      <div className="text-xs text-[#9F7A89] font-medium">{label}</div>
      {subtitle && <div className="text-xs text-[#9F7A89] mt-0.5">{subtitle}</div>}
    </Link>
  );
}
