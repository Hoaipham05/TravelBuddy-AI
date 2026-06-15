import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "../components/dialog";

/* ─────────────────────────────────────────────────
   CSS — injected once via <style>
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
  --green:   #10B981;
  --yellow:  #FDE68A;
  --bg:      #F0F9FF;
  --surface: #FFFFFF;
  --text:    #0F172A;
  --muted:   #64748B;
  --border:  #E2E8F0;
  --dark:    #0F172A;
  --r:       12px;
  --shadow-card: 0 24px 64px rgba(14,165,233,0.13), 0 8px 24px rgba(0,0,0,0.07);
}

html { scroll-behavior: smooth; }
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
}

/* ══════════════════ HEADER ══════════════════ */
.lp-header {
  position: fixed;
  inset: 0 0 auto 0;
  z-index: 200;
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 2rem;
  gap: 1.5rem;
  background: rgba(255,255,255,0.88);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(14,165,233,0.1);
  box-shadow: 0 1px 0 rgba(0,0,0,0.04);
}

.lp-logo {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  text-decoration: none;
  flex-shrink: 0;
}
.lp-logo-mark {
  width: 38px; height: 38px;
  background: linear-gradient(135deg, var(--sky) 0%, var(--ocean) 100%);
  border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 14px rgba(14,165,233,0.38);
  font-size: 1.125rem; color: #fff; flex-shrink: 0;
}
.lp-logo-name {
  font-family: 'Nunito', sans-serif;
  font-size: 1.125rem; font-weight: 800;
  color: var(--deep); letter-spacing: -0.01em;
  line-height: 1.2;
}
.lp-logo-sub {
  font-size: 0.6875rem; font-weight: 500;
  color: var(--muted); letter-spacing: 0.05em;
  text-transform: uppercase; display: block;
}

/* nav */
.lp-nav {
  flex: 1; display: flex; justify-content: center; gap: 0.125rem;
}
.lp-nav-item {
  display: flex; align-items: center; gap: 0.375rem;
  padding: 0.4375rem 0.875rem;
  border-radius: 8px;
  font-size: 0.875rem; font-weight: 500;
  color: #94A3B8;
  cursor: not-allowed;
  position: relative;
  user-select: none;
  transition: background 0.15s;
}
.lp-nav-item:hover { background: rgba(0,0,0,0.03); }
.lp-nav-lock { font-size: 0.65rem; }

/* tooltip on hover */
.lp-nav-item .lp-tip {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%; transform: translateX(-50%) translateY(-4px);
  background: #1E293B; color: #fff;
  font-size: 0.6875rem; font-weight: 500;
  padding: 0.3125rem 0.625rem;
  border-radius: 6px; white-space: nowrap;
  opacity: 0; pointer-events: none;
  transition: opacity 0.15s, transform 0.15s;
  z-index: 300;
}
.lp-nav-item .lp-tip::before {
  content: ''; position: absolute; bottom: 100%; left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent; border-bottom-color: #1E293B;
}
.lp-nav-item:hover .lp-tip { opacity: 1; transform: translateX(-50%) translateY(0); }

/* header actions */
.lp-header-right { display: flex; align-items: center; gap: 0.625rem; flex-shrink: 0; }
.lp-btn-ghost {
  padding: 0.4375rem 1rem;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  font-size: 0.875rem; font-weight: 600;
  color: var(--muted); background: transparent;
  cursor: pointer; font-family: inherit;
  transition: all 0.15s;
}
.lp-btn-ghost:hover { border-color: var(--sky); color: var(--sky); }

.lp-btn-solid {
  padding: 0.4375rem 1.25rem;
  background: linear-gradient(135deg, var(--sky), var(--ocean));
  border: none; border-radius: 8px;
  font-size: 0.875rem; font-weight: 600;
  color: #fff; cursor: pointer; font-family: inherit;
  box-shadow: 0 3px 10px rgba(14,165,233,0.32);
  transition: all 0.2s;
}
.lp-btn-solid:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(14,165,233,0.42); }

