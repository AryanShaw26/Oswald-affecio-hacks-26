import { useState, useRef, useEffect } from 'react';

/**
 * MessageComposer -- the text input area with a Send button.
 *
 * Props:
 *   onSend      (message: string) => void   called when the user submits
 *   disabled    boolean                  disables input while checks run
 */
export default function MessageComposer({ onSend, disabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
  };

  // Auto-resize textarea based on content
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight}px`;
  }, [text]);

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-3 bg-white rounded-2xl shadow-lg p-3 border border-pink-200 focus-within:ring-2 focus-within:ring-[#BE185D]"
    >
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={disabled ? 'Running safety checks…' : 'Type a message…'}
        disabled={disabled}
        rows={1}
        maxLength={2000}
        className="flex-1 resize-none border-none outline-none text-sm text-[#1F1720] placeholder-[#9F7A89] bg-transparent disabled:opacity-50"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
          }
        }}
      />
      <button
        type="submit"
        disabled={!text.trim() || disabled}
        className="p-2 rounded-xl bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white hover:brightness-110 active:scale-95 transition-all disabled:opacity-50 flex-shrink-0"
        aria-label="Send message"
      >
        {disabled ? (
          <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
          </svg>
        )}
      </button>
    </form>
  );
}
