import { useState, useRef, useEffect, useCallback } from "react";

/* ════════════════════════════════════════════════════════════════════════════
   TravelBuddy AI — Chat engine dùng chung
   • useAssistant(): hook quản lý SSE streaming + vision + session
   • MessageList / Composer / Suggestions: thành phần UI tái sử dụng
   • Dùng bởi cả trang đầy đủ (/assistant) lẫn widget nổi trên mọi trang.

   API đi qua proxy: /api/session/{id}/stream (SSE) + /api/vision/identify.
   Vite (dev) proxy /api → :8001 ; nginx (prod) có location /api/session/ riêng
   để tắt buffering cho SSE.
═══════════════════════════════════════════════════════════════════════════════ */

// Cho phép override khi cần (VITE_API_BASE), mặc định đi qua proxy "/api".
export const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export const MODEL_OPTIONS = [
  { value: "openai", label: "OpenAI" },
  { value: "qwen3_4b", label: "Qwen3-4B" },
];

// ─────────────────────────────────────────────────────────────────────────────
//  CITATION & IMAGE PARSERS  (từ TOOL_CALL events)
// ─────────────────────────────────────────────────────────────────────────────

function isValidExternalUrl(url) {
  if (!url || typeof url !== "string") return false;
  const v = url.trim();
  if (!/^https?:\/\//i.test(v)) return false;
  try {
    const u = new URL(v);
    const host = (u.hostname || "").toLowerCase();
    if (!host) return false;
    if (host === "localhost" || host === "127.0.0.1" || host === "::1") return false;
    return true;
  } catch {
    return false;
  }
}

function parseCitations(events) {
  const map = {};
  for (const ev of (events || [])) {
    if (ev.event !== "TOOL_CALL") continue;
    const obs = ev.data?.observation || "";
    const patterns = [
      /\[(\d+)\]\s+([^\n]+)\n(?:🔗\s*)?URL:\s*(https?:\/\/\S+)/g,
      /\[(\d+)\]\s+([^\n]+)[\s\S]{0,160}?(https?:\/\/\S+)/g,
    ];
    for (const re of patterns) {
      let m;
      while ((m = re.exec(obs)) !== null) {
        const idx = m[1];
        const title = (m[2] || "").trim();
        const url = (m[3] || "").trim().replace(/[),.;]+$/, "");
        if (!idx || !isValidExternalUrl(url)) continue;
        if (!map[idx]) map[idx] = { title: title || `Nguon ${idx}`, url };
      }
    }
  }
  return map;
}

function extractJsonArray(raw) {
  const start = raw.indexOf("[");
  if (start < 0) return null;
  let depth = 0;
  for (let i = start; i < raw.length; i++) {
    const ch = raw[i];
    if (ch === "[") depth++;
    if (ch === "]") {
      depth--;
      if (depth === 0) return raw.slice(start, i + 1);
    }
  }
  return null;
}

function parseImages(events) {
  const images = [];
  for (const ev of (events || [])) {
    if (ev.event !== "TOOL_CALL") continue;
    const obs = ev.data?.observation || "";
    const marker = "IMAGES_JSON:";
    if (!obs.includes(marker)) continue;
    const after = obs.split(marker)[1] || "";
    const arrRaw = extractJsonArray(after.trim());
    if (!arrRaw) continue;
    try {
      const arr = JSON.parse(arrRaw);
      if (Array.isArray(arr)) images.push(...arr);
    } catch { /* ignore */ }
  }
  const dedup = [];
  const seen = new Set();
  for (const img of images) {
    const key = img?.url || img?.thumb;
    if (!key || seen.has(key)) continue;
    seen.add(key);
    dedup.push(img);
  }
  return dedup;
}

// ─────────────────────────────────────────────────────────────────────────────
//  MARKDOWN RENDERER
// ─────────────────────────────────────────────────────────────────────────────

