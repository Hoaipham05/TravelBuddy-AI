/* ════════════════════════════════════════════════════════════
   In-app toast + modal dialogs — thay cho alert()/confirm() mặc định.
   Dùng được ở bất cứ đâu: import { toast, alertDialog, confirmDialog }.
═══════════════════════════════════════════════════════════════ */

const CSS = `
@keyframes tb-toast-in { from { opacity:0; transform:translate(-50%,14px); } to { opacity:1; transform:translate(-50%,0); } }
.tb-toast {
  position:fixed; bottom:1.75rem; left:50%; transform:translate(-50%,14px);
  background:#0F172A; color:#fff; padding:0.875rem 1.5rem; border-radius:12px;
  font-family:'Nunito',sans-serif; font-size:0.9375rem; font-weight:700;
  z-index:3000; box-shadow:0 12px 30px rgba(0,0,0,0.32); opacity:0;
  transition:opacity 0.25s, transform 0.25s; max-width:90vw; text-align:center;
}
.tb-toast.in { opacity:1; transform:translate(-50%,0); }

.tb-modal-overlay {
  position:fixed; inset:0; z-index:3100;
  background:rgba(8,15,30,0.55); backdrop-filter:blur(4px); -webkit-backdrop-filter:blur(4px);
  display:flex; align-items:center; justify-content:center; padding:1.5rem;
  opacity:0; transition:opacity 0.2s;
}
.tb-modal-overlay.in { opacity:1; }
.tb-modal {
  background:#fff; border-radius:18px; width:100%; max-width:400px;
  box-shadow:0 24px 64px rgba(15,23,42,0.3); padding:1.75rem;
  transform:translateY(12px) scale(0.97); transition:transform 0.22s cubic-bezier(0.22,1,0.36,1);
  font-family:'Inter',-apple-system,sans-serif;
}
.tb-modal-overlay.in .tb-modal { transform:translateY(0) scale(1); }
.tb-modal-icon {
  width:48px; height:48px; border-radius:14px; display:flex; align-items:center; justify-content:center;
  font-size:1.5rem; margin-bottom:1rem; background:linear-gradient(135deg,#0EA5E9,#0284C7); color:#fff;
}
.tb-modal-icon.danger { background:linear-gradient(135deg,#FB7185,#E11D48); }
.tb-modal-title { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.25rem; color:#0F172A; margin-bottom:0.4rem; letter-spacing:-0.01em; }
.tb-modal-msg { font-size:0.9375rem; color:#475569; line-height:1.6; margin-bottom:1.5rem; }
.tb-modal-actions { display:flex; gap:0.625rem; justify-content:flex-end; }
.tb-modal-btn {
  padding:0.625rem 1.25rem; border-radius:11px; border:none;
  font-family:'Nunito',sans-serif; font-weight:800; font-size:0.875rem; cursor:pointer;
  transition:transform 0.15s, box-shadow 0.15s, background 0.15s;
}
.tb-modal-ok { background:linear-gradient(135deg,#0EA5E9,#0284C7); color:#fff; box-shadow:0 5px 14px rgba(14,165,233,0.38); }
.tb-modal-ok:hover { transform:translateY(-1px); box-shadow:0 8px 20px rgba(14,165,233,0.46); }
.tb-modal-ok.danger { background:linear-gradient(135deg,#FB7185,#E11D48); box-shadow:0 5px 14px rgba(225,29,72,0.38); }
.tb-modal-cancel { background:#fff; border:1.5px solid #E2E8F0; color:#64748B; }
.tb-modal-cancel:hover { border-color:#CBD5E1; background:#F8FAFC; }
`;

let injected = false;
function ensureCSS() {
  if (injected || typeof document === "undefined") return;
  injected = true;
  const s = document.createElement("style");
  s.setAttribute("data-tb-dialog", "");
  s.textContent = CSS;
  document.head.appendChild(s);
}

export function toast(message, ms = 2600) {
  ensureCSS();
  const el = document.createElement("div");
  el.className = "tb-toast";
  el.textContent = message;
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add("in"));
  setTimeout(() => {
    el.classList.remove("in");
    setTimeout(() => el.remove(), 260);
  }, ms);
}

function dialog({ title, message, icon, okText = "Đồng ý", cancelText, danger }) {
  ensureCSS();
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "tb-modal-overlay";

    const card = document.createElement("div");
    card.className = "tb-modal";

    if (icon) {
      const ic = document.createElement("div");
      ic.className = "tb-modal-icon" + (danger ? " danger" : "");
      ic.textContent = icon;
      card.appendChild(ic);
    }
    if (title) {
      const t = document.createElement("div");
      t.className = "tb-modal-title";
      t.textContent = title;
      card.appendChild(t);
    }
    const msg = document.createElement("div");
    msg.className = "tb-modal-msg";
    msg.textContent = message;
    card.appendChild(msg);

    const actions = document.createElement("div");
    actions.className = "tb-modal-actions";

    let cancelBtn = null;
    if (cancelText) {
      cancelBtn = document.createElement("button");
      cancelBtn.className = "tb-modal-btn tb-modal-cancel";
      cancelBtn.textContent = cancelText;
      actions.appendChild(cancelBtn);
    }
    const okBtn = document.createElement("button");
    okBtn.className = "tb-modal-btn tb-modal-ok" + (danger ? " danger" : "");
    okBtn.textContent = okText;
    actions.appendChild(okBtn);

    card.appendChild(actions);
    overlay.appendChild(card);
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add("in"));

    const close = (val) => {
      overlay.classList.remove("in");
      document.removeEventListener("keydown", onKey);
      setTimeout(() => overlay.remove(), 200);
      resolve(val);
    };
    const onKey = (e) => {
      if (e.key === "Escape") close(false);
      else if (e.key === "Enter") close(true);
    };

    okBtn.addEventListener("click", () => close(true));
    if (cancelBtn) cancelBtn.addEventListener("click", () => close(false));
    overlay.addEventListener("click", (e) => { if (e.target === overlay) close(false); });
    document.addEventListener("keydown", onKey);
    setTimeout(() => okBtn.focus(), 60);
  });
}

export function alertDialog(message, opts = {}) {
  return dialog({ title: opts.title, message, icon: opts.icon ?? "ℹ️", okText: opts.okText || "Đã hiểu" });
}

export function confirmDialog(message, opts = {}) {
  return dialog({
    title: opts.title,
    message,
    icon: opts.icon ?? (opts.danger ? "⚠️" : "❓"),
    okText: opts.okText || "Đồng ý",
    cancelText: opts.cancelText || "Huỷ",
    danger: opts.danger,
  });
}