/* ══════════════════ PAGE SKELETON ══════════════════ */
.lp-page { display: flex; flex-direction: column; min-height: 100vh; }

.lp-hero {
  flex: 1; display: flex;
  min-height: calc(100vh - 64px - 68px);
  margin-top: 64px;
}

/* ══════════════════ LEFT PANEL ══════════════════ */
.lp-left {
  flex: 0 0 58%;
  position: relative;
  background: linear-gradient(150deg,
    var(--deepest)  0%,
    var(--deep)    28%,
    var(--ocean)   62%,
    #22D3EE        100%);
  padding: 4rem 3.5rem 3.5rem;
  display: flex; flex-direction: column; justify-content: center;
  overflow: hidden;
}

/* dot texture */
.lp-left::before {
  content: '';
  position: absolute; inset: 0;
  background-image: radial-gradient(circle, rgba(255,255,255,0.065) 1.5px, transparent 1.5px);
  background-size: 28px 28px;
  pointer-events: none;
}

/* curved right edge */
.lp-left::after {
  content: '';
  position: absolute;
  top: 0; bottom: 0; right: -60px;
  width: 120px;
  background: var(--bg);
  border-radius: 60px 0 0 60px / 50%;
  pointer-events: none;
}

.lp-left-content { position: relative; z-index: 2; max-width: 520px; }

/* live badge */
.lp-live-badge {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  backdrop-filter: blur(8px);
  border-radius: 100px;
  padding: 0.375rem 1rem 0.375rem 0.625rem;
  font-size: 0.8125rem; font-weight: 600;
  color: rgba(255,255,255,0.92);
  margin-bottom: 1.75rem;
  width: fit-content;
}
.lp-live-dot {
  width: 8px; height: 8px;
  background: var(--green); border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(16,185,129,0.3);
  animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%,100% { box-shadow: 0 0 0 3px rgba(16,185,129,0.25); }
  50%     { box-shadow: 0 0 0 6px rgba(16,185,129,0.1); }
}

/* hero heading */
.lp-h1 {
  font-family: 'Nunito', sans-serif;
  font-size: 3.125rem; font-weight: 900;
  color: #fff; line-height: 1.12;
  letter-spacing: -0.025em;
  margin-bottom: 1.25rem;
}
.lp-h1 .hi {
  color: var(--yellow);
  position: relative;
}
.lp-h1 .hi::after {
  content: '';
  position: absolute; bottom: 1px; left: 0; right: 0;
  height: 3px;
  background: rgba(253,230,138,0.35);
  border-radius: 2px;
}
.lp-h1 .brand {
  background: linear-gradient(96deg, #FDE68A 0%, #FCD34D 35%, #67E8F9 100%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; color: transparent;
}

.lp-sub {
  font-size: 1.0625rem;
  color: rgba(255,255,255,0.78);
  line-height: 1.7;
  margin-bottom: 2.75rem;
}

/* feature 2×2 grid */
.lp-feat-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 0.875rem; margin-bottom: 2.5rem;
}
.lp-feat {
  background: rgba(255,255,255,0.22);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.32);
  border-radius: 14px;
  padding: 1rem 1.0625rem;
  display: flex; align-items: flex-start; gap: 0.75rem;
  transition: transform 0.25s, background 0.25s;
  cursor: default;
}
.lp-feat:hover { transform: translateY(-3px); background: rgba(255,255,255,0.3); }
.lp-feat-icon {
  width: 38px; height: 38px; flex-shrink: 0;
  background: rgba(255,255,255,0.32);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem;
}
.lp-feat-info h4 {
  font-family: 'Nunito', sans-serif;
  font-size: 0.875rem; font-weight: 800; color: #fff;
  margin-bottom: 0.2rem;
}
.lp-feat-info p { font-size: 0.75rem; color: rgba(255,255,255,0.82); line-height: 1.45; }