function renderMd(raw, citations) {
  if (!raw) return "";
  // Safety net: never render structured-answer markers as literal text.
  raw = raw.replace(/\[\[PART:[a-z_]+\]\]/gi, "");
  const lines = raw.split("\n");
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (/^\s*---+\s*$/.test(line)) {
      out.push('<hr style="border:none;border-top:1px solid rgba(148,163,184,0.35);margin:10px 0;"/>');
      i++;
      continue;
    }
    if (/^\s*\|/.test(line)) {
      const tableLines = [];
      while (i < lines.length && /^\s*\|/.test(lines[i])) { tableLines.push(lines[i]); i++; }
      const rows = tableLines.filter(l => !/^\s*\|[-:\s|]+\|\s*$/.test(l));
      out.push('<div class="md-table-wrap"><table class="md-table">');
      rows.forEach((r, ri) => {
        const cells = r.split("|").filter((_, ci) => ci !== 0 && ci !== r.split("|").length - 1);
        const tag = ri === 0 ? "th" : "td";
        out.push(`<tr>${cells.map(c => `<${tag}>${inlineMd(c.trim(), citations)}</${tag}>`).join("")}</tr>`);
      });
      out.push("</table></div>");
      continue;
    }
    if (line.includes("\t")) {
      const tableLines = [];
      while (i < lines.length && lines[i].includes("\t")) { tableLines.push(lines[i]); i++; }
      const rows = tableLines.map(r => r.split("\t").map(c => c.trim())).filter(r => r.length >= 2 && r.some(c => c));
      if (rows.length > 0) {
        out.push('<div class="md-table-wrap"><table class="md-table">');
        rows.forEach((cells, ri) => {
          const tag = ri === 0 ? "th" : "td";
          out.push(`<tr>${cells.map(c => `<${tag}>${inlineMd(c, citations)}</${tag}>`).join("")}</tr>`);
        });
        out.push("</table></div>");
        continue;
      }
    }
    const h3 = line.match(/^### (.+)/);
    const h2 = line.match(/^## (.+)/);
    const h1 = line.match(/^# (.+)/);
    if (h3) { out.push(`<h3>${inlineMd(h3[1], citations)}</h3>`); i++; continue; }
    if (h2) { out.push(`<h2>${inlineMd(h2[1], citations)}</h2>`); i++; continue; }
    if (h1) { out.push(`<h1>${inlineMd(h1[1], citations)}</h1>`); i++; continue; }
    const num = line.match(/^(\d+)\. (.+)/);
    if (num) {
      const items = [];
      while (i < lines.length && lines[i].match(/^\d+\. /)) {
        items.push(`<li>${inlineMd(lines[i].replace(/^\d+\. /, ""), citations)}</li>`);
        i++;
      }
      out.push(`<ol>${items.join("")}</ol>`);
      continue;
    }
    const bul = line.match(/^[\-\*] (.+)/);
    if (bul) {
      const items = [];
      while (i < lines.length && lines[i].match(/^[\-\*] /)) {
        items.push(`<li>${inlineMd(lines[i].replace(/^[\-\*] /, ""), citations)}</li>`);
        i++;
      }
      out.push(`<ul>${items.join("")}</ul>`);
      continue;
    }
    if (line.trim() === "") { out.push("<br/>"); i++; continue; }
    out.push(`<p>${inlineMd(line, citations)}</p>`);
    i++;
  }
  return out.join("\n");
}

function inlineMd(text, citations) {
  return text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener" class="md-link">$1 ↗</a>')
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[(\d+)\]/g, (_, n) => {
      const c = citations && citations[n];
      if (!c || !isValidExternalUrl(c.url)) {
        return `<span class="cite-badge" aria-disabled="true">[${n}]</span>`;
      }
      const tip = c.title ? `title="${c.title.replace(/"/g, "&quot;")}"` : "";
      return `<a class="cite-badge" href="${c.url}" target="_blank" rel="noopener" ${tip}>[${n}]</a>`;
    });
}

// ─────────────────────────────────────────────────────────────────────────────
//  5-PART STRUCTURED ANSWER (TravelBuddy AI — tư vấn chuyến đi đầy đủ)
// ─────────────────────────────────────────────────────────────────────────────

const PART_META = {
  intro:     { icon: "🏝️", title: "Giới thiệu điểm đến" },
  itinerary: { icon: "📅", title: "Gợi ý lịch trình" },
  flights:   { icon: "✈️", title: "Chuyến bay" },
  hotels:    { icon: "🏨", title: "Khách sạn" },
  budget:    { icon: "💰", title: "Tổng kết ngân sách" },
};

// Tách câu trả lời theo các dòng đánh dấu [[PART:key]]. Trả về null khi không có
// marker (hỏi đáp tự do) để Message fallback về markdown thường.
function splitParts(raw) {
  if (!raw || !/\[\[PART:[a-z_]+\]\]/i.test(raw)) return null;
  const re = /\[\[PART:([a-z_]+)\]\]/gi;
  const marks = [];
  let m;
  while ((m = re.exec(raw)) !== null) {
    marks.push({ key: m[1].toLowerCase(), start: m.index, contentStart: re.lastIndex });
  }
  if (!marks.length) return null;
  const parts = [];
  const lead = raw.slice(0, marks[0].start).trim();
  if (lead) parts.push({ key: "_lead", body: lead });
  marks.forEach((mk, i) => {
    const end = i + 1 < marks.length ? marks[i + 1].start : raw.length;
    const body = raw.slice(mk.contentStart, end).trim();
    if (body) parts.push({ key: mk.key, body });
  });
  return parts.length ? parts : null;
}

// Lấy dòng tiêu đề (heading "### .." hoặc "**..**") ở đầu phần để làm header thẻ,
// đồng thời tách nó ra khỏi nội dung để không bị lặp tiêu đề.
function extractTitle(body) {
  const lines = body.split("\n");
  let i = 0;
  while (i < lines.length && lines[i].trim() === "") i++;
  if (i >= lines.length) return { title: null, body };
  const first = lines[i].trim();
  const h = first.match(/^#{1,4}\s+(.+?)\s*#*$/);
  const b = first.match(/^\*\*(.+?)\*\*\s*$/);
  let title = h ? h[1] : (b ? b[1] : null);
  if (!title) return { title: null, body };
  title = title.replace(/\*\*/g, "").replace(/`/g, "").trim();
  const rest = lines.slice(i + 1).join("\n").trim();
  return { title, body: rest };
}

function PartCards({ parts, theme, citations }) {
  const t = THEMES[theme];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      {parts.map((p, idx) => {
        const meta = PART_META[p.key];
        const { title: extractedTitle, body: extractedBody } = extractTitle(p.body);
        const titleText = extractedTitle || (meta ? meta.title : null);
        const bodyText = extractedTitle ? extractedBody : p.body;
        // Nếu tiêu đề đã mở đầu bằng emoji/ký hiệu thì không chèn icon nữa (tránh lặp).
        const startsWithLetter = titleText && /^[\p{L}\p{N}]/u.test(titleText);
        const icon = meta ? meta.icon : "📌";
        return (
          <div key={idx} style={{
            border: `1px solid ${t.msgBorder}`,
            borderRadius: "14px",
            overflow: "hidden",
            background: t.msgBg,
            boxShadow: theme === "dark" ? "0 2px 14px rgba(0,0,0,0.35)" : "0 2px 14px rgba(0,0,0,0.08)",
          }}>
            {titleText && (
              <div style={{
                display: "flex", alignItems: "center", gap: "9px",
                padding: "11px 16px",
                fontWeight: 700, fontSize: "16px", letterSpacing: "0.2px", lineHeight: "1.3",
                color: "#fff",
                background: "linear-gradient(135deg, #0ea5e9, #0284c7)",
              }}>
                {startsWithLetter && <span style={{ fontSize: "18px", flexShrink: 0 }}>{icon}</span>}
                <span>{titleText}</span>
              </div>
            )}
            <div className={`md-body md-${theme}`} style={{ padding: "12px 16px", fontSize: "14.5px", lineHeight: "1.65", color: t.text }}
              dangerouslySetInnerHTML={{ __html: renderMd(bodyText, citations) }} />
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  ICONS
// ─────────────────────────────────────────────────────────────────────────────

export const Icon = {
  Send: () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>),
  Plane: () => (<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21 4 19.5 2.5S18 2 16.5 3.5L13 7 4.8 5.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z" /></svg>),
  ChevronDown: ({ open }) => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.25s ease" }}><polyline points="6 9 12 15 18 9" /></svg>),
  Sun: () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>),
  Moon: () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>),
  Trash: () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" /><path d="M10 11v6" /><path d="M14 11v6" /><path d="M9 6V4h6v2" /></svg>),
  Cpu: () => (<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" /><line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" /><line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" /><line x1="20" y1="9" x2="23" y2="9" /><line x1="20" y1="14" x2="23" y2="14" /><line x1="1" y1="9" x2="4" y2="9" /><line x1="1" y1="14" x2="4" y2="14" /></svg>),
  ImageIcon: () => (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></svg>),
  X: () => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>),
  ExtLink: () => (<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>),
  Scan: () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2" /><path d="M17 3h2a2 2 0 0 1 2 2v2" /><path d="M21 17v2a2 2 0 0 1-2 2h-2" /><path d="M7 21H5a2 2 0 0 1-2-2v-2" /><line x1="7" y1="12" x2="17" y2="12" /></svg>),
  Brain: () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.7-3.6 2.5 2.5 0 0 1 .3-4.87A2.5 2.5 0 0 1 9.5 2Z" /><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.7-3.6 2.5 2.5 0 0 0-.3-4.87A2.5 2.5 0 0 0 14.5 2Z" /></svg>),
  Plus: () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>),
  History: () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v5h5" /><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8" /><path d="M12 7v5l4 2" /></svg>),
  Chat: () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>),
};

// ─────────────────────────────────────────────────────────────────────────────
//  THEMES
// ─────────────────────────────────────────────────────────────────────────────

export const THEMES = {
  dark: {
    bg: "radial-gradient(ellipse at 20% 50%, rgba(124,58,237,0.07) 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, rgba(6,182,212,0.05) 0%, transparent 55%), #080812",
    surface: "rgba(10,10,20,0.85)", surfaceBorder: "rgba(255,255,255,0.06)",
    msgBg: "rgba(30,30,50,0.9)", msgBorder: "rgba(255,255,255,0.08)",
    inputBg: "rgba(255,255,255,0.04)", inputBorder: "rgba(255,255,255,0.1)",
    text: "#cbd5e1", textDim: "#64748b", textDimmer: "#334155", textBright: "#f1f5f9",
    link: "#38bdf8", tableBorder: "rgba(255,255,255,0.08)",
    thinkBg: "rgba(15,15,25,0.8)", chipBorder: "rgba(255,255,255,0.08)", chipText: "#94a3b8",
    citeBg: "rgba(12,12,28,0.95)", citeBorder: "rgba(255,255,255,0.07)", citeHover: "rgba(124,58,237,0.1)",
    imgBorder: "rgba(255,255,255,0.09)", imgBg: "rgba(20,20,38,0.7)", previewBg: "rgba(124,58,237,0.12)",
  },
  light: {
    bg: "radial-gradient(ellipse at 20% 50%, rgba(14,165,233,0.05) 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, rgba(6,182,212,0.04) 0%, transparent 55%), #F0F9FF",
    surface: "rgba(255,255,255,0.92)", surfaceBorder: "rgba(14,165,233,0.12)",
    msgBg: "#ffffff", msgBorder: "rgba(14,165,233,0.12)",
    inputBg: "rgba(2,132,199,0.04)", inputBorder: "rgba(14,165,233,0.22)",
    text: "#334155", textDim: "#64748b", textDimmer: "#94a3b8", textBright: "#0F172A",
    link: "#0284c7", tableBorder: "rgba(14,165,233,0.15)",
    thinkBg: "rgba(240,249,255,0.9)", chipBorder: "rgba(14,165,233,0.2)", chipText: "#0369A1",
    citeBg: "rgba(240,249,255,0.98)", citeBorder: "rgba(14,165,233,0.12)", citeHover: "rgba(14,165,233,0.08)",
    imgBorder: "rgba(14,165,233,0.15)", imgBg: "rgba(240,249,255,0.6)", previewBg: "rgba(14,165,233,0.08)",
  },
};

const EVENT_META = {
  AGENT_START: { color: "#22d3ee", label: "START" },
  LLM_METRIC: { color: "#a78bfa", label: "METRIC" },
  AGENT_STEP: { color: "#34d399", label: "THINK" },
  TOOL_CALL: { color: "#fb923c", label: "TOOL" },
  AGENT_END: { color: "#22d3ee", label: "END" },
};

// ─────────────────────────────────────────────────────────────────────────────
//  PRESENTATIONAL SUBCOMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

function ImageGallery({ images, theme }) {
  const t = THEMES[theme];
  const [lightbox, setLightbox] = useState(null);
  if (!images || images.length === 0) return null;
  return (
    <>
      <div style={{ display: "flex", gap: "8px", overflowX: "auto", padding: "2px 0 10px", scrollbarWidth: "thin" }}>
        {images.map((img, i) => (
          <div key={i} onClick={() => setLightbox(img)} style={{
            flexShrink: 0, width: "145px", borderRadius: "10px", overflow: "hidden",
            cursor: "zoom-in", border: `1px solid ${t.imgBorder}`, background: t.imgBg,
            transition: "transform 0.2s, box-shadow 0.2s", boxShadow: "0 2px 8px rgba(0,0,0,0.14)",
          }}
            onMouseEnter={e => { e.currentTarget.style.transform = "scale(1.04)"; e.currentTarget.style.boxShadow = "0 6px 22px rgba(14,165,233,0.22)"; }}
            onMouseLeave={e => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.14)"; }}>
            <img src={img.thumb || img.url} alt={img.title || `Ảnh ${i + 1}`} loading="lazy"
              style={{ width: "100%", height: "92px", objectFit: "cover", display: "block" }}
              onError={e => { e.target.parentElement.style.display = "none"; }} />
            {img.title && (
              <div style={{ fontSize: "10px", color: t.textDim, padding: "4px 7px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{img.title}</div>
            )}
          </div>
        ))}
      </div>
      {lightbox && (
        <div onClick={() => setLightbox(null)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.88)", zIndex: 99999, display: "flex", alignItems: "center", justifyContent: "center", cursor: "zoom-out", backdropFilter: "blur(10px)" }}>
          <div onClick={e => e.stopPropagation()} style={{ maxWidth: "90vw", maxHeight: "85vh", borderRadius: "14px", overflow: "hidden", position: "relative", boxShadow: "0 20px 60px rgba(0,0,0,0.6)" }}>
            <img src={lightbox.url} alt={lightbox.title} style={{ maxWidth: "90vw", maxHeight: "80vh", objectFit: "contain", display: "block" }} />
            {lightbox.title && (
              <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "linear-gradient(transparent,rgba(0,0,0,0.82))", padding: "24px 14px 10px", fontSize: "12px", color: "#e2e8f0" }}>
                {lightbox.title}
                {lightbox.source && (<a href={lightbox.source} target="_blank" rel="noopener" onClick={e => e.stopPropagation()} style={{ color: "#7dd3fc", marginLeft: "8px", fontSize: "11px" }}>Nguồn ↗</a>)}
              </div>
            )}
            <button onClick={() => setLightbox(null)} style={{ position: "absolute", top: "10px", right: "10px", background: "rgba(0,0,0,0.55)", border: "none", borderRadius: "50%", width: "30px", height: "30px", cursor: "pointer", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center" }}><Icon.X /></button>
          </div>
        </div>
      )}
    </>
  );
}

function CitationPanel({ citations, theme }) {
  const t = THEMES[theme];
  const entries = Object.entries(citations).filter(([, v]) => isValidExternalUrl(v?.url)).sort(([a], [b]) => Number(a) - Number(b));
  if (entries.length === 0) return null;
  return (
    <div style={{ marginTop: "8px", padding: "9px 11px", background: t.citeBg, border: `1px solid ${t.citeBorder}`, borderRadius: "10px", fontSize: "11.5px" }}>
      <div style={{ fontSize: "9.5px", color: t.textDim, letterSpacing: "0.1em", fontWeight: "700", marginBottom: "7px", textTransform: "uppercase" }}>📚 Nguồn tham khảo</div>
      {entries.map(([num, { title, url }]) => (
        <a key={num} href={url} target="_blank" rel="noopener" style={{ display: "flex", alignItems: "flex-start", gap: "8px", padding: "5px 6px", borderRadius: "7px", color: "inherit", textDecoration: "none", transition: "background 0.15s", marginBottom: "2px" }}
          onMouseEnter={e => { e.currentTarget.style.background = t.citeHover; }}
          onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}>
          <span style={{ flexShrink: 0, width: "19px", height: "19px", background: "linear-gradient(135deg, #0ea5e9, #06b6d4)", borderRadius: "5px", fontSize: "10px", fontWeight: "800", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", marginTop: "1px" }}>{num}</span>
          <span style={{ flex: 1, minWidth: 0 }}>
            <span style={{ color: t.textBright, fontWeight: "500", display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: "11.5px" }}>{title}</span>
            <span style={{ color: t.link, fontSize: "10.5px", display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{url.replace(/^https?:\/\//, "").slice(0, 58)}{url.length > 63 ? "…" : ""}</span>
          </span>
          <span style={{ flexShrink: 0, opacity: 0.5, marginTop: "3px" }}><Icon.ExtLink /></span>
        </a>
      ))}
    </div>
  );
}

function ThinkingBlock({ events, theme }) {
  const [open, setOpen] = useState(false);
  if (!events || events.length === 0) return null;
  const t = THEMES[theme];
  const stepCount = events.filter(e => e.event === "AGENT_STEP").length;
  const toolCount = events.filter(e => e.event === "TOOL_CALL").length;
  const totalMs = events.filter(e => e.event === "LLM_METRIC").reduce((a, e) => a + (e.data.latency_ms || 0), 0);
  return (
    <div style={{ marginBottom: "6px" }}>
      <button onClick={() => setOpen(o => !o)} style={{ display: "flex", alignItems: "center", gap: "8px", background: "rgba(14,165,233,0.08)", border: "1px solid rgba(14,165,233,0.25)", borderRadius: "8px", padding: "6px 12px", color: "#0ea5e9", fontSize: "12px", fontFamily: "inherit", cursor: "pointer", transition: "all 0.2s", letterSpacing: "0.02em", maxWidth: "100%", overflow: "hidden" }}
        onMouseEnter={e => e.currentTarget.style.background = "rgba(14,165,233,0.15)"}
        onMouseLeave={e => e.currentTarget.style.background = "rgba(14,165,233,0.08)"}>
        <Icon.Cpu />
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          Đã suy luận {(totalMs / 1000).toFixed(1)}s · {stepCount} bước{toolCount > 0 ? ` · ${toolCount} tool` : ""}
        </span>
        <Icon.ChevronDown open={open} />
      </button>
      {open && (
        <div style={{ marginTop: "6px", background: t.thinkBg, border: "1px solid rgba(14,165,233,0.2)", borderRadius: "10px", padding: "12px", maxHeight: "380px", overflowY: "auto", fontFamily: "'JetBrains Mono','Fira Code',monospace", fontSize: "11.5px", lineHeight: "1.7" }}>
          {events.map((ev, i) => {
            const meta = EVENT_META[ev.event] || { color: "#94a3b8", label: ev.event };
            return (
              <div key={i} style={{ display: "flex", gap: "10px", alignItems: "flex-start", padding: "5px 0", borderBottom: i < events.length - 1 ? `1px solid ${t.tableBorder}` : "none" }}>
                <span style={{ color: meta.color, background: `${meta.color}18`, border: `1px solid ${meta.color}40`, borderRadius: "4px", padding: "1px 6px", fontSize: "10px", fontWeight: "700", letterSpacing: "0.08em", flexShrink: 0, marginTop: "1px" }}>{meta.label}</span>
                <EventBody ev={ev} theme={theme} />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function EventBody({ ev, theme }) {
  const d = ev.data;
  const ts = ev.timestamp ? ev.timestamp.split("T")[1]?.slice(0, 8) : "";
  const dim = { color: theme === "dark" ? "#475569" : "#9ca3af", fontSize: "10px" };
  const val = { color: theme === "dark" ? "#e2e8f0" : "#374151" };
  if (ev.event === "AGENT_START") return (<span style={val}><span style={dim}>[{ts}] </span>Input: <em style={{ color: "#0891b2" }}>"{d.input?.slice(0, 80)}{d.input?.length > 80 ? "…" : ""}"</em><span style={dim}> · {d.model}</span></span>);
  if (ev.event === "LLM_METRIC") return (<span style={val}><span style={dim}>[{ts}] </span><strong style={{ color: "#7c3aed" }}>{d.latency_ms}ms</strong>{d.total_tokens ? <span style={dim}> · {d.total_tokens} tok ({d.prompt_tokens}↑ {d.completion_tokens}↓)</span> : null}</span>);
  if (ev.event === "AGENT_STEP") return (<span style={{ color: theme === "dark" ? "#94a3b8" : "#6b7280", wordBreak: "break-word" }}><span style={dim}>[{ts}] Step {d.step}: </span><span style={{ color: theme === "dark" ? "#d1fae5" : "#065f46" }}>{d.response_preview?.slice(0, 200)}{d.response_preview?.length > 200 ? "…" : ""}</span></span>);
  if (ev.event === "TOOL_CALL") return (<span style={{ wordBreak: "break-word" }}><span style={dim}>[{ts}] </span><span style={{ color: "#ea580c", fontWeight: "700" }}>{d.tool}</span><span style={dim}>(</span><span style={{ color: "#b45309" }}>{d.arguments?.slice(0, 100)}</span><span style={dim}>)</span>{d.observation && <><br /><span style={{ color: "#059669" }}>→ {d.observation?.slice(0, 250)}</span></>}</span>);
  if (ev.event === "AGENT_END") return (<span style={val}><span style={dim}>[{ts}] </span>Xong trong <strong style={{ color: "#0891b2" }}>{d.steps} bước</strong></span>);
  return <span style={{ color: "#94a3b8" }}>{JSON.stringify(d).slice(0, 100)}</span>;
}

function TypingDots() {
  return (
    <div style={{ display: "flex", gap: "5px", alignItems: "center", padding: "2px 0" }}>
      {[0, 1, 2].map(i => (<div key={i} style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#0ea5e9", animation: `tb-bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />))}
    </div>
  );
}

