import { useState, useEffect } from 'react';
import { createReport } from '../services/api';

/**
 * ReportUserModal — modal dialog for reporting another user.
 *
 * Props:
 *   userId     number  — target user ID to report (required)
 *   isOpen     boolean
 *   onClose    () => void
 *   onReport   (report) => void   — called on successful submission
 */
const REPORT_REASONS = [
  { value: 'scam', label: 'Scam / Fraud' },
  { value: 'harassment', label: 'Harassment' },
  { value: 'fake_profile', label: 'Fake Profile' },
  { value: 'spam', label: 'Suspicious Behavior' },
  { value: 'inappropriate_content', label: 'Inappropriate Content' },
  { value: 'other', label: 'Other' },
];

export default function ReportUserModal({ userId, isOpen, onClose, onReport }) {
  const [selectedReason, setSelectedReason] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const resetForm = () => {
    setSelectedReason('');
    setDescription('');
    setError('');
    setSuccess(false);
  };

  // ─── Submit handler ──────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const result = await createReport(userId, selectedReason, description);
      setSuccess(true);
      if (onReport) onReport(result);
    } catch (err) {
      const status = err.response?.status;
      if (status === 401) {
        setError('You need to be signed in to report users.');
      } else if (status === 403) {
        setError('You do not have permission to report this user.');
      } else if (status === 400) {
        setError(err.response?.data?.detail || 'Unable to submit report. Please check your input.');
      } else if (status >= 500) {
        setError('Server unavailable. Please try again in a moment.');
      } else {
        setError('Unable to submit report. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md p-6">
        <h2 className="text-xl font-bold text-[#831843] mb-4">Report User</h2>

        {success ? (
          <div className="flex flex-col items-center gap-3 py-6">
            <span className="text-4xl">✅</span>
            <p className="text-sm font-medium text-[#16A34A] text-center">
              Your report has been submitted and is pending review.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Reason selector */}
            <div>
              <label className="block text-sm font-medium text-[#1F1720] mb-2">
                Report reason
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {REPORT_REASONS.map((reason) => (
                  <label
                    key={reason.value}
                    className={`flex items-center gap-2 p-2 rounded-xl border text-sm cursor-pointer transition-all ${
                      selectedReason === reason.value
                        ? 'border-[#BE185D] bg-[#FCE7F3] text-[#831843]'
                        : 'border-pink-200 text-[#9F7A89] hover:border-[#BE185D] hover:bg-pink-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="reason"
                      value={reason.value}
                      checked={selectedReason === reason.value}
                      onChange={(e) => setSelectedReason(e.target.value)}
                      className="accent-[#BE185D]"
                    />
                    <span>{reason.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Description */}
            <div>
              <label htmlFor="report-description" className="block text-sm font-medium text-[#1F1720] mb-1">
                Description (required)
              </label>
              <textarea
                id="report-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the issue in detail..."
                rows={3}
                maxLength={2000}
                className="w-full border border-pink-200 rounded-xl px-4 py-3 text-sm text-[#1F1720] placeholder-[#9F7A89] bg-white focus:outline-none focus:ring-2 focus:ring-[#BE185D] resize-none transition"
                required
              />
            </div>

            {/* Error message */}
            {error && (
              <p role="alert" className="text-sm text-[#DC2626] bg-red-50 rounded-xl px-4 py-2 border border-red-200">
                {error}
              </p>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => { resetForm(); onClose(); }}
                className="flex-1 py-2 rounded-full border border-[#BE185D] text-[#BE185D] font-semibold hover:bg-[#FCE7F3] transition-all"
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !selectedReason || !description.trim()}
                className="flex-1 py-2 rounded-full font-semibold text-white bg-gradient-to-r from-[#BE185D] to-[#E11D48] hover:brightness-110 active:scale-95 transition-all disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Submitting…
                  </>
                ) : (
                  'Submit Report'
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