/* destination chips */
.lp-dest-label {
  font-size: 0.6875rem; font-weight: 700;
  color: rgba(255,255,255,0.48); text-transform: uppercase;
  letter-spacing: 0.08em; margin-bottom: 0.625rem;
}
.lp-dest-row { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.lp-dest-chip {
  display: flex; align-items: center; gap: 0.3rem;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 100px;
  padding: 0.3125rem 0.75rem;
  font-size: 0.8125rem; color: rgba(255,255,255,0.88);
  font-weight: 500; cursor: default;
  transition: background 0.2s;
}
.lp-dest-chip:hover { background: rgba(255,255,255,0.18); }

/* decorative floating elements */
.lp-deco1 {
  position: absolute; right: 90px; top: 12%;
  width: 80px; height: 80px; opacity: 0.12;
  pointer-events: none;
  animation: float-a 4.5s ease-in-out infinite;
  display: flex; align-items: center; justify-content: center;
}
.lp-deco2 {
  position: absolute; right: 100px; bottom: 18%;
  font-size: 2.5rem; opacity: 0.07;
  pointer-events: none;
  animation: float-a 5.5s ease-in-out infinite reverse;
}
@keyframes float-a {
  0%,100% { transform: translateY(0) rotate(-15deg); }
  50%     { transform: translateY(-14px) rotate(-15deg); }
}

/* ══════════════════ RIGHT PANEL ══════════════════ */
.lp-right {
  flex: 0 0 42%;
  display: flex; align-items: center; justify-content: center;
  padding: 3rem 2.5rem 3rem 3.5rem;
  background: var(--bg);
}

/* ══════════════════ CARD ══════════════════ */
.lp-card {
  background: #fff;
  border-radius: 24px;
  box-shadow: var(--shadow-card);
  padding: 2.5rem 2.25rem;
  width: 100%; max-width: 400px;
  animation: card-in 0.55s cubic-bezier(0.22,1,0.36,1);
}
@keyframes card-in {
  from { opacity: 0; transform: translateY(18px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0)    scale(1); }
}

.lp-card-head { text-align: center; margin-bottom: 1.75rem; }

.lp-card-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 60px; height: 60px;
  background: linear-gradient(135deg, var(--sky), var(--deep));
  border-radius: 18px; margin-bottom: 1rem;
  font-size: 1.625rem;
  box-shadow: 0 8px 24px rgba(14,165,233,0.32);
  animation: icon-bob 3s ease-in-out infinite;
}
@keyframes icon-bob {
  0%,100% { transform: translateY(0); }
  50%     { transform: translateY(-5px); }
}

.lp-card-title {
  font-family: 'Nunito', sans-serif;
  font-size: 1.625rem; font-weight: 900; color: var(--text);
  letter-spacing: -0.02em; margin-bottom: 0.375rem;
}
.lp-card-desc { font-size: 0.875rem; color: var(--muted); line-height: 1.55; }

/* ══════════════════ FORM ══════════════════ */
.lp-form { display: flex; flex-direction: column; gap: 1rem; }

