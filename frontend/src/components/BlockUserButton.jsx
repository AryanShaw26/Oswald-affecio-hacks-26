import { useState } from 'react';
import { blockUser, unblockUser } from '../services/api';

/**
 * BlockUserButton — renders a button (and confirmation modal) for blocking
 * or unblocking a user.  Uses the backend as the source of truth.
 *
 * Props:
 *   targetUserId   number   — the user to block/unblock
 *   initialBlocked boolean  — whether the user is currently blocked
 *   onToggle       (newState: boolean) => void
 *   size           'sm' | 'md'
 *   variant        'card' | 'inline'
 */
const BLOCK_REASONS = [
  'Inappropriate messages',
  'Scam or fraud attempt',
  'Harassment or abuse',
  'Fake profile or spam',
  'Suspicious behavior',
  'Other',
];

export default function BlockUserButton({ targetUserId, initialBlocked = false, onToggle, size = 'md', variant = 'card' }) {
  const [blocked, setBlocked] = useState(initialBlocked);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [reason, setReason] = useState('');

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
  };

  const handleBlock = async () => {
    setError('');
    setLoading(true);
    try {
      await blockUser(targetUserId, reason || null);
      setBlocked(true);
      setShowConfirm(false);
      setReason('');
      if (onToggle) onToggle(true);
    } catch (err) {
      const status = err.response?.status;
      if (status === 401) {
        setError('You need to be signed in to block users.');
      } else if (status === 403) {
        setError('You do not have permission to block this user.');
      } else if (status === 400) {
        setError(err.response?.data?.detail || 'Unable to block this user.');
      } else if (status >= 500) {
        setError('Server unavailable. Please try again in a moment.');
      } else {
        setError('Unable to block this user. Please check your connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  // ─── Unblock handler ────────────────────────────────────────────────
  const handleUnblock = async () => {
    setError('');
    setLoading(true);
    try {
      await unblockUser(targetUserId);
      setBlocked(false);
      if (onToggle) onToggle(false);
    } catch (err) {
      const status = err.response?.status;
      if (status === 401) {
        setError('You need to be signed in to unblock users.');
      } else if (status === 403) {
        setError('You do not have permission to unblock this user.');
      } else if (status === 400) {
        setError(err.response?.data?.detail || 'Unable to unblock this user.');
      } else if (status >= 500) {
        setError('Server unavailable. Please try again in a moment.');
      } else {
        setError('Unable to unblock this user. Please check your connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  const baseBtnClass = `rounded-full font-semibold transition-all flex items-center justify-center gap-2 ${sizeClasses[size]} disabled:opacity-60`;

  const renderButton = () => {
    if (blocked) {
      return (
        <button
          onClick={handleUnblock}
          disabled={loading}
          className={`${baseBtnClass} border border-pink-200 text-[#9F7A89] hover:bg-[#FCE7F3] hover:text-[#BE185D]`}
        >
          {loading ? (
            <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : null}
          {loading ? 'Unblocking…' : 'Unblock User'}
        </button>
      );
    }

    if (variant === 'card') {
      return (
        <button
          onClick={() => setShowConfirm(true)}
          disabled={loading}
          className={`${baseBtnClass} border border-[#BE185D] text-[#BE185D] hover:bg-[#FCE7F3]`}
        >
          {loading ? (
            <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : '🚫'}
          {loading ? 'Blocking…' : 'Block User'}
        </button>
      );
    }

    // Inline variant
    return (
      <button
        onClick={() => setShowConfirm(true)}
        disabled={loading}
        className={`${baseBtnClass} border border-pink-200 text-[#9F7A89] hover:border-[#BE185D] hover:text-[#BE185D] hover:bg-[#FCE7F3]`}
      >
        {loading ? (
          <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : '🚫 Block'}
      </button>
    );
  };

  return (
    <>
      {renderButton()}

      {error && (
        <p role="alert" className="mt-2 text-xs text-[#DC2626] bg-red-50 rounded-lg px-3 py-1.5 border border-red-200">
          {error}
        </p>
      )}

      {/* Confirmation Modal — shown when blocking */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-sm p-6">
            <h3 className="text-lg font-bold text-[#831843] mb-3">Block User?</h3>
            <p className="text-sm text-[#9F7A89] mb-4">
              Are you sure you want to block this user? They will no longer be able to message you
              or appear in your results.
            </p>

            <div className="mb-4">
              <label className="block text-xs font-medium text-[#1F1720] mb-1">
                Reason (optional)
              </label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full border border-pink-200 rounded-xl px-3 py-2 text-sm text-[#1F1720] bg-white focus:outline-none focus:ring-2 focus:ring-[#BE185D] transition"
              >
                <option value="">Select a reason…</option>
                {BLOCK_REASONS.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => { setShowConfirm(false); setReason(''); }}
                className="flex-1 py-2 rounded-full border border-pink-200 text-[#9F7A89] font-semibold hover:bg-pink-50 transition-all"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handleBlock}
                disabled={loading}
                className="flex-1 py-2 rounded-full font-semibold text-white bg-gradient-to-r from-[#BE185D] to-[#E11D48] hover:brightness-110 active:scale-95 transition-all disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : null}
                {loading ? 'Blocking…' : 'Block User'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}