function Message({ msg, theme }) {
  const isUser = msg.role === "user";
  const t = THEMES[theme];
  const citations = isUser ? {} : parseCitations(msg.events);
  const images = isUser ? [] : parseImages(msg.events);
  const hasCitations = Object.keys(citations).length > 0;
  const parts = (!isUser && !msg.loading) ? splitParts(msg.content) : null;
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: "20px", animation: "tb-fadeUp 0.3s ease" }}>
      {!isUser && (
        <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: "linear-gradient(135deg, #0ea5e9, #06b6d4)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginRight: "10px", marginTop: "2px", color: "#fff", boxShadow: "0 0 12px rgba(14,165,233,0.3)" }}><Icon.Plane /></div>
      )}
      <div style={{ maxWidth: "82%", minWidth: "60px" }}>
        {!isUser && <ThinkingBlock events={msg.events} theme={theme} />}
        {images.length > 0 && <ImageGallery images={images} theme={theme} />}
        {parts ? (
          <PartCards parts={parts} theme={theme} citations={citations} />
        ) : (
        <div style={{
          background: isUser ? "linear-gradient(135deg, #0ea5e9, #0284c7)" : t.msgBg,
          border: isUser ? "none" : `1px solid ${t.msgBorder}`,
          borderRadius: isUser ? "18px 18px 4px 18px" : "4px 18px 18px 18px",
          padding: "12px 16px", color: isUser ? "#f0f9ff" : t.text, fontSize: "14.5px", lineHeight: "1.65",
          boxShadow: isUser ? "0 4px 20px rgba(14,165,233,0.3)" : theme === "dark" ? "0 2px 12px rgba(0,0,0,0.3)" : "0 2px 12px rgba(0,0,0,0.07)",
        }}>
          {isUser && msg.imagePreview && (
            <div style={{ marginBottom: "8px" }}><img src={msg.imagePreview} alt="ảnh đính kèm" style={{ maxWidth: "200px", maxHeight: "155px", borderRadius: "8px", objectFit: "cover", display: "block" }} /></div>
          )}
          {isUser ? (<span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>)
            : msg.loading ? (<TypingDots />)
              : (<div className={`md-body md-${theme}`} dangerouslySetInnerHTML={{ __html: renderMd(msg.content, citations) }} />)}
        </div>
        )}
        {!isUser && !msg.loading && hasCitations && (<CitationPanel citations={citations} theme={theme} />)}
        {msg.took_ms && !isUser && (<div style={{ fontSize: "11px", color: t.textDim, marginTop: "4px", paddingLeft: "4px" }}>{(msg.took_ms / 1000).toFixed(2)}s</div>)}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  SHARED STYLES (inject once)
