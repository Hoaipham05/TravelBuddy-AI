import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "./dialog";

/* ════════════════════════════════════════════════════════════
   Shared site chrome — Header + Footer dùng chung cho mọi trang.
   Giữ giao diện & vị trí cố định, đồng nhất toàn site.
═══════════════════════════════════════════════════════════════ */

const CSS = `
.sc-header { position:sticky; top:0; z-index:200; height:64px; display:flex; align-items:center; padding:0 1.75rem; gap:1.25rem; background:rgba(255,255,255,0.92); backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px); border-bottom:1px solid rgba(14,165,233,0.1); box-shadow:0 1px 0 rgba(0,0,0,0.04); }
.sc-logo { display:flex; align-items:center; gap:0.625rem; cursor:pointer; flex-shrink:0; }
.sc-logo-mark { width:38px; height:38px; background:linear-gradient(135deg,#0EA5E9,#0284C7); border-radius:11px; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 14px rgba(14,165,233,0.38); color:#fff; flex-shrink:0; }
.sc-logo-name { font-family:'Nunito',sans-serif; font-size:1.125rem; font-weight:800; color:#0369A1; line-height:1.2; }
.sc-logo-sub { font-size:0.6875rem; font-weight:500; color:#64748B; letter-spacing:0.05em; text-transform:uppercase; display:block; }
.sc-nav { flex:1; display:flex; justify-content:center; gap:0.125rem; }
.sc-nav-item { display:flex; align-items:center; gap:0.375rem; padding:0.4375rem 0.8125rem; border-radius:9px; font-size:0.875rem; font-weight:600; color:#64748B; cursor:pointer; user-select:none; background:none; border:none; font-family:inherit; transition:all 0.15s; }
.sc-nav-item:hover { background:rgba(14,165,233,0.08); color:#0284C7; }
.sc-nav-item.active { background:linear-gradient(135deg,#0EA5E9,#0284C7); color:#fff; box-shadow:0 3px 10px rgba(14,165,233,0.3); }
.sc-nav-item.active:hover { color:#fff; }
.sc-right { display:flex; align-items:center; gap:0.5rem; flex-shrink:0; }
.sc-tour-btn { display:flex; align-items:center; gap:0.375rem; padding:0.4375rem 0.875rem; border-radius:9px; border:1.5px solid #E2E8F0; background:#fff; font-size:0.8125rem; font-weight:600; color:#0284C7; cursor:pointer; font-family:inherit; transition:all 0.15s; }
.sc-tour-btn:hover { border-color:#0EA5E9; background:#F0F9FF; }
.sc-icon-btn { width:38px; height:38px; border-radius:10px; border:1.5px solid #E2E8F0; background:#fff; display:flex; align-items:center; justify-content:center; cursor:pointer; color:#64748B; position:relative; transition:all 0.15s; }
.sc-icon-btn:hover { border-color:#0EA5E9; color:#0EA5E9; }
.sc-icon-btn .sc-dot { position:absolute; top:7px; right:8px; width:7px; height:7px; background:#FB7185; border-radius:50%; border:1.5px solid #fff; }
.sc-avatar-wrap { position:relative; }
.sc-avatar { display:flex; align-items:center; gap:0.5rem; padding:0.25rem 0.5rem 0.25rem 0.25rem; border-radius:100px; border:1.5px solid #E2E8F0; background:#fff; cursor:pointer; transition:all 0.15s; }
.sc-avatar:hover { border-color:#0EA5E9; box-shadow:0 3px 10px rgba(14,165,233,0.12); }
.sc-avatar-img { width:30px; height:30px; border-radius:50%; background:linear-gradient(135deg,#F97316,#FB7185); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; font-size:0.8125rem; font-family:'Nunito',sans-serif; }
.sc-avatar-name { font-size:0.8125rem; font-weight:700; color:#0F172A; max-width:110px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sc-menu { position:absolute; top:calc(100% + 10px); right:0; width:230px; background:#fff; border-radius:14px; box-shadow:0 16px 48px rgba(15,23,42,0.16); border:1px solid #E2E8F0; padding:0.5rem; z-index:250; animation:sc-menu-in 0.18s ease; }
@keyframes sc-menu-in { from { opacity:0; transform:translateY(-6px); } to { opacity:1; transform:translateY(0); } }
.sc-menu-head { padding:0.75rem 0.75rem 0.625rem; border-bottom:1px solid #E2E8F0; margin-bottom:0.375rem; }
.sc-menu-head .nm { font-weight:800; font-family:'Nunito',sans-serif; color:#0F172A; font-size:0.9375rem; }
.sc-menu-head .em { font-size:0.75rem; color:#64748B; }
.sc-menu-item { display:flex; align-items:center; gap:0.625rem; padding:0.5625rem 0.75rem; border-radius:9px; font-size:0.875rem; font-weight:500; color:#0F172A; cursor:pointer; background:none; border:none; width:100%; font-family:inherit; text-align:left; transition:background 0.12s; }
.sc-menu-item:hover { background:#F1F5F9; }
.sc-menu-item.danger { color:#DC2626; }
.sc-menu-item.danger:hover { background:#FEF2F2; }
.sc-menu-badge { margin-left:auto; font-size:0.6875rem; font-weight:700; padding:0.1rem 0.45rem; border-radius:100px; background:#FEF3C7; color:#B45309; }

.sc-footer { background:#0F172A; padding:1.125rem 2rem; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.75rem; }
.sc-footer-brand { display:flex; align-items:center; gap:0.5rem; font-family:'Nunito',sans-serif; font-size:0.875rem; font-weight:700; color:rgba(255,255,255,0.5); }
.sc-footer-brand .hi { color:#0EA5E9; }
.sc-footer-links { display:flex; gap:1.5rem; }
.sc-footer-links a { font-size:0.8125rem; color:rgba(255,255,255,0.4); text-decoration:none; cursor:pointer; transition:color 0.15s; }
.sc-footer-links a:hover { color:rgba(255,255,255,0.8); }

@media (max-width:860px) {
  .sc-nav { display:none; }
  .sc-tour-btn span { display:none; }
}
@media (max-width:600px) {
  .sc-header { padding:0 1rem; }
  .sc-logo-sub { display:none; }
  .sc-avatar-name { display:none; }
  .sc-footer { flex-direction:column; text-align:center; }
  .sc-footer-links { gap:1rem; flex-wrap:wrap; justify-content:center; }
}
@media print { .sc-header, .sc-footer { display:none !important; } }
`;