.lp-field { display: flex; flex-direction: column; gap: 0.375rem; }
.lp-lbl { font-size: 0.8125rem; font-weight: 600; color: #334155; }

.lp-ibox { position: relative; display: flex; align-items: center; }
.lp-icon-l {
  position: absolute; left: 0.875rem;
  color: #94A3B8; pointer-events: none;
  display: flex; align-items: center;
}

.lp-input {
  width: 100%;
  padding: 0.75rem 0.875rem 0.75rem 2.625rem;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  font-size: 0.9375rem; color: var(--text);
  background: #FAFBFC;
  font-family: inherit; outline: none;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
}
.lp-input:focus {
  border-color: var(--sky); background: #fff;
  box-shadow: 0 0 0 3px rgba(14,165,233,0.1);
}
.lp-input::placeholder { color: #CBD5E1; font-size: 0.875rem; }

.lp-toggle {
  position: absolute; right: 0.875rem;
  background: none; border: none; padding: 0;
  color: #94A3B8; cursor: pointer;
  display: flex; align-items: center;
  transition: color 0.2s;
}
.lp-toggle:hover { color: var(--sky); }

/* remember + forgot row */
.lp-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: -0.125rem;
}
.lp-check {
  display: flex; align-items: center; gap: 0.5rem;
  cursor: pointer; user-select: none;
}
.lp-check input[type=checkbox] { width: 15px; height: 15px; accent-color: var(--sky); cursor: pointer; }
.lp-check-lbl { font-size: 0.8125rem; color: var(--muted); }
.lp-forgot {
  font-size: 0.8125rem; font-weight: 600; color: var(--sky);
  background: none; border: none; cursor: pointer;
  font-family: inherit; padding: 0; transition: color 0.15s;
}
.lp-forgot:hover { color: var(--deep); text-decoration: underline; }

/* submit */
.lp-submit {
  width: 100%; padding: 0.9375rem;
  background: linear-gradient(135deg, var(--sky), var(--deepest));
  border: none; border-radius: 11px;
  font-family: 'Nunito', sans-serif;
  font-size: 1rem; font-weight: 800;
  color: #fff; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  box-shadow: 0 6px 18px rgba(14,165,233,0.38);
  transition: transform 0.2s, box-shadow 0.2s;
  margin-top: 0.25rem; letter-spacing: 0.01em;
}
.lp-submit:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(14,165,233,0.46); }
.lp-submit:active:not(:disabled) { transform: translateY(0); }
.lp-submit:disabled { opacity: 0.65; cursor: not-allowed; }

/* divider */
.lp-div {
  display: flex; align-items: center; gap: 0.875rem;
  font-size: 0.8125rem; color: #CBD5E1; font-weight: 500;
}
.lp-div::before,.lp-div::after {
  content: ''; flex: 1; height: 1px; background: var(--border);
}

