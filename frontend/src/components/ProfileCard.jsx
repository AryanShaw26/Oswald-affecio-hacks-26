/**
 * ProfileCard -- discovery card showing user basics + trust badge.
 */
export default function ProfileCard({ name, age, bio, interests = [], score, verified = false, imageUrl }) {
  return (
    <div className="bg-white rounded-2xl shadow-md overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-200 flex flex-col">
      {/* Profile image */}
      <div className="relative h-56 bg-gradient-to-br from-[#831843] to-[#BE185D] flex items-center justify-center">
        {imageUrl ? (
          <img src={imageUrl} alt={`${name}'s profile`} className="w-full h-full object-cover" />
        ) : (
          <span className="text-6xl select-none">👤</span>
        )}
        {/* Trust score badge */}
        {score !== undefined && (
          <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm rounded-full px-2 py-1 flex items-center gap-1 text-xs font-semibold text-[#831843]">
            🛡️ {score}
          </div>
        )}
        {verified && (
          <div className="absolute top-3 left-3 bg-[#BE185D] text-white text-xs font-semibold px-2 py-1 rounded-full">
            ✓ Verified
          </div>
        )}
      </div>

      {/* Card body */}
      <div className="p-4 flex flex-col gap-2 flex-1">
        <div className="flex items-baseline justify-between">
          <h3 className="font-bold text-lg text-[#1F1720]">{name}, {age}</h3>
        </div>
        {bio && <p className="text-sm text-[#9F7A89] line-clamp-2">{bio}</p>}
        {interests.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {interests.slice(0, 4).map((tag) => (
              <span key={tag} className="text-xs bg-[#FCE7F3] text-[#BE185D] font-medium px-2 py-0.5 rounded-full">
                {tag}
              </span>
            ))}
          </div>
        )}
        <div className="mt-auto pt-3 flex gap-2">
          <button className="flex-1 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-[#BE185D] to-[#E11D48] text-white hover:brightness-110 active:scale-95 transition-all">
            Connect
          </button>
          <button className="py-2 px-3 rounded-full border border-[#BE185D] text-[#BE185D] text-sm font-semibold hover:bg-[#FFF1F2] transition-all">
            Profile
          </button>
        </div>
      </div>
    </div>
  );
}