// ─────────────────────────────────────────────────────────────────────────────

export const ASSISTANT_CSS = `
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,300;0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');
@keyframes tb-fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes tb-bounce{0%,80%,100%{transform:scale(0.7);opacity:0.5}40%{transform:scale(1);opacity:1}}
@keyframes tb-pulse{0%,100%{opacity:0.4}50%{opacity:1}}
@keyframes tb-spin{to{transform:rotate(360deg)}}
@keyframes tb-pop{from{opacity:0;transform:translateY(16px) scale(0.96)}to{opacity:1;transform:translateY(0) scale(1)}}
a.cite-badge, span.cite-badge{display:inline-flex;align-items:center;justify-content:center;background:linear-gradient(135deg,rgba(14,165,233,0.2),rgba(6,182,212,0.16));border:1px solid rgba(14,165,233,0.38);border-radius:4px;padding:0 5px;font-size:10px;font-weight:800;color:#0284c7;text-decoration:none;margin:0 1px;vertical-align:super;line-height:1.6;transition:background 0.15s,color 0.15s;cursor:pointer;font-family:'JetBrains Mono',monospace;}
a.cite-badge:hover{background:rgba(14,165,233,0.42);color:#fff;}
span.cite-badge[aria-disabled="true"]{opacity:0.65;cursor:default;}
.md-body{font-family:'Be Vietnam Pro',sans-serif}
.md-body h1,.md-body h2,.md-body h3{margin:10px 0 4px;font-weight:600}
.md-body ul,.md-body ol{padding-left:20px;margin:6px 0}
.md-body li{margin:3px 0}
.md-body p{margin:4px 0}
.md-body code{padding:1px 5px;border-radius:3px;font-family:'JetBrains Mono',monospace;font-size:12.5px}
.md-body strong{font-weight:600}
.md-body em{font-style:italic}
.md-dark .md-table-wrap{overflow-x:auto;margin:10px 0;border-radius:8px;border:1px solid rgba(255,255,255,0.08)}
.md-dark .md-table{width:100%;border-collapse:collapse;font-size:13.5px}
.md-dark .md-table th{background:rgba(14,165,233,0.2);color:#e2e8f0;font-weight:600;padding:8px 12px;text-align:left;font-size:12.5px}
.md-dark .md-table td{padding:7px 12px;border-top:1px solid rgba(255,255,255,0.06);color:#cbd5e1}
.md-dark .md-table tr:nth-child(even) td{background:rgba(255,255,255,0.03)}
.md-dark .md-link{color:#38bdf8;text-decoration:none}.md-dark .md-link:hover{text-decoration:underline}
.md-dark h1,.md-dark h2,.md-dark h3{color:#e2e8f0}.md-dark strong{color:#e2e8f0}.md-dark em{color:#7dd3fc}
.md-dark code{color:#67e8f9;background:rgba(103,232,249,0.08)}
.md-light .md-table-wrap{overflow-x:auto;margin:10px 0;border-radius:8px;border:1px solid rgba(14,165,233,0.18)}
.md-light .md-table{width:100%;border-collapse:collapse;font-size:13.5px}
.md-light .md-table th{background:rgba(14,165,233,0.1);color:#0369a1;font-weight:700;padding:8px 12px;text-align:left;font-size:12.5px}
.md-light .md-table td{padding:7px 12px;border-top:1px solid rgba(14,165,233,0.1);color:#334155}
.md-light .md-table tr:nth-child(even) td{background:rgba(14,165,233,0.03)}
.md-light .md-link{color:#0284c7;text-decoration:none}.md-light .md-link:hover{text-decoration:underline}
.md-light h1,.md-light h2,.md-light h3{color:#0F172A}.md-light strong{color:#0F172A}.md-light em{color:#0369a1}
.md-light code{color:#0369a1;background:rgba(3,105,161,0.08)}
.tb-scroll::-webkit-scrollbar{width:5px;height:5px}.tb-scroll::-webkit-scrollbar-track{background:transparent}.tb-scroll::-webkit-scrollbar-thumb{background:rgba(14,165,233,0.3);border-radius:3px}
`;

