import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { createProfile, getMyProfile, getProfile, getProfileTrustScore, updateMyProfile } from '../services/api';

const emptyForm = {
  name: '',
  age: '',
  bio: '',
  location: '',
  profile_picture: '',
  interests: '',
};

export default function Profile() {
  const { user } = useAuth();
  const { id } = useParams();
  const [profile, setProfile] = useState(null);
  const [trust, setTrust] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState(emptyForm);
  const [isEditing, setIsEditing] = useState(false);

  const targetId = id ? Number(id) : user?.id;
  const isOwnProfile = !id || Number(id) === user?.id;

  const applyProfileToForm = (value) => {
    setForm({
      name: value?.name || '',
      age: value?.age ?? '',
      bio: value?.bio || '',
      location: value?.location || '',
      profile_picture: value?.profile_picture || '',
      interests: (value?.interests || []).map((interest) => interest.name || interest).join(', '),
    });
  };

  useEffect(() => {
    const fetchProfile = async () => {
      if (!user && !id) return;
      if (id && user && Number(id) !== user.id) {
        setLoading(false);
        setProfile(null);
        setError('This profile is private and not available to your account.');
        return;
      }
      setLoading(true);
      setError('');
      try {
        const data = isOwnProfile ? await getMyProfile() : await getProfile(targetId);
        setProfile(data);
        applyProfileToForm(data);
        try {
          const trustData = await getProfileTrustScore(data.id);
          setTrust(trustData);
        } catch {
          setTrust(null);
        }
      } catch (err) {
        if (err.response?.status === 404) {
          setProfile(null);
          setTrust(null);
          if (isOwnProfile) setForm(emptyForm);
        } else {
          setError('Unable to load profile data.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [id, user, isOwnProfile, targetId]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const payload = {
        name: form.name,
        age: form.age ? Number(form.age) : null,
        bio: form.bio || null,
        location: form.location || null,
        profile_picture: form.profile_picture || null,
        interests: (form.interests || '')
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
      };

      if (profile) {
        const updated = await updateMyProfile(payload);
        setProfile(updated);
        applyProfileToForm(updated);
        setSuccess('Profile updated successfully.');
      } else {
        const created = await createProfile(payload);
        setProfile(created);
        applyProfileToForm(created);
        setSuccess('Profile created successfully.');
      }
      setIsEditing(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to save your profile.');
    } finally {
      setSaving(false);
    }
  };

  if (!user && !id) {
    return (
      <div className="min-h-screen bg-[#FFF1F2] pt-20 flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-lg border border-pink-200 p-8 max-w-md text-center">
          <h2 className="text-2xl font-bold text-[#831843] mb-3">Sign in to view your profile</h2>
          <Link to="/login" className="inline-block mt-4 px-6 py-3 rounded-full bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white font-semibold">
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FFF1F2] pt-20 px-4">
        <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-md p-6 text-center text-[#9F7A89]">
          Loading profile...
        </div>
      </div>
    );
  }

  if (error && !profile && !isOwnProfile) {
    return (
      <div className="min-h-screen bg-[#FFF1F2] pt-20 px-4">
        <div className="max-w-4xl mx-auto bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
          <h2 className="text-xl font-bold text-[#831843]">Unable to load profile</h2>
          <p className="text-sm text-[#9F7A89] mt-2">{error}</p>
        </div>
      </div>
    );
  }

  const displayHeader = profile ? `${profile.name}` : 'Create your profile';

  return (
    <div className="min-h-screen bg-[#FFF1F2] pt-20 px-4">
      <div className="max-w-5xl mx-auto py-8">
        <div className="bg-white rounded-3xl shadow-md border border-pink-200 overflow-hidden">
          <div className="bg-gradient-to-r from-[#831843] to-[#BE185D] px-6 py-10 text-white">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-wide text-pink-100">Profile</p>
                <h1 className="text-3xl font-bold">{displayHeader}</h1>
              </div>
              {isOwnProfile && !isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-5 py-3 rounded-full bg-white text-[#831843] font-semibold hover:bg-[#FCE7F3] transition"
                >
                  {profile ? 'Edit Profile' : 'Create Profile'}
                </button>
              )}
            </div>
          </div>

          <div className="grid lg:grid-cols-[1.15fr_0.85fr] gap-6 p-6">
            <section>
              {profile && !isEditing ? (
                <div className="space-y-6">
                  <div className="flex items-center gap-5">
                    <div className="w-20 h-20 rounded-full bg-[#FCE7F3] flex items-center justify-center text-3xl overflow-hidden">
                      {profile.profile_picture ? (
                        <img src={profile.profile_picture} alt={profile.name} className="w-full h-full object-cover" />
                      ) : (
                        '👤'
                      )}
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-[#1F1720]">{profile.name}</h2>
                      <p className="text-[#9F7A89]">{profile.age ? `${profile.age} years old` : 'Age not shared'}</p>
                    </div>
                  </div>

                  {profile.bio && <p className="text-[#1F1720] leading-relaxed">{profile.bio}</p>}

                  <div className="grid sm:grid-cols-2 gap-4 text-sm">
                    <InfoBlock label="Location" value={profile.location || 'Not specified'} />
                    <InfoBlock label="Profile completion" value={`${profile.completion_percentage || 0}%`} />
                  </div>

                  <div>
                    <p className="text-sm font-semibold text-[#831843] mb-2">Interests</p>
                    <div className="flex flex-wrap gap-2">
                      {(profile.interests || []).length > 0 ? (
                        profile.interests.map((interest) => (
                          <span key={interest.id || interest.name} className="rounded-full bg-[#FCE7F3] text-[#BE185D] px-3 py-1 text-xs font-medium">
                            {interest.name || interest}
                          </span>
                        ))
                      ) : (
                        <span className="text-[#9F7A89] text-sm">No interests added yet.</span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid sm:grid-cols-2 gap-4">
                    <Field label="Full name" name="name" value={form.name} onChange={handleChange} />
                    <Field label="Age" name="age" type="number" value={form.age} onChange={handleChange} />
                  </div>
                  <Field label="Bio" name="bio" value={form.bio} onChange={handleChange} textarea />
                  <div className="grid sm:grid-cols-2 gap-4">
                    <Field label="Location" name="location" value={form.location} onChange={handleChange} />
                    <Field label="Profile picture URL" name="profile_picture" value={form.profile_picture} onChange={handleChange} />
                  </div>
                  <Field label="Interests (comma separated)" name="interests" value={form.interests} onChange={handleChange} />

                  {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2">{error}</p>}
                  {success && <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-xl px-4 py-2">{success}</p>}

                  <div className="flex gap-3">
                    <button type="submit" disabled={saving} className="flex-1 rounded-full bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white font-semibold py-3 disabled:opacity-60">
                      {saving ? 'Saving…' : profile ? 'Save changes' : 'Create profile'}
                    </button>
                    {profile && (
                      <button type="button" onClick={() => { setIsEditing(false); applyProfileToForm(profile); }} className="px-5 rounded-full border border-[#BE185D] text-[#BE185D] font-semibold">
                        Cancel
                      </button>
                    )}
                  </div>
                </form>
              )}
            </section>

            <aside className="space-y-4">
              <div className="bg-[#FFF1F2] border border-pink-200 rounded-2xl p-4">
                <p className="text-sm font-semibold text-[#831843] mb-2">Trust signal</p>
                {trust ? (
                  <div>
                    <div className="text-4xl font-bold text-[#831843]">{trust.score}</div>
                    <div className="text-sm text-[#9F7A89] uppercase tracking-wide">{trust.risk_level}</div>
                    <ul className="mt-3 text-sm text-[#1F1720] space-y-2">
                      {(trust.explanation || []).map ? trust.explanation.map((item) => <li key={item}>• {item}</li>) : <li>• {trust.explanation}</li>}
                    </ul>
                  </div>
                ) : (
                  <p className="text-sm text-[#9F7A89]">No trust score has been calculated yet.</p>
                )}
              </div>

              {isOwnProfile && profile && !isEditing && (
                <Link to="/discover" className="block w-full text-center rounded-full border border-[#BE185D] text-[#BE185D] font-semibold py-3 hover:bg-[#FCE7F3] transition">
                  Explore profiles
                </Link>
              )}
            </aside>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoBlock({ label, value }) {
  return (
    <div className="bg-[#FFF1F2] rounded-xl p-3 border border-pink-100">
      <div className="text-xs uppercase tracking-wide text-[#9F7A89]">{label}</div>
      <div className="text-sm font-medium text-[#1F1720] mt-1">{value}</div>
    </div>
  );
}

function Field({ label, name, value, onChange, type = 'text', textarea = false }) {
  const inputProps = { id: name, name, value: value ?? '', onChange, type };
  return (
    <label className="block text-sm font-medium text-[#1F1720]">
      <span className="mb-1 block">{label}</span>
      {textarea ? (
        <textarea {...inputProps} rows="4" className="w-full border border-pink-200 rounded-xl px-4 py-3 bg-white focus:outline-none focus:ring-2 focus:ring-[#BE185D]" />
      ) : (
        <input {...inputProps} className="w-full border border-pink-200 rounded-xl px-4 py-3 bg-white focus:outline-none focus:ring-2 focus:ring-[#BE185D]" />
      )}
    </label>
  );
}
