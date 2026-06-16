import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { SiteHeader, SiteFooter } from "../components/SiteChrome";
import { toast } from "../components/dialog";

/* ════════════════════════════════════════════════════════════
   TravelBuddy — Cộng đồng Traveler
   Mạng xã hội du lịch thu nhỏ, tổ chức theo điểm đến.
   Mỗi bài viết BẮT BUỘC gắn với một lịch trình người dùng đã tạo
   (đính kèm để cộng đồng xem & tải PDF tham khảo).
   Data đồng bộ thật từ BE (bảng reviews + trip_data JSONB):
     GET  /api/travel/community/posts
     POST /api/travel/community/posts                 (cần đăng nhập + trip_data)
     POST /api/travel/community/posts/{id}/helpful
═══════════════════════════════════════════════════════════════ */

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Inter',-apple-system,sans-serif; background:#F0F9FF; color:#0F172A; -webkit-font-smoothing:antialiased; }
:root {
  --sky:#0EA5E9; --ocean:#0284C7; --deep:#0369A1; --deepest:#075985;
  --sunset:#F97316; --coral:#FB7185; --green:#10B981; --amber:#F59E0B; --violet:#7C3AED;
  --muted:#64748B; --border:#E2E8F0;
}
.cm-wrap { min-height:calc(100vh - 64px); }

