import { useEffect } from 'react';
import SafetyAlert from './SafetyAlert';
import SafetyAnalysisDisplay from './SafetyAnalysisDisplay';
import { riskToLevel } from '../utils/riskUtils';

/**
 * PreSendModal — step-by-step review modal that walks through the V5
 * Privacy Guardian check and V4 Safety Analysis before the user sends.
 *
 * Props:
 *   modal           { open, message, privacyResult, safetyResult, stage }
 *   onRunPrivacyCheck  () => Promise<void>
 *   onRunSafetyCheck   () => Promise<void>
 *   onConfirm          () => void
 *   onEdit             () => void
 *   onCancel           () => void
 *   isChecking         boolean
 */
export default function PreSendModal({
  modal,
  onRunPrivacyCheck,
  onRunSafetyCheck,
  onConfirm,
  onEdit,
  onCancel,
  isChecking,
}) {
  const { message, privacyResult, safetyResult, stage } = modal;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg p-6">
        {/* Stage indicator dots */}
        <div className="flex items-center justify-center gap-2 mb-6">
          <div className={`w-3 h-3 rounded-full ${privacyResult ? 'bg-green-500' : 'bg-pink-200'}`} />
          <div className="h-0.5 flex-1 bg-pink-200" />
          <div className={`w-3 h-3 rounded-full ${safetyResult ? 'bg-green-500' : 'bg-pink-200'}`} />
        </div>

        <h3 className="text-lg font-bold text-[#831843] mb-4">
          {stage === 'confirm'
            ? 'Ready to Send?'
            : stage === 'privacy'
            ? 'Checking Privacy…'
            : 'Checking Safety…'}
        </h3>

        {/* ── Stage 1 — Privacy Guardian (V5) ── */}
        {stage === 'privacy' && (
          <>
            <p className="text-sm text-[#9F7A89] mb-4">
              Running Privacy Guardian check on your message…
            </p>
            <p className="text-sm text-[#1F1720] bg-[#FCE7F3] rounded-xl p-3 mb-4 break-words italic">
              “{message}”
            </p>
            <div className="flex justify-center py-2">
              <Spinner />
            </div>
            <AutoRunner skip={!isChecking} onDone={onRunPrivacyCheck} />
          </>
        )}

        {/* ── Stage 2 — Safety Analysis (V4) ── */}
        {stage === 'safety' && privacyResult && (
          <>
            {privacyResult.flagged && (
              <SafetyAlert
                level={riskToLevel('high')}
                message={privacyResult.warning}
                detectedTypes={privacyResult.detected_types}
                recommendation={privacyResult.recommendation}
              />
            )}
            {!privacyResult.flagged && (
              <p className="text-sm text-[#16A34A] bg-green-50 rounded-xl p-3 mb-4">
                ✓ Privacy check passed — no sensitive data detected.
              </p>
            )}

            <p className="text-sm text-[#9F7A89] mb-4">
              {privacyResult.flagged
                ? 'Privacy check flagged your message. Continue to safety analysis?'
                : 'Running Safety Analysis…'}
            </p>

            {!privacyResult.flagged && (
              <div className="flex justify-center py-2">
                <Spinner />
              </div>
            )}
            {!privacyResult.flagged && (
              <AutoRunner skip={!isChecking} onDone={onRunSafetyCheck} />
            )}
          </>
        )}

        {/* ── Stage 3 — Confirm ── */}
        {stage === 'confirm' && (
          <>
            {safetyResult && <SafetyAnalysisDisplay result={safetyResult} />}

            <p className="text-sm text-[#9F7A89] mb-6">
              Your message will be sent after final verification.
            </p>
            <div className="flex gap-3">
              <button
                onClick={onEdit}
                className="flex-1 py-2 rounded-full border border-[#BE185D] text-[#BE185D] font-semibold hover:bg-[#FCE7F3] transition-all"
              >
                Edit Message
              </button>
              <button
                onClick={onCancel}
                className="flex-1 py-2 rounded-full border border-pink-200 text-[#9F7A89] font-semibold hover:bg-pink-50 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={onConfirm}
                className="flex-1 py-2 rounded-full font-semibold text-white bg-gradient-to-r from-[#BE185D] to-[#E11D48] hover:brightness-110 active:scale-95 transition-all"
              >
                Send
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <svg className="w-6 h-6 animate-spin text-[#BE185D]" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

/** Auto-runner — triggers the wrapped API check once loading completes. */
function AutoRunner({ skip, onDone }) {
  useEffect(() => {
    if (skip) return;
    onDone();
  }, [skip, onDone]);
  return null;
}
