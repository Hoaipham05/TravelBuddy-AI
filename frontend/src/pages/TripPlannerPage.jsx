import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { SiteHeader, SiteFooter } from "../components/SiteChrome";
import { toast, confirmDialog } from "../components/dialog";

/* ════════════════════════════════════════════════════════════
   TravelBuddy — Trip Planner (Lập kế hoạch)
   4 bước: Thiết lập → Xây lịch trình → Hành trang → Xuất & Lưu
   Data đồng bộ thật từ BE: /api/travel/{destinations,pois,packing}
═══════════════════════════════════════════════════════════════ */

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --sky:#0EA5E9; --ocean:#0284C7; --deep:#0369A1; --deepest:#075985;
  --sunset:#F97316; --coral:#FB7185; --green:#10B981; --amber:#F59E0B;
  --violet:#7C3AED; --yellow:#FDE68A; --bg:#F0F9FF; --surface:#FFFFFF;
  --text:#0F172A; --muted:#64748B; --border:#E2E8F0; --dark:#0F172A;
}
html { scroll-behavior:smooth; }
body { font-family:'Inter',-apple-system,sans-serif; background:var(--bg); color:var(--text); -webkit-font-smoothing:antialiased; }

/* ─── HEADER ─── */
.tp-header { position:sticky; top:0; z-index:200; height:64px; display:flex; align-items:center; padding:0 1.75rem; gap:1.25rem; background:rgba(255,255,255,0.92); backdrop-filter:blur(20px); border-bottom:1px solid rgba(14,165,233,0.1); }
.tp-logo { display:flex; align-items:center; gap:0.625rem; cursor:pointer; flex-shrink:0; }
.tp-logo-mark { width:38px; height:38px; background:linear-gradient(135deg,var(--sky),var(--ocean)); border-radius:11px; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 14px rgba(14,165,233,0.38); color:#fff; }
.tp-logo-name { font-family:'Nunito',sans-serif; font-size:1.125rem; font-weight:800; color:var(--deep); line-height:1.2; }
.tp-logo-sub { font-size:0.6875rem; font-weight:500; color:var(--muted); letter-spacing:0.05em; text-transform:uppercase; display:block; }
.tp-nav { flex:1; display:flex; justify-content:center; gap:0.125rem; }
.tp-nav-item { display:flex; align-items:center; gap:0.375rem; padding:0.4375rem 0.8125rem; border-radius:9px; font-size:0.875rem; font-weight:600; color:var(--muted); cursor:pointer; background:none; border:none; font-family:inherit; transition:all 0.15s; }
.tp-nav-item:hover { background:rgba(14,165,233,0.08); color:var(--ocean); }
.tp-nav-item.active { background:linear-gradient(135deg,var(--sky),var(--ocean)); color:#fff; box-shadow:0 3px 10px rgba(14,165,233,0.3); }
.tp-avatar { display:flex; align-items:center; gap:0.5rem; padding:0.25rem 0.75rem 0.25rem 0.25rem; border-radius:100px; border:1.5px solid var(--border); background:#fff; cursor:pointer; flex-shrink:0; }
.tp-avatar-img { width:30px; height:30px; border-radius:50%; background:linear-gradient(135deg,var(--sunset),var(--coral)); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; font-size:0.8125rem; font-family:'Nunito',sans-serif; }
.tp-avatar-name { font-size:0.8125rem; font-weight:700; }

/* ─── STEPPER ─── */
.tp-steps-wrap { background:#fff; border-bottom:1px solid var(--border); padding:1rem 2rem; position:sticky; top:64px; z-index:150; }
.tp-steps { max-width:760px; margin:0 auto; display:flex; align-items:center; }
.tp-step { display:flex; align-items:center; gap:0.625rem; flex:1; }
.tp-step:last-child { flex:0; }
.tp-step-num { width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; flex-shrink:0; border:2px solid var(--border); background:#fff; color:var(--muted); transition:all 0.25s; }
.tp-step.active .tp-step-num { background:linear-gradient(135deg,var(--sky),var(--ocean)); border-color:transparent; color:#fff; box-shadow:0 4px 12px rgba(14,165,233,0.4); }
.tp-step.done .tp-step-num { background:var(--green); border-color:transparent; color:#fff; }
.tp-step-label { font-size:0.8125rem; font-weight:700; color:var(--muted); white-space:nowrap; }
.tp-step.active .tp-step-label { color:var(--ocean); }
.tp-step.done .tp-step-label { color:var(--green); }
.tp-step-bar { flex:1; height:2.5px; background:var(--border); margin:0 0.75rem; border-radius:2px; }
.tp-step.done .tp-step-bar { background:var(--green); }

/* ─── PAGE SHELL ─── */
.tp-main { max-width:1240px; margin:0 auto; padding:2rem; }
.tp-h2 { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.625rem; letter-spacing:-0.02em; margin-bottom:0.375rem; }
.tp-h2-sub { font-size:0.9375rem; color:var(--muted); margin-bottom:1.75rem; }

/* ─── STEP 1: SETUP FORM ─── */
.tp-setup { max-width:760px; margin:0 auto; }
.tp-card { background:#fff; border-radius:20px; box-shadow:0 10px 40px rgba(15,23,42,0.07); border:1px solid rgba(226,232,240,0.7); padding:2rem; }
.tp-grid2 { display:grid; grid-template-columns:1fr 1fr; gap:1.25rem; }
.tp-field { display:flex; flex-direction:column; gap:0.4375rem; margin-bottom:1.25rem; }
.tp-field.full { grid-column:1 / -1; }
.tp-lbl { font-size:0.8125rem; font-weight:700; color:#334155; display:flex; align-items:center; gap:0.375rem; }
.tp-lbl .req { color:var(--coral); }
.tp-input, .tp-select { width:100%; padding:0.75rem 0.875rem; border:1.5px solid var(--border); border-radius:11px; font-size:0.9375rem; font-family:inherit; color:var(--text); background:#FAFBFC; outline:none; transition:all 0.18s; }
.tp-input:focus, .tp-select:focus { border-color:var(--sky); background:#fff; box-shadow:0 0 0 3px rgba(14,165,233,0.1); }
.tp-hint { font-size:0.75rem; color:var(--muted); }

/* destination ideal-time banner */
.tp-ideal { margin-top:0.75rem; border-radius:13px; padding:0.875rem 1rem; display:flex; gap:0.75rem; align-items:flex-start; font-size:0.875rem; line-height:1.5; }
.tp-ideal.good { background:#F0FDF4; border:1px solid #86EFAC; color:#15803D; }
.tp-ideal.warn { background:#FFFBEB; border:1px solid #FDE68A; color:#B45309; }
.tp-ideal .mi { font-size:1.25rem; flex-shrink:0; }
.tp-months { display:flex; flex-wrap:wrap; gap:0.3rem; margin-top:0.4rem; }
.tp-month { font-size:0.6875rem; font-weight:700; padding:0.15rem 0.5rem; border-radius:100px; background:rgba(255,255,255,0.7); border:1px solid currentColor; }

/* style picker */
.tp-styles { display:grid; grid-template-columns:repeat(4,1fr); gap:0.75rem; }
.tp-style { border:1.5px solid var(--border); border-radius:14px; padding:1rem 0.75rem; text-align:center; cursor:pointer; transition:all 0.18s; background:#fff; }
.tp-style:hover { border-color:var(--sky); transform:translateY(-2px); }
.tp-style.on { border-color:var(--sky); background:#F0F9FF; box-shadow:0 4px 14px rgba(14,165,233,0.18); }
.tp-style .ic { font-size:1.75rem; }
.tp-style .nm { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.875rem; margin-top:0.375rem; }

.tp-prefs { display:flex; flex-wrap:wrap; gap:0.5rem; }
.tp-pref { font-size:0.8125rem; font-weight:600; padding:0.4375rem 0.875rem; border-radius:100px; border:1.5px solid var(--border); background:#fff; cursor:pointer; transition:all 0.15s; user-select:none; }
.tp-pref:hover { border-color:var(--sky); }
.tp-pref.on { background:linear-gradient(135deg,var(--sky),var(--ocean)); color:#fff; border-color:transparent; }

/* ─── BUTTONS ─── */
.tp-btn { display:inline-flex; align-items:center; justify-content:center; gap:0.5rem; padding:0.875rem 1.75rem; border-radius:12px; border:none; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; cursor:pointer; transition:transform 0.15s, box-shadow 0.15s; }
.tp-btn-primary { background:linear-gradient(135deg,var(--sky),var(--ocean)); color:#fff; box-shadow:0 6px 18px rgba(14,165,233,0.38); }
.tp-btn-primary:hover { transform:translateY(-2px); box-shadow:0 10px 26px rgba(14,165,233,0.46); }
.tp-btn-primary:disabled { opacity:0.5; cursor:not-allowed; transform:none; }
.tp-btn-ghost { background:#fff; border:1.5px solid var(--border); color:var(--muted); }
.tp-btn-ghost:hover { border-color:var(--sky); color:var(--ocean); }
.tp-btn-green { background:linear-gradient(135deg,var(--green),#059669); color:#fff; box-shadow:0 6px 18px rgba(16,185,129,0.35); }
.tp-btn-green:hover { transform:translateY(-2px); }
.tp-actions { display:flex; justify-content:space-between; gap:1rem; margin-top:1.75rem; }

/* ─── STEP 2: BUILDER ─── */
.tp-tripbar { display:flex; align-items:center; gap:1rem; flex-wrap:wrap; background:linear-gradient(120deg,var(--deepest),var(--ocean)); color:#fff; border-radius:16px; padding:1rem 1.5rem; margin-bottom:1.5rem; }
.tp-tripbar .dest { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.25rem; }
.tp-tripbar .meta { font-size:0.8125rem; color:rgba(255,255,255,0.82); }
.tp-tripbar .spacer { flex:1; }
.tp-tripbar .cost { text-align:right; }
.tp-tripbar .cost .n { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.375rem; }
.tp-tripbar .cost .l { font-size:0.6875rem; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:0.05em; }

.tp-build { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:1.5rem; align-items:start; }

/* LEFT: POI list */
.tp-panel { background:#fff; border-radius:18px; border:1px solid rgba(226,232,240,0.7); box-shadow:0 6px 20px rgba(15,23,42,0.06); min-width:0; }
.tp-panel-head { padding:1.125rem 1.25rem; border-bottom:1px solid var(--border); }
.tp-panel-title { font-family:'Nunito',sans-serif; font-weight:800; font-size:1.0625rem; display:flex; align-items:center; gap:0.5rem; }
.tp-searchbox { display:flex; align-items:center; gap:0.5rem; margin-top:0.875rem; border:1.5px solid var(--border); border-radius:10px; padding:0.5rem 0.75rem; }
.tp-searchbox input { border:none; outline:none; flex:1; font-family:inherit; font-size:0.875rem; background:none; }
.tp-searchbox svg { color:var(--muted); }
.tp-cats { display:flex; gap:0.375rem; overflow-x:auto; padding:0.75rem 1.25rem; border-bottom:1px solid var(--border); scrollbar-width:thin; }
.tp-cat { flex-shrink:0; font-size:0.75rem; font-weight:700; padding:0.375rem 0.75rem; border-radius:100px; border:1.5px solid var(--border); background:#fff; cursor:pointer; white-space:nowrap; transition:all 0.15s; }
.tp-cat:hover { border-color:var(--sky); }
.tp-cat.on { background:var(--deep); color:#fff; border-color:transparent; }
.tp-sortbar { display:flex; align-items:center; gap:0.5rem; padding:0.625rem 1.25rem; font-size:0.75rem; color:var(--muted); border-bottom:1px solid var(--border); }
.tp-sortbar select { font-family:inherit; font-size:0.75rem; font-weight:700; color:var(--text); border:1px solid var(--border); border-radius:7px; padding:0.2rem 0.4rem; background:#fff; cursor:pointer; }

.tp-poi-list { max-height:620px; overflow-y:auto; padding:0.75rem; }
.tp-poi { display:flex; gap:0.875rem; padding:0.75rem; border-radius:13px; transition:background 0.15s; }
.tp-poi:hover { background:#F8FAFC; }
.tp-poi + .tp-poi { border-top:1px solid var(--border); }
.tp-poi-thumb { width:74px; height:74px; border-radius:12px; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:1.75rem; color:#fff; position:relative; overflow:hidden; }
.tp-poi-info { flex:1; min-width:0; }
.tp-poi-name { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; line-height:1.25; margin-bottom:0.25rem; }
.tp-poi-cat { display:inline-block; font-size:0.625rem; font-weight:800; text-transform:uppercase; letter-spacing:0.03em; padding:0.1rem 0.45rem; border-radius:100px; margin-bottom:0.3rem; }
.tp-poi-meta { display:flex; flex-wrap:wrap; gap:0.625rem; font-size:0.75rem; color:var(--muted); }
.tp-poi-meta .star { color:var(--amber); font-weight:700; }
.tp-poi-add { flex-shrink:0; align-self:center; }
.tp-add-btn { border:none; border-radius:10px; padding:0.5rem 0.75rem; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; cursor:pointer; white-space:nowrap; transition:all 0.15s; background:linear-gradient(135deg,var(--sky),var(--ocean)); color:#fff; }
.tp-add-btn:hover { transform:translateY(-1px); box-shadow:0 4px 12px rgba(14,165,233,0.35); }
.tp-add-btn.added { background:#ECFDF5; color:#059669; border:1.5px solid #6EE7B7; cursor:default; }
.tp-add-btn.added:hover { transform:none; box-shadow:none; }

/* RIGHT: Smart Note */
.tp-day-tabs { display:flex; gap:0.375rem; overflow-x:auto; padding:1rem 1.25rem 0; }
.tp-day-tab { flex-shrink:0; padding:0.5rem 0.875rem; border-radius:10px 10px 0 0; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; border:1.5px solid var(--border); border-bottom:none; background:#F8FAFC; color:var(--muted); cursor:pointer; transition:all 0.15s; }
.tp-day-tab.on { background:#fff; color:var(--ocean); border-color:var(--border); position:relative; top:1px; }
.tp-day-tab .cnt { font-size:0.6875rem; opacity:0.7; }
.tp-note { padding:1.25rem; }
.tp-note-date { font-size:0.8125rem; color:var(--muted); margin-bottom:1rem; font-weight:600; }
.tp-timeline { position:relative; }
.tp-tl-item { display:flex; gap:0.625rem; padding-bottom:1rem; align-items:stretch; }
.tp-tl-time { flex-shrink:0; width:80px; padding-top:0.5rem; }
.tp-tl-time input { width:100%; border:1.5px solid var(--border); border-radius:8px; padding:0.35rem 0.4rem; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; color:var(--deep); background:#F0F9FF; cursor:pointer; }
.tp-tl-time input:focus { border-color:var(--sky); outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.12); }
.tp-tl-time input::-webkit-calendar-picker-indicator { opacity:0.5; cursor:pointer; }
.tp-tl-rail { flex-shrink:0; width:14px; position:relative; }
.tp-tl-rail .dot { position:absolute; left:0; top:14px; width:13px; height:13px; border-radius:50%; background:var(--sky); border:2.5px solid #fff; box-shadow:0 0 0 2px var(--sky); z-index:2; }
.tp-tl-item:not(:last-child) .tp-tl-rail::before { content:''; position:absolute; left:5.5px; top:24px; bottom:-1rem; width:2px; background:var(--border); }
.tp-tl-body { flex:1; min-width:0; background:#F8FAFC; border-radius:12px; padding:0.75rem 0.875rem; border:1px solid var(--border); }
.tp-tl-body.conflict { border-color:var(--coral); background:#FFF1F2; }
.tp-tl-row { display:flex; align-items:flex-start; gap:0.5rem; }
.tp-tl-name { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; flex:1; }
.tp-tl-x { background:none; border:none; color:#CBD5E1; cursor:pointer; font-size:1rem; line-height:1; padding:0.1rem; transition:color 0.15s; }
.tp-tl-x:hover { color:var(--coral); }
.tp-tl-sub { font-size:0.75rem; color:var(--muted); margin-top:0.2rem; display:flex; gap:0.75rem; flex-wrap:wrap; }
.tp-conflict-tag { font-size:0.6875rem; font-weight:800; color:var(--coral); margin-top:0.3rem; }
.tp-empty { text-align:center; padding:2.5rem 1rem; color:var(--muted); }
.tp-empty .ic { font-size:2.5rem; opacity:0.5; }
.tp-empty p { font-size:0.875rem; margin-top:0.5rem; }
.tp-note-tools { display:flex; gap:0.5rem; margin-top:0.5rem; }
.tp-tool-btn { flex:1; border:1.5px dashed var(--border); background:#fff; border-radius:10px; padding:0.625rem; font-size:0.8125rem; font-weight:700; color:var(--muted); cursor:pointer; transition:all 0.15s; }
.tp-tool-btn:hover { border-color:var(--sky); color:var(--ocean); background:#F0F9FF; }
.tp-custom-add { display:flex; gap:0.5rem; width:100%; }
.tp-custom-add input { flex:1; border:1.5px solid var(--sky); border-radius:10px; padding:0.625rem 0.75rem; font-family:inherit; font-size:0.875rem; outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.1); }
.tp-custom-ok { border:none; border-radius:10px; padding:0 1rem; background:linear-gradient(135deg,var(--sky),var(--ocean)); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; cursor:pointer; flex-shrink:0; }
.tp-custom-cancel { border:1.5px solid var(--border); border-radius:10px; padding:0 0.875rem; background:#fff; color:var(--muted); font-family:inherit; font-weight:700; font-size:0.8125rem; cursor:pointer; flex-shrink:0; }
.tp-freenote { width:100%; margin-top:1rem; border:1.5px solid var(--border); border-radius:12px; padding:0.75rem; font-family:inherit; font-size:0.875rem; resize:vertical; min-height:70px; outline:none; background:#FFFBEB; }
.tp-freenote:focus { border-color:var(--amber); }
.tp-day-cost { display:flex; align-items:center; justify-content:space-between; margin-top:1rem; padding:0.875rem 1rem; background:linear-gradient(120deg,#F0F9FF,#ECFEFF); border-radius:12px; border:1px solid #BAE6FD; }
.tp-day-cost .l { font-size:0.8125rem; font-weight:700; color:var(--deep); }
.tp-day-cost .n { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.125rem; color:var(--ocean); }

/* ─── STEP 3: PACKING ─── */
.tp-pack-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1.25rem; }
.tp-pack-col { background:#fff; border-radius:16px; border:1px solid rgba(226,232,240,0.7); box-shadow:0 6px 20px rgba(15,23,42,0.06); padding:1.25rem; }
.tp-pack-col h4 { font-family:'Nunito',sans-serif; font-weight:800; font-size:1rem; margin-bottom:0.875rem; padding-bottom:0.625rem; border-bottom:2px solid var(--border); }
.tp-pack-item { display:flex; align-items:center; gap:0.625rem; padding:0.5rem; border-radius:9px; cursor:pointer; transition:background 0.12s; }
.tp-pack-item:hover { background:#F8FAFC; }
.tp-pack-item input { width:18px; height:18px; accent-color:var(--green); cursor:pointer; flex-shrink:0; }
.tp-pack-item .nm { font-size:0.875rem; flex:1; }
.tp-pack-item.checked .nm { color:var(--muted); }
.tp-pack-item .qty { font-size:0.6875rem; font-weight:800; color:var(--ocean); background:#F0F9FF; padding:0.1rem 0.45rem; border-radius:100px; }
.tp-pack-item .note { font-size:0.6875rem; color:var(--muted); }
.tp-pack-add { display:flex; gap:0.5rem; margin-top:0.625rem; }
.tp-pack-add input { flex:1; border:1.5px solid var(--border); border-radius:8px; padding:0.4rem 0.6rem; font-family:inherit; font-size:0.8125rem; outline:none; }
.tp-pack-add button { border:none; background:var(--sky); color:#fff; border-radius:8px; padding:0 0.75rem; font-weight:800; cursor:pointer; font-size:1.125rem; }
.tp-pack-summary { background:linear-gradient(120deg,#ECFDF5,#F0FDFA); border:1px solid #6EE7B7; border-radius:14px; padding:1rem 1.25rem; margin-bottom:1.5rem; display:flex; align-items:center; gap:0.75rem; font-size:0.9375rem; color:#065F46; }

/* ─── STEP 4: EXPORT ─── */
.tp-export { max-width:820px; margin:0 auto; }
.tp-doc { background:#fff; border-radius:18px; border:1px solid var(--border); box-shadow:0 10px 40px rgba(15,23,42,0.08); overflow:hidden; }
.tp-doc-head { background:linear-gradient(120deg,var(--deepest),var(--ocean) 70%,var(--sky)); color:#fff; padding:2rem; text-align:center; position:relative; overflow:hidden; }
.tp-doc-head::before { content:''; position:absolute; inset:0; background-image:radial-gradient(circle,rgba(255,255,255,0.09) 1.5px,transparent 1.5px); background-size:24px 24px; }
.tp-doc-head > * { position:relative; z-index:2; }
.tp-doc-head h1 { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.75rem; }
.tp-doc-head .sub { color:rgba(255,255,255,0.85); margin-top:0.375rem; font-size:0.9375rem; }
.tp-doc-body { padding:1.75rem 2rem; }
.tp-doc-day { margin-bottom:1.5rem; }
.tp-doc-day-head { display:flex; align-items:center; justify-content:space-between; padding-bottom:0.5rem; border-bottom:2px solid var(--border); margin-bottom:0.75rem; }
.tp-doc-day-head .d { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.0625rem; color:var(--deep); }
.tp-doc-day-head .c { font-weight:800; color:var(--ocean); font-size:0.9375rem; }
.tp-doc-line { display:flex; gap:0.875rem; padding:0.4rem 0; font-size:0.9375rem; }
.tp-doc-line .t { font-family:'Nunito',sans-serif; font-weight:800; color:var(--ocean); width:54px; flex-shrink:0; }
.tp-doc-line .n { flex:1; }
.tp-doc-line .p { color:var(--muted); font-size:0.875rem; }
.tp-doc-total { background:linear-gradient(120deg,#F0F9FF,#ECFEFF); border-radius:14px; padding:1.25rem 1.5rem; display:flex; align-items:center; justify-content:space-between; margin-top:1rem; }
.tp-doc-total .l { font-family:'Nunito',sans-serif; font-weight:800; font-size:1.0625rem; }
.tp-doc-total .n { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.625rem; color:var(--ocean); }
.tp-doc-pack { margin-top:1.5rem; padding-top:1.25rem; border-top:2px dashed var(--border); }
.tp-doc-pack h3 { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.0625rem; margin-bottom:0.625rem; }
.tp-doc-pack-tags { display:flex; flex-wrap:wrap; gap:0.4rem; }
.tp-doc-pack-tag { font-size:0.8125rem; background:#F1F5F9; border-radius:100px; padding:0.25rem 0.75rem; }
.tp-export-actions { display:flex; flex-wrap:wrap; gap:0.75rem; justify-content:center; margin-top:1.5rem; }

/* loading */
.tp-loading { text-align:center; padding:3rem; color:var(--muted); }
.tp-spin { width:34px; height:34px; border:3px solid var(--border); border-top-color:var(--sky); border-radius:50%; animation:tp-spin 0.7s linear infinite; margin:0 auto 0.875rem; }
@keyframes tp-spin { to { transform:rotate(360deg); } }

/* toast */
.tp-toast { position:fixed; bottom:1.75rem; left:50%; transform:translateX(-50%); background:var(--dark); color:#fff; padding:0.875rem 1.5rem; border-radius:12px; font-size:0.9375rem; font-weight:600; z-index:500; box-shadow:0 12px 30px rgba(0,0,0,0.3); animation:tp-toast-in 0.3s ease; }
@keyframes tp-toast-in { from { opacity:0; transform:transl(-50%,12px); } to { opacity:1; } }

@media (max-width:980px) {
  .tp-build { grid-template-columns:1fr; }
  .tp-pack-grid { grid-template-columns:1fr; }
  .tp-nav { display:none; }
  .tp-styles { grid-template-columns:repeat(2,1fr); }
}
@media (max-width:640px) {
  .tp-main { padding:1.25rem; }
  .tp-grid2 { grid-template-columns:1fr; }
  .tp-step-label { display:none; }
  .tp-avatar-name { display:none; }
}
@media print {
  .tp-no-print { display:none !important; }
  .tp-main { padding:0; max-width:100%; }
  body { background:#fff; }
  .tp-doc { box-shadow:none; border:none; }
  /* khi in, nền gradient bị bỏ → cho tiêu đề màu xanh thương hiệu thay vì xám */
  .tp-doc-head { background:#fff !important; padding-bottom:0.75rem; }
  .tp-doc-head::before { display:none; }
  .tp-doc-head h1 { color:#0284C7 !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  .tp-doc-head .sub { color:#475569 !important; }
}
`;

/* ─── icons ─── */
const IconPlane = ({ size = 20, color = "white" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5L21 16z"/></svg>
);
const IconSearch = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>);
const IconArrow = ({ size = 15 }) => (<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>);
const IconBack = ({ size = 15 }) => (<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>);

/* ─── meta maps ─── */
const CAT = {
  beach:      { label: "Biển",          emoji: "🏖️", color: "#0EA5E9" },
  nature:     { label: "Thiên nhiên",   emoji: "🌳", color: "#10B981" },
  landmark:   { label: "Địa danh",      emoji: "🏛️", color: "#F59E0B" },
  viewpoint:  { label: "Ngắm cảnh",     emoji: "🌄", color: "#F97316" },
  market:     { label: "Chợ & Mua sắm", emoji: "🛍️", color: "#FB7185" },
  museum:     { label: "Bảo tàng",      emoji: "🖼️", color: "#8B5CF6" },
  religion:   { label: "Tâm linh",      emoji: "🛕", color: "#A855F7" },
  theme_park: { label: "Giải trí",      emoji: "🎡", color: "#EC4899" },
  park:       { label: "Công viên",     emoji: "🌲", color: "#22C55E" },
  food:       { label: "Ẩm thực",       emoji: "🍜", color: "#EF4444" },
};
const catMeta = (c) => CAT[c] || { label: "Khác", emoji: "📍", color: "#64748B" };

const STYLES = [
  { key: "beach",    ic: "🏖️", nm: "Biển",      season: "summer" },
  { key: "city",     ic: "🏙️", nm: "Thành phố", season: "dry" },
  { key: "mountain", ic: "⛰️", nm: "Núi rừng",  season: "cool" },
  { key: "general",  ic: "🌏", nm: "Tổng hợp",  season: "rainy" },
];

const ORIGINS = [
  { code: "HAN", nm: "Hà Nội" }, { code: "SGN", nm: "TP. Hồ Chí Minh" },
  { code: "DAD", nm: "Đà Nẵng" }, { code: "CXR", nm: "Nha Trang" },
  { code: "PQC", nm: "Phú Quốc" }, { code: "HUI", nm: "Huế" },
  { code: "DLI", nm: "Đà Lạt" }, { code: "HPH", nm: "Hải Phòng" },
  { code: "VCA", nm: "Cần Thơ" },
];

const PACK_CAT = {
  clothing:    "Quần áo",
  accessories: "Phụ kiện",
  health:      "Sức khỏe & Vệ sinh",
  documents:   "Giấy tờ & Thẻ",
  electronics: "Thiết bị điện tử",
  food:        "Đồ ăn vặt",
  other:       "Khác",
};
const MONTHS = ["T1","T2","T3","T4","T5","T6","T7","T8","T9","T10","T11","T12"];

/* ─── helpers ─── */
const todayStr = () => new Date().toISOString().slice(0, 10);
const pad = (n) => String(n).padStart(2, "0");
const toMin = (hhmm) => { const [h, m] = hhmm.split(":").map(Number); return h * 60 + m; };
const toHHMM = (mins) => `${pad(Math.floor((mins % 1440) / 60))}:${pad(mins % 60)}`;
const fmtVND = (n) => {
  if (!n || n <= 0) return "Miễn phí";
  if (n >= 1e6) return (n / 1e6).toFixed(n % 1e6 ? 1 : 0) + "tr";
  return Math.round(n / 1000) + "k";
};
const fmtDur = (m) => {
  if (!m) return "~1 giờ";
  if (m >= 60) return `~${(m / 60).toFixed(m % 60 ? 1 : 0)} giờ`;
  return `~${m} phút`;
};
const dayDate = (startStr, idx) => {
  const d = new Date(startStr + "T00:00:00");
  d.setDate(d.getDate() + idx);
  const wd = ["CN","Thứ 2","Thứ 3","Thứ 4","Thứ 5","Thứ 6","Thứ 7"][d.getDay()];
  return `${wd}, ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
};

function getUser() {
  try { return JSON.parse(localStorage.getItem("tb_user") || sessionStorage.getItem("tb_user") || "null"); }
  catch { return null; }
}

const DRAFT_KEY = "tb_trip_draft";

export default function TripPlannerPage() {
  const navigate = useNavigate();
  const user = getUser();
  const initials = (user?.full_name || "Demo").trim().split(" ").slice(-2).map((s) => s[0]).join("").toUpperCase();

  /* load draft */
  const draft = useMemo(() => {
    try { return JSON.parse(localStorage.getItem(DRAFT_KEY) || "null"); } catch { return null; }
  }, []);

  const [tripId, setTripId] = useState(() => draft?.tripId || Date.now());
  const [step, setStep] = useState(draft?.step || 1);
  const [destinations, setDestinations] = useState([]);
  const [form, setForm] = useState(draft?.form || {
    destSlug: "", destName: "", origin: "HAN", days: 3, startDate: todayStr(),
    style: "beach", prefs: [], travelers: 2, budget: "",
  });
  const [pois, setPois] = useState([]);
  const [loadingPois, setLoadingPois] = useState(false);
  const [activeCat, setActiveCat] = useState("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("rating");
  const [itinerary, setItinerary] = useState(draft?.itinerary || {});
  const [notes, setNotes] = useState(draft?.notes || {});
  const [activeDay, setActiveDay] = useState(0);
  const [packing, setPacking] = useState([]);
  const [packChecked, setPackChecked] = useState(draft?.packChecked || {});
  const [customPack, setCustomPack] = useState(draft?.customPack || []);
  const [customInputs, setCustomInputs] = useState({});
  const [customOpen, setCustomOpen] = useState(false);
  const [customDraft, setCustomDraft] = useState("");

  const showToast = useCallback((m) => toast(m), []);

  /* fetch destinations once */
  useEffect(() => {
    fetch("/api/travel/destinations?limit=50")
      .then((r) => r.json())
      .then((d) => setDestinations(d.items || []))
      .catch(() => showToast("Không tải được danh sách điểm đến"));
  }, [showToast]);

  /* persist draft */
  useEffect(() => {
    localStorage.setItem(DRAFT_KEY, JSON.stringify({ tripId, step, form, itinerary, notes, packChecked, customPack }));
  }, [tripId, step, form, itinerary, notes, packChecked, customPack]);

  const selectedDest = destinations.find((d) => d.slug === form.destSlug);
  const setF = (k, v) => setForm((p) => ({ ...p, [k]: v }));

  /* ideal-time check */
  const startMonth = form.startDate ? new Date(form.startDate + "T00:00:00").getMonth() + 1 : null;
  const isIdeal = selectedDest?.best_months?.includes(startMonth);

  /* ─── fetch POIs + packing when entering step 2/3 ─── */
  const loadPois = useCallback((slug) => {
    setLoadingPois(true);
    fetch(`/api/travel/pois?destination=${slug}&limit=200`)
      .then((r) => r.json())
      .then((d) => setPois(d.items || []))
      .catch(() => showToast("Không tải được địa điểm"))
      .finally(() => setLoadingPois(false));
  }, [showToast]);

  const loadPacking = useCallback(() => {
    const style = STYLES.find((s) => s.key === form.style) || STYLES[0];
    const clamp = Math.min(4, Math.max(3, Number(form.days) || 3));
    fetch(`/api/travel/packing/templates?trip_type=${form.style}&season=${style.season}&days=${clamp}`)
      .then((r) => r.json())
      .then((d) => {
        const items = (d.items || []).flatMap((t) => t.items || []);
        // dedup by item_name
        const seen = new Set();
        const uniq = items.filter((it) => { const k = it.item_name; if (seen.has(k)) return false; seen.add(k); return true; });
        setPacking(uniq);
        setPackChecked((prev) => {
          if (Object.keys(prev).length) return prev;
          const init = {};
          uniq.forEach((it) => { if (it.is_default_checked) init[it.id] = true; });
          return init;
        });
      })
      .catch(() => showToast("Không tải được gợi ý hành trang"));
  }, [form.style, form.days, showToast]);

  useEffect(() => {
    if (step >= 2 && form.destSlug && pois.length === 0 && !loadingPois) loadPois(form.destSlug);
    if (step === 3 && packing.length === 0) loadPacking();
  }, [step, form.destSlug]); // eslint-disable-line

  /* ─── itinerary ops ─── */
  const addedPoiIds = useMemo(() => {
    const s = new Set();
    Object.values(itinerary).forEach((arr) => arr.forEach((it) => it.poiId && s.add(it.poiId)));
    return s;
  }, [itinerary]);

  const dayItems = (itinerary[activeDay] || []).slice().sort((a, b) => toMin(a.time) - toMin(b.time));

  const addPoi = (poi) => {
    setItinerary((prev) => {
      const arr = (prev[activeDay] || []).slice();
      const last = arr.slice().sort((a, b) => toMin(a.time) - toMin(b.time)).pop();
      const start = last ? Math.min(toMin(last.time) + (last.dur || 120), 21 * 60) : 8 * 60;
      arr.push({
        uid: `${poi.id}-${arr.length}-${start}`,
        poiId: poi.id, name: poi.name, time: toHHMM(start),
        dur: poi.estimated_duration_min || 120,
        fee: poi.entrance_fee_amount || 0, category: poi.category,
      });
      return { ...prev, [activeDay]: arr };
    });
    showToast(`Đã thêm "${poi.name}" vào Ngày ${activeDay + 1}`);
  };

  const addCustom = () => {
    const name = customDraft.trim();
    if (!name) return;
    setItinerary((prev) => {
      const arr = (prev[activeDay] || []).slice();
      const last = arr.slice().sort((a, b) => toMin(a.time) - toMin(b.time)).pop();
      const start = last ? Math.min(toMin(last.time) + (last.dur || 120), 21 * 60) : 8 * 60;
      arr.push({ uid: `custom-${Date.now()}`, poiId: null, name, time: toHHMM(start), dur: 90, fee: 0, category: "custom" });
      return { ...prev, [activeDay]: arr };
    });
    setCustomDraft("");
  };

  const removeItem = (uid) => setItinerary((prev) => ({ ...prev, [activeDay]: (prev[activeDay] || []).filter((it) => it.uid !== uid) }));
  const editTime = (uid, time) => {
    if (!time) return; // ignore empty value while typing
    setItinerary((prev) => ({ ...prev, [activeDay]: (prev[activeDay] || []).map((it) => it.uid === uid ? { ...it, time } : it) }));
  };

  /* conflict detection (overlap) */
  const conflicts = useMemo(() => {
    // chỉ cảnh báo khi hai hoạt động trùng ĐÚNG cùng một khung giờ
    const byTime = {};
    dayItems.forEach((it) => { (byTime[it.time] = byTime[it.time] || []).push(it.uid); });
    const set = new Set();
    Object.values(byTime).forEach((uids) => { if (uids.length > 1) uids.forEach((u) => set.add(u)); });
    return set;
  }, [dayItems]);

  const dayCost = (idx) => (itinerary[idx] || []).reduce((s, it) => s + (it.fee || 0), 0) * (Number(form.travelers) || 1);
  const totalCost = useMemo(() => Array.from({ length: Number(form.days) }).reduce((s, _, i) => s + dayCost(i), 0), [itinerary, form.days, form.travelers]);
  const totalPlaces = useMemo(() => Object.values(itinerary).reduce((s, a) => s + a.length, 0), [itinerary]);

  /* ─── POI filter/sort ─── */
  const availableCats = useMemo(() => [...new Set(pois.map((p) => p.category))], [pois]);
  const noAccent = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const shownPois = useMemo(() => {
    let list = pois.filter((p) => activeCat === "all" || p.category === activeCat);
    if (search.trim()) { const q = noAccent(search); list = list.filter((p) => noAccent(p.name).includes(q)); }
    list = list.slice();
    if (sort === "rating") list.sort((a, b) => (b.avg_rating || 0) - (a.avg_rating || 0));
    else if (sort === "price") list.sort((a, b) => (a.entrance_fee_amount || 0) - (b.entrance_fee_amount || 0));
    else if (sort === "duration") list.sort((a, b) => (a.estimated_duration_min || 0) - (b.estimated_duration_min || 0));
    else if (sort === "route") {
      // nearest-neighbour from centroid → optimal-ish route order
      if (list.length > 1) {
        const cLat = list.reduce((s, p) => s + (p.lat || 0), 0) / list.length;
        const cLng = list.reduce((s, p) => s + (p.lng || 0), 0) / list.length;
        const dist = (a, b) => Math.hypot((a.lat || 0) - (b.lat || 0), (a.lng || 0) - (b.lng || 0));
        const remaining = list.slice();
        const ordered = [];
        let cur = remaining.reduce((best, p) => dist(p, { lat: cLat, lng: cLng }) < dist(best, { lat: cLat, lng: cLng }) ? p : best, remaining[0]);
        while (remaining.length) {
          const idx = remaining.indexOf(cur);
          ordered.push(cur); remaining.splice(idx, 1);
          if (remaining.length) cur = remaining.reduce((best, p) => dist(p, cur) < dist(best, cur) ? p : best, remaining[0]);
        }
        list = ordered;
      }
    }
    return list;
  }, [pois, activeCat, search, sort]);

  /* ─── packing grouped ─── */
  const allPackItems = useMemo(() => {
    const base = packing.map((it) => ({ ...it, custom: false }));
    const extra = customPack.map((it, i) => ({ id: `cp-${i}`, ...it, custom: true }));
    return [...base, ...extra];
  }, [packing, customPack]);
  const packByCat = useMemo(() => {
    const g = {};
    allPackItems.forEach((it) => { (g[it.category] = g[it.category] || []).push(it); });
    return g;
  }, [allPackItems]);
  const packedCount = allPackItems.filter((it) => packChecked[it.id]).length;

  const qtyLabel = (rule) => {
    if (!rule) return "";
    if (rule === "days") return `×${form.days}`;
    if (rule.startsWith("fixed:")) return `×${rule.split(":")[1]}`;
    return "";
  };

  const addCustomPack = (cat) => {
    const val = (customInputs[cat] || "").trim();
    if (!val) return;
    const item = { category: cat, item_name: val, quantity_rule: "fixed:1", is_default_checked: false };
    setCustomPack((p) => [...p, item]);
    setCustomInputs((p) => ({ ...p, [cat]: "" }));
  };

  /* ─── nav guards ─── */
  const canStep2 = form.destSlug && form.origin && form.days >= 1 && form.startDate;
  const goStep2 = () => { if (!canStep2) { showToast("Vui lòng điền điểm đến, điểm đi, số ngày, ngày bắt đầu"); return; } setStep(2); window.scrollTo(0, 0); };
  const go = (s) => { setStep(s); window.scrollTo(0, 0); };

  /* ─── lưu kế hoạch vào "Kế hoạch của tôi" (upsert theo tripId) ─── */
  const persistTrip = (status) => {
    try {
      const saved = JSON.parse(localStorage.getItem("tb_saved_trips") || "[]");
      const snapshot = {
        id: tripId,
        destName: form.destName,
        originName: ORIGINS.find((o) => o.code === form.origin)?.nm || form.origin,
        form, itinerary, notes, packChecked, customPack,
        days: Number(form.days), travelers: Number(form.travelers),
        startDate: form.startDate,
        totalCost, totalPlaces,
        savedAt: new Date().toISOString(),
      };
      const idx = saved.findIndex((t) => t.id === tripId);
      if (idx >= 0) {
        // trạng thái phản ánh đúng hành động gần nhất: Lưu → saved, In/PDF → exported
        saved[idx] = { ...saved[idx], ...snapshot, status };
      } else {
        saved.push({ ...snapshot, status, createdAt: new Date().toISOString() });
      }
      localStorage.setItem("tb_saved_trips", JSON.stringify(saved));
      return true;
    } catch { return false; }
  };

  /* sau khi lưu xong: báo thành công + hỏi chia sẻ cộng đồng, rồi mới điều hướng về trang chủ */
  const finishFlow = async () => {
    const share = await confirmDialog(
      "Kế hoạch đã được lưu vào “Kế hoạch của tôi”. Bạn có muốn chia sẻ lịch trình này lên cộng đồng Traveler không?",
      { title: "🎉 Lưu thành công!", okText: "Chia sẻ ngay", cancelText: "Để sau" }
    );
    if (share) {
      showToast("Tính năng chia sẻ lên cộng đồng Traveler đang được phát triển ✨");
      setTimeout(() => navigate("/"), 1200);
    } else {
      navigate("/");
    }
  };

  const saveTrip = () => {
    if (!persistTrip("saved")) { showToast("Lưu thất bại"); return; }
    localStorage.removeItem(DRAFT_KEY); // dọn nháp → lần sau bắt đầu kế hoạch mới, không đè bản đã lưu
    finishFlow();
  };

  // Trình duyệt KHÔNG phân biệt được người dùng bấm "Lưu" hay "Huỷ" trong hộp thoại in
  // (afterprint kích hoạt cho cả hai). Vì vậy hỏi xác nhận lại — chỉ lưu khi thực sự đã xuất PDF.
  const exportTrip = () => {
    const onAfter = async () => {
      window.removeEventListener("afterprint", onAfter);
      const done = await confirmDialog(
        "Nếu bạn đã in hoặc lưu file PDF thành công, nhấn “Đã xuất xong” để đánh dấu “Đã xuất PDF” và lưu vào “Kế hoạch của tôi”.",
        { title: "Bạn đã xuất PDF chưa?", okText: "Đã xuất xong", cancelText: "Chưa / Đã huỷ" }
      );
      if (!done) { showToast("Đã huỷ — kế hoạch chưa được lưu."); return; }
      if (!persistTrip("exported")) { showToast("Lưu thất bại"); return; }
      localStorage.removeItem(DRAFT_KEY);
      finishFlow();
    };
    window.addEventListener("afterprint", onAfter);
    window.print();
  };

  const resetTrip = async () => {
    const ok = await confirmDialog("Bản nháp hiện tại sẽ bị xoá và bạn bắt đầu lại từ đầu.", {
      title: "Tạo kế hoạch mới?", okText: "Tạo mới", cancelText: "Huỷ", danger: true,
    });
    if (!ok) return;
    localStorage.removeItem(DRAFT_KEY);
    setTripId(Date.now()); // kế hoạch mới = id mới → không đè bản đã lưu
    setForm({ destSlug: "", destName: "", origin: "HAN", days: 3, startDate: todayStr(), style: "beach", prefs: [], travelers: 2, budget: "" });
    setItinerary({}); setNotes({}); setPacking([]); setPackChecked({}); setCustomPack([]); setPois([]); setStep(1); window.scrollTo(0, 0);
  };

  const NAV = [
    { key: "home", label: "Trang chủ" }, { key: "plan", label: "Lập kế hoạch" },
    { key: "flight", label: "Vé máy bay" }, { key: "hotel", label: "Khách sạn" },
    { key: "community", label: "Cộng đồng" }, { key: "ai", label: "Trợ lý AI" },
  ];
  const onNav = (k) => { if (k === "home") navigate("/"); else if (k === "plan") return; else showToast("Trang này đang được thiết kế"); };

  const STEP_LABELS = ["Thiết lập", "Xây lịch trình", "Hành trang", "Xuất & Lưu"];

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />

      {/* HEADER */}
      <SiteHeader active="plan" />

      {/* STEPPER */}
      <div className="tp-steps-wrap tp-no-print">
        <div className="tp-steps">
          {STEP_LABELS.map((lbl, i) => {
            const n = i + 1;
            const cls = step === n ? "active" : step > n ? "done" : "";
            return (
              <div key={lbl} className={"tp-step " + cls} style={i < 3 ? {} : { flex: "0" }}>
                <div className="tp-step-num">{step > n ? "✓" : n}</div>
                <div className="tp-step-label">{lbl}</div>
                {i < 3 && <div className="tp-step-bar" />}
              </div>
            );
          })}
        </div>
      </div>

      <main className="tp-main">

        {/* ══════════ STEP 1 — SETUP ══════════ */}
        {step === 1 && (
          <div className="tp-setup">
            <h2 className="tp-h2">Bắt đầu hành trình mới</h2>
            <p className="tp-h2-sub">Cho chúng tôi biết vài thông tin, hệ thống sẽ gợi ý địa điểm phù hợp cho bạn.</p>

            <div className="tp-card">
              <div className="tp-grid2">
                <div className="tp-field">
                  <label className="tp-lbl">Điểm đến <span className="req">*</span></label>
                  <select className="tp-select" value={form.destSlug}
                    onChange={(e) => { const d = destinations.find((x) => x.slug === e.target.value); setForm((p) => ({ ...p, destSlug: e.target.value, destName: d?.name || "" })); setPois([]); }}>
                    <option value="">— Chọn điểm đến —</option>
                    {destinations.map((d) => <option key={d.slug} value={d.slug}>{d.name}</option>)}
                  </select>
                </div>
                <div className="tp-field">
                  <label className="tp-lbl">Điểm xuất phát <span className="req">*</span></label>
                  <select className="tp-select" value={form.origin} onChange={(e) => setF("origin", e.target.value)}>
                    {ORIGINS.map((o) => <option key={o.code} value={o.code}>{o.nm}</option>)}
                  </select>
                </div>
              </div>

              {/* ideal time banner */}
              {selectedDest && (
                <div className={"tp-ideal " + (isIdeal ? "good" : "warn")}>
                  <span className="mi">{isIdeal ? "🌞" : "💡"}</span>
                  <div>
                    {isIdeal
                      ? <><b>Thời điểm lý tưởng!</b> Tháng {startMonth} là một trong những tháng đẹp nhất để đến {selectedDest.name}.</>
                      : <><b>Gợi ý thời điểm:</b> {selectedDest.name} đẹp nhất vào các tháng dưới đây — cân nhắc nếu lịch của bạn linh hoạt.</>}
                    <div className="tp-months">
                      {(selectedDest.best_months || []).map((m) => <span key={m} className="tp-month">{MONTHS[m - 1]}</span>)}
                    </div>
                  </div>
                </div>
              )}

              <div className="tp-grid2" style={{ marginTop: "1.25rem" }}>
                <div className="tp-field">
                  <label className="tp-lbl">Số ngày <span className="req">*</span></label>
                  <input className="tp-input" type="number" min="1" max="30" value={form.days} onChange={(e) => setF("days", Math.max(1, Math.min(30, Number(e.target.value))))} />
                </div>
                <div className="tp-field">
                  <label className="tp-lbl">Ngày bắt đầu <span className="req">*</span></label>
                  <input className="tp-input" type="date" value={form.startDate} onChange={(e) => setF("startDate", e.target.value)} />
                </div>
                <div className="tp-field">
                  <label className="tp-lbl">Số người đi</label>
                  <input className="tp-input" type="number" min="1" max="20" value={form.travelers} onChange={(e) => setF("travelers", Math.max(1, Number(e.target.value)))} />
                </div>
                <div className="tp-field">
                  <label className="tp-lbl">Ngân sách / người (tùy chọn)</label>
                  <input className="tp-input" type="text" placeholder="VD: 5.000.000đ" value={form.budget} onChange={(e) => setF("budget", e.target.value)} />
                </div>
              </div>

              <div className="tp-field full" style={{ marginBottom: "1.25rem" }}>
                <label className="tp-lbl">Phong cách chuyến đi (gợi ý hành trang)</label>
                <div className="tp-styles">
                  {STYLES.map((s) => (
                    <div key={s.key} className={"tp-style" + (form.style === s.key ? " on" : "")} onClick={() => setF("style", s.key)}>
                      <div className="nm">{s.nm}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="tp-field full">
                <label className="tp-lbl">Sở thích (lọc địa điểm)</label>
                <div className="tp-prefs">
                  {Object.keys(CAT).map((c) => (
                    <span key={c} className={"tp-pref" + (form.prefs.includes(c) ? " on" : "")}
                      onClick={() => setF("prefs", form.prefs.includes(c) ? form.prefs.filter((x) => x !== c) : [...form.prefs, c])}>
                      {catMeta(c).label}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="tp-actions">
              <button className="tp-btn tp-btn-ghost" onClick={() => navigate("/")}><IconBack /> Về trang chủ</button>
              <button className="tp-btn tp-btn-primary" onClick={goStep2} disabled={!canStep2}>Bắt đầu xây lịch trình <IconArrow /></button>
            </div>
          </div>
        )}

        {/* ══════════ STEP 2 — BUILDER ══════════ */}
        {step === 2 && (
          <>
            <div className="tp-tripbar tp-no-print">
              <div>
                <div className="dest">{form.destName}</div>
                <div className="meta">{ORIGINS.find((o) => o.code === form.origin)?.nm} → {form.destName} · {form.days} ngày · {form.travelers} người · {totalPlaces} địa điểm</div>
              </div>
              <div className="spacer" />
              <div className="cost"><div className="n">{totalCost.toLocaleString("vi-VN")}đ</div><div className="l">Tổng ước tính</div></div>
            </div>

            <div className="tp-build">
              {/* LEFT */}
              <div className="tp-panel tp-no-print">
                <div className="tp-panel-head">
                  <div className="tp-panel-title">Địa điểm tại {form.destName}</div>
                  <div className="tp-searchbox"><IconSearch /><input placeholder="Tìm địa điểm..." value={search} onChange={(e) => setSearch(e.target.value)} /></div>
                </div>
                <div className="tp-cats">
                  <span className={"tp-cat" + (activeCat === "all" ? " on" : "")} onClick={() => setActiveCat("all")}>Tất cả ({pois.length})</span>
                  {availableCats.map((c) => (
                    <span key={c} className={"tp-cat" + (activeCat === c ? " on" : "")} onClick={() => setActiveCat(c)}>{catMeta(c).label}</span>
                  ))}
                </div>
                <div className="tp-poi-list">
                  {loadingPois && <div className="tp-loading"><div className="tp-spin" />Đang tải địa điểm...</div>}
                  {!loadingPois && shownPois.length === 0 && <div className="tp-empty"><div className="ic">🔍</div><p>Không tìm thấy địa điểm phù hợp</p></div>}
                  {shownPois.map((p) => {
                    const m = catMeta(p.category);
                    const added = addedPoiIds.has(p.id);
                    return (
                      <div key={p.id} className="tp-poi">
                        <div className="tp-poi-thumb" style={{ background: `linear-gradient(135deg, ${m.color}, ${m.color}cc)` }}>
                          {p.primary_image_url ? <img src={p.primary_image_url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} onError={(e) => { e.currentTarget.style.display = "none"; }} /> : m.emoji}
                        </div>
                        <div className="tp-poi-info">
                          <span className="tp-poi-cat" style={{ background: m.color + "22", color: m.color }}>{m.label}</span>
                          <div className="tp-poi-name">{p.name}</div>
                          <div className="tp-poi-meta">
                            {p.avg_rating > 0 && <span className="star">★ {p.avg_rating.toFixed(1)}</span>}
                            <span>{fmtVND(p.entrance_fee_amount)}</span>
                            <span>{fmtDur(p.estimated_duration_min)}</span>
                          </div>
                        </div>
                        <div className="tp-poi-add">
                          {added
                            ? <button className="tp-add-btn added">✓ Đã thêm</button>
                            : <button className="tp-add-btn" onClick={() => addPoi(p)}>+ Thêm</button>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* RIGHT — Smart Note */}
              <div className="tp-panel">
                <div className="tp-day-tabs tp-no-print">
                  {Array.from({ length: Number(form.days) }).map((_, i) => (
                    <button key={i} className={"tp-day-tab" + (activeDay === i ? " on" : "")} onClick={() => setActiveDay(i)}>
                      Ngày {i + 1} <span className="cnt">({(itinerary[i] || []).length})</span>
                    </button>
                  ))}
                </div>
                <div className="tp-note">
                  <div className="tp-note-date">📅 {dayDate(form.startDate, activeDay)}</div>

                  {dayItems.length === 0 ? (
                    <div className="tp-empty"><div className="ic">📝</div><p>Chưa có hoạt động nào.<br />Thêm địa điểm từ cột bên trái hoặc tự thêm bên dưới.</p></div>
                  ) : (
                    <div className="tp-timeline">
                      {dayItems.map((it) => {
                        const m = catMeta(it.category);
                        const conf = conflicts.has(it.uid);
                        return (
                          <div key={it.uid} className="tp-tl-item">
                            <div className="tp-tl-time"><input type="time" value={it.time} onChange={(e) => editTime(it.uid, e.target.value)} /></div>
                            <div className="tp-tl-rail"><span className="dot" style={{ background: m.color, boxShadow: `0 0 0 2px ${m.color}` }} /></div>
                            <div className={"tp-tl-body" + (conf ? " conflict" : "")}>
                              <div className="tp-tl-row">
                                <div className="tp-tl-name">{it.name}</div>
                                <button className="tp-tl-x" onClick={() => removeItem(it.uid)} title="Xóa">✕</button>
                              </div>
                              <div className="tp-tl-sub">
                                <span>{fmtDur(it.dur)}</span>
                                <span>{fmtVND(it.fee)}{it.fee > 0 && form.travelers > 1 ? ` ×${form.travelers}` : ""}</span>
                              </div>
                              {conf && <div className="tp-conflict-tag">Trùng giờ với hoạt động khác — chỉnh lại thời gian</div>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  <div className="tp-note-tools tp-no-print">
                    {!customOpen ? (
                      <button className="tp-tool-btn" onClick={() => setCustomOpen(true)}>+ Thêm địa điểm / hoạt động tự nhập</button>
                    ) : (
                      <div className="tp-custom-add">
                        <input autoFocus value={customDraft}
                          onChange={(e) => setCustomDraft(e.target.value)}
                          onKeyDown={(e) => { if (e.key === "Enter") addCustom(); if (e.key === "Escape") { setCustomOpen(false); setCustomDraft(""); } }}
                          placeholder="VD: Ăn tối tại nhà hàng Madame Lân..." />
                        <button className="tp-custom-ok" onClick={addCustom}>Thêm</button>
                        <button className="tp-custom-cancel" onClick={() => { setCustomOpen(false); setCustomDraft(""); }}>Xong</button>
                      </div>
                    )}
                  </div>

                  <textarea className="tp-freenote" placeholder="Ghi chú tự do cho ngày này (VD: nhớ đặt bàn nhà hàng trước 2 tiếng...)"
                    value={notes[activeDay] || ""} onChange={(e) => setNotes((p) => ({ ...p, [activeDay]: e.target.value }))} />

                  <div className="tp-day-cost">
                    <span className="l">Chi phí ước tính Ngày {activeDay + 1}</span>
                    <span className="n">{dayCost(activeDay).toLocaleString("vi-VN")}đ</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="tp-actions tp-no-print">
              <button className="tp-btn tp-btn-ghost" onClick={() => go(1)}><IconBack /> Quay lại</button>
              <button className="tp-btn tp-btn-primary" onClick={() => go(3)} disabled={totalPlaces === 0}>Tiếp: Hành trang <IconArrow /></button>
            </div>
          </>
        )}

        {/* ══════════ STEP 3 — PACKING ══════════ */}
        {step === 3 && (
          <>
            <h2 className="tp-h2">Danh sách hành trang</h2>
            <p className="tp-h2-sub">Gợi ý tự động dựa trên phong cách "{STYLES.find((s) => s.key === form.style)?.nm}" và {form.days} ngày tại {form.destName}.</p>

            <div className="tp-pack-summary">
              <div>Đã chuẩn bị <b>{packedCount}/{allPackItems.length}</b> món. Bỏ tích những gì bạn không cần, hoặc thêm món riêng vào từng nhóm.</div>
            </div>

            {allPackItems.length === 0 ? (
              <div className="tp-loading"><div className="tp-spin" />Đang tải gợi ý hành trang...</div>
            ) : (
              <div className="tp-pack-grid">
                {Object.keys(packByCat).map((cat) => (
                  <div key={cat} className="tp-pack-col">
                    <h4>{PACK_CAT[cat] || cat}</h4>
                    {packByCat[cat].map((it) => (
                      <label key={it.id} className={"tp-pack-item" + (packChecked[it.id] ? " checked" : "")}>
                        <input type="checkbox" checked={!!packChecked[it.id]} onChange={(e) => setPackChecked((p) => ({ ...p, [it.id]: e.target.checked }))} />
                        <span className="nm">{it.item_name} {it.note && <span className="note">· {it.note}</span>}</span>
                        {qtyLabel(it.quantity_rule) && <span className="qty">{qtyLabel(it.quantity_rule)}</span>}
                      </label>
                    ))}
                    <div className="tp-pack-add">
                      <input placeholder="Thêm món..." value={customInputs[cat] || ""} onChange={(e) => setCustomInputs((p) => ({ ...p, [cat]: e.target.value }))} onKeyDown={(e) => e.key === "Enter" && addCustomPack(cat)} />
                      <button onClick={() => addCustomPack(cat)}>+</button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="tp-actions">
              <button className="tp-btn tp-btn-ghost" onClick={() => go(2)}><IconBack /> Quay lại lịch trình</button>
              <button className="tp-btn tp-btn-primary" onClick={() => go(4)}>Xem & xuất kế hoạch <IconArrow /></button>
            </div>
          </>
        )}

        {/* ══════════ STEP 4 — EXPORT ══════════ */}
        {step === 4 && (
          <div className="tp-export">
            <h2 className="tp-h2 tp-no-print">Hoàn tất!</h2>
            <p className="tp-h2-sub tp-no-print">Đây là bản xem trước lịch trình của bạn. Bạn có thể in/PDF, lưu hoặc chỉnh sửa lại.</p>

            <div className="tp-doc" id="tp-doc">
              <div className="tp-doc-head">
                <h1>LỊCH TRÌNH {form.destName.toUpperCase()}</h1>
                <div className="sub">{dayDate(form.startDate, 0).split(", ")[1]} – {dayDate(form.startDate, form.days - 1).split(", ")[1]} · {form.days} ngày · {form.travelers} người</div>
              </div>
              <div className="tp-doc-body">
                {Array.from({ length: Number(form.days) }).map((_, i) => {
                  const items = (itinerary[i] || []).slice().sort((a, b) => toMin(a.time) - toMin(b.time));
                  return (
                    <div key={i} className="tp-doc-day">
                      <div className="tp-doc-day-head">
                        <span className="d">Ngày {i + 1} — {dayDate(form.startDate, i)}</span>
                        <span className="c">{dayCost(i).toLocaleString("vi-VN")}đ</span>
                      </div>
                      {items.length === 0 ? <div className="tp-doc-line"><span className="p">— Chưa có hoạt động —</span></div> :
                        items.map((it) => (
                          <div key={it.uid} className="tp-doc-line">
                            <span className="t">{it.time}</span>
                            <span className="n">{it.name}</span>
                            <span className="p">{fmtVND(it.fee)}</span>
                          </div>
                        ))}
                      {notes[i] && <div className="tp-doc-line"><span className="p">📌 {notes[i]}</span></div>}
                    </div>
                  );
                })}

                <div className="tp-doc-total">
                  <span className="l">TỔNG CHI PHÍ DỰ KIẾN</span>
                  <span className="n">{totalCost.toLocaleString("vi-VN")}đ</span>
                </div>

                {packedCount > 0 && (
                  <div className="tp-doc-pack">
                    <h3>Hành trang ({packedCount} món)</h3>
                    <div className="tp-doc-pack-tags">
                      {allPackItems.filter((it) => packChecked[it.id]).map((it) => (
                        <span key={it.id} className="tp-doc-pack-tag">{it.item_name}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="tp-export-actions tp-no-print">
              <button className="tp-btn tp-btn-ghost" onClick={() => go(3)}><IconBack /> Chỉnh sửa</button>
              <button className="tp-btn tp-btn-primary" onClick={exportTrip}>In / Lưu PDF</button>
              <button className="tp-btn tp-btn-green" onClick={saveTrip}>Lưu kế hoạch</button>
              <button className="tp-btn tp-btn-ghost" onClick={resetTrip}>+ Kế hoạch mới</button>
            </div>
          </div>
        )}
      </main>

      <SiteFooter />
    </>
  );
}