// ─────────────────────────────────────────────────────────────────────────────
//  IMAGE NORMALIZER (cho vision)
// ─────────────────────────────────────────────────────────────────────────────

async function normalizeImageForVision(file) {
  const toDataUrl = (blob) => new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = (ev) => resolve(ev.target.result);
    fr.onerror = reject;
    fr.readAsDataURL(blob);
  });
  const fileDataUrl = await toDataUrl(file);
  const img = new Image();
  await new Promise((resolve, reject) => { img.onload = resolve; img.onerror = reject; img.src = fileDataUrl; });
  const maxSide = 1280;
  const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
  const w = Math.max(1, Math.round(img.width * scale));
  const h = Math.max(1, Math.round(img.height * scale));
  const canvas = document.createElement("canvas");
  canvas.width = w; canvas.height = h;
  canvas.getContext("2d").drawImage(img, 0, 0, w, h);
  const jpegDataUrl = canvas.toDataURL("image/jpeg", 0.9);
  return { preview: jpegDataUrl, mediaType: "image/jpeg", base64: jpegDataUrl.split(",")[1] };
}

const WELCOME = {
  role: "assistant",
  content: "Xin chào! Tôi là **TravelBuddy** 🌏 — trợ lý du lịch thông minh của bạn.\n\nTôi có thể giúp bạn:\n- Giới thiệu **điểm đến** & gợi ý **lịch trình** theo ngày\n- Tìm **chuyến bay** và **khách sạn** phù hợp ngân sách\n- Tra **thời tiết**, **visa**, **tỷ giá**, **hành trang**\n- 📸 **Upload ảnh** địa điểm để nhận diện\n\nHãy cho tôi biết bạn muốn đi đâu! ✈️",
  events: [],
};