.cm-hero { background:linear-gradient(125deg,#5B21B6,var(--ocean) 55%,var(--sky)); padding:2.25rem 2rem 2.5rem; position:relative; overflow:hidden; }
.cm-hero::before { content:''; position:absolute; inset:0; background-image:radial-gradient(circle,rgba(255,255,255,0.08) 1.5px,transparent 1.5px); background-size:26px 26px; }
.cm-hero-in { max-width:1000px; margin:0 auto; position:relative; z-index:2; }
.cm-hero h1 { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.875rem; color:#fff; letter-spacing:-0.02em; }
.cm-hero p { color:rgba(255,255,255,0.85); font-size:0.9375rem; margin-top:0.3rem; max-width:580px; }

.cm-main { max-width:1000px; margin:0 auto; padding:1.5rem 2rem 3.5rem; display:grid; grid-template-columns:minmax(0,1fr) 280px; gap:1.5rem; align-items:start; }

/* composer */
.cm-composer { background:#fff; border:1px solid var(--border); border-radius:16px; box-shadow:0 4px 16px rgba(15,23,42,0.05); padding:1.125rem; margin-bottom:1.25rem; }
.cm-comp-top { display:flex; gap:0.75rem; align-items:flex-start; }
.cm-avatar { width:42px; height:42px; border-radius:50%; flex-shrink:0; display:flex; align-items:center; justify-content:center; color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; }
.cm-comp-ta { flex:1; min-width:0; }
.cm-comp-ta textarea { width:100%; border:1.5px solid var(--border); border-radius:12px; padding:0.7rem 0.85rem; font-family:inherit; font-size:0.9375rem; resize:vertical; min-height:62px; outline:none; transition:all 0.15s; }
.cm-comp-ta textarea:focus { border-color:var(--sky); box-shadow:0 0 0 3px rgba(14,165,233,0.1); }
.cm-trip-pick { display:flex; align-items:center; gap:0.5rem; margin-top:0.6rem; background:#F0F9FF; border:1px solid #BAE6FD; border-radius:11px; padding:0.5rem 0.65rem; flex-wrap:wrap; }
.cm-trip-pick .lab { font-size:0.75rem; font-weight:800; color:var(--deep); display:flex; align-items:center; gap:0.3rem; }
.cm-trip-pick select { flex:1; min-width:160px; border:1.5px solid var(--border); border-radius:9px; padding:0.4rem 0.55rem; font-family:inherit; font-size:0.8125rem; font-weight:600; background:#fff; outline:none; cursor:pointer; }
.cm-comp-tools { display:flex; align-items:center; gap:0.75rem; margin-top:0.7rem; flex-wrap:wrap; }
.cm-rate { display:flex; align-items:center; gap:0.15rem; }
.cm-rate .st { font-size:1.25rem; color:#CBD5E1; cursor:pointer; line-height:1; transition:color 0.1s; }
.cm-rate .st.on { color:var(--amber); }
.cm-post-btn { margin-left:auto; border:none; border-radius:10px; padding:0.55rem 1.3rem; background:var(--ocean); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.875rem; cursor:pointer; transition:background 0.15s; }
.cm-post-btn:hover { background:var(--deep); }
.cm-post-btn:disabled { opacity:0.55; cursor:not-allowed; }
.cm-noplan { display:flex; align-items:center; gap:0.75rem; background:#FFFBEB; border:1px solid #FDE68A; border-radius:11px; padding:0.75rem 0.9rem; margin-top:0.6rem; font-size:0.875rem; color:#92400E; }
.cm-noplan button { margin-left:auto; border:none; border-radius:9px; padding:0.45rem 0.9rem; background:var(--ocean); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; cursor:pointer; white-space:nowrap; }
.cm-shared { margin-top:0.6rem; background:#ECFDF5; border:1px solid #6EE7B7; color:#047857; border-radius:11px; padding:0.6rem 0.8rem; font-size:0.8125rem; line-height:1.45; }

/* filter bar */
.cm-filters { display:flex; align-items:center; gap:0.5rem; margin-bottom:1rem; flex-wrap:wrap; }
.cm-seg { display:inline-flex; background:#E7EEF5; border-radius:10px; padding:0.2rem; }
.cm-seg button { border:none; background:none; padding:0.4rem 0.85rem; border-radius:8px; font-family:inherit; font-size:0.8125rem; font-weight:700; color:var(--muted); cursor:pointer; transition:all 0.15s; }
.cm-seg button.on { background:#fff; color:var(--ocean); box-shadow:0 1px 4px rgba(15,23,42,0.1); }
.cm-filters .dsel { margin-left:auto; }
.cm-filters select { padding:0.45rem 0.7rem; border:1.5px solid var(--border); border-radius:10px; font-family:inherit; font-size:0.8125rem; font-weight:700; background:#fff; cursor:pointer; }

/* post card */
.cm-post { background:#fff; border:1px solid var(--border); border-radius:16px; box-shadow:0 2px 12px rgba(15,23,42,0.05); padding:1.125rem 1.25rem; transition:box-shadow 0.15s; }
.cm-post + .cm-post { margin-top:1rem; }
.cm-post:hover { box-shadow:0 8px 22px rgba(15,23,42,0.08); }
.cm-post-head { display:flex; align-items:center; gap:0.7rem; }
.cm-post-head .nm { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; display:flex; align-items:center; gap:0.4rem; }
.cm-lv { font-size:0.625rem; font-weight:800; color:var(--violet); background:#F3E8FF; padding:0.1rem 0.45rem; border-radius:100px; }
.cm-post-head .sub { font-size:0.75rem; color:var(--muted); display:flex; align-items:center; gap:0.4rem; flex-wrap:wrap; }
.cm-dest { display:inline-flex; align-items:center; gap:0.2rem; font-weight:700; color:var(--ocean); cursor:pointer; }
.cm-dest:hover { text-decoration:underline; }
.cm-post-rate { margin-left:auto; color:var(--amber); font-size:0.875rem; letter-spacing:-1px; white-space:nowrap; }
.cm-post-body { font-size:0.9375rem; line-height:1.6; color:#1E293B; margin:0.75rem 0; white-space:pre-wrap; }

/* attached trip card */
.cm-trip { display:flex; align-items:center; gap:0.875rem; background:linear-gradient(120deg,#F0F9FF,#ECFEFF); border:1px solid #BAE6FD; border-radius:13px; padding:0.8rem 0.95rem; margin-bottom:0.75rem; }
.cm-trip-ic { width:42px; height:42px; flex-shrink:0; border-radius:11px; background:linear-gradient(135deg,var(--sky),var(--ocean)); display:flex; align-items:center; justify-content:center; font-size:1.25rem; }
.cm-trip-info { flex:1; min-width:0; }
.cm-trip-info .t { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.875rem; color:var(--deep); }
.cm-trip-info .m { font-size:0.75rem; color:var(--muted); margin-top:0.1rem; }
.cm-trip-pdf { flex-shrink:0; display:inline-flex; align-items:center; gap:0.35rem; border:1.5px solid var(--ocean); border-radius:9px; padding:0.45rem 0.8rem; background:#fff; color:var(--ocean); font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; cursor:pointer; transition:all 0.15s; }
.cm-trip-pdf:hover { background:var(--ocean); color:#fff; }

.cm-post-foot { display:flex; align-items:center; gap:0.4rem; border-top:1px solid var(--border); padding-top:0.7rem; }
.cm-act { display:inline-flex; align-items:center; gap:0.4rem; padding:0.45rem 0.8rem; border:none; background:none; border-radius:9px; font-family:inherit; font-size:0.8125rem; font-weight:700; color:var(--muted); cursor:pointer; transition:all 0.15s; }
.cm-act:hover { background:#F1F5F9; color:var(--ocean); }
.cm-act.liked { color:var(--coral); }

/* sidebar */
.cm-side { display:flex; flex-direction:column; gap:1rem; position:sticky; top:80px; }
.cm-card { background:#fff; border:1px solid var(--border); border-radius:16px; padding:1.125rem; box-shadow:0 4px 16px rgba(15,23,42,0.05); }
.cm-card h3 { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; margin-bottom:0.875rem; display:flex; align-items:center; gap:0.4rem; }
.cm-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:0.5rem; text-align:center; }
.cm-stat .n { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.25rem; color:var(--ocean); }
.cm-stat .l { font-size:0.6875rem; color:var(--muted); }
.cm-trend { display:flex; flex-direction:column; gap:0.15rem; }
.cm-trend button { display:flex; align-items:center; justify-content:space-between; border:none; background:none; padding:0.5rem; border-radius:9px; font-family:inherit; font-size:0.875rem; font-weight:600; color:#334155; cursor:pointer; text-align:left; transition:background 0.12s; }
.cm-trend button:hover { background:#F1F5F9; }
.cm-trend button.on { background:#EFF8FF; color:var(--ocean); }
.cm-trend .c { font-size:0.75rem; color:var(--muted); font-weight:700; }
.cm-trend .rank { color:var(--violet); font-weight:800; margin-right:0.5rem; }

.cm-loading, .cm-empty { text-align:center; padding:3rem 1rem; color:var(--muted); background:#fff; border:1px solid var(--border); border-radius:16px; }
.cm-spin { width:32px; height:32px; border:3px solid var(--border); border-top-color:var(--sky); border-radius:50%; animation:cm-spin 0.7s linear infinite; margin:0 auto 0.875rem; }
@keyframes cm-spin { to { transform:rotate(360deg); } }
.cm-empty .ic { font-size:2.5rem; }

@media (max-width:860px) {
  .cm-main { grid-template-columns:1fr; }
  .cm-side { position:static; flex-direction:column-reverse; }
}
@media (max-width:600px) { .cm-hero, .cm-main { padding-left:1.25rem; padding-right:1.25rem; } }
`;

/* ─── helpers ─── */
const AV_GRADIENTS = [
  "linear-gradient(135deg,#F97316,#FB7185)", "linear-gradient(135deg,#0EA5E9,#0284C7)",
  "linear-gradient(135deg,#10B981,#059669)", "linear-gradient(135deg,#7C3AED,#A855F7)",
  "linear-gradient(135deg,#F59E0B,#F97316)", "linear-gradient(135deg,#EC4899,#BE185D)",
];
const avGrad = (name) => { let h = 0; for (const c of (name || "?")) h = (h * 31 + c.charCodeAt(0)) >>> 0; return AV_GRADIENTS[h % AV_GRADIENTS.length]; };
const initials = (name) => (name || "?").trim().split(" ").slice(-2).map((s) => s[0]).join("").toUpperCase();
const starStr = (r) => "★".repeat(Math.round(r || 0));
const fmtVND = (n) => (!n || n <= 0) ? "Miễn phí" : Number(n).toLocaleString("vi-VN") + "đ";
const timeAgo = (iso) => {
  const s = Math.max(1, (Date.now() - new Date(iso)) / 1000);
  if (s < 60) return "vừa xong";
  const m = s / 60; if (m < 60) return `${Math.floor(m)} phút trước`;
  const h = m / 60; if (h < 24) return `${Math.floor(h)} giờ trước`;
  const d = h / 24; if (d < 30) return `${Math.floor(d)} ngày trước`;
  const mo = d / 30; if (mo < 12) return `${Math.floor(mo)} tháng trước`;
  return `${Math.floor(mo / 12)} năm trước`;
};
function getUser() { try { return JSON.parse(localStorage.getItem("tb_user") || sessionStorage.getItem("tb_user") || "null"); } catch { return null; } }
function getToken() { return localStorage.getItem("tb_token") || sessionStorage.getItem("tb_token"); }
function getLiked() { try { return new Set(JSON.parse(localStorage.getItem("tb_liked_posts") || "[]")); } catch { return new Set(); } }
function getSavedTrips() { try { const a = JSON.parse(localStorage.getItem("tb_saved_trips") || "[]"); return Array.isArray(a) ? a : []; } catch { return []; } }

/* Trích snapshot lịch trình gọn để đính kèm bài viết */
function tripSnapshot(t) {
  return {
    destName: t.destName || t.form?.destName || "Lịch trình",
    destSlug: t.form?.destSlug || t.destSlug || "",
    days: Number(t.days || t.form?.days || 0),
    travelers: Number(t.travelers || t.form?.travelers || 1),
    startDate: t.startDate || t.form?.startDate || "",
    totalCost: Number(t.totalCost || 0),
    totalPlaces: Number(t.totalPlaces || 0),
    itinerary: t.itinerary || {},
    notes: t.notes || {},
  };
}

/* Xuất lịch trình ra PDF (mở cửa sổ in → lưu PDF) */
function printTripPdf(trip) {
  if (!trip) return;
  const w = window.open("", "_blank", "width=820,height=900");
  if (!w) { toast("Trình duyệt đang chặn cửa sổ in. Hãy cho phép pop-up."); return; }
  const days = Number(trip.days) || Object.keys(trip.itinerary || {}).length || 1;
  let body = "";
  for (let i = 0; i < days; i++) {
    const acts = (trip.itinerary?.[i] || trip.itinerary?.[String(i)] || []).slice()
      .sort((a, b) => (a.time || "").localeCompare(b.time || ""));
    body += `<div class="day"><div class="dh">Ngày ${i + 1}</div>`;
    if (!acts.length) body += `<div class="row"><span class="p">— Chưa có hoạt động —</span></div>`;
    acts.forEach((a) => {
      body += `<div class="row"><span class="t">${a.time || ""}</span><span class="n">${(a.name || "").replace(/</g, "&lt;")}</span><span class="p">${fmtVND(a.fee)}</span></div>`;
    });
    if (trip.notes?.[i] || trip.notes?.[String(i)]) body += `<div class="note">📌 ${(trip.notes[i] || trip.notes[String(i)]).replace(/</g, "&lt;")}</div>`;
    body += `</div>`;
  }
  w.document.write(`<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Lịch trình ${trip.destName}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=Inter:wght@400;600&display=swap');
    *{box-sizing:border-box;margin:0;padding:0;font-family:'Inter',sans-serif}
    body{padding:28px;color:#0F172A}
    .head{background:linear-gradient(120deg,#075985,#0284C7 70%,#0EA5E9);color:#fff;border-radius:14px;padding:22px;text-align:center}
    .head h1{font-family:'Nunito';font-weight:900;font-size:22px;letter-spacing:.3px}
    .head .sub{opacity:.9;font-size:13px;margin-top:4px}
    .day{margin-top:18px}
    .dh{font-family:'Nunito';font-weight:900;color:#0369A1;font-size:16px;border-bottom:2px solid #E2E8F0;padding-bottom:5px;margin-bottom:6px}
    .row{display:flex;gap:14px;padding:4px 0;font-size:14px}
    .row .t{font-family:'Nunito';font-weight:800;color:#0284C7;width:52px;flex-shrink:0}
    .row .n{flex:1}
    .row .p{color:#64748B;font-size:13px}
    .note{font-size:13px;color:#92400E;background:#FFFBEB;border-radius:8px;padding:6px 10px;margin-top:6px}
    .total{display:flex;justify-content:space-between;align-items:center;background:#F0F9FF;border-radius:12px;padding:14px 18px;margin-top:18px}
    .total .l{font-family:'Nunito';font-weight:800}
    .total .n{font-family:'Nunito';font-weight:900;font-size:22px;color:#0284C7}
    .ft{text-align:center;color:#94A3B8;font-size:11px;margin-top:22px}
    @media print{body{padding:0}}
  </style></head><body>
    <div class="head"><h1>LỊCH TRÌNH ${(trip.destName || "").toUpperCase()}</h1>
      <div class="sub">${days} ngày${trip.travelers ? ` · ${trip.travelers} người` : ""}${trip.startDate ? ` · Khởi hành ${trip.startDate.split("-").reverse().join("/")}` : ""}</div></div>
    ${body}
    <div class="total"><span class="l">TỔNG CHI PHÍ DỰ KIẾN</span><span class="n">${fmtVND(trip.totalCost)}</span></div>
    <div class="ft">Lịch trình chia sẻ từ Cộng đồng TravelBuddy</div>
  </body></html>`);
  w.document.close(); w.focus();
  setTimeout(() => { w.print(); }, 350);
}

const IconArrow = () => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7" /></svg>);
const IconPdf = () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6M12 18v-6M9 15l3 3 3-3" /></svg>);

export default function CommunityPage() {
  const navigate = useNavigate();
  const user = getUser();
  const [destinations, setDestinations] = useState([]);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState("recent");
  const [filterDest, setFilterDest] = useState("");
  const [liked, setLiked] = useState(getLiked);

  // lịch trình đã lưu, mới nhất lên đầu
  const [savedTrips] = useState(() => getSavedTrips().slice().sort((a, b) => new Date(b.savedAt || 0) - new Date(a.savedAt || 0)));
  const [tripId, setTripId] = useState("");
  const [sharedNew, setSharedNew] = useState(false);
  const [draft, setDraft] = useState("");
  const [rating, setRating] = useState(5);
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    fetch("/api/travel/destinations?limit=50").then((r) => r.json())
      .then((d) => setDestinations(d.items || [])).catch(() => {});
    // lọc theo điểm đến nếu vào từ HomePage (click điểm đến nổi bật)
    try {
      const dst = localStorage.getItem("tb_community_dest");
      if (dst) { setFilterDest(dst); localStorage.removeItem("tb_community_dest"); }
    } catch (e) {}
  }, []);

  /* tự chọn lịch trình vừa tạo nếu đến từ nút "Chia sẻ ngay" của trình lập kế hoạch */
  useEffect(() => {
    if (!savedTrips.length) return;
    const shared = localStorage.getItem("tb_share_trip_id");
    if (shared) {
      const found = savedTrips.find((t) => String(t.id) === String(shared));
      setTripId(String((found || savedTrips[0]).id));   // ưu tiên đúng lịch vừa tạo
      setSharedNew(true);
      localStorage.removeItem("tb_share_trip_id");
    } else {
      setTripId(String(savedTrips[0].id));               // mặc định: lịch mới nhất
    }
  }, [savedTrips]);

  const load = useCallback(() => {
    setLoading(true);
    const qs = `sort=${sort}${filterDest ? `&destination=${filterDest}` : ""}&limit=50`;
    fetch(`/api/travel/community/posts?${qs}`).then((r) => r.json())
      .then((d) => setPosts(d.items || []))
      .catch(() => toast("Không tải được bài cộng đồng"))
      .finally(() => setLoading(false));
  }, [sort, filterDest]);
  useEffect(() => { load(); }, [load]);

  const selectedTrip = savedTrips.find((t) => String(t.id) === String(tripId));

  const submitPost = async () => {
    const content = draft.trim();
    if (!selectedTrip) { toast("Chọn lịch trình bạn muốn chia sẻ"); return; }
    if (content.length < 3) { toast("Hãy viết vài dòng chia sẻ về chuyến đi nhé!"); return; }
    const token = getToken();
    if (!token) { toast("Bạn cần đăng nhập để đăng bài"); navigate("/login"); return; }
    const snap = tripSnapshot(selectedTrip);
    const destSlug = snap.destSlug || destinations.find((d) => d.name === snap.destName)?.slug;
    if (!destSlug) { toast("Lịch trình thiếu thông tin điểm đến"); return; }
    setPosting(true);
    try {
      const res = await fetch("/api/travel/community/posts", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ destination_slug: destSlug, content, rating, trip_data: snap }),
      });
      if (res.status === 401) { toast("Phiên đăng nhập đã hết hạn — vui lòng đăng nhập lại."); navigate("/login"); return; }
      if (!res.ok) throw new Error();
      const post = await res.json();
      if (!filterDest || filterDest === post.destination_slug) setPosts((p) => [post, ...p]);
      setDraft(""); setRating(5);
      toast("✅ Đã chia sẻ lịch trình lên cộng đồng!");
    } catch {
      toast("Đăng bài thất bại. Thử lại sau.");
    } finally {
      setPosting(false);
    }
  };

  const toggleHelpful = async (post) => {
    if (liked.has(post.id)) return;
    setPosts((p) => p.map((x) => x.id === post.id ? { ...x, helpful_count: (x.helpful_count || 0) + 1 } : x));
    const next = new Set(liked); next.add(post.id); setLiked(next);
    localStorage.setItem("tb_liked_posts", JSON.stringify([...next]));
    try { await fetch(`/api/travel/community/posts/${post.id}/helpful`, { method: "POST" }); } catch { /* ignore */ }
  };

  const sharePost = (post) => {
    const txt = `${post.author_name} chia sẻ lịch trình ${post.destination_name}: "${post.content}"`;
    if (navigator.clipboard) navigator.clipboard.writeText(txt).then(() => toast("Đã sao chép nội dung bài viết"));
    else toast("Chia sẻ: " + post.destination_name);
  };

  const trending = useMemo(() => {
    const m = new Map();
    posts.forEach((p) => { if (p.destination_name) m.set(p.destination_slug, { slug: p.destination_slug, name: p.destination_name, count: (m.get(p.destination_slug)?.count || 0) + 1 }); });
    return [...m.values()].sort((a, b) => b.count - a.count).slice(0, 6);
  }, [posts]);
  const totalHelpful = useMemo(() => posts.reduce((s, p) => s + (p.helpful_count || 0), 0), [posts]);

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />
      <SiteHeader active="community" />

      <div className="cm-wrap">
        <section className="cm-hero">
          <div className="cm-hero-in">
            <h1>Cộng đồng Traveler</h1>
            <p>Mỗi bài chia sẻ đều kèm <b>lịch trình thật</b> đã trải nghiệm — xem, tải PDF và lên kế hoạch cho chuyến đi của bạn.</p>
          </div>
        </section>

        <div className="cm-main">
          <div>
            {/* composer */}
            <div className="cm-composer">
              <div className="cm-comp-top">
                <div className="cm-avatar" style={{ background: avGrad(user?.full_name) }}>{initials(user?.full_name)}</div>
                <div className="cm-comp-ta">
                  <textarea placeholder={`${(user?.full_name || "Bạn").split(" ").slice(-1)[0]} ơi, chia sẻ trải nghiệm chuyến đi của bạn...`}
                    value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={2000} disabled={!savedTrips.length} />

                  {savedTrips.length === 0 ? (
                    <div className="cm-noplan">
                      <span>📋 Bạn cần lập & lưu một lịch trình trước khi chia sẻ lên cộng đồng.</span>
                      <button onClick={() => navigate("/plan")}>Lập kế hoạch</button>
                    </div>
                  ) : (
                    <>
                      <div className="cm-trip-pick">
                        <span className="lab">📋 Lịch trình đính kèm</span>
                        <select value={tripId} onChange={(e) => setTripId(e.target.value)}>
                          {savedTrips.map((t) => (
                            <option key={t.id} value={t.id}>{(t.destName || "Lịch trình")} · {t.days || t.form?.days || "?"} ngày · {fmtVND(t.totalCost)}</option>
                          ))}
                        </select>
                      </div>
                      <div className="cm-comp-tools">
                        <div className="cm-rate" title="Đánh giá chuyến đi">
                          {[1, 2, 3, 4, 5].map((n) => (
                            <span key={n} className={"st" + (n <= rating ? " on" : "")} onClick={() => setRating(n)}>★</span>
                          ))}
                        </div>
                        <button className="cm-post-btn" onClick={submitPost} disabled={posting}>{posting ? "Đang đăng…" : "Chia sẻ"}</button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* filters */}
            <div className="cm-filters">
              <div className="cm-seg">
                <button className={sort === "recent" ? "on" : ""} onClick={() => setSort("recent")}>Mới nhất</button>
                <button className={sort === "helpful" ? "on" : ""} onClick={() => setSort("helpful")}>Hữu ích nhất</button>
              </div>
              <div className="dsel">
                <select value={filterDest} onChange={(e) => setFilterDest(e.target.value)}>
                  <option value="">Tất cả điểm đến</option>
                  {destinations.map((d) => <option key={d.slug} value={d.slug}>{d.name}</option>)}
                </select>
              </div>
            </div>

            {/* feed */}
            {loading ? (
              <div className="cm-loading"><div className="cm-spin" />Đang tải bài cộng đồng…</div>
            ) : posts.length === 0 ? (
              <div className="cm-empty"><div className="ic">📝</div><p>Chưa có bài nào{filterDest ? " cho điểm đến này" : ""}. Hãy là người đầu tiên chia sẻ!</p></div>
            ) : posts.map((p) => {
              const trip = p.trip_data;
              return (
                <div key={p.id} className="cm-post">
                  <div className="cm-post-head">
                    <div className="cm-avatar" style={{ background: avGrad(p.author_name), width: 40, height: 40 }}>{initials(p.author_name)}</div>
                    <div>
                      <div className="nm">{p.author_name}{p.author_level && <span className="cm-lv">{p.author_level}</span>}</div>
                      <div className="sub">
                        {timeAgo(p.created_at)}
                        {p.destination_name && <>· <span className="cm-dest" onClick={() => setFilterDest(p.destination_slug)}>📍 {p.destination_name}</span></>}
                      </div>
                    </div>
                    {p.rating > 0 && <div className="cm-post-rate">{starStr(p.rating)}</div>}
                  </div>

                  <div className="cm-post-body">{p.content}</div>

                  {trip && (
                    <div className="cm-trip">
                      <div className="cm-trip-ic">🗺️</div>
                      <div className="cm-trip-info">
                        <div className="t">Lịch trình {trip.destName} · {trip.days} ngày</div>
                        <div className="m">{trip.totalPlaces ? `${trip.totalPlaces} địa điểm · ` : ""}Tổng dự kiến {fmtVND(trip.totalCost)}{trip.travelers ? ` · ${trip.travelers} người` : ""}</div>
                      </div>
                      <button className="cm-trip-pdf" onClick={() => printTripPdf(trip)}><IconPdf /> Tải PDF</button>
                    </div>
                  )}

                  <div className="cm-post-foot">
                    <button className={"cm-act" + (liked.has(p.id) ? " liked" : "")} onClick={() => toggleHelpful(p)}>
                      {liked.has(p.id) ? "❤️" : "🤍"} Hữu ích {p.helpful_count > 0 && `· ${p.helpful_count}`}
                    </button>
                    <button className="cm-act" onClick={() => toast("Bình luận đang được phát triển ✨")}>💬 Bình luận</button>
                    <button className="cm-act" onClick={() => sharePost(p)}>🔗 Chia sẻ</button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* SIDEBAR */}
          <aside className="cm-side">
            <div className="cm-card">
              <h3>📊 Cộng đồng</h3>
              <div className="cm-stats">
                <div className="cm-stat"><div className="n">{posts.length}</div><div className="l">bài viết</div></div>
                <div className="cm-stat"><div className="n">{trending.length}</div><div className="l">điểm đến</div></div>
                <div className="cm-stat"><div className="n">{totalHelpful}</div><div className="l">lượt hữu ích</div></div>
              </div>
            </div>

            {trending.length > 0 && (
              <div className="cm-card">
                <h3>🔥 Điểm đến được chia sẻ nhiều</h3>
                <div className="cm-trend">
                  <button className={!filterDest ? "on" : ""} onClick={() => setFilterDest("")}>
                    <span>Tất cả điểm đến</span><span className="c">{posts.length}</span>
                  </button>
                  {trending.map((t, i) => (
                    <button key={t.slug} className={filterDest === t.slug ? "on" : ""} onClick={() => setFilterDest(t.slug)}>
                      <span><span className="rank">#{i + 1}</span>{t.name}</span><span className="c">{t.count} bài</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="cm-card" style={{ background: "linear-gradient(135deg,#EFF8FF,#F0FDFA)" }}>
              <h3>💡 Mẹo chia sẻ</h3>
              <p style={{ fontSize: "0.8125rem", color: "var(--muted)", lineHeight: 1.55 }}>
                Mỗi bài viết gắn kèm lịch trình bạn đã tạo. Người khác có thể <b>tải PDF</b> để tham khảo và lên kế hoạch tương tự. Bài hữu ích sẽ giúp điểm đến lên trang chủ!
              </p>
            </div>
          </aside>
        </div>
      </div>

      <SiteFooter />
    </>
  );
}