const IconPlane = ({ size = 20, color = "white" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5L21 16z"/></svg>
);
const IconCompass = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16.2 7.8l-2.9 6.4-6.4 2.9 2.9-6.4 6.4-2.9z"/></svg>);
const IconBell = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8a6 6 0 00-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 01-3.4 0"/></svg>);
const IconUser = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>);
const IconHeart = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 00-7.8 7.8l1.1 1L12 21l7.7-7.6 1.1-1a5.5 5.5 0 000-7.8z"/></svg>);
const IconTrips = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"/></svg>);
const IconLogout = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/></svg>);

const NAV = [
  { key: "home",      icon: "🏠", label: "Trang chủ" },
  { key: "plan",      icon: "📅", label: "Lập kế hoạch" },
  { key: "flight",    icon: "✈️", label: "Vé máy bay" },
  { key: "hotel",     icon: "🏨", label: "Khách sạn" },
  { key: "community", icon: "👥", label: "Cộng đồng" },
  { key: "ai",        icon: "🤖", label: "Trợ lý AI" },
];
const ROUTES = { home: "/", plan: "/plan", flight: "/flights" };

function getUser() {
  try { return JSON.parse(localStorage.getItem("tb_user") || sessionStorage.getItem("tb_user") || "null"); }
  catch { return null; }
}

export function SiteHeader({ active = "home", onStartTour }) {
  const navigate = useNavigate();
  const user = getUser();
  const fullName = user?.full_name || "Traveler";
  const firstName = fullName.trim().split(" ").slice(-1)[0];
  const initials = fullName.trim().split(" ").slice(-2).map((s) => s[0]).join("").toUpperCase();

  const [menuOpen, setMenuOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    const h = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setMenuOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const onNav = (n) => {
    if (n.key === active) return;
    if (ROUTES[n.key]) navigate(ROUTES[n.key]);
    else toast(`Trang "${n.label}" đang được thiết kế — sẽ sớm ra mắt!`);
  };
  const logout = () => {
    ["tb_token", "tb_user"].forEach((k) => { localStorage.removeItem(k); sessionStorage.removeItem(k); });
    navigate("/login");
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />
      <header className="sc-header">
        <div className="sc-logo" onClick={() => navigate("/")}>
          <div className="sc-logo-mark"><IconPlane size={20} /></div>
          <div>
            <span className="sc-logo-name">TravelBuddy</span>
          </div>
        </div>

        <nav className="sc-nav">
          {NAV.map((n) => (
            <button key={n.key} data-nav={n.key} className={"sc-nav-item" + (n.key === active ? " active" : "")} onClick={() => onNav(n)}>
              <span>{n.icon}</span><span>{n.label}</span>
            </button>
          ))}
        </nav>

        <div className="sc-right">
          <button className="sc-tour-btn" onClick={onStartTour || (() => { try { localStorage.setItem("tb_force_tour", "1"); } catch (e) {} navigate("/"); })}>
            <IconCompass /><span>Xem hướng dẫn</span>
          </button>
          <button className="sc-icon-btn" onClick={() => toast("Bạn chưa có thông báo mới")}>
            <IconBell /><span className="sc-dot" />
          </button>
          <div className="sc-avatar-wrap" ref={wrapRef}>
            <button className="sc-avatar" data-nav="profile" onClick={() => setMenuOpen((o) => !o)}>
              <span className="sc-avatar-img">{initials}</span>
              <span className="sc-avatar-name">{firstName}</span>
            </button>
            {menuOpen && (
              <div className="sc-menu">
                <div className="sc-menu-head">
                  <div className="nm">{fullName}</div>
                  <div className="em">{user?.email || "demo@travelbuddy.local"}</div>
                </div>
                <button className="sc-menu-item" onClick={() => toast("Trang Hồ sơ đang được thiết kế")}>
                  <IconUser /> Hồ sơ của tôi
                  <span className="sc-menu-badge">{user?.level || "Explorer"}</span>
                </button>
                <button className="sc-menu-item" onClick={() => { setMenuOpen(false); navigate("/my-trips"); }}>
                  <IconTrips /> Kế hoạch của tôi
                </button>
                <button className="sc-menu-item" onClick={() => toast("Wishlist đang được thiết kế")}>
                  <IconHeart /> Wishlist của tôi
                </button>
                <button className="sc-menu-item danger" onClick={logout}>
                  <IconLogout /> Đăng xuất
                </button>
              </div>
            )}
          </div>
        </div>
      </header>
    </>
  );
}

export function SiteFooter() {
  return (
    <footer className="sc-footer">
      <div className="sc-footer-brand">
        <IconPlane size={14} color="rgba(255,255,255,0.5)" />
        <span>© 2026 <span className="hi">TravelBuddy AI</span> — Nền tảng du lịch thông minh Việt Nam</span>
      </div>
      <div className="sc-footer-links">
        <a>Về chúng tôi</a><a>Chính sách bảo mật</a><a>Điều khoản</a><a>Liên hệ</a>
      </div>
    </footer>
  );
}