// ─────────────────────────────────────────────────────────────────────────────
//  LỊCH SỬ HỘI THOẠI — lưu localStorage (mỗi cuộc trò chuyện 1 session_id)
// ─────────────────────────────────────────────────────────────────────────────

const LS_INDEX = "tb_chat_index";              // [{id, title, updatedAt}]
const LS_MSGS = (id) => `tb_chat_msgs_${id}`;  // mảng message của 1 cuộc

const newId = () => (crypto.randomUUID ? crypto.randomUUID() : "c-" + Date.now() + "-" + Math.floor(Math.random() * 1e6));

function loadIndex() {
  try { return JSON.parse(localStorage.getItem(LS_INDEX)) || []; } catch { return []; }
}
function saveIndex(list) {
  try { localStorage.setItem(LS_INDEX, JSON.stringify(list)); } catch { /* quota */ }
}
function loadMsgs(id) {
  try { return JSON.parse(localStorage.getItem(LS_MSGS(id))); } catch { return null; }
}
function saveMsgs(id, msgs) {
  // Bỏ ảnh base64 (imagePreview) để không vượt quota; giữ events cho citations/gallery.
  const slim = (msgs || []).map(m => ({
    role: m.role, content: m.content, events: m.events || [],
    took_ms: m.took_ms, hadImage: !!m.imagePreview,
  }));
  try { localStorage.setItem(LS_MSGS(id), JSON.stringify(slim)); } catch { /* quota */ }
}
function dropMsgs(id) {
  try { localStorage.removeItem(LS_MSGS(id)); } catch { /* ignore */ }
}
function deriveTitle(msgs) {
  const firstUser = (msgs || []).find(m => m.role === "user" && (m.content || "").trim());
  const txt = (firstUser?.content || "").trim().replace(/\s+/g, " ");
  if (!txt) return "Cuộc trò chuyện mới";
  return txt.length > 42 ? txt.slice(0, 42) + "…" : txt;
}

// ═════════════════════════════════════════════════════════════════════════════
//  HOOK: useAssistant — toàn bộ logic chat (SSE + vision + session)
// ═════════════════════════════════════════════════════════════════════════════

