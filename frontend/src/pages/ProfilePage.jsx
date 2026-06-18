import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { SiteHeader, SiteFooter } from "../components/SiteChrome";
import { toast } from "../components/dialog";

/* ════════════════════════════════════════════════════════════
   TravelBuddy — Hồ sơ của tôi (rút gọn)
   • Thông tin cá nhân (chỉnh sửa & lưu lên BE)
   • Sở thích du lịch — để người khác xem được khi bấm vào hồ sơ của bạn
   Lưu thật vào users.travel_preferences qua PUT /api/travel/profile.
═══════════════════════════════════════════════════════════════ */

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Inter',-apple-system,sans-serif; background:#F0F9FF; color:#0F172A; -webkit-font-smoothing:antialiased; }

.pf-wrap { background:#F0F9FF; min-height:calc(100vh - 64px); }
.pf-main { max-width:860px; margin:0 auto; padding:0 2rem 3.5rem; }

.pf-banner { position:relative; height:172px; border-radius:0 0 24px 24px; overflow:hidden;
  background:linear-gradient(135deg,#075985 0%,#0369A1 32%,#0284C7 64%,#22D3EE 100%); }
.pf-banner::before { content:''; position:absolute; inset:0;
  background-image:radial-gradient(circle, rgba(255,255,255,0.08) 1.5px, transparent 1.5px); background-size:26px 26px; }
.pf-banner-deco { position:absolute; right:6%; top:-10px; font-size:7rem; opacity:0.12; pointer-events:none; user-select:none; }

.pf-head { position:relative; z-index:2; display:flex; align-items:flex-end; gap:1.5rem; margin-top:-60px; padding:0 0.5rem; flex-wrap:wrap; }
.pf-avatar { width:124px; height:124px; flex-shrink:0; border-radius:50%; border:5px solid #fff;
  background:linear-gradient(135deg,#F97316,#FB7185); display:flex; align-items:center; justify-content:center;
  color:#fff; font-family:'Nunito',sans-serif; font-weight:900; font-size:2.75rem; background-size:cover; background-position:center;
  box-shadow:0 14px 32px rgba(15,23,42,0.18); }
.pf-head-info { flex:1; min-width:200px; padding-bottom:0.5rem; }
.pf-name { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.75rem; letter-spacing:-0.02em; color:#0F172A; }
.pf-email { font-size:0.9375rem; color:#64748B; margin-top:0.3rem; }
.pf-head-actions { display:flex; gap:0.625rem; padding-bottom:0.625rem; }
.pf-btn { display:inline-flex; align-items:center; gap:0.45rem; padding:0.625rem 1.125rem; border-radius:10px;
  font-family:'Nunito',sans-serif; font-weight:800; font-size:0.875rem; cursor:pointer; transition:all 0.15s; }
.pf-btn.primary { border:none; background:linear-gradient(135deg,#0EA5E9,#0284C7); color:#fff;
  box-shadow:0 4px 14px rgba(14,165,233,0.32); }
.pf-btn.primary:hover { transform:translateY(-1px); box-shadow:0 7px 18px rgba(14,165,233,0.42); }
.pf-btn.ghost { border:1.5px solid #E2E8F0; background:#fff; color:#0284C7; }
.pf-btn.ghost:hover { border-color:#0EA5E9; background:#F0F9FF; }

.pf-card { background:#fff; border:1px solid rgba(226,232,240,0.9); border-radius:18px; padding:1.5rem;
  box-shadow:0 2px 10px rgba(15,23,42,0.05); margin-top:1.5rem; }
.pf-card-head { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:1.25rem; }
.pf-card-title { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.125rem; color:#0F172A; display:flex; align-items:center; gap:0.5rem; }
.pf-link-btn { background:none; border:none; color:#0284C7; font-family:'Nunito',sans-serif; font-weight:800;
  font-size:0.8125rem; cursor:pointer; padding:0.3rem 0.6rem; border-radius:8px; transition:background 0.13s; }
.pf-link-btn:hover { background:#F0F9FF; }

.pf-fields { display:grid; grid-template-columns:1fr 1fr; gap:1rem 1.25rem; }
.pf-field { display:flex; flex-direction:column; gap:0.375rem; }
.pf-field.full { grid-column:1 / -1; }
.pf-lbl { font-size:0.75rem; font-weight:800; letter-spacing:0.04em; text-transform:uppercase; color:#94A3B8; }
.pf-val { font-size:0.9375rem; color:#0F172A; font-weight:500; padding:0.3rem 0; }
.pf-val.muted { color:#94A3B8; font-style:italic; font-weight:400; }
.pf-input, .pf-textarea { width:100%; padding:0.65rem 0.85rem; border:1.5px solid #E2E8F0; border-radius:10px;
  font-size:0.9375rem; color:#0F172A; background:#FAFBFC; font-family:inherit; outline:none; resize:none;
  transition:border-color 0.18s, box-shadow 0.18s, background 0.18s; }
.pf-input:focus, .pf-textarea:focus { border-color:#0EA5E9; background:#fff; box-shadow:0 0 0 3px rgba(14,165,233,0.1); }

.pf-chips { display:flex; flex-wrap:wrap; gap:0.5rem; }
.pf-chip { display:inline-flex; align-items:center; gap:0.4rem; padding:0.45rem 0.9rem; border-radius:100px;
  border:1.5px solid #E2E8F0; background:#fff; font-size:0.8125rem; font-weight:700; color:#64748B;
  cursor:pointer; transition:all 0.15s; user-select:none; }
.pf-chip:hover { border-color:#0EA5E9; }
.pf-chip.on { background:linear-gradient(135deg,#0EA5E9,#0284C7); color:#fff; border-color:transparent;
  box-shadow:0 4px 12px rgba(14,165,233,0.28); }
.pf-hint { font-size:0.8125rem; color:#94A3B8; margin-top:0.875rem; }

@media (max-width:600px) {
  .pf-main { padding:0 1.25rem 2.5rem; }
  .pf-head { gap:1rem; margin-top:-52px; }
  .pf-avatar { width:100px; height:100px; font-size:2.25rem; }
  .pf-name { font-size:1.5rem; }
  .pf-fields { grid-template-columns:1fr; }
  .pf-head-actions { width:100%; }
  .pf-btn { flex:1; justify-content:center; }
}
`;

const IconEdit = () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>);
const IconCheck = () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>);

const INTERESTS = [
  { k: "beach", e: "🏖️", l: "Biển đảo" }, { k: "mountain", e: "⛰️", l: "Núi rừng" },
  { k: "food", e: "🍜", l: "Ẩm thực" }, { k: "culture", e: "🏛️", l: "Văn hoá" },
  { k: "adventure", e: "🧗", l: "Phiêu lưu" }, { k: "photo", e: "📸", l: "Sống ảo" },
  { k: "luxury", e: "✨", l: "Nghỉ dưỡng" }, { k: "budget", e: "💰", l: "Tiết kiệm" },
  { k: "nightlife", e: "🌃", l: "Về đêm" }, { k: "nature", e: "🌿", l: "Thiên nhiên" },
];

function getUserStore() {
  if (localStorage.getItem("tb_user")) return localStorage;
  if (sessionStorage.getItem("tb_user")) return sessionStorage;
  return localStorage;
}
function getUser() {
  try { return JSON.parse(localStorage.getItem("tb_user") || sessionStorage.getItem("tb_user") || "null") || {}; }
  catch { return {}; }
}
function getToken() { return localStorage.getItem("tb_token") || sessionStorage.getItem("tb_token"); }
const initialsOf = (name) => (name || "?").trim().split(" ").slice(-2).map((s) => s[0]).join("").toUpperCase();

export default function ProfilePage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(getUser);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const prefs = user.travel_preferences || {};
  const [form, setForm] = useState({
    full_name: user.full_name || "Traveler",
    phone: prefs.phone || user.phone || "",
    location: prefs.location || user.location || "",
    birthday: prefs.birthday || user.birthday || "",
    bio: prefs.bio || user.bio || "",
  });
  const [interests, setInterests] = useState(
    Array.isArray(prefs.interests) ? prefs.interests
      : (Array.isArray(user.interests) ? user.interests : [])
  );

  const set = (k) => (e) => setForm((p) => ({ ...p, [k]: e.target.value }));
  const toggleInterest = (k) =>
    setInterests((prev) => (prev.includes(k) ? prev.filter((x) => x !== k) : [...prev, k]));

  /* PUT lên BE → lưu vào users.travel_preferences, cập nhật tb_user để header & hồ sơ công khai đồng bộ */
  const pushUpdate = async (patch, okMsg) => {
    const token = getToken();
    if (!token) { toast("Bạn cần đăng nhập"); navigate("/login"); return false; }
    setSaving(true);
    try {
      const res = await fetch("/api/travel/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(patch),
      });
      if (res.status === 401) { toast("Phiên đăng nhập đã hết hạn"); navigate("/login"); return false; }
      if (!res.ok) throw new Error();
      const updated = await res.json();
      getUserStore().setItem("tb_user", JSON.stringify(updated));
      setUser(updated);
      toast(okMsg);
      return true;
    } catch { toast("Lưu thất bại, thử lại sau"); return false; }
    finally { setSaving(false); }
  };

  const saveProfile = async () => {
    if (!form.full_name.trim()) { toast("Vui lòng nhập họ và tên"); return; }
    const ok = await pushUpdate({
      full_name: form.full_name.trim(), phone: form.phone, location: form.location,
      birthday: form.birthday, bio: form.bio,
    }, "Đã lưu hồ sơ thành công ✓");
    if (ok) setEditing(false);
  };

  const cancelEdit = () => {
    const p = user.travel_preferences || {};
    setForm({
      full_name: user.full_name || "Traveler", phone: p.phone || "", location: p.location || "",
      birthday: p.birthday || "", bio: p.bio || "",
    });
    setEditing(false);
  };

  const saveInterests = () => pushUpdate({ interests }, "Đã cập nhật sở thích du lịch ✓");

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />
      <SiteHeader active="profile" />

      <div className="pf-wrap">
        <div className="pf-banner"><span className="pf-banner-deco">🌏</span></div>

        <main className="pf-main">
          <div className="pf-head">
            <div className="pf-avatar" style={user.avatar_url ? { backgroundImage: `url(${user.avatar_url})` } : undefined}>
              {!user.avatar_url && initialsOf(user.full_name)}
            </div>
            <div className="pf-head-info">
              <h1 className="pf-name">{user.full_name || "Traveler"}</h1>
              <p className="pf-email">{user.email || "demo@travelbuddy.local"}</p>
            </div>
            <div className="pf-head-actions">
              {!editing ? (
                <button className="pf-btn primary" onClick={() => setEditing(true)}><IconEdit /> Chỉnh sửa hồ sơ</button>
              ) : (
                <>
                  <button className="pf-btn ghost" onClick={cancelEdit} disabled={saving}>Huỷ</button>
                  <button className="pf-btn primary" onClick={saveProfile} disabled={saving}><IconCheck /> {saving ? "Đang lưu…" : "Lưu thay đổi"}</button>
                </>
              )}
            </div>
          </div>

          {/* Thông tin cá nhân */}
          <div className="pf-card">
            <div className="pf-card-head">
              <div className="pf-card-title">👤 Thông tin cá nhân</div>
              {!editing && <button className="pf-link-btn" onClick={() => setEditing(true)}>Chỉnh sửa</button>}
            </div>
            <div className="pf-fields">
              <div className="pf-field">
                <span className="pf-lbl">Họ và tên</span>
                {editing
                  ? <input className="pf-input" value={form.full_name} onChange={set("full_name")} placeholder="Nguyễn Văn A" />
                  : <span className="pf-val">{user.full_name || "Traveler"}</span>}
              </div>
              <div className="pf-field">
                <span className="pf-lbl">Email</span>
                <span className="pf-val">{user.email || "demo@travelbuddy.local"}</span>
              </div>
              <div className="pf-field">
                <span className="pf-lbl">Số điện thoại</span>
                {editing
                  ? <input className="pf-input" value={form.phone} onChange={set("phone")} placeholder="09xx xxx xxx" />
                  : <span className={"pf-val" + (form.phone ? "" : " muted")}>{form.phone || "Chưa cập nhật"}</span>}
              </div>
              <div className="pf-field">
                <span className="pf-lbl">Ngày sinh</span>
                {editing
                  ? <input className="pf-input" type="date" value={form.birthday} onChange={set("birthday")} />
                  : <span className={"pf-val" + (form.birthday ? "" : " muted")}>{form.birthday || "Chưa cập nhật"}</span>}
              </div>
              <div className="pf-field full">
                <span className="pf-lbl">Nơi ở</span>
                {editing
                  ? <input className="pf-input" value={form.location} onChange={set("location")} placeholder="TP. Hồ Chí Minh, Việt Nam" />
                  : <span className={"pf-val" + (form.location ? "" : " muted")}>{form.location || "Chưa cập nhật"}</span>}
              </div>
              <div className="pf-field full">
                <span className="pf-lbl">Giới thiệu bản thân</span>
                {editing
                  ? <textarea className="pf-textarea" rows={3} value={form.bio} onChange={set("bio")} placeholder="Đôi dòng về phong cách du lịch của bạn..." />
                  : <span className={"pf-val" + (form.bio ? "" : " muted")}>{form.bio || "Chưa có giới thiệu — hãy kể về hành trình của bạn!"}</span>}
              </div>
            </div>
          </div>

          {/* Sở thích du lịch */}
          <div className="pf-card">
            <div className="pf-card-head">
              <div className="pf-card-title">🎯 Sở thích du lịch</div>
              <button className="pf-link-btn" onClick={saveInterests} disabled={saving}>Lưu</button>
            </div>
            <div className="pf-chips">
              {INTERESTS.map((it) => (
                <button key={it.k} className={"pf-chip" + (interests.includes(it.k) ? " on" : "")}
                  onClick={() => toggleInterest(it.k)}>
                  <span>{it.e}</span> {it.l}
                </button>
              ))}
            </div>
            <p className="pf-hint">Sở thích này sẽ hiển thị công khai — khi người khác bấm vào hồ sơ của bạn trong cộng đồng, họ có thể xem được bạn thích kiểu du lịch nào.</p>
          </div>
        </main>
      </div>

      <SiteFooter />
    </>
  );
}
