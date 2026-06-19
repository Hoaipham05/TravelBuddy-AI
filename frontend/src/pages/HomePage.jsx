import { useState, useEffect, useRef, useLayoutEffect } from "react";
import { useNavigate } from "react-router-dom";
import { SiteHeader, SiteFooter } from "../components/SiteChrome";
import { toast } from "../components/dialog";

/* ─────────────────────────────────────────────────
   CSS
───────────────────────────────────────────────── */
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --sky:     #0EA5E9;
  --ocean:   #0284C7;
  --deep:    #0369A1;
  --deepest: #075985;
  --sunset:  #F97316;
  --coral:   #FB7185;
  --green:   #10B981;
  --yellow:  #FDE68A;
  --amber:   #F59E0B;
  --bg:      #F0F9FF;
  --surface: #FFFFFF;
  --text:    #0F172A;
  --muted:   #64748B;
  --border:  #E2E8F0;
  --dark:    #0F172A;
}

html { scroll-behavior: smooth; }
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}
.hp-mute { color: var(--muted); }

/* ══════════════════ HEADER ══════════════════ */
.hp-header {
  position: sticky; top: 0; z-index: 200;
  height: 64px; display: flex; align-items: center;
  padding: 0 1.75rem; gap: 1.25rem;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(14,165,233,0.1);
  box-shadow: 0 1px 0 rgba(0,0,0,0.04);
}
.hp-logo { display: flex; align-items: center; gap: 0.625rem; text-decoration: none; flex-shrink: 0; cursor: pointer; }
.hp-logo-mark {
  width: 38px; height: 38px;
  background: linear-gradient(135deg, var(--sky), var(--ocean));
  border-radius: 11px; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 14px rgba(14,165,233,0.38); color: #fff; flex-shrink: 0;
}
.hp-logo-name { font-family: 'Nunito', sans-serif; font-size: 1.125rem; font-weight: 800; color: var(--deep); line-height: 1.2; }
.hp-logo-sub { font-size: 0.6875rem; font-weight: 500; color: var(--muted); letter-spacing: 0.05em; text-transform: uppercase; display: block; }

