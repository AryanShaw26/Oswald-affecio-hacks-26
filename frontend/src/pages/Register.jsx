import { useState } from 'react';
import { Link } from 'react-router-dom';

const STEPS = ['Profile Basics', 'Your Interests', 'Privacy & Consent'];

export default function Register() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({ name: '', email: '', password: '', interests: [], consent: false });

  const INTERESTS = ['Travel', 'Music', 'Fitness', 'Books', 'Cooking', 'Art', 'Tech', 'Yoga', 'Photography', 'Gaming'];

  const toggleInterest = (tag) =>
    setForm((f) => ({
      ...f,
      interests: f.interests.includes(tag) ? f.interests.filter((i) => i !== tag) : [...f.interests, tag],
    }));

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  return (
    <div className="min-h-screen bg-[#831843] flex items-center justify-center px-4 pt-16">
      <div className="w-full max-w-lg bg-[#FFF1F2] rounded-3xl shadow-2xl p-8">
        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-2 flex-1 last:flex-none">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                i < step ? 'bg-[#16A34A] text-white' : i === step ? 'bg-[#BE185D] text-white' : 'bg-pink-200 text-[#9F7A89]'
              }`}>
                {i < step ? '✓' : i + 1}
              </div>
              <span className={`text-xs font-medium hidden sm:block ${i === step ? 'text-[#BE185D]' : 'text-[#9F7A89]'}`}>{label}</span>
              {i < STEPS.length - 1 && <div className="flex-1 h-0.5 bg-pink-200 mx-1" />}
            </div>
          ))}
        </div>

        {/* Step 0 -- Profile Basics */}
        {step === 0 && (
          <div className="space-y-5">
            <h2 className="text-xl font-bold text-[#831843]">Let's get started</h2>
            {['name', 'email', 'password'].map((field) => (
              <div key={field}>
                <label htmlFor={field} className="block text-sm font-medium text-[#1F1720] mb-1 capitalize">
                  {field === 'name' ? 'Full Name' : field === 'email' ? 'Email address' : 'Password'}
                </label>
                <input
                  id={field}
                  name={field}
                  type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'}
                  value={form[field]}
                  onChange={handleChange}
                  required
                  className="w-full border border-pink-200 rounded-xl px-4 py-3 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#BE185D]"
                />
              </div>
            ))}
          </div>
        )}

        {/* Step 1 -- Interests */}
        {step === 1 && (
          <div>
            <h2 className="text-xl font-bold text-[#831843] mb-2">What are you into?</h2>
            <p className="text-sm text-[#9F7A89] mb-5">Choose up to 6 interests to personalize your discovery feed.</p>
            <div className="flex flex-wrap gap-2">
              {INTERESTS.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleInterest(tag)}
                  className={`px-4 py-2 rounded-full text-sm font-medium border transition-all ${
                    form.interests.includes(tag)
                      ? 'bg-[#BE185D] border-[#BE185D] text-white'
                      : 'bg-white border-pink-200 text-[#9F7A89] hover:border-[#BE185D] hover:text-[#BE185D]'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2 -- Privacy & Consent */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-[#831843]">Your privacy matters</h2>
            <div className="bg-[#FCE7F3] rounded-xl p-4 text-sm text-[#1F1720] space-y-2 leading-relaxed">
              <p>🛡️ TrustMatch AI uses AI to detect potential risks in conversations. You are always in control.</p>
              <p>🔒 We never sell your data. Your information is used only to improve your safety and experience.</p>
              <p>⚙️ You can delete your account and all data at any time from the Safety Center.</p>
            </div>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                name="consent"
                checked={form.consent}
                onChange={handleChange}
                className="mt-1 accent-[#BE185D]"
              />
              <span className="text-sm text-[#1F1720]">
                I agree to TrustMatch AI's{' '}
                <span className="text-[#BE185D] underline cursor-pointer">Privacy Policy</span>
                {' '}and{' '}
                <span className="text-[#BE185D] underline cursor-pointer">Terms of Service</span>.
              </span>
            </label>
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3 mt-8">
          {step > 0 && (
            <button onClick={back} className="flex-1 py-3 rounded-full border border-[#BE185D] text-[#BE185D] font-semibold hover:bg-[#FCE7F3] transition-all">
              Back
            </button>
          )}
          {step < STEPS.length - 1 ? (
            <button onClick={next} className="flex-1 py-3 rounded-full font-semibold text-white bg-gradient-to-r from-[#BE185D] to-[#E11D48] hover:brightness-110 transition-all">
              Continue
            </button>
          ) : (
            <button
              disabled={!form.consent}
              className="flex-1 py-3 rounded-full font-semibold text-white bg-gradient-to-r from-[#BE185D] to-[#E11D48] hover:brightness-110 transition-all disabled:opacity-50"
            >
              Create Account
            </button>
          )}
        </div>

        <p className="text-center text-sm text-[#9F7A89] mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-[#BE185D] font-semibold hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