export function useAssistant() {
  // ── Lịch sử hội thoại: khôi phục cuộc gần nhất khi mở lại ──────────────────
  const [chatList, setChatList] = useState(() => loadIndex());
  const [currentId, setCurrentId] = useState(() => {
    const idx = loadIndex();
    return idx.length ? idx[0].id : newId();
  });
  const [messages, setMessages] = useState(() => {
    const idx = loadIndex();
    if (idx.length) {
      const m = loadMsgs(idx[0].id);
      if (m && m.length) return m;
    }
    return [WELCOME];
  });

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [thinkingEnabled, setThinkingEnabled] = useState(false);
  const [selectedModel, setSelectedModel] = useState("openai");

  const [imagePreview, setImagePreview] = useState(null);
  const [imageBase64, setImageBase64] = useState(null);
  const [imageMediaType, setImageMediaType] = useState("image/jpeg");
  const [identifyingImage, setIdentifyingImage] = useState(false);

  // Lưu cuộc trò chuyện hiện tại vào localStorage khi có ít nhất 1 tin nhắn user.
  useEffect(() => {
    if (!messages.some(m => m.role === "user")) return;
    saveMsgs(currentId, messages);
    setChatList(prev => {
      const meta = { id: currentId, title: deriveTitle(messages), updatedAt: Date.now() };
      const next = [meta, ...prev.filter(c => c.id !== currentId)].sort((a, b) => b.updatedAt - a.updatedAt);
      saveIndex(next);
      return next;
    });
  }, [messages, currentId]);

  const handleImageSelect = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const n = await normalizeImageForVision(file);
      setImageMediaType(n.mediaType); setImagePreview(n.preview); setImageBase64(n.base64);
    } catch {
      setImageMediaType(file.type || "image/jpeg");
      const reader = new FileReader();
      reader.onload = (ev) => { const d = ev.target.result; setImagePreview(d); setImageBase64(d.split(",")[1]); };
      reader.readAsDataURL(file);
    }
    e.target.value = "";
  }, []);

  const clearImage = useCallback(() => { setImagePreview(null); setImageBase64(null); }, []);

  const sendMessage = useCallback(async (overrideText) => {
    const text = (overrideText !== undefined ? overrideText : input).trim();
    if ((!text && !imageBase64) || loading) return;
    setInput("");
    setLoading(true);

    let finalMessage = text;
    const capturedPreview = imagePreview;
    const capturedBase64 = imageBase64;
    const capturedMT = imageMediaType;
    clearImage();

    if (capturedBase64) {
      setIdentifyingImage(true);
      try {
        const vr = await fetch(`${API_BASE}/vision/identify`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: capturedBase64, media_type: capturedMT }),
        });
        if (vr.ok) {
          const vd = await vr.json();
          const identified = vd.result || "";
          finalMessage = identified
            ? identified + "\n\n" + (text || "Bạn có thể tư vấn chuyến đi đến đây cho tôi không?")
            : (text || "Đây là ảnh địa điểm nào? Bạn có thể tư vấn không?");
        } else {
          let reason = "Khong nhan dien duoc anh";
          try { reason = (await vr.json())?.detail || reason; } catch { /* ignore */ }
          finalMessage = [text || "Tôi muốn đến địa điểm trong ảnh", "", `Luu y he thong: Vision nhan dien anh that bai (${reason}).`, "Hay uu tien giup nguoi dung xac dinh dia diem tu mo ta anh."].join("\n");
        }
      } catch {
        finalMessage = [text || "Tôi muốn đến địa điểm trong ảnh", "", "Luu y he thong: Khong ket noi duoc dich vu nhan dien anh.", "Hay giup nguoi dung xac dinh dia diem bang cach hoi them dac diem nhan dang."].join("\n");
      }
      setIdentifyingImage(false);
    }

    setMessages(prev => [...prev, { role: "user", content: text || "(Đính kèm ảnh)", imagePreview: capturedPreview }]);
    const _id = Date.now();
    setMessages(prev => [...prev, { role: "assistant", content: "", loading: true, events: [], _id }]);

    const collectedEvents = [];
    try {
      const url = `${API_BASE}/session/${currentId}/stream?message=${encodeURIComponent(finalMessage)}&enable_thinking=${thinkingEnabled}&model_choice=${encodeURIComponent(selectedModel)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const ev = JSON.parse(line.slice(6));
            collectedEvents.push(ev);
            if (ev.event === "AGENT_END") {
              setMessages(prev => prev.map(m => m._id === _id ? { ...m, loading: false, content: ev.data.final_answer, events: [...collectedEvents] } : m));
            } else {
              setMessages(prev => prev.map(m => m._id === _id ? { ...m, events: [...collectedEvents] } : m));
            }
          } catch { /* ignore */ }
        }
      }
    } catch (err) {
      setMessages(prev => prev.map(m => m._id === _id ? { ...m, loading: false, content: `❌ Lỗi kết nối: ${err.message}\n\nKiểm tra máy chủ AI.`, events: collectedEvents } : m));
    }
    setLoading(false);
  }, [input, loading, currentId, imagePreview, imageBase64, imageMediaType, clearImage, thinkingEnabled, selectedModel]);

  // ── Quản lý lịch sử ─────────────────────────────────────────────────────────
  const newChat = useCallback(() => {
    if (loading) return;
    clearImage();
    setCurrentId(newId());
    setMessages([WELCOME]);
    setInput("");
  }, [loading, clearImage]);

  const selectChat = useCallback((id) => {
    if (loading || id === currentId) return;
    clearImage();
    const m = loadMsgs(id);
    setCurrentId(id);
    setMessages(m && m.length ? m : [WELCOME]);
    setInput("");
  }, [loading, currentId, clearImage]);

  const deleteChat = useCallback((id) => {
    fetch(`${API_BASE}/session/${id}`, { method: "DELETE" }).catch(() => { });
    dropMsgs(id);
    setChatList(prev => {
      const next = prev.filter(c => c.id !== id);
      saveIndex(next);
      if (id === currentId) {
        clearImage();
        if (next.length) {
          const nm = loadMsgs(next[0].id);
          setCurrentId(next[0].id);
          setMessages(nm && nm.length ? nm : [WELCOME]);
        } else {
          setCurrentId(newId());
          setMessages([WELCOME]);
        }
      }
      return next;
    });
  }, [currentId, clearImage]);

  // "Xoá hội thoại" hiện tại = xoá luôn khỏi lịch sử.
  const clearChat = useCallback(() => deleteChat(currentId), [deleteChat, currentId]);

  return {
    messages, input, setInput, loading, sessionId: currentId,
    thinkingEnabled, setThinkingEnabled, selectedModel, setSelectedModel,
    imagePreview, imageBase64, identifyingImage,
    handleImageSelect, clearImage, sendMessage, clearChat,
    chatList, currentId, newChat, selectChat, deleteChat,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
//  MESSAGE LIST
// ─────────────────────────────────────────────────────────────────────────────

export function MessageList({ messages, theme, identifyingImage }) {
  const t = THEMES[theme];
  const bottomRef = useRef(null);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  return (
    <>
      {messages.map((msg, i) => <Message key={msg._id || i} msg={msg} theme={theme} />)}
      {identifyingImage && (
        <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "12px", animation: "tb-fadeUp 0.3s ease" }}>
          <div style={{ background: t.msgBg, border: `1px solid ${t.msgBorder}`, borderRadius: "14px", padding: "10px 16px", fontSize: "13px", color: t.textDim, display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{ width: "14px", height: "14px", border: "2px solid #0ea5e9", borderTopColor: "transparent", borderRadius: "50%", animation: "tb-spin 0.8s linear infinite" }} />
            🔍 Đang nhận diện địa điểm từ ảnh…
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  COMPOSER (input bar)
// ─────────────────────────────────────────────────────────────────────────────

export function Composer({ chat, theme, fileInputRef, compact = false }) {
  const t = THEMES[theme];
  const inputRef = useRef(null);
  const { input, setInput, loading, sendMessage, imagePreview, clearImage,
    thinkingEnabled, setThinkingEnabled, selectedModel, setSelectedModel } = chat;
  const canSend = !loading && (!!input.trim() || !!chat.imageBase64);
  const handleKey = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); inputRef.current?.focus(); } };

  return (
    <div>
      {imagePreview && (
        <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 12px", marginBottom: "8px", background: t.previewBg, border: "1px solid rgba(14,165,233,0.25)", borderRadius: "10px" }}>
          <img src={imagePreview} alt="preview" style={{ width: "44px", height: "44px", borderRadius: "7px", objectFit: "cover" }} />
          <div style={{ flex: 1, fontSize: "12px", color: "#0284c7", lineHeight: "1.4" }}>📸 <strong>Ảnh đính kèm</strong> — AI sẽ nhận diện địa điểm khi gửi</div>
          <button onClick={clearImage} style={{ background: "rgba(248,113,113,0.12)", border: "1px solid rgba(248,113,113,0.28)", borderRadius: "7px", padding: "4px 10px", cursor: "pointer", color: "#ef4444", display: "flex", alignItems: "center", gap: "4px", fontSize: "11.5px", fontFamily: "inherit" }}><Icon.X /> Xoá</button>
        </div>
      )}
      <div style={{ display: "flex", gap: "8px", alignItems: "flex-end", background: t.inputBg, border: `1px solid ${loading ? "rgba(14,165,233,0.4)" : imagePreview ? "rgba(14,165,233,0.35)" : t.inputBorder}`, borderRadius: "14px", padding: "9px 9px 9px 11px", transition: "border-color 0.2s" }}>
        <button onClick={() => fileInputRef.current?.click()} disabled={loading} title="Đính kèm ảnh địa điểm" style={{ width: "34px", height: "34px", borderRadius: "9px", flexShrink: 0, background: imagePreview ? "rgba(14,165,233,0.18)" : t.inputBg, border: `1px solid ${imagePreview ? "rgba(14,165,233,0.45)" : t.inputBorder}`, cursor: loading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", color: imagePreview ? "#0284c7" : t.textDim }}><Icon.ImageIcon /></button>
        {!compact && (
          <>
            <button onClick={() => setThinkingEnabled(v => !v)} disabled={loading} title="Bật/tắt thinking mode (tool calling tắt khi bật)" style={{ height: "34px", borderRadius: "9px", flexShrink: 0, background: thinkingEnabled ? "linear-gradient(135deg, rgba(14,165,233,0.25), rgba(6,182,212,0.15))" : t.inputBg, border: thinkingEnabled ? "1px solid rgba(14,165,233,0.55)" : `1px solid ${t.inputBorder}`, padding: "0 9px", color: thinkingEnabled ? "#0284c7" : t.textDim, cursor: loading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", gap: "5px", fontSize: "11.5px", fontFamily: "inherit" }}><Icon.Brain /> {thinkingEnabled ? "ON" : "OFF"}</button>
            <select value={selectedModel} onChange={e => setSelectedModel(e.target.value)} disabled={loading} title="Chọn model" style={{ height: "34px", borderRadius: "9px", border: `1px solid ${t.inputBorder}`, background: t.inputBg, color: t.text, padding: "0 9px", fontSize: "12px", fontFamily: "inherit", flexShrink: 0, cursor: loading ? "not-allowed" : "pointer" }}>
              {MODEL_OPTIONS.map(opt => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
            </select>
          </>
        )}
        <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
          placeholder={imagePreview ? "Thêm câu hỏi về địa điểm này…" : "Hỏi về điểm đến, vé, khách sạn, thời tiết…"}
          disabled={loading} rows={1}
          style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: t.text, fontSize: "14.5px", fontFamily: "inherit", resize: "none", lineHeight: "1.5", maxHeight: "120px", overflowY: "auto", opacity: loading ? 0.5 : 1 }}
          onInput={e => { e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px"; }} />
        <button onClick={() => sendMessage()} disabled={!canSend} style={{ width: "38px", height: "38px", borderRadius: "10px", flexShrink: 0, background: !canSend ? "rgba(14,165,233,0.15)" : "linear-gradient(135deg, #0ea5e9, #0284c7)", border: "none", cursor: !canSend ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", color: !canSend ? t.textDim : "white", transition: "all 0.2s", boxShadow: !canSend ? "none" : "0 4px 15px rgba(14,165,233,0.4)" }}>
          {loading ? <div style={{ width: "16px", height: "16px", border: `2px solid ${t.textDimmer}`, borderTopColor: "#0ea5e9", borderRadius: "50%", animation: "tb-spin 0.8s linear infinite" }} /> : <Icon.Send />}
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  SUGGESTION CHIPS
// ─────────────────────────────────────────────────────────────────────────────

export const DEFAULT_SUGGESTIONS = [
  "Gợi ý lịch trình Đà Nẵng 3 ngày, 2 người",
  "Tôi muốn đi Phú Quốc 2 đêm, budget 5 triệu từ Hà Nội",
  "Thời tiết Đà Lạt tuần này thế nào?",
  "Đi Nhật Bản có cần visa không?",
];

export function Suggestions({ items, onPick, theme }) {
  const t = THEMES[theme];
  return (
    <div style={{ display: "flex", gap: "8px", justifyContent: "center", padding: "0 16px 10px", flexWrap: "wrap" }}>
      {(items || DEFAULT_SUGGESTIONS).map((s, i) => (
        <button key={i} onClick={() => onPick(s)} style={{ background: t.inputBg, border: `1px solid ${t.chipBorder}`, borderRadius: "20px", padding: "7px 14px", color: t.chipText, fontSize: "12.5px", cursor: "pointer", transition: "all 0.2s", fontFamily: "inherit" }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(14,165,233,0.5)"; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = t.chipBorder; }}>{s}</button>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  CHAT HISTORY — danh sách cuộc trò chuyện (sidebar trang / list trong widget)
// ─────────────────────────────────────────────────────────────────────────────

export function ChatHistory({ chat, theme, onSelect }) {
  const t = THEMES[theme];
  const { chatList, currentId, newChat, selectChat, deleteChat } = chat;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      <button onClick={newChat} style={{
        display: "flex", alignItems: "center", justifyContent: "center", gap: "7px",
        margin: "0 0 10px", padding: "10px", borderRadius: "11px", border: "none", cursor: "pointer",
        background: "linear-gradient(135deg, #0ea5e9, #0284c7)", color: "#fff",
        fontFamily: "inherit", fontWeight: 700, fontSize: "13.5px", flexShrink: 0,
        boxShadow: "0 4px 14px rgba(14,165,233,0.3)",
      }}>
        <Icon.Plus /> Cuộc trò chuyện mới
      </button>

      <div className="tb-scroll" style={{ flex: 1, overflowY: "auto", minHeight: 0 }}>
        {chatList.length === 0 && (
          <div style={{ fontSize: "12.5px", color: t.textDim, textAlign: "center", padding: "18px 8px", lineHeight: 1.5 }}>
            Chưa có lịch sử.<br />Hãy bắt đầu một cuộc trò chuyện!
          </div>
        )}
        {chatList.map((c) => {
          const active = c.id === currentId;
          return (
            <div key={c.id}
              onClick={() => { selectChat(c.id); onSelect && onSelect(); }}
              style={{
                display: "flex", alignItems: "center", gap: "8px", padding: "9px 10px",
                borderRadius: "10px", marginBottom: "3px", cursor: "pointer",
                background: active ? "rgba(14,165,233,0.12)" : "transparent",
                border: `1px solid ${active ? "rgba(14,165,233,0.3)" : "transparent"}`,
                transition: "background 0.15s",
              }}
              onMouseEnter={e => { if (!active) e.currentTarget.style.background = t.citeHover; }}
              onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}>
              <span style={{ color: active ? "#0284c7" : t.textDim, flexShrink: 0 }}><Icon.Chat /></span>
              <span style={{ flex: 1, minWidth: 0, fontSize: "13px", color: active ? t.textBright : t.text, fontWeight: active ? 600 : 400, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.title}</span>
              <button title="Xoá" onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }}
                style={{ flexShrink: 0, background: "none", border: "none", cursor: "pointer", color: t.textDimmer, padding: "2px", display: "flex", alignItems: "center", borderRadius: "5px" }}
                onMouseEnter={e => { e.currentTarget.style.color = "#ef4444"; }}
                onMouseLeave={e => { e.currentTarget.style.color = t.textDimmer; }}>
                <Icon.Trash />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