.hp-nav { flex: 1; display: flex; justify-content: center; gap: 0.125rem; }
.hp-nav-item {
  display: flex; align-items: center; gap: 0.375rem;
  padding: 0.4375rem 0.8125rem; border-radius: 9px;
  font-size: 0.875rem; font-weight: 600; color: var(--muted);
  cursor: pointer; user-select: none; background: none; border: none;
  font-family: inherit; transition: all 0.15s; position: relative;
}
.hp-nav-item:hover { background: rgba(14,165,233,0.08); color: var(--ocean); }
.hp-nav-item.active { background: linear-gradient(135deg, var(--sky), var(--ocean)); color: #fff; box-shadow: 0 3px 10px rgba(14,165,233,0.3); }
.hp-nav-item.active:hover { color: #fff; }

.hp-header-right { display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0; }
.hp-tour-btn {
  display: flex; align-items: center; gap: 0.375rem;
  padding: 0.4375rem 0.875rem; border-radius: 9px;
  border: 1.5px solid var(--border); background: #fff;
  font-size: 0.8125rem; font-weight: 600; color: var(--ocean);
  cursor: pointer; font-family: inherit; transition: all 0.15s;
}
.hp-tour-btn:hover { border-color: var(--sky); background: #F0F9FF; }
.hp-icon-btn {
  width: 38px; height: 38px; border-radius: 10px;
  border: 1.5px solid var(--border); background: #fff;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: var(--muted); position: relative; transition: all 0.15s;
}
.hp-icon-btn:hover { border-color: var(--sky); color: var(--sky); }
.hp-icon-btn .hp-dot { position: absolute; top: 7px; right: 8px; width: 7px; height: 7px; background: var(--coral); border-radius: 50%; border: 1.5px solid #fff; }

/* avatar + menu */
.hp-avatar-wrap { position: relative; }
.hp-avatar {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.25rem 0.5rem 0.25rem 0.25rem; border-radius: 100px;
  border: 1.5px solid var(--border); background: #fff;
  cursor: pointer; transition: all 0.15s;
}
.hp-avatar:hover { border-color: var(--sky); box-shadow: 0 3px 10px rgba(14,165,233,0.12); }
.hp-avatar-img {
  width: 30px; height: 30px; border-radius: 50%;
  background: linear-gradient(135deg, var(--sunset), var(--coral));
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 800; font-size: 0.8125rem; font-family: 'Nunito', sans-serif;
}
.hp-avatar-name { font-size: 0.8125rem; font-weight: 700; color: var(--text); max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hp-menu {
  position: absolute; top: calc(100% + 10px); right: 0;
  width: 230px; background: #fff; border-radius: 14px;
  box-shadow: 0 16px 48px rgba(15,23,42,0.16); border: 1px solid var(--border);
  padding: 0.5rem; z-index: 250; animation: menu-in 0.18s ease;
}
@keyframes menu-in { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
.hp-menu-head { padding: 0.75rem 0.75rem 0.625rem; border-bottom: 1px solid var(--border); margin-bottom: 0.375rem; }
.hp-menu-head .nm { font-weight: 800; font-family: 'Nunito', sans-serif; color: var(--text); font-size: 0.9375rem; }
.hp-menu-head .em { font-size: 0.75rem; color: var(--muted); }
.hp-menu-item {
  display: flex; align-items: center; gap: 0.625rem;
  padding: 0.5625rem 0.75rem; border-radius: 9px;
  font-size: 0.875rem; font-weight: 500; color: var(--text);
  cursor: pointer; background: none; border: none; width: 100%;
  font-family: inherit; text-align: left; transition: background 0.12s;
}
.hp-menu-item:hover { background: #F1F5F9; }
.hp-menu-item.danger { color: #DC2626; }
.hp-menu-item.danger:hover { background: #FEF2F2; }
.hp-menu-badge { margin-left: auto; font-size: 0.6875rem; font-weight: 700; padding: 0.1rem 0.45rem; border-radius: 100px; background: #FEF3C7; color: #B45309; }

/* ══════════════════ HERO ══════════════════ */
.hp-hero {
  position: relative; overflow: hidden;
  min-height: 480px; display: flex; align-items: center;
  padding: 3.5rem 2rem;
  background:
    linear-gradient(165deg, rgba(7,89,133,0.7) 0%, rgba(2,132,199,0.5) 50%, rgba(14,165,233,0.42) 100%),
    url('https://tourism.danang.vn/wp-content/uploads/2023/02/cau-rong-da-nang.jpeg') center/cover;
}
.hp-hero::after {
  content: ''; position: absolute; inset: 0;
  background-image: radial-gradient(circle, rgba(255,255,255,0.07) 1.5px, transparent 1.5px);
  background-size: 30px 30px; pointer-events: none;
}
.hp-hero-inner { position: relative; z-index: 2; max-width: 1180px; margin: 0 auto; width: 100%; text-align: center; display: flex; flex-direction: column; align-items: center; }
.hp-hero-badge {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.22);
  backdrop-filter: blur(8px); border-radius: 100px;
  padding: 0.375rem 1rem 0.375rem 0.625rem;
  font-size: 0.8125rem; font-weight: 600; color: #fff; margin-bottom: 1.25rem;
}
.hp-live-dot { width: 8px; height: 8px; background: var(--green); border-radius: 50%; box-shadow: 0 0 0 3px rgba(16,185,129,0.3); animation: pulse-dot 2s infinite; }
@keyframes pulse-dot { 0%,100% { box-shadow: 0 0 0 3px rgba(16,185,129,0.25); } 50% { box-shadow: 0 0 0 6px rgba(16,185,129,0.1); } }
.hp-hero h1 {
  font-family: 'Nunito', sans-serif; font-weight: 900;
  font-size: 3rem; line-height: 1.1; color: #fff;
  letter-spacing: -0.025em; margin-bottom: 1rem; max-width: 720px;
  text-shadow: 0 2px 16px rgba(7,20,45,0.45);
}
.hp-hero h1 .hi { color: var(--yellow); }
.hp-hero p { font-size: 1.0625rem; color: rgba(255,255,255,0.95); line-height: 1.6; max-width: 560px; margin-bottom: 2rem; text-shadow: 0 1px 10px rgba(7,20,45,0.4); }

/* search bar */
.hp-search {
  display: flex; align-items: center; gap: 0.5rem;
  background: #fff; border-radius: 16px; padding: 0.5rem;
  max-width: 640px; box-shadow: 0 20px 50px rgba(0,0,0,0.22);
}
.hp-search-field { flex: 1; display: flex; align-items: center; gap: 0.625rem; padding: 0.5rem 0.875rem; }
.hp-search-field svg { color: var(--muted); flex-shrink: 0; }
.hp-search-field input { border: none; outline: none; font-family: inherit; font-size: 0.9375rem; width: 100%; color: var(--text); background: none; }
.hp-search-field input::placeholder { color: #94A3B8; }
.hp-search-btn {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.75rem 1.5rem; border: none; border-radius: 12px;
  background: linear-gradient(135deg, var(--sunset), #EA580C);
  color: #fff; font-family: 'Nunito', sans-serif; font-weight: 800; font-size: 0.9375rem;
  cursor: pointer; box-shadow: 0 6px 16px rgba(249,115,22,0.4); transition: transform 0.15s, box-shadow 0.15s; flex-shrink: 0;
}
.hp-search-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(249,115,22,0.5); }

.hp-hero-stats { display: flex; gap: 2.25rem; margin-top: 2rem; flex-wrap: wrap; justify-content: center; }
.hp-stat .n { font-family: 'Nunito', sans-serif; font-weight: 900; font-size: 1.5rem; color: #fff; }
.hp-stat .l { font-size: 0.8125rem; color: rgba(255,255,255,0.7); }

/* ══════════════════ SECTION SHELL ══════════════════ */
.hp-section { max-width: 1180px; margin: 0 auto; padding: 3.5rem 2rem; }
.hp-sec-head { margin-bottom: 1.75rem; }
.hp-sec-eyebrow { font-size: 0.75rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; color: var(--sky); margin-bottom: 0.5rem; }
.hp-sec-title { font-family: 'Nunito', sans-serif; font-weight: 900; font-size: 1.875rem; color: var(--text); letter-spacing: -0.02em; }
.hp-sec-sub { font-size: 0.9375rem; color: var(--muted); margin-top: 0.375rem; max-width: 560px; }
.hp-sec-head-row { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
.hp-link-more { display: inline-flex; align-items: center; gap: 0.375rem; font-size: 0.875rem; font-weight: 700; color: var(--ocean); cursor: pointer; background: none; border: none; font-family: inherit; }
.hp-link-more:hover { gap: 0.5rem; }

/* ══════════════════ QUICK ACTIONS ══════════════════ */
.hp-quick { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: -2.75rem; position: relative; z-index: 10; max-width: 1180px; margin-left: auto; margin-right: auto; padding: 0 2rem; }
.hp-quick-card {
  background: #fff; border-radius: 16px; padding: 1.25rem;
  box-shadow: 0 10px 30px rgba(15,23,42,0.08); border: 1px solid rgba(226,232,240,0.8);
  cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; text-align: left;
}
.hp-quick-card:hover { transform: translateY(-5px); box-shadow: 0 18px 40px rgba(14,165,233,0.18); }
.hp-quick-ico { width: 46px; height: 46px; border-radius: 13px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; margin-bottom: 0.875rem; }
.hp-quick-card h4 { font-family: 'Nunito', sans-serif; font-weight: 800; font-size: 1rem; color: var(--text); margin-bottom: 0.25rem; }
.hp-quick-card p { font-size: 0.8125rem; color: var(--muted); line-height: 1.45; }

/* ══════════════════ DESTINATION CARDS ══════════════════ */
.hp-dest-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.25rem; }
.hp-dest-grid .big { grid-column: span 2; grid-row: span 2; }
.hp-dest {
  position: relative; border-radius: 18px; overflow: hidden;
  min-height: 200px; cursor: pointer; display: flex; flex-direction: column; justify-content: flex-end;
  box-shadow: 0 6px 20px rgba(15,23,42,0.1);
  background: linear-gradient(135deg, var(--ocean), var(--deepest));
}
.hp-dest.big { min-height: 420px; }
.hp-dest img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transition: transform 0.6s ease; }
.hp-dest:hover img { transform: scale(1.08); }
.hp-dest::after { content: ''; position: absolute; inset: 0; background: linear-gradient(to top, rgba(7,15,30,0.82) 0%, rgba(7,15,30,0.25) 45%, transparent 75%); }
.hp-dest-body { position: relative; z-index: 2; padding: 1.125rem; color: #fff; }
.hp-dest-tag {
  position: absolute; top: 1rem; left: 1rem; z-index: 2;
  background: rgba(255,255,255,0.92); color: var(--ocean);
  font-size: 0.6875rem; font-weight: 800; padding: 0.25rem 0.625rem; border-radius: 100px;
  backdrop-filter: blur(4px);
}
.hp-dest-name { font-family: 'Nunito', sans-serif; font-weight: 800; font-size: 1.0625rem; margin-bottom: 0.25rem; }
.hp-dest.big .hp-dest-name { font-size: 1.625rem; }
.hp-dest-meta { display: flex; align-items: center; gap: 0.75rem; font-size: 0.8125rem; color: rgba(255,255,255,0.85); }
.hp-dest-meta .star { color: var(--yellow); }

/* ══════════════════ EXPERIENCES ══════════════════ */
.hp-exp-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.hp-exp {
  background: #fff; border-radius: 18px; overflow: hidden;
  box-shadow: 0 6px 20px rgba(15,23,42,0.07); border: 1px solid rgba(226,232,240,0.7);
}
.hp-exp-img { height: 170px; position: relative; overflow: hidden; background: linear-gradient(135deg, var(--sky), var(--deep)); }
.hp-exp-img img { width: 100%; height: 100%; object-fit: cover; }
.hp-exp-body { padding: 1.125rem 1.25rem 1.375rem; }
.hp-exp-body h4 { font-family: 'Nunito', sans-serif; font-weight: 800; font-size: 1.0625rem; color: var(--text); margin-bottom: 0.375rem; }
.hp-exp-body p { font-size: 0.875rem; color: var(--muted); line-height: 1.55; }

/* ══════════════════ DEALS (split) ══════════════════ */
.hp-deals { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.hp-deal-col { background: #fff; border-radius: 18px; padding: 1.5rem; box-shadow: 0 6px 20px rgba(15,23,42,0.07); border: 1px solid rgba(226,232,240,0.7); }
.hp-deal-col h3 { font-family: 'Nunito', sans-serif; font-weight: 800; font-size: 1.125rem; color: var(--text); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
.hp-deal-row { display: flex; align-items: center; gap: 0.875rem; padding: 0.875rem; border-radius: 13px; transition: background 0.15s; cursor: pointer; }
.hp-deal-row:hover { background: #F8FAFC; }
.hp-deal-row + .hp-deal-row { border-top: 1px solid var(--border); }
.hp-deal-ico { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; }
.hp-deal-info { flex: 1; min-width: 0; }
.hp-deal-info .t { font-weight: 700; font-size: 0.9375rem; color: var(--text); }
.hp-deal-info .s { font-size: 0.8125rem; color: var(--muted); }
.hp-deal-price { text-align: right; flex-shrink: 0; }
.hp-deal-price .p { font-family: 'Nunito', sans-serif; font-weight: 900; font-size: 1.0625rem; color: var(--ocean); }
.hp-deal-price .old { font-size: 0.75rem; color: #94A3B8; text-decoration: line-through; }

/* ══════════════════ COMMUNITY ══════════════════ */
.hp-comm-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.hp-post { background: #fff; border-radius: 16px; padding: 1.25rem; box-shadow: 0 6px 20px rgba(15,23,42,0.06); border: 1px solid rgba(226,232,240,0.7); }
.hp-post-head { display: flex; align-items: center; gap: 0.625rem; margin-bottom: 0.875rem; }
.hp-post-av { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 800; font-size: 0.8125rem; font-family: 'Nunito', sans-serif; flex-shrink: 0; }
.hp-post-who .n { font-weight: 700; font-size: 0.875rem; color: var(--text); }
.hp-post-who .w { font-size: 0.75rem; color: var(--muted); }
.hp-post-txt { font-size: 0.9375rem; color: #334155; line-height: 1.6; margin-bottom: 0.875rem; }
.hp-post-foot { display: flex; gap: 1.25rem; font-size: 0.8125rem; color: var(--muted); }
.hp-post-foot span { display: flex; align-items: center; gap: 0.3rem; }

/* ══════════════════ CTA BAND ══════════════════ */
.hp-cta { max-width: 1180px; margin: 1rem auto 4rem; padding: 0 2rem; }
.hp-cta-inner {
  position: relative; overflow: hidden;
  background: linear-gradient(120deg, var(--deepest), var(--ocean) 70%, var(--sky));
  border-radius: 24px; padding: 3rem 3rem; text-align: center; color: #fff;
}
.hp-cta-inner::before { content: ''; position: absolute; inset: 0; background-image: radial-gradient(circle, rgba(255,255,255,0.08) 1.5px, transparent 1.5px); background-size: 26px 26px; }
.hp-cta-inner > * { position: relative; z-index: 2; }
.hp-cta h2 { font-family: 'Nunito', sans-serif; font-weight: 900; font-size: 2rem; margin-bottom: 0.75rem; letter-spacing: -0.02em; }
.hp-cta p { font-size: 1.0625rem; color: rgba(255,255,255,0.85); margin-bottom: 1.75rem; }
.hp-cta-btn {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.9375rem 2rem; border-radius: 13px; border: none;
  background: #fff; color: var(--deep);
  font-family: 'Nunito', sans-serif; font-weight: 800; font-size: 1rem;
  cursor: pointer; box-shadow: 0 10px 26px rgba(0,0,0,0.2); transition: transform 0.18s;
}
.hp-cta-btn:hover { transform: translateY(-2px); }

/* ══════════════════ FOOTER ══════════════════ */
.hp-footer { background: var(--dark); padding: 1.125rem 2rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem; }
.hp-footer-brand { display: flex; align-items: center; gap: 0.5rem; font-family: 'Nunito', sans-serif; font-size: 0.875rem; font-weight: 700; color: rgba(255,255,255,0.5); }
.hp-footer-brand .hi { color: var(--sky); }
.hp-footer-links { display: flex; gap: 1.5rem; }
.hp-footer-links a { font-size: 0.8125rem; color: rgba(255,255,255,0.4); text-decoration: none; cursor: pointer; transition: color 0.15s; }
.hp-footer-links a:hover { color: rgba(255,255,255,0.8); }

/* ══════════════════ AI FLOATING ══════════════════ */
.hp-ai-fab {
  position: fixed; right: 1.75rem; bottom: 1.75rem; z-index: 180;
  display: flex; align-items: center; gap: 0.625rem;
  padding: 0.875rem 1.25rem; border-radius: 100px; border: none;
  background: linear-gradient(135deg, #7C3AED, var(--ocean));
  color: #fff; font-family: 'Nunito', sans-serif; font-weight: 800; font-size: 0.9375rem;
  cursor: pointer; box-shadow: 0 12px 30px rgba(124,58,237,0.4); transition: transform 0.18s, box-shadow 0.18s;
}
.hp-ai-fab:hover { transform: translateY(-3px) scale(1.03); box-shadow: 0 18px 40px rgba(124,58,237,0.5); }
.hp-ai-fab .ai-pulse { width: 9px; height: 9px; background: #4ADE80; border-radius: 50%; box-shadow: 0 0 0 3px rgba(74,222,128,0.35); animation: pulse-dot 2s infinite; }

/* ══════════════════ ONBOARDING TOUR ══════════════════ */
.tour-overlay { position: fixed; inset: 0; z-index: 1000; pointer-events: auto; }
.tour-spot {
  position: fixed; border-radius: 12px; z-index: 1001;
  box-shadow: 0 0 0 9999px rgba(8,15,30,0.74);
  border: 2.5px solid rgba(255,255,255,0.95);
  transition: all 0.35s cubic-bezier(0.22,1,0.36,1);
  pointer-events: none;
}
.tour-pop {
  position: fixed; z-index: 1002; width: 320px;
  background: #fff; border-radius: 16px; padding: 1.25rem;
  box-shadow: 0 24px 60px rgba(0,0,0,0.35);
  animation: pop-in 0.3s cubic-bezier(0.22,1,0.36,1);
  transition: top 0.35s cubic-bezier(0.22,1,0.36,1), left 0.35s cubic-bezier(0.22,1,0.36,1);
}
@keyframes pop-in { from { opacity: 0; transform: translateY(8px) scale(0.96); } to { opacity: 1; transform: translateY(0) scale(1); } }
.tour-pop::before {
  content: ''; position: absolute; top: -8px; width: 16px; height: 16px;
  background: #fff; transform: rotate(45deg);
  left: var(--arrow-x, 32px); border-radius: 3px 0 0 0;
}
.tour-pop-ico { width: 46px; height: 46px; border-radius: 13px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; margin-bottom: 0.875rem; }
.tour-pop h4 { font-family: 'Nunito', sans-serif; font-weight: 900; font-size: 1.125rem; color: var(--text); margin-bottom: 0.375rem; }
.tour-pop p { font-size: 0.875rem; color: var(--muted); line-height: 1.6; margin-bottom: 1.125rem; }
.tour-pop-foot { display: flex; align-items: center; justify-content: space-between; }
.tour-dots { display: flex; gap: 0.375rem; }
.tour-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--border); transition: all 0.2s; }
.tour-dot.on { background: var(--sky); width: 20px; border-radius: 100px; }
.tour-btns { display: flex; gap: 0.5rem; }
.tour-skip { background: none; border: none; font-family: inherit; font-size: 0.8125rem; font-weight: 600; color: var(--muted); cursor: pointer; padding: 0.5rem 0.5rem; }
.tour-skip:hover { color: var(--text); }
.tour-next {
  display: inline-flex; align-items: center; gap: 0.375rem;
  padding: 0.5rem 1.125rem; border-radius: 10px; border: none;
  background: linear-gradient(135deg, var(--sky), var(--ocean)); color: #fff;
  font-family: 'Nunito', sans-serif; font-weight: 800; font-size: 0.875rem;
  cursor: pointer; box-shadow: 0 4px 12px rgba(14,165,233,0.35); transition: transform 0.15s;
}
.tour-next:hover { transform: translateY(-1px); }

/* ══════════════════ RESPONSIVE ══════════════════ */
@media (max-width: 1024px) {
  .hp-quick { grid-template-columns: repeat(2, 1fr); }
  .hp-dest-grid { grid-template-columns: repeat(2, 1fr); }
  .hp-dest-grid .big { grid-column: span 2; grid-row: auto; }
  .hp-dest.big { min-height: 240px; }
  .hp-exp-grid, .hp-comm-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 860px) {
  .hp-nav { display: none; }
  .hp-tour-btn span { display: none; }
}
@media (max-width: 680px) {
  .hp-hero h1 { font-size: 2rem; }
  .hp-search { flex-direction: column; align-items: stretch; }
  .hp-search-btn { justify-content: center; }
  .hp-deals, .hp-exp-grid, .hp-comm-grid, .hp-dest-grid, .hp-quick { grid-template-columns: 1fr; }
  .hp-dest-grid .big { grid-column: auto; }
  .hp-section { padding: 2.5rem 1.25rem; }
  .hp-avatar-name { display: none; }
  .hp-cta-inner { padding: 2rem 1.5rem; }
  .hp-cta h2 { font-size: 1.5rem; }
  .hp-footer { flex-direction: column; text-align: center; }
  .tour-pop { width: calc(100vw - 2rem); }
  .hp-ai-fab span { display: none; }
}
`;

/* ─────────────────────────────────────────────────
   SVG icons
───────────────────────────────────────────────── */
const IconPlane = ({ size = 24, color = "white" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5L21 16z"/>
  </svg>
);
const IconBell = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8a6 6 0 00-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 01-3.4 0"/>
  </svg>
);
const IconCompass = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><path d="M16.2 7.8l-2.9 6.4-6.4 2.9 2.9-6.4 6.4-2.9z"/>
  </svg>
);
const IconArrow = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14M12 5l7 7-7 7"/>
  </svg>
);
const IconUser = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>
  </svg>
);
const IconHeart = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.8 4.6a5.5 5.5 0 00-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 00-7.8 7.8l1.1 1L12 21l7.7-7.6 1.1-1a5.5 5.5 0 000-7.8z"/>
  </svg>
);
const IconLogout = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/>
  </svg>
);
const IconSpark = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2l1.8 5.2L19 9l-5.2 1.8L12 16l-1.8-5.2L5 9l5.2-1.8L12 2zM19 14l.9 2.6L22 17.5l-2.1.9L19 21l-.9-2.6L16 17.5l2.1-.9L19 14z"/>
  </svg>
);

/* ─────────────────────────────────────────────────
   DATA
───────────────────────────────────────────────── */
const NAV = [
  { key: "home",      icon: "🏠", label: "Trang chủ" },
  { key: "plan",      icon: "📅", label: "Lập kế hoạch" },
  { key: "flight",    icon: "✈️", label: "Vé máy bay" },
  { key: "hotel",     icon: "🏨", label: "Khách sạn" },
  { key: "community", icon: "👥", label: "Cộng đồng" },
  { key: "ai",        icon: "🤖", label: "Trợ lý AI" },
];

const DESTS = [
  { name: "Phú Quốc",  tag: "🔥 Hot nhất",  rating: "4.9", trips: "2.1k", img: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=900&q=80", big: true },
  { name: "Đà Lạt",    tag: "Lãng mạn",     rating: "4.8", trips: "1.8k", img: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=600&q=80" },
  { name: "Hạ Long",   tag: "Di sản",       rating: "4.9", trips: "1.5k", img: "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=600&q=80" },
  { name: "Sapa",      tag: "Núi rừng",     rating: "4.7", trips: "1.2k", img: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&q=80" },
  { name: "Nha Trang", tag: "Biển xanh",    rating: "4.8", trips: "1.6k", img: "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?w=600&q=80" },
];

// ảnh dự phòng cho điểm đến (DB chưa có ảnh) — map theo tên
const DEST_IMG = {
  "Phú Quốc": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=900&q=80",
  "Đà Lạt": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=600&q=80",
  "Hạ Long": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=600&q=80",
  "Sapa": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&q=80",
  "Nha Trang": "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?w=600&q=80",
  "Hội An": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=600&q=80",
  "Đà Nẵng": "https://images.unsplash.com/photo-1565024144860-1bc4f2d3c8b8?w=600&q=80",
  "Hà Nội": "https://images.unsplash.com/photo-1509023464722-18d996393ca8?w=600&q=80",
  "Huế": "https://images.unsplash.com/photo-1528127269322-539801943592?w=600&q=80",
};
const DEST_TAGS = ["🔥 Hot nhất", "Được yêu thích", "Nổi bật", "Đáng đi", "Cộng đồng khen"];

const EXPERIENCES = [
  { emoji: "🏖️", title: "Nghỉ dưỡng biển", desc: "Thư giãn tại những bãi biển đẹp nhất Việt Nam, resort 5 sao sát mặt nước.", img: "https://images.unsplash.com/photo-1473116763249-2faaef81ccda?w=700&q=80" },
  { emoji: "⛰️", title: "Trekking & núi rừng", desc: "Chinh phục Fansipan, ruộng bậc thang Sapa, săn mây bình minh.", img: "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=700&q=80" },
  { emoji: "🍜", title: "Food tour ẩm thực", desc: "Khám phá phở, bún bò, bánh mì và ẩm thực đường phố ba miền.", img: "https://images.unsplash.com/photo-1555126634-323283e090fa?w=700&q=80" },
];

const POSTS = [
  { name: "Nguyễn Lan", when: "2 giờ trước", av: "linear-gradient(135deg,#F97316,#FB7185)", txt: "Vừa đi Hội An về, phố cổ về đêm lung linh thật sự 🏮 Mọi người nhớ thử cao lầu ở quán gần Chùa Cầu nhé!", likes: "124", cmts: "18" },
  { name: "Trần Huy",  when: "5 giờ trước", av: "linear-gradient(135deg,#0EA5E9,#0284C7)", txt: "Lịch trình Đà Lạt 3N2Đ tự túc dưới 2 triệu, mình đã chia sẻ template rồi, clone về dùng luôn nha 🌲", likes: "98", cmts: "31" },
  { name: "Mai Phương", when: "1 ngày trước", av: "linear-gradient(135deg,#10B981,#059669)", txt: "Săn được vé Hà Nội - Phú Quốc chỉ 650k nhờ biểu đồ giá của TravelBuddy 😍 quá hời luôn!", likes: "211", cmts: "44" },
];

const TOUR = [
  { key: "plan",      icon: "📅", bg: "linear-gradient(135deg,#0EA5E9,#0284C7)", title: "Lập kế hoạch", desc: "Tạo lịch trình du lịch theo ngày bằng công cụ kéo-thả. Thêm điểm đến, khách sạn, hoạt động và để AI tối ưu lộ trình cho bạn." },
  { key: "flight",    icon: "✈️", bg: "linear-gradient(135deg,#F59E0B,#F97316)", title: "Vé máy bay", desc: "Xem biểu đồ giá vé 30–90 ngày kèm dự báo thời tiết. Hệ thống gợi ý ngày bay vừa rẻ vừa đẹp trời." },
  { key: "hotel",     icon: "🏨", bg: "linear-gradient(135deg,#10B981,#059669)", title: "Khách sạn", desc: "Tìm kiếm, lọc theo giá – số sao – tiện ích và so sánh song song nhiều khách sạn trên bản đồ trực quan." },
  { key: "community", icon: "👥", bg: "linear-gradient(135deg,#F97316,#FB7185)", title: "Cộng đồng Traveler", desc: "Đọc review thật, xem ảnh thực tế và clone lịch trình mẫu từ cộng đồng chỉ với một cú nhấp." },
  { key: "ai",        icon: "🤖", bg: "linear-gradient(135deg,#7C3AED,#4F46E5)", title: "Trợ lý AI", desc: "Bế tắc khi lên kế hoạch? Hỏi AI bằng ngôn ngữ tự nhiên để nhận gợi ý điểm đến, vé, khách sạn và ngân sách." },
  { key: "profile",   icon: "👤", bg: "linear-gradient(135deg,#F97316,#FB7185)", title: "Hồ sơ của bạn", desc: "Lưu sở thích du lịch và lịch sử chuyến đi – cá nhân hoá gợi ý cho từng hành trình." },
];

/* ─────────────────────────────────────────────────
   COMPONENT
───────────────────────────────────────────────── */
function getUser() {
  try {
    const raw = localStorage.getItem("tb_user") || sessionStorage.getItem("tb_user");
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

export default function HomePage() {
  const navigate = useNavigate();

  /* điểm đến nổi bật — tổng hợp từ cộng đồng (nhiều review tích cực + hữu ích) */
  const [featured, setFeatured] = useState(null);
  useEffect(() => {
    fetch("/api/travel/community/featured-destinations?limit=5")
      .then((r) => r.json())
      .then((d) => setFeatured(d.items || []))
      .catch(() => setFeatured([]));
  }, []);
  const destCards = (featured && featured.length)
    ? featured.map((f, i) => ({
        name: f.name, slug: f.slug, rating: f.avg_rating,
        meta: `${(f.total_helpful || 0).toLocaleString("vi-VN")} lượt thích`,
        img: f.image_url || DEST_IMG[f.name] || DEST_IMG["Phú Quốc"],
        tag: DEST_TAGS[i] || "Nổi bật", big: i === 0,
      }))
    : DESTS.map((d) => ({ name: d.name, slug: null, rating: d.rating, meta: `${d.trips} lịch trình`, img: d.img, tag: d.tag, big: d.big }));
  const openCommunity = (slug) => { try { if (slug) localStorage.setItem("tb_community_dest", slug); } catch (e) {} navigate("/community"); };
  const user = getUser();
  const fullName = user?.full_name || "Traveler";
  const firstName = fullName.trim().split(" ").slice(-1)[0];
  const initials = fullName.trim().split(" ").slice(-2).map((s) => s[0]).join("").toUpperCase();

  const [menuOpen, setMenuOpen] = useState(false);
  const [tourStep, setTourStep] = useState(-1); // -1 = closed
  const [rect, setRect] = useState(null);

  const navRefs = useRef({});
  const avatarRef = useRef(null);
  const menuWrapRef = useRef(null);


  /* auto-start tour first visit */
  useEffect(() => {
    if (localStorage.getItem("tb_force_tour")) {
      localStorage.removeItem("tb_force_tour");
      const t = setTimeout(() => setTourStep(0), 400);
      return () => clearTimeout(t);
    }
    if (!localStorage.getItem("tb_tour_done")) {
      const t = setTimeout(() => setTourStep(0), 700);
      return () => clearTimeout(t);
    }
  }, []);

  /* close avatar menu on outside click */
  useEffect(() => {
    const h = (e) => { if (menuWrapRef.current && !menuWrapRef.current.contains(e.target)) setMenuOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  /* measure target for current tour step — find nav items in shared header by data-nav */
  const measure = () => {
    if (tourStep < 0) return;
    const step = TOUR[tourStep];
    const el = document.querySelector(`[data-nav="${step.key}"]`);
    if (el) setRect(el.getBoundingClientRect());
  };
  useLayoutEffect(measure, [tourStep]);
  useEffect(() => {
    if (tourStep < 0) return;
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    return () => { window.removeEventListener("resize", measure); window.removeEventListener("scroll", measure, true); };
  }, [tourStep]);

  const startTour = () => setTourStep(0);
  const endTour = () => { setTourStep(-1); localStorage.setItem("tb_tour_done", "1"); };
  const nextStep = () => { if (tourStep >= TOUR.length - 1) endTour(); else setTourStep((s) => s + 1); };

  const NAV_ROUTES = { home: "/", plan: "/plan", flight: "/flights", hotel: "/hotels", community: "/community" };
  const onNav = (item) => {
    if (item.key === "home") return;
    if (NAV_ROUTES[item.key]) { navigate(NAV_ROUTES[item.key]); return; }
    toast(`Trang "${item.label}" đang được thiết kế — sẽ sớm ra mắt! ✨`);
  };

  const logout = () => {
    ["tb_token", "tb_user"].forEach((k) => { localStorage.removeItem(k); sessionStorage.removeItem(k); });
    navigate("/login");
  };

  /* tour popover position */
  const PAD = 8;
  let spot = null, pop = null, arrowX = 32;
  if (rect) {
    spot = { top: rect.top - PAD, left: rect.left - PAD, width: rect.width + PAD * 2, height: rect.height + PAD * 2 };
    const popW = Math.min(320, window.innerWidth - 32);
    let left = rect.left + rect.width / 2 - 40;
    left = Math.max(16, Math.min(left, window.innerWidth - popW - 16));
    pop = { top: rect.bottom + PAD + 14, left, width: popW };
    arrowX = Math.max(16, Math.min(rect.left + rect.width / 2 - left - 8, popW - 32));
  }

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />

      {/* ─── HEADER ─── */}
      <SiteHeader active="home" onStartTour={startTour} />

      {/* ─── HERO ─── */}
      <section className="hp-hero">
        <div className="hp-hero-inner">
          <div className="hp-hero-badge">
            <span className="hp-live-dot" /> Nền tảng du lịch AI thông minh #1 Việt Nam
          </div>
          <h1>Chào <span className="hi">{firstName}</span>, hôm nay mình đi đâu? ✨</h1>
          <p>Lên kế hoạch, săn vé rẻ, đặt khách sạn và khám phá Việt Nam cùng cộng đồng traveler — tất cả trong một nền tảng.</p>

          <div className="hp-hero-stats">
            <div className="hp-stat"><div className="n">10+</div><div className="l">Điểm đến nổi bật</div></div>
            <div className="hp-stat"><div className="n">220+</div><div className="l">Khách sạn</div></div>
            <div className="hp-stat"><div className="n">24/7</div><div className="l">Trợ lý AI</div></div>
            <div className="hp-stat"><div className="n">5.000+</div><div className="l">Traveler tin dùng</div></div>
          </div>
        </div>
      </section>

      {/* ─── DESTINATIONS ─── */}
      <section className="hp-section" style={{ paddingTop: "3rem" }}>
        <div className="hp-sec-head hp-sec-head-row">
          <div>
            <div className="hp-sec-eyebrow">Điểm đến</div>
            <h2 className="hp-sec-title">Điểm đến nổi bật</h2>
            <p className="hp-sec-sub">Những nơi được cộng đồng traveler yêu thích và ghé thăm nhiều nhất.</p>
          </div>
          <button className="hp-link-more" onClick={() => openCommunity()}>
            Xem cộng đồng <IconArrow />
          </button>
        </div>

        <div className="hp-dest-grid">
          {destCards.map((d) => (
            <div key={d.name} className={"hp-dest" + (d.big ? " big" : "")} onClick={() => openCommunity(d.slug)}>
              <img src={d.img} alt={d.name} loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} />
              <span className="hp-dest-tag">{d.tag}</span>
              <div className="hp-dest-body">
                <div className="hp-dest-name">{d.name}</div>
                <div className="hp-dest-meta">
                  <span><span className="star">★</span> {d.rating}</span>
                  <span>· {d.meta}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── EXPERIENCES ─── */}
      <section className="hp-section" style={{ paddingTop: 0 }}>
        <div className="hp-sec-head">
          <div className="hp-sec-eyebrow">Trải nghiệm</div>
          <h2 className="hp-sec-title">Hoạt động du lịch thú vị</h2>
          <p className="hp-sec-sub">Chọn phong cách du lịch của bạn — biển, núi, hay ẩm thực đường phố.</p>
        </div>
        <div className="hp-exp-grid">
          {EXPERIENCES.map((x) => (
            <div key={x.title} className="hp-exp">
              <div className="hp-exp-img">
                <img src={x.img} alt={x.title} loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} />
              </div>
              <div className="hp-exp-body">
                <h4>{x.title}</h4>
                <p>{x.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── COMMUNITY ─── */}
      <section className="hp-section" style={{ paddingTop: 0 }}>
        <div className="hp-sec-head hp-sec-head-row">
          <div>
            <div className="hp-sec-eyebrow">Cộng đồng</div>
            <h2 className="hp-sec-title">Traveler đang chia sẻ</h2>
            <p className="hp-sec-sub">Kinh nghiệm thật, lịch trình thật từ cộng đồng yêu xê dịch.</p>
          </div>
          <button className="hp-link-more" onClick={() => openCommunity()}>
            Vào cộng đồng <IconArrow />
          </button>
        </div>
        <div className="hp-comm-grid">
          {POSTS.map((p, i) => (
            <div key={i} className="hp-post">
              <div className="hp-post-head">
                <div className="hp-post-av" style={{ background: p.av }}>{p.name.split(" ").slice(-1)[0][0]}</div>
                <div className="hp-post-who">
                  <div className="n">{p.name}</div>
                  <div className="w">{p.when}</div>
                </div>
              </div>
              <div className="hp-post-txt">{p.txt}</div>
              <div className="hp-post-foot">
                <span>❤️ {p.likes}</span>
                <span>💬 {p.cmts}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── CTA ─── */}
      <div className="hp-cta">
        <div className="hp-cta-inner">
          <h2>Sẵn sàng cho chuyến đi tiếp theo? 🌏</h2>
          <p>Để TravelBuddy AI giúp bạn lên kế hoạch hoàn hảo chỉ trong vài phút.</p>
          <button className="hp-cta-btn" onClick={() => navigate("/plan")}>
            Bắt đầu lập kế hoạch <IconArrow size={17} />
          </button>
        </div>
      </div>

      {/* ─── FOOTER ─── */}
      <SiteFooter />

      {/* Nút Trợ lý AI dùng chung là <AssistantWidget/> (nút robot nổi trên mọi trang) */}

      {/* ─── ONBOARDING TOUR ─── */}
      {tourStep >= 0 && rect && (
        <div className="tour-overlay" onClick={endTour}>
          <div className="tour-spot" style={spot} />
          <div
            className="tour-pop"
            style={{ top: pop.top, left: pop.left, width: pop.width, "--arrow-x": `${arrowX}px` }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="tour-pop-ico" style={{ background: TOUR[tourStep].bg }}>{TOUR[tourStep].icon}</div>
            <h4>{TOUR[tourStep].title}</h4>
            <p>{TOUR[tourStep].desc}</p>
            <div className="tour-pop-foot">
              <div className="tour-dots">
                {TOUR.map((_, i) => <span key={i} className={"tour-dot" + (i === tourStep ? " on" : "")} />)}
              </div>
              <div className="tour-btns">
                <button className="tour-skip" onClick={endTour}>Bỏ qua</button>
                <button className="tour-next" onClick={nextStep}>
                  {tourStep >= TOUR.length - 1 ? "Hoàn tất 🎉" : <>Tiếp theo <IconArrow size={14} /></>}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
