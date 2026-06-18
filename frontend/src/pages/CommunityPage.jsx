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

.cm-hero { background:linear-gradient(125deg,var(--deepest),var(--ocean) 60%,var(--sky)); padding:2.25rem 2rem 2.5rem; position:relative; overflow:hidden; }
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
.cm-act.on { color:var(--ocean); background:#EFF8FF; }

/* bình luận (tối giản) */
.cm-comments { border-top:1px solid var(--border); margin-top:0.5rem; padding-top:0.8rem; display:flex; flex-direction:column; gap:0.65rem; }
.cm-cmt { display:flex; gap:0.55rem; align-items:flex-start; }
.cm-cmt-av { width:30px; height:30px; border-radius:50%; flex-shrink:0; display:flex; align-items:center; justify-content:center; color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.6875rem; }
.cm-cmt-body { background:#F1F5F9; border-radius:12px; padding:0.45rem 0.75rem; font-size:0.8125rem; line-height:1.45; min-width:0; flex:1; }
.cm-cmt-nm { font-family:'Nunito',sans-serif; font-weight:800; margin-right:0.4rem; }
.cm-cmt-tx { color:#1E293B; }
.cm-cmt-tm { display:block; font-size:0.6875rem; color:var(--muted); margin-top:0.15rem; }
.cm-cmt-foot { display:flex; gap:0.4rem; margin-top:0.2rem; padding-left:0.1rem; }
.cm-reply-btn { border:none; background:none; font-size:0.6875rem; font-weight:700; color:var(--muted); cursor:pointer; padding:0.15rem 0.45rem; border-radius:6px; transition:all 0.12s; }
.cm-reply-btn:hover { color:var(--ocean); background:#EFF8FF; }
.cm-replies { margin-left:2.4rem; padding-left:0.625rem; border-left:2px solid var(--border); display:flex; flex-direction:column; gap:0.45rem; margin-top:0.25rem; }
.cm-replies .cm-cmt-av { width:24px; height:24px; font-size:0.5625rem; }
.cm-reply-input-wrap { margin-top:0.35rem; margin-left:2.4rem; display:flex; gap:0.45rem; align-items:center; }
.cm-reply-input-wrap .cm-cmt-av { width:24px; height:24px; font-size:0.5625rem; }
.cm-reply-input-wrap input { flex:1; border:1.5px solid var(--border); border-radius:100px; padding:0.4rem 0.75rem; font-family:inherit; font-size:0.8rem; outline:none; transition:border-color 0.15s; }
.cm-reply-input-wrap input:focus { border-color:var(--sky); }
.cm-reply-input-wrap button { flex-shrink:0; border:none; border-radius:100px; padding:0.4rem 0.85rem; background:var(--ocean); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.75rem; cursor:pointer; white-space:nowrap; }
.cm-reply-input-wrap button:disabled { opacity:0.5; }
.cm-cmt-empty { font-size:0.8125rem; color:var(--muted); }
.cm-cmt-input { display:flex; gap:0.5rem; align-items:center; }
.cm-cmt-input input { flex:1; border:1.5px solid var(--border); border-radius:100px; padding:0.5rem 0.9rem; font-family:inherit; font-size:0.8125rem; outline:none; transition:border-color 0.15s; }
.cm-cmt-input input:focus { border-color:var(--sky); }
.cm-cmt-input button { flex-shrink:0; border:none; border-radius:100px; padding:0.5rem 1.05rem; background:var(--ocean); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; cursor:pointer; }
.cm-cmt-input button:hover { background:var(--deep); }
.cm-cmt-input button:disabled { opacity:0.5; cursor:not-allowed; }

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

/* ── ảnh: composer + thư viện bài + lightbox ── */
.cm-photo-btn { display:inline-flex; align-items:center; gap:0.35rem; border:1.5px solid var(--border); background:#fff; border-radius:9px; padding:0.4rem 0.7rem; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; color:var(--ocean); cursor:pointer; transition:all 0.15s; }
.cm-photo-btn:hover { border-color:var(--sky); background:#F0F9FF; }
.cm-thumbs { display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.6rem; }
.cm-thumb { position:relative; width:74px; height:74px; border-radius:10px; overflow:hidden; border:1px solid var(--border); background:#F1F5F9 center/cover no-repeat; }
.cm-thumb .x { position:absolute; top:2px; right:2px; width:20px; height:20px; border:none; border-radius:50%; background:rgba(15,23,42,0.7); color:#fff; font-size:0.75rem; line-height:1; cursor:pointer; display:flex; align-items:center; justify-content:center; }
.cm-thumb.up { display:flex; align-items:center; justify-content:center; color:var(--muted); font-size:0.7rem; }
.cm-thumb .mini-spin { width:18px; height:18px; border:2px solid var(--border); border-top-color:var(--sky); border-radius:50%; animation:cm-spin 0.7s linear infinite; }

.cm-gallery { display:grid; gap:6px; margin-bottom:0.75rem; border-radius:12px; overflow:hidden; }
.cm-gallery.n1 { grid-template-columns:1fr; }
.cm-gallery.n2 { grid-template-columns:1fr 1fr; }
.cm-gallery.n3, .cm-gallery.n4 { grid-template-columns:1fr 1fr 1fr; }
.cm-gphoto { position:relative; width:100%; aspect-ratio:4/3; background:#E2E8F0 center/cover no-repeat; cursor:zoom-in; }
.cm-gallery.n1 .cm-gphoto { aspect-ratio:16/9; }
.cm-gphoto .more { position:absolute; inset:0; background:rgba(15,23,42,0.55); color:#fff; display:flex; align-items:center; justify-content:center; font-family:'Nunito',sans-serif; font-weight:900; font-size:1.5rem; }
.cm-gphoto .save-mini { position:absolute; bottom:6px; right:6px; border:none; border-radius:100px; padding:0.3rem 0.6rem; background:rgba(255,255,255,0.92); color:var(--deep); font-family:'Nunito',sans-serif; font-weight:800; font-size:0.7rem; cursor:pointer; display:inline-flex; align-items:center; gap:0.25rem; opacity:0; transition:opacity 0.15s; }
.cm-gphoto:hover .save-mini { opacity:1; }
.cm-gphoto .save-mini.saved { opacity:1; background:#FEF3C7; color:#B45309; }

.cm-cmt-imgs { display:flex; gap:0.4rem; flex-wrap:wrap; margin-top:0.4rem; }
.cm-cmt-imgs img { width:64px; height:64px; object-fit:cover; border-radius:8px; cursor:zoom-in; border:1px solid var(--border); }
.cm-cmt-save { border:none; background:none; font-size:0.6875rem; font-weight:700; color:var(--muted); cursor:pointer; padding:0.15rem 0.45rem; border-radius:6px; transition:all 0.12s; }
.cm-cmt-save:hover { color:var(--amber); background:#FFFBEB; }
.cm-cmt-save.saved { color:#B45309; }
.cm-cmt-photo-btn { flex-shrink:0; border:none; background:none; font-size:1.1rem; cursor:pointer; padding:0 0.2rem; opacity:0.7; }
.cm-cmt-photo-btn:hover { opacity:1; }

/* lightbox */
.cm-lb { position:fixed; inset:0; z-index:400; background:rgba(15,23,42,0.92); display:flex; align-items:center; justify-content:center; padding:2rem; animation:cm-fade 0.18s; }
@keyframes cm-fade { from { opacity:0; } to { opacity:1; } }
.cm-lb img { max-width:92vw; max-height:80vh; border-radius:12px; box-shadow:0 20px 60px rgba(0,0,0,0.5); }
.cm-lb-x { position:absolute; top:1.25rem; right:1.5rem; width:42px; height:42px; border:none; border-radius:50%; background:rgba(255,255,255,0.15); color:#fff; font-size:1.5rem; cursor:pointer; }
.cm-lb-bar { position:absolute; bottom:1.5rem; left:50%; transform:translateX(-50%); display:flex; gap:0.6rem; }
.cm-lb-save { border:none; border-radius:100px; padding:0.6rem 1.2rem; background:#fff; color:var(--deep); font-family:'Nunito',sans-serif; font-weight:800; font-size:0.875rem; cursor:pointer; display:inline-flex; align-items:center; gap:0.4rem; }
.cm-lb-save.saved { background:#FEF3C7; color:#B45309; }
.cm-lb-nav { position:absolute; top:50%; transform:translateY(-50%); width:46px; height:46px; border:none; border-radius:50%; background:rgba(255,255,255,0.15); color:#fff; font-size:1.5rem; cursor:pointer; }
.cm-lb-nav.prev { left:1.5rem; } .cm-lb-nav.next { right:1.5rem; }

/* tên/avatar tác giả bấm được → mở hồ sơ */
.cm-author { cursor:pointer; }
.cm-author:hover { text-decoration:underline; }
.cm-avatar.cm-author:hover, .cm-cmt-av.cm-author:hover { text-decoration:none; filter:brightness(1.05); }

/* modal hồ sơ công khai */
.cm-pm { position:fixed; inset:0; z-index:400; background:rgba(15,23,42,0.55); display:flex; align-items:center; justify-content:center; padding:1.5rem; animation:cm-fade 0.18s; }
.cm-pm-card { width:100%; max-width:380px; background:#fff; border-radius:20px; overflow:hidden; box-shadow:0 24px 60px rgba(15,23,42,0.3); animation:cm-pm-in 0.2s ease; }
@keyframes cm-pm-in { from { opacity:0; transform:translateY(10px) scale(0.98); } to { opacity:1; transform:translateY(0) scale(1); } }
.cm-pm-banner { height:92px; background:linear-gradient(125deg,var(--deepest),var(--ocean) 60%,var(--sky)); position:relative; }
.cm-pm-x { position:absolute; top:0.6rem; right:0.7rem; width:32px; height:32px; border:none; border-radius:50%; background:rgba(255,255,255,0.25); color:#fff; font-size:1.2rem; cursor:pointer; }
.cm-pm-av { width:84px; height:84px; border-radius:50%; border:4px solid #fff; margin:-46px auto 0; display:flex; align-items:center; justify-content:center; color:#fff; font-family:'Nunito',sans-serif; font-weight:900; font-size:2rem; background-size:cover; background-position:center; }
.cm-pm-body { padding:0.5rem 1.5rem 1.5rem; text-align:center; }
.cm-pm-name { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.25rem; margin-top:0.5rem; }
.cm-pm-meta { font-size:0.8125rem; color:var(--muted); margin-top:0.2rem; }
.cm-pm-sec { text-align:left; margin-top:1.1rem; }
.cm-pm-sec h4 { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; color:var(--deep); margin-bottom:0.5rem; }
.cm-pm-bio { font-size:0.875rem; color:#334155; line-height:1.55; background:#F8FAFC; border-radius:10px; padding:0.6rem 0.8rem; }
.cm-pm-tags { display:flex; flex-wrap:wrap; gap:0.4rem; }
.cm-pm-tag { display:inline-flex; align-items:center; gap:0.3rem; padding:0.35rem 0.7rem; border-radius:100px; background:#EFF8FF; border:1px solid #BAE6FD; color:var(--deep); font-size:0.75rem; font-weight:700; }
.cm-pm-empty { font-size:0.8125rem; color:var(--muted); font-style:italic; }
.cm-pm-loading { padding:2rem; text-align:center; color:var(--muted); }

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

/* Nén & resize ảnh phía client (cạnh dài tối đa 1600px, JPEG ~0.82) trước khi upload */
function compressImage(file, maxDim = 1600, quality = 0.82) {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith("image/")) { reject(new Error("not an image")); return; }
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      let { width: w, height: h } = img;
      if (Math.max(w, h) > maxDim) { const r = maxDim / Math.max(w, h); w = Math.round(w * r); h = Math.round(h * r); }
      const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
      cv.getContext("2d").drawImage(img, 0, 0, w, h);
      const type = file.type === "image/png" ? "image/png" : "image/jpeg";
      cv.toBlob((blob) => blob ? resolve(new File([blob], file.name.replace(/\.\w+$/, type === "image/png" ? ".png" : ".jpg"), { type })) : reject(new Error("toBlob failed")), type, quality);
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("load failed")); };
    img.src = url;
  });
}

/* Upload 1 ảnh → trả URL (/api/uploads/..). Tự nén trước. */
async function uploadImage(file) {
  const token = getToken();
  let toSend = file;
  try { toSend = await compressImage(file); } catch { /* dùng file gốc nếu nén lỗi */ }
  const fd = new FormData();
  fd.append("file", toSend);
  const res = await fetch("/api/travel/uploads/image", {
    method: "POST", headers: token ? { Authorization: `Bearer ${token}` } : {}, body: fd,
  });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || "Upload thất bại"); }
  return (await res.json()).url;
}

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

/* nhãn sở thích du lịch (khớp với ProfilePage) */
const INTEREST_LABELS = {
  beach: "🏖️ Biển đảo", mountain: "⛰️ Núi rừng", food: "🍜 Ẩm thực", culture: "🏛️ Văn hoá",
  adventure: "🧗 Phiêu lưu", photo: "📸 Sống ảo", luxury: "✨ Nghỉ dưỡng", budget: "💰 Tiết kiệm",
  nightlife: "🌃 Về đêm", nature: "🌿 Thiên nhiên",
};

/* Modal hồ sơ công khai của một thành viên — xem sở thích du lịch */
function ProfileModal({ userId, onClose }) {
  const [data, setData] = useState(undefined);
  useEffect(() => {
    let alive = true;
    fetch(`/api/travel/users/${userId}`).then((r) => r.ok ? r.json() : null)
      .then((d) => { if (alive) setData(d); }).catch(() => { if (alive) setData(null); });
    return () => { alive = false; };
  }, [userId]);

  const prefs = data?.travel_preferences || {};
  const interests = Array.isArray(prefs.interests) ? prefs.interests : [];

  return (
    <div className="cm-pm" onClick={onClose}>
      <div className="cm-pm-card" onClick={(e) => e.stopPropagation()}>
        <div className="cm-pm-banner"><button className="cm-pm-x" onClick={onClose}>×</button></div>
        {data === undefined ? (
          <div className="cm-pm-loading">Đang tải hồ sơ…</div>
        ) : !data ? (
          <div className="cm-pm-loading">Không tìm thấy hồ sơ.</div>
        ) : (
          <>
            <div className="cm-pm-av" style={data.avatar_url
              ? { backgroundImage: `url(${data.avatar_url})` }
              : { background: avGrad(data.full_name) }}>
              {!data.avatar_url && initials(data.full_name)}
            </div>
            <div className="cm-pm-body">
              <div className="cm-pm-name">{data.full_name}</div>
              <div className="cm-pm-meta">{data.post_count > 0 ? `${data.post_count} bài chia sẻ` : "Thành viên cộng đồng"}</div>

              {prefs.bio && (
                <div className="cm-pm-sec"><h4>Giới thiệu</h4><div className="cm-pm-bio">{prefs.bio}</div></div>
              )}
              <div className="cm-pm-sec">
                <h4>🎯 Sở thích du lịch</h4>
                {interests.length ? (
                  <div className="cm-pm-tags">
                    {interests.map((k) => <span key={k} className="cm-pm-tag">{INTEREST_LABELS[k] || k}</span>)}
                  </div>
                ) : (
                  <div className="cm-pm-empty">Thành viên này chưa cập nhật sở thích.</div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

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
  const [photos, setPhotos] = useState([]);        // ảnh đính kèm bài (URL đã upload)
  const [uploading, setUploading] = useState(0);    // số ảnh đang upload

  /* lightbox xem ảnh: { imgs:[], idx } */
  const [lightbox, setLightbox] = useState(null);
  /* modal hồ sơ công khai của tác giả */
  const [profileId, setProfileId] = useState(null);

  /* bình luận */
  const [openC, setOpenC] = useState(() => new Set());
  const [cmts, setCmts] = useState({});
  const [cdraft, setCdraft] = useState({});
  const [csending, setCsending] = useState(false);
  /* trả lời bình luận */
  const [replyTo, setReplyTo] = useState(() => new Set());
  const [rdraft, setRdraft] = useState({});
  const [rsending, setRsending] = useState(false);

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

  /* nạp danh sách "hữu ích" đã lưu → đánh dấu các bài đã lưu (đồng bộ đa thiết bị) */
  useEffect(() => {
    const token = getToken();
    if (!token) return;
    fetch("/api/travel/community/saved", { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.ok ? r.json() : { items: [] })
      .then((d) => {
        const ids = (d.items || []).filter((it) => it.kind === "post").map((it) => it.review_id);
        if (ids.length) setLiked((prev) => { const n = new Set(prev); ids.forEach((id) => n.add(id)); return n; });
      }).catch(() => {});
  }, []);

  const selectedTrip = savedTrips.find((t) => String(t.id) === String(tripId));

  /* upload nhiều ảnh cho composer */
  const onPickPhotos = async (e) => {
    const files = [...(e.target.files || [])]; e.target.value = "";
    if (!files.length) return;
    const room = Math.max(0, 6 - photos.length);
    if (!room) { toast("Tối đa 6 ảnh mỗi bài"); return; }
    setUploading((n) => n + Math.min(room, files.length));
    for (const f of files.slice(0, room)) {
      try { const url = await uploadImage(f); setPhotos((p) => [...p, url]); }
      catch (err) { toast(err.message || "Upload ảnh thất bại"); }
      finally { setUploading((n) => Math.max(0, n - 1)); }
    }
  };

  const openProfile = (uid) => { if (uid) setProfileId(uid); };

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
        body: JSON.stringify({ destination_slug: destSlug, content, rating, trip_data: snap, images: photos }),
      });
      if (res.status === 401) { toast("Phiên đăng nhập đã hết hạn — vui lòng đăng nhập lại."); navigate("/login"); return; }
      if (!res.ok) throw new Error();
      const post = await res.json();
      if (!filterDest || filterDest === post.destination_slug) setPosts((p) => [post, ...p]);
      setDraft(""); setRating(5); setPhotos([]);
      toast("✅ Đã chia sẻ lịch trình lên cộng đồng!");
    } catch {
      toast("Đăng bài thất bại. Thử lại sau.");
    } finally {
      setPosting(false);
    }
  };

  /* "Hữu ích" — toggle bật/tắt như thả cảm xúc. Bật = lưu vào Wishlist, tắt = gỡ. */
  const toggleHelpful = async (post) => {
    const token = getToken();
    if (!token) { toast("Đăng nhập để dùng tính năng này"); navigate("/login"); return; }
    const wasLiked = liked.has(post.id);
    const delta = wasLiked ? -1 : 1;
    // optimistic
    setPosts((p) => p.map((x) => x.id === post.id ? { ...x, helpful_count: Math.max(0, (x.helpful_count || 0) + delta) } : x));
    const next = new Set(liked);
    if (wasLiked) next.delete(post.id); else next.add(post.id);
    setLiked(next);
    localStorage.setItem("tb_liked_posts", JSON.stringify([...next]));
    try {
      const res = await fetch(`/api/travel/community/posts/${post.id}/helpful`, {
        method: wasLiked ? "DELETE" : "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) { toast("Phiên đăng nhập đã hết hạn"); navigate("/login"); return; }
      if (!res.ok) throw new Error();
      const d = await res.json().catch(() => ({}));
      if (typeof d.helpful_count === "number") {
        setPosts((p) => p.map((x) => x.id === post.id ? { ...x, helpful_count: d.helpful_count } : x));
      }
    } catch {
      // rollback
      setPosts((p) => p.map((x) => x.id === post.id ? { ...x, helpful_count: Math.max(0, (x.helpful_count || 0) - delta) } : x));
      const back = new Set(liked);
      if (wasLiked) back.add(post.id); else back.delete(post.id);
      setLiked(back);
      localStorage.setItem("tb_liked_posts", JSON.stringify([...back]));
      toast("Có lỗi, thử lại sau");
    }
  };

  const toggleComments = (pid) => {
    setOpenC((prev) => { const n = new Set(prev); n.has(pid) ? n.delete(pid) : n.add(pid); return n; });
    if (cmts[pid] === undefined) {
      fetch(`/api/travel/community/posts/${pid}/comments`).then((r) => r.json())
        .then((d) => setCmts((m) => ({ ...m, [pid]: d.items || [] }))).catch(() => {});
    }
  };

  const submitComment = async (pid, parentId = null) => {
    const content = (parentId ? (rdraft[parentId] || "") : (cdraft[pid] || "")).trim();
    if (!content) return;
    const token = getToken();
    if (!token) { toast("Bạn cần đăng nhập để bình luận"); navigate("/login"); return; }
    if (parentId) setRsending(true); else setCsending(true);
    try {
      const res = await fetch(`/api/travel/community/posts/${pid}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ content, parent_id: parentId || null }),
      });
      if (res.status === 401) { toast("Phiên đăng nhập đã hết hạn — vui lòng đăng nhập lại."); navigate("/login"); return; }
      if (!res.ok) throw new Error();
      const c = await res.json();
      setCmts((m) => ({ ...m, [pid]: [...(m[pid] || []), c] }));
      if (parentId) {
        setRdraft((d) => ({ ...d, [parentId]: "" }));
        setReplyTo((r) => { const n = new Set(r); n.delete(parentId); return n; });
      } else {
        setCdraft((d) => ({ ...d, [pid]: "" }));
      }
      setPosts((ps) => ps.map((x) => x.id === pid ? { ...x, comment_count: (x.comment_count || 0) + 1 } : x));
    } catch { toast("Không gửi được bình luận"); }
    finally { if (parentId) setRsending(false); else setCsending(false); }
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
                      {(photos.length > 0 || uploading > 0) && (
                        <div className="cm-thumbs">
                          {photos.map((url, i) => (
                            <div key={url} className="cm-thumb" style={{ backgroundImage: `url(${url})` }}>
                              <button className="x" onClick={() => setPhotos((p) => p.filter((_, j) => j !== i))} title="Gỡ ảnh">×</button>
                            </div>
                          ))}
                          {Array.from({ length: uploading }).map((_, i) => (
                            <div key={"up" + i} className="cm-thumb up"><span className="mini-spin" /></div>
                          ))}
                        </div>
                      )}
                      <div className="cm-comp-tools">
                        <div className="cm-rate" title="Đánh giá chuyến đi">
                          {[1, 2, 3, 4, 5].map((n) => (
                            <span key={n} className={"st" + (n <= rating ? " on" : "")} onClick={() => setRating(n)}>★</span>
                          ))}
                        </div>
                        <label className="cm-photo-btn">
                          📷 Thêm ảnh
                          <input type="file" accept="image/*" multiple hidden onChange={onPickPhotos} />
                        </label>
                        <button className="cm-post-btn" onClick={submitPost} disabled={posting || uploading > 0}>{posting ? "Đang đăng…" : "Chia sẻ"}</button>
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
                    <div className="cm-avatar cm-author" style={{ background: avGrad(p.author_name), width: 40, height: 40 }}
                      onClick={() => openProfile(p.author_id)} title="Xem hồ sơ">{initials(p.author_name)}</div>
                    <div>
                      <div className="nm"><span className="cm-author" onClick={() => openProfile(p.author_id)}>{p.author_name}</span></div>
                      <div className="sub">
                        {timeAgo(p.created_at)}
                        {p.destination_name && <>· <span className="cm-dest" onClick={() => setFilterDest(p.destination_slug)}>📍 {p.destination_name}</span></>}
                      </div>
                    </div>
                    {p.rating > 0 && <div className="cm-post-rate">{starStr(p.rating)}</div>}
                  </div>

                  <div className="cm-post-body">{p.content}</div>

                  {Array.isArray(p.images) && p.images.length > 0 && (
                    <div className={`cm-gallery n${Math.min(p.images.length, 4)}`}>
                      {p.images.slice(0, 4).map((url, i) => (
                        <div key={url} className="cm-gphoto" style={{ backgroundImage: `url(${url})` }}
                          onClick={() => setLightbox({ imgs: p.images, idx: i })}>
                          {i === 3 && p.images.length > 4 && <div className="more">+{p.images.length - 4}</div>}
                        </div>
                      ))}
                    </div>
                  )}

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
                    <button className={"cm-act" + (liked.has(p.id) ? " liked" : "")} onClick={() => toggleHelpful(p)}
                      title={liked.has(p.id) ? "Bỏ hữu ích (gỡ khỏi Wishlist)" : "Thấy hữu ích → lưu vào Wishlist"}>
                      {liked.has(p.id) ? "❤️" : "🤍"} Hữu ích {p.helpful_count > 0 && `· ${p.helpful_count}`}
                    </button>
                    <button className={"cm-act" + (openC.has(p.id) ? " on" : "")} onClick={() => toggleComments(p.id)}>
                      💬 Bình luận {p.comment_count > 0 && `· ${p.comment_count}`}
                    </button>
                  </div>

                  {openC.has(p.id) && (() => {
                    const allCmts = cmts[p.id] || [];
                    const topLevel = allCmts.filter((c) => !c.parent_id);
                    const byParent = allCmts.reduce((m, c) => { if (c.parent_id) { (m[c.parent_id] = m[c.parent_id] || []).push(c); } return m; }, {});
                    return (
                      <div className="cm-comments">
                        {cmts[p.id] !== undefined && allCmts.length === 0 && <div className="cm-cmt-empty">Chưa có bình luận. Hãy là người đầu tiên!</div>}
                        {topLevel.map((c) => (
                          <div key={c.id}>
                            <div className="cm-cmt">
                              <div className="cm-cmt-av cm-author" style={{ background: avGrad(c.author_name) }}
                                onClick={() => openProfile(c.author_id)} title="Xem hồ sơ">{initials(c.author_name)}</div>
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div className="cm-cmt-body">
                                  <span className="cm-cmt-nm cm-author" onClick={() => openProfile(c.author_id)}>{c.author_name}</span>
                                  <span className="cm-cmt-tx">{c.content}</span>
                                  <span className="cm-cmt-tm">{timeAgo(c.created_at)}</span>
                                </div>
                                <div className="cm-cmt-foot">
                                  <button className="cm-reply-btn" onClick={() => setReplyTo((r) => { const n = new Set(r); n.has(c.id) ? n.delete(c.id) : n.add(c.id); return n; })}>
                                    {replyTo.has(c.id) ? "Huỷ" : "Trả lời"}
                                  </button>
                                </div>
                              </div>
                            </div>
                            {(byParent[c.id] || []).length > 0 && (
                              <div className="cm-replies">
                                {(byParent[c.id] || []).map((r) => (
                                  <div key={r.id} className="cm-cmt">
                                    <div className="cm-cmt-av cm-author" style={{ background: avGrad(r.author_name) }}
                                      onClick={() => openProfile(r.author_id)} title="Xem hồ sơ">{initials(r.author_name)}</div>
                                    <div className="cm-cmt-body">
                                      <span className="cm-cmt-nm cm-author" onClick={() => openProfile(r.author_id)}>{r.author_name}</span>
                                      <span className="cm-cmt-tx">{r.content}</span>
                                      <span className="cm-cmt-tm">{timeAgo(r.created_at)}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                            {replyTo.has(c.id) && (
                              <div className="cm-reply-input-wrap">
                                <div className="cm-cmt-av" style={{ background: avGrad(user?.full_name) }}>{initials(user?.full_name)}</div>
                                <input value={rdraft[c.id] || ""}
                                  onChange={(e) => setRdraft((d) => ({ ...d, [c.id]: e.target.value }))}
                                  onKeyDown={(e) => { if (e.key === "Enter") submitComment(p.id, c.id); }}
                                  placeholder={`Trả lời ${c.author_name.trim().split(" ").slice(-1)[0]}...`}
                                  maxLength={1000} autoFocus />
                                <button onClick={() => submitComment(p.id, c.id)} disabled={rsending}>Gửi</button>
                              </div>
                            )}
                          </div>
                        ))}
                        <div className="cm-cmt-input">
                          <div className="cm-cmt-av" style={{ background: avGrad(user?.full_name) }}>{initials(user?.full_name)}</div>
                          <input value={cdraft[p.id] || ""} onChange={(e) => setCdraft((d) => ({ ...d, [p.id]: e.target.value }))}
                            onKeyDown={(e) => { if (e.key === "Enter") submitComment(p.id); }} placeholder="Viết bình luận..." maxLength={1000} />
                          <button onClick={() => submitComment(p.id)} disabled={csending}>Gửi</button>
                        </div>
                      </div>
                    );
                  })()}
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

      {lightbox && (() => {
        const { imgs, idx } = lightbox;
        const url = imgs[idx];
        return (
          <div className="cm-lb" onClick={() => setLightbox(null)}>
            <button className="cm-lb-x" onClick={() => setLightbox(null)}>×</button>
            {imgs.length > 1 && (
              <button className="cm-lb-nav prev" onClick={(e) => { e.stopPropagation(); setLightbox((l) => ({ ...l, idx: (l.idx - 1 + imgs.length) % imgs.length })); }}>‹</button>
            )}
            <img src={url} alt="" onClick={(e) => e.stopPropagation()} />
            {imgs.length > 1 && (
              <button className="cm-lb-nav next" onClick={(e) => { e.stopPropagation(); setLightbox((l) => ({ ...l, idx: (l.idx + 1) % imgs.length })); }}>›</button>
            )}
          </div>
        );
      })()}

      {profileId && <ProfileModal userId={profileId} onClose={() => setProfileId(null)} />}

      <SiteFooter />
    </>
  );
}