/* google */
.lp-google {
  width: 100%; padding: 0.8125rem;
  background: #fff; border: 1.5px solid var(--border);
  border-radius: 11px;
  font-family: inherit; font-size: 0.9375rem; font-weight: 600;
  color: #374151; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 0.625rem;
  transition: all 0.2s;
}
.lp-google:hover { background: #F8FAFC; border-color: #CBD5E1; box-shadow: 0 3px 10px rgba(0,0,0,0.07); }

/* card footer */
.lp-card-foot {
  text-align: center;
  font-size: 0.875rem; color: var(--muted);
  margin-top: 1.25rem;
}
.lp-card-foot a {
  color: var(--sky); font-weight: 700;
  text-decoration: none; cursor: pointer;
  font-family: 'Nunito', sans-serif;
}
.lp-card-foot a:hover { text-decoration: underline; }

/* error */
.lp-err {
  display: flex; align-items: flex-start; gap: 0.625rem;
  background: #FEF2F2; border: 1px solid #FCA5A5;
  border-radius: 10px; padding: 0.75rem 1rem;
  font-size: 0.875rem; color: #DC2626;
  animation: shake 0.38s ease;
}
@keyframes shake {
  0%,100% { transform: translateX(0); }
  20%,60% { transform: translateX(-4px); }
  40%,80% { transform: translateX(4px); }
}

/* spinner */
@keyframes spin { to { transform: rotate(360deg); } }
.lp-spin {
  width: 18px; height: 18px; flex-shrink: 0;
  border: 2.5px solid rgba(255,255,255,0.3);
  border-top-color: #fff; border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* success */
.lp-success {
  display: flex; align-items: center; gap: 0.625rem;
  background: #F0FDF4; border: 1px solid #86EFAC;
  border-radius: 10px; padding: 0.75rem 1rem;
  font-size: 0.875rem; color: #16A34A; font-weight: 500;
}

/* ══════════════════ FOOTER ══════════════════ */
.lp-footer {
  background: var(--dark);
  padding: 1.125rem 2rem;
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 0.75rem;
}
.lp-footer-brand {
  display: flex; align-items: center; gap: 0.5rem;
  font-family: 'Nunito', sans-serif;
  font-size: 0.875rem; font-weight: 700;
  color: rgba(255,255,255,0.5);
}
.lp-footer-brand .hi { color: var(--sky); }
.lp-footer-links { display: flex; gap: 1.5rem; }
.lp-footer-links a {
  font-size: 0.8125rem; color: rgba(255,255,255,0.4);
  text-decoration: none; transition: color 0.15s; cursor: pointer;
}
.lp-footer-links a:hover { color: rgba(255,255,255,0.8); }

/* ══════════════════ RESPONSIVE ══════════════════ */
@media (max-width: 960px) {
  .lp-nav { display: none; }
  .lp-hero { flex-direction: column; min-height: auto; }
  .lp-left { flex: none; padding: 2.5rem 2rem 3.5rem; }
  .lp-left::after { display: none; }
  .lp-h1 { font-size: 2.25rem; }
  .lp-right { flex: none; padding: 2rem 1.5rem 2.5rem; }
  .lp-card { max-width: 480px; margin: 0 auto; }
  .lp-deco1 { font-size: 3rem; right: 1.5rem; }
  .lp-deco2 { display: none; }
}

@media (max-width: 600px) {
  .lp-header { padding: 0 1rem; }
  .lp-header-right .lp-btn-ghost { display: none; }
  .lp-logo-sub { display: none; }
  .lp-left { padding: 2rem 1.25rem 3rem; }
  .lp-h1 { font-size: 1.875rem; }
  .lp-sub { font-size: 0.9375rem; }
  .lp-feat-grid { gap: 0.625rem; }
  .lp-right { padding: 1.75rem 1rem 2.25rem; }
  .lp-card { padding: 1.75rem 1.25rem; border-radius: 20px; }
  .lp-footer { flex-direction: column; text-align: center; padding: 1.25rem 1rem; }
  .lp-footer-links { gap: 1rem; flex-wrap: wrap; justify-content: center; }
}
`;

/* ─────────────────────────────────────────────────
   SVG icon helpers
───────────────────────────────────────────────── */
const IconMail = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="20" height="16" rx="2"/>
    <path d="M2 7l10 7 10-7"/>
  </svg>
);

const IconLock = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2"/>
    <path d="M7 11V7a5 5 0 0110 0v4"/>
  </svg>
);

const IconEye = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12S5 4 12 4s11 8 11 8-4 8-11 8S1 12 1 12z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
);

const IconEyeOff = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19M1 1l22 22"/>
  </svg>
);

const IconArrow = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14M12 5l7 7-7 7"/>
  </svg>
);

const IconPlane = ({ size = 24, color = "white" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color} xmlns="http://www.w3.org/2000/svg">
    <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5L21 16z"/>
  </svg>
);

const GoogleLogo = () => (
  <svg width="18" height="18" viewBox="0 0 48 48">
    <path fill="#FFC107" d="M43.6 20H24v8.5h11.1C33.6 33.1 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.7 1.1 7.8 2.9l6-6C34.4 6.2 29.5 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-4z"/>
    <path fill="#FF3D00" d="M6.3 14.7l7 5.1C15.1 16.4 19.2 13.5 24 13.5c3 0 5.7 1.1 7.8 2.9l6-6C34.4 6.2 29.5 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>
    <path fill="#4CAF50" d="M24 44c5.2 0 9.9-1.9 13.4-5l-6.2-5.2C29.3 35.3 26.8 36 24 36c-5.3 0-9.6-2.9-11.1-7.5L5.8 34c3.3 6.4 10 10 18.2 10z"/>
    <path fill="#1976D2" d="M43.6 20H24v8.5h11.1c-.8 2.2-2.3 4.1-4.3 5.3l6.2 5.2C40.8 35.7 44 30.3 44 24c0-1.3-.1-2.7-.4-4z"/>
  </svg>
);

/* ─────────────────────────────────────────────────
   DATA
───────────────────────────────────────────────── */
const NAV = [
  { icon: "📅", label: "Lập kế hoạch" },
  { icon: "✈️", label: "Vé máy bay" },
  { icon: "🏨", label: "Khách sạn" },
  { icon: "👥", label: "Cộng đồng Traveler" },
  { icon: "🤖", label: "Trợ lý AI" },
];

const FEATURES = [
  { icon: "✈️", title: "Vé máy bay giá rẻ",   desc: "So sánh giá VietJet, Bamboo, Vietnam Airlines theo ngày" },
  { icon: "🏨", title: "Khách sạn tốt nhất",   desc: "Hàng trăm lựa chọn từ 1–5 sao, lọc theo tiêu chí" },
  { icon: "🤖", title: "Trợ lý AI 24/7",        desc: "Lên kế hoạch tự động bằng ngôn ngữ tự nhiên" },
  { icon: "👥", title: "Cộng đồng Traveler",    desc: "Chia sẻ lịch trình thực tế, review chân thật" },
];

const DESTS = ["📍 Đà Nẵng", "📍 Hà Nội", "📍 Phú Quốc", "📍 Hội An", "📍 Đà Lạt", "+ 5 nơi"];

/* ─────────────────────────────────────────────────
   COMPONENT
───────────────────────────────────────────────── */
export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm]         = useState({ email: "", password: "" });
  const [showPw, setShowPw]     = useState(false);
  const [remember, setRemember] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [success, setSuccess]   = useState(false);

  const set = (k) => (e) => setForm((p) => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.password) {
      setError("Vui lòng nhập đầy đủ email và mật khẩu");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email, password: form.password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Đăng nhập không thành công");
      const store = remember ? localStorage : sessionStorage;
      store.setItem("tb_token", data.access_token);
      store.setItem("tb_user", JSON.stringify(data.user));
      setSuccess(true);
      setTimeout(() => { navigate("/"); }, 1000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />

      <div className="lp-page">

        {/* ─── HEADER ─── */}
        <header className="lp-header">
          <a className="lp-logo" href="/">
            <div className="lp-logo-mark"><IconPlane size={20} /></div>
            <div>
              <span className="lp-logo-name">TravelBuddy</span>
              
            </div>
          </a>

          <nav className="lp-nav">
            {NAV.map((n) => (
              <div key={n.label} className="lp-nav-item" role="button" aria-disabled="true">
                <span>{n.icon}</span>
                <span>{n.label}</span>
                <div className="lp-tip">Vui lòng đăng nhập để sử dụng</div>
              </div>
            ))}
          </nav>

          <div className="lp-header-right">
            <button className="lp-btn-ghost">Đăng ký</button>
            <button className="lp-btn-solid">Đăng nhập</button>
          </div>
        </header>

        {/* ─── HERO ─── */}
        <section className="lp-hero">

          {/* LEFT — branding */}
          <div className="lp-left">
            <div className="lp-deco1"><IconPlane size={80} /></div>
            <div className="lp-deco2">🌏</div>

            <div className="lp-left-content">
              <div className="lp-live-badge">
                <span className="lp-live-dot" />
                Nền tảng du lịch AI thông minh
              </div>

              <h1 className="lp-h1">
                Khám phá <span className="hi">Việt Nam</span><br />
                cùng <span className="brand">TravelBuddy</span>
              </h1>

              <p className="lp-sub">
                Lập kế hoạch thông minh, vé máy bay giá rẻ, khách sạn tốt nhất và
                cộng đồng traveler — tất cả trong một nền tảng duy nhất.
              </p>

              <div className="lp-feat-grid">
                {FEATURES.map((f) => (
                  <div key={f.title} className="lp-feat">
                    <div className="lp-feat-icon">{f.icon}</div>
                    <div className="lp-feat-info">
                      <h4>{f.title}</h4>
                      <p>{f.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <p className="lp-dest-label">10 điểm đến nổi bật</p>
              <div className="lp-dest-row">
                {DESTS.map((d) => (
                  <div key={d} className="lp-dest-chip">{d}</div>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT — login card */}
          <div className="lp-right">
            <div className="lp-card">

              <div className="lp-card-head">
                <div className="lp-card-icon"><IconPlane size={30} /></div>
                <h2 className="lp-card-title">Chào mừng trở lại 👋</h2>
                <p className="lp-card-desc">Đăng nhập để bắt đầu hành trình của bạn</p>
              </div>

              <form className="lp-form" onSubmit={handleSubmit} autoComplete="on">

                {/* error */}
                {error && (
                  <div className="lp-err" role="alert">
                    <span>⚠️</span><span>{error}</span>
                  </div>
                )}

                {/* success */}
                {success && (
                  <div className="lp-success" role="status">
                    <span>✅</span><span>Đăng nhập thành công! Đang chuyển hướng...</span>
                  </div>
                )}

                {/* email */}
                <div className="lp-field">
                  <label className="lp-lbl" htmlFor="tb-email">Email</label>
                  <div className="lp-ibox">
                    <span className="lp-icon-l"><IconMail /></span>
                    <input
                      id="tb-email"
                      type="email"
                      className="lp-input"
                      placeholder="you@example.com"
                      value={form.email}
                      onChange={set("email")}
                      autoComplete="email"
                      required
                      disabled={loading || success}
                    />
                  </div>
                </div>

                {/* password */}
                <div className="lp-field">
                  <label className="lp-lbl" htmlFor="tb-password">Mật khẩu</label>
                  <div className="lp-ibox">
                    <span className="lp-icon-l"><IconLock /></span>
                    <input
                      id="tb-password"
                      type={showPw ? "text" : "password"}
                      className="lp-input"
                      placeholder="Nhập mật khẩu"
                      value={form.password}
                      onChange={set("password")}
                      autoComplete="current-password"
                      required
                      disabled={loading || success}
                    />
                    <button
                      type="button"
                      className="lp-toggle"
                      onClick={() => setShowPw((p) => !p)}
                      tabIndex={-1}
                      aria-label={showPw ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                    >
                      {showPw ? <IconEyeOff /> : <IconEye />}
                    </button>
                  </div>
                </div>

                {/* remember + forgot */}
                <div className="lp-row">
                  <label className="lp-check">
                    <input
                      type="checkbox"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                    />
                    <span className="lp-check-lbl">Nhớ đăng nhập</span>
                  </label>
                  <button type="button" className="lp-forgot">Quên mật khẩu?</button>
                </div>

                {/* submit */}
                <button type="submit" className="lp-submit" disabled={loading || success}>
                  {loading ? (
                    <><span className="lp-spin" /> Đang đăng nhập...</>
                  ) : (
                    <>Đăng nhập <IconArrow /></>
                  )}
                </button>

                <div className="lp-div">HOẶC</div>

                {/* google */}
                <button
                  type="button"
                  className="lp-google"
                  onClick={() => toast("Đăng nhập Google sẽ sớm ra mắt!")}
                >
                  <GoogleLogo />
                  Tiếp tục với Google
                </button>
              </form>

              <p className="lp-card-foot">
                Chưa có tài khoản?{" "}
                <a href="#" onClick={(e) => { e.preventDefault(); toast("Tính năng đăng ký sẽ sớm ra mắt!"); }}>
                  Đăng ký miễn phí
                </a>
              </p>
            </div>
          </div>
        </section>

        {/* ─── FOOTER ─── */}
        <footer className="lp-footer">
          <div className="lp-footer-brand">
            <IconPlane size={14} color="rgba(255,255,255,0.5)" />
            <span>
              © 2026 <span className="hi">TravelBuddy AI</span> — Nền tảng du lịch thông minh Việt Nam
            </span>
          </div>
          <div className="lp-footer-links">
            <a href="#">Về chúng tôi</a>
            <a href="#">Chính sách bảo mật</a>
            <a href="#">Điều khoản sử dụng</a>
            <a href="#">Liên hệ</a>
          </div>
        </footer>

      </div>
    </>
  );
}
