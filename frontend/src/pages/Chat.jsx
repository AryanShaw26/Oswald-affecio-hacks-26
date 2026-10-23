import { useState, useRef, useEffect } from 'react';
import MessageComposer from '../components/MessageComposer';
import SafetyAnalysisDisplay from '../components/SafetyAnalysisDisplay';
import PreSendModal from '../components/PreSendModal';
import useAuth from '../hooks/useAuth';
import { checkPrivacy, analyzeSafety } from '../services/api';

/**
 * Chat — the integrated conversation interface where V4 (Conversation Safety)
 * and V5 (Privacy Guardian) meet.
 *
 * Flow on send:
 *   1. V5 /privacy/check   — if flagged, show privacy warning & let user decide
 *   2. V4 /safety/analyze  — show risk assessment
 *   3. User confirms (or edits message) → message lands in the chat
 */
export default function Chat() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [isChecking, setIsChecking] = useState(false);
  const [modal, setModal] = useState({
    open: false,
    message: '',
    privacyResult: null,
    safetyResult: null,
    stage: 'privacy',
  });

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollTo({
      top: messagesEndRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages, modal]);

  const openModal = (message) =>
    setModal({ open: true, message, privacyResult: null, safetyResult: null, stage: 'privacy' });

  const closeModal = () =>
    setModal({ open: false, message: '', privacyResult: null, safetyResult: null, stage: 'privacy' });

  // Stage 1: Privacy Guardian (V5)
  const runPrivacyCheck = async () => {
    setIsChecking(true);
    try {
      const result = await checkPrivacy(modal.message);
      setModal((m) => ({ ...m, privacyResult: result, stage: 'safety' }));
    } catch {
      setModal((m) => ({
        ...m,
        privacyResult: {
          flagged: true,
          risk_level: 'high',
          detected_types: ['Service Unavailable'],
          warning: 'Privacy check service is unavailable.',
          recommendation: 'Try again in a moment.',
        },
        stage: 'safety',
      }));
    } finally {
      setIsChecking(false);
    }
  };

  // Stage 2: Safety Analysis (V4)
  const runSafetyCheck = async () => {
    setIsChecking(true);
    try {
      const result = await analyzeSafety(modal.message);
      setModal((m) => ({ ...m, safetyResult: result, stage: 'confirm' }));
    } catch {
      setModal((m) => ({ ...m, safetyResult: null, stage: 'confirm' }));
    } finally {
      setIsChecking(false);
    }
  };

  // Stage 3: Confirm & send
  const handleConfirmSend = () => {
    const newMessage = {
      id: Date.now(),
      text: modal.message,
      sender: 'user',
      timestamp: new Date().toISOString(),
      safetyResult: modal.safetyResult,
    };
    setMessages((prev) => [...prev, newMessage]);

    // Bot-style acknowledgment
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          text: 'Your message has been sent. It passed both privacy and safety checks.',
          sender: 'system',
          timestamp: new Date().toISOString(),
        },
      ]);
    }, 500);

    closeModal();
  };

  return (
    <div className="min-h-screen bg-[#FFF1F2] pt-20">
      <div className="max-w-4xl mx-auto px-4 pb-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[#831843]">Chat</h1>
          {user && <p className="text-sm text-[#9F7A89] mt-1">Signed in as {user.email}</p>}
        </div>

        {/* Messages area */}
        <div
          ref={messagesEndRef}
          className="h-[500px] overflow-y-auto bg-white rounded-3xl shadow-lg border border-pink-200 p-6 mb-4"
        >
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-[#9F7A89]">
              <span className="text-5xl mb-4">💬</span>
              <p className="text-lg font-medium text-[#831843]">No messages yet</p>
              <p className="text-sm mt-2">
                Type a message below. It will be checked by the Privacy Guardian (V5) and
                Safety Analysis (V4) before sending.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div key={msg.id}>
                  {msg.safetyResult && <SafetyAnalysisDisplay result={msg.safetyResult} />}
                  <div
                    className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm ${
                      msg.sender === 'user'
                        ? 'bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white ml-auto rounded-br-none'
                        : 'bg-[#FCE7F3] text-[#1F1720] rounded-bl-none'
                    }`}
                  >
                    {msg.text}
                  </div>
                  <div
                    className="text-xs text-[#9F7A89] mt-1"
                    style={{ textAlign: msg.sender === 'user' ? 'right' : 'left' }}
                  >
                    {new Date(msg.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Message composer */}
        <MessageComposer onSend={openModal} disabled={isChecking} />

        {/* V4 + V5 Pre-Send Modal */}
        {modal.open && (
          <PreSendModal
            modal={modal}
            onRunPrivacyCheck={runPrivacyCheck}
            onRunSafetyCheck={runSafetyCheck}
            onConfirm={handleConfirmSend}
            onEdit={closeModal}
            onCancel={closeModal}
            isChecking={isChecking}
          />
        )}
      </div>
    </div>
  );
}
