import { useState, useRef, useEffect, useCallback } from "react";

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

/** Parse [N] Title\n🔗 URL: https://... từ web_search observation */
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
  return map; // { "1": {title, url}, ... }
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

/** Parse 🖼️ IMAGES_JSON:[...] từ search_images observation */
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
    } catch {
      // ignore malformed payload
    }
  }

  const dedup = [];
  const seen = new Set();
  for (const img of images) {
    const key = img?.url || img?.thumb;
    if (!key || seen.has(key)) continue;
    seen.add(key);
    dedup.push(img);
  }
  return dedup; // [{url, title, thumb, source}, ...]
}

// ─────────────────────────────────────────────────────────────────────────────
//  MARKDOWN RENDERER
// ─────────────────────────────────────────────────────────────────────────────

function renderMd(raw, citations) {
  if (!raw) return "";
  const lines = raw.split("\n");
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    // Horizontal rule: ---
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

    // Tab-delimited table fallback (common in model outputs)
    if (line.includes("\t")) {
      const tableLines = [];
      while (i < lines.length && lines[i].includes("\t")) {
        tableLines.push(lines[i]);
        i++;
      }
      const rows = tableLines
        .map(r => r.split("\t").map(c => c.trim()))
        .filter(r => r.length >= 2 && r.some(c => c));
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
//  ICONS
// ─────────────────────────────────────────────────────────────────────────────

const Icon = {
  Send: () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>),
  Plane: () => (<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21 4 19.5 2.5S18 2 16.5 3.5L13 7 4.8 5.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>),
  ChevronDown: ({ open }) => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.25s ease" }}><polyline points="6 9 12 15 18 9"/></svg>),
  Sun: () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>),
  Moon: () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>),
  Trash: () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>),
  Cpu: () => (<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>),
  ImageIcon: () => (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>),
  X: () => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>),
  ExtLink: () => (<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>),
  Scan: () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/></svg>),
  Brain: () => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.7-3.6 2.5 2.5 0 0 1 .3-4.87A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.7-3.6 2.5 2.5 0 0 0-.3-4.87A2.5 2.5 0 0 0 14.5 2Z"/></svg>),
};

// ─────────────────────────────────────────────────────────────────────────────
//  THEMES
// ─────────────────────────────────────────────────────────────────────────────

const THEMES = {
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
    bg: "radial-gradient(ellipse at 20% 50%, rgba(124,58,237,0.04) 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, rgba(6,182,212,0.03) 0%, transparent 55%), #f8f7ff",
    surface: "rgba(255,255,255,0.92)", surfaceBorder: "rgba(0,0,0,0.08)",
    msgBg: "#ffffff", msgBorder: "rgba(0,0,0,0.07)",
    inputBg: "rgba(0,0,0,0.03)", inputBorder: "rgba(0,0,0,0.12)",
    text: "#374151", textDim: "#6b7280", textDimmer: "#9ca3af", textBright: "#111827",
    link: "#2563eb", tableBorder: "rgba(0,0,0,0.1)",
    thinkBg: "rgba(245,243,255,0.9)", chipBorder: "rgba(0,0,0,0.1)", chipText: "#6b7280",
    citeBg: "rgba(248,247,255,0.98)", citeBorder: "rgba(0,0,0,0.07)", citeHover: "rgba(124,58,237,0.06)",
    imgBorder: "rgba(0,0,0,0.09)", imgBg: "rgba(240,238,255,0.6)", previewBg: "rgba(124,58,237,0.07)",
  },
};

const EVENT_META = {
  AGENT_START: { color: "#22d3ee", label: "START" },
  LLM_METRIC:  { color: "#a78bfa", label: "METRIC" },
  AGENT_STEP:  { color: "#34d399", label: "THINK" },
  TOOL_CALL:   { color: "#fb923c", label: "TOOL" },
  AGENT_END:   { color: "#22d3ee", label: "END" },
};

// ─────────────────────────────────────────────────────────────────────────────
//  IMAGE GALLERY
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
            transition: "transform 0.2s, box-shadow 0.2s",
            boxShadow: "0 2px 8px rgba(0,0,0,0.14)",
          }}
            onMouseEnter={e => { e.currentTarget.style.transform = "scale(1.04)"; e.currentTarget.style.boxShadow = "0 6px 22px rgba(124,58,237,0.22)"; }}
            onMouseLeave={e => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.14)"; }}
          >
            <img src={img.thumb || img.url} alt={img.title || `Ảnh ${i + 1}`} loading="lazy"
              style={{ width: "100%", height: "92px", objectFit: "cover", display: "block" }}
              onError={e => { e.target.parentElement.style.display = "none"; }} />
            {img.title && (
              <div style={{ fontSize: "10px", color: t.textDim, padding: "4px 7px",
                whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {img.title}
              </div>
            )}
          </div>
        ))}
      </div>

      {lightbox && (
        <div onClick={() => setLightbox(null)} style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.88)",
          zIndex: 9999, display: "flex", alignItems: "center", justifyContent: "center",
          cursor: "zoom-out", backdropFilter: "blur(10px)",
        }}>
          <div onClick={e => e.stopPropagation()} style={{
            maxWidth: "90vw", maxHeight: "85vh", borderRadius: "14px",
            overflow: "hidden", position: "relative", boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
          }}>
            <img src={lightbox.url} alt={lightbox.title}
              style={{ maxWidth: "90vw", maxHeight: "80vh", objectFit: "contain", display: "block" }} />
            {lightbox.title && (
              <div style={{
                position: "absolute", bottom: 0, left: 0, right: 0,
                background: "linear-gradient(transparent,rgba(0,0,0,0.82))",
                padding: "24px 14px 10px", fontSize: "12px", color: "#e2e8f0",
              }}>
                {lightbox.title}
                {lightbox.source && (
                  <a href={lightbox.source} target="_blank" rel="noopener"
                    onClick={e => e.stopPropagation()}
                    style={{ color: "#a78bfa", marginLeft: "8px", fontSize: "11px" }}>
                    Nguồn ↗
                  </a>
                )}
              </div>
            )}
            <button onClick={() => setLightbox(null)} style={{
              position: "absolute", top: "10px", right: "10px",
              background: "rgba(0,0,0,0.55)", border: "none", borderRadius: "50%",
              width: "30px", height: "30px", cursor: "pointer", color: "#fff",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}><Icon.X /></button>
          </div>
        </div>
      )}
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  CITATION PANEL  (footnotes ở chân message – như NotebookLM)
// ─────────────────────────────────────────────────────────────────────────────

function CitationPanel({ citations, theme }) {
  const t = THEMES[theme];
  const entries = Object.entries(citations)
    .filter(([, v]) => isValidExternalUrl(v?.url))
    .sort(([a], [b]) => Number(a) - Number(b));
  if (entries.length === 0) return null;

  return (
    <div style={{
      marginTop: "8px", padding: "9px 11px",
      background: t.citeBg, border: `1px solid ${t.citeBorder}`,
      borderRadius: "10px", fontSize: "11.5px",
    }}>
      <div style={{
        fontSize: "9.5px", color: t.textDim, letterSpacing: "0.1em",
        fontWeight: "700", marginBottom: "7px", textTransform: "uppercase",
      }}>
        📚 Nguồn tham khảo
      </div>
      {entries.map(([num, { title, url }]) => (
        <a key={num} href={url} target="_blank" rel="noopener" style={{
          display: "flex", alignItems: "flex-start", gap: "8px",
          padding: "5px 6px", borderRadius: "7px",
          color: "inherit", textDecoration: "none", transition: "background 0.15s",
          marginBottom: "2px",
        }}
          onMouseEnter={e => { e.currentTarget.style.background = t.citeHover; }}
          onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}
        >
          <span style={{
            flexShrink: 0, width: "19px", height: "19px",
            background: "linear-gradient(135deg, #7c3aed, #06b6d4)",
            borderRadius: "5px", fontSize: "10px", fontWeight: "800",
            color: "#fff", display: "flex", alignItems: "center", justifyContent: "center",
            marginTop: "1px",
          }}>{num}</span>
          <span style={{ flex: 1, minWidth: 0 }}>
            <span style={{
              color: t.textBright, fontWeight: "500", display: "block",
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              fontSize: "11.5px",
            }}>{title}</span>
            <span style={{
              color: t.link, fontSize: "10.5px", display: "block",
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            }}>
              {url.replace(/^https?:\/\//, "").slice(0, 58)}{url.length > 63 ? "…" : ""}
            </span>
          </span>
          <span style={{ flexShrink: 0, opacity: 0.5, marginTop: "3px" }}><Icon.ExtLink /></span>
        </a>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  THINKING BLOCK
// ─────────────────────────────────────────────────────────────────────────────

function ThinkingBlock({ events, theme }) {
  const [open, setOpen] = useState(false);
  if (!events || events.length === 0) return null;
  const t = THEMES[theme];
  const stepCount = events.filter(e => e.event === "AGENT_STEP").length;
  const toolCount = events.filter(e => e.event === "TOOL_CALL").length;
  const totalMs = events.filter(e => e.event === "LLM_METRIC").reduce((a, e) => a + (e.data.latency_ms || 0), 0);

  return (
    <div style={{ marginBottom: "6px" }}>
      <button onClick={() => setOpen(o => !o)} style={{
        display: "flex", alignItems: "center", gap: "8px",
        background: "rgba(139,92,246,0.08)", border: "1px solid rgba(139,92,246,0.25)",
        borderRadius: "8px", padding: "6px 12px", color: "#a78bfa",
        fontSize: "12px", fontFamily: "inherit", cursor: "pointer",
        transition: "all 0.2s", letterSpacing: "0.02em",
        maxWidth: "100%", overflow: "hidden",
      }}
        onMouseEnter={e => e.currentTarget.style.background = "rgba(139,92,246,0.15)"}
        onMouseLeave={e => e.currentTarget.style.background = "rgba(139,92,246,0.08)"}
      >
        <Icon.Cpu style={{ flexShrink: 0 }} />
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          Thought for {(totalMs / 1000).toFixed(1)}s · {stepCount} step{stepCount !== 1 ? "s" : ""}
          {toolCount > 0 ? ` · ${toolCount} tool${toolCount !== 1 ? "s" : ""}` : ""}
        </span>
        <Icon.ChevronDown open={open} style={{ flexShrink: 0 }} />
      </button>

      {open && (
        <div style={{
          marginTop: "6px", background: t.thinkBg,
          border: "1px solid rgba(139,92,246,0.2)", borderRadius: "10px",
          padding: "12px", maxHeight: "380px", overflowY: "auto",
          fontFamily: "'JetBrains Mono','Fira Code',monospace", fontSize: "11.5px", lineHeight: "1.7",
        }}>
          {events.map((ev, i) => {
            const meta = EVENT_META[ev.event] || { color: "#94a3b8", label: ev.event };
            return (
              <div key={i} style={{
                display: "flex", gap: "10px", alignItems: "flex-start", padding: "5px 0",
                borderBottom: i < events.length - 1 ? `1px solid ${t.tableBorder}` : "none",
              }}>
                <span style={{
                  color: meta.color, background: `${meta.color}18`,
                  border: `1px solid ${meta.color}40`, borderRadius: "4px",
                  padding: "1px 6px", fontSize: "10px", fontWeight: "700",
                  letterSpacing: "0.08em", flexShrink: 0, marginTop: "1px",
                }}>{meta.label}</span>
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

  if (ev.event === "AGENT_START") return (<span style={val}><span style={dim}>[{ts}] </span>Input: <em style={{ color: "#67e8f9" }}>"{d.input?.slice(0, 80)}{d.input?.length > 80 ? "…" : ""}"</em><span style={dim}> · {d.model}</span></span>);
  if (ev.event === "LLM_METRIC") return (<span style={val}><span style={dim}>[{ts}] </span><strong style={{ color: "#a78bfa" }}>{d.latency_ms}ms</strong>{d.total_tokens ? <span style={dim}> · {d.total_tokens} tok ({d.prompt_tokens}↑ {d.completion_tokens}↓)</span> : null}</span>);
  if (ev.event === "AGENT_STEP") return (<span style={{ color: theme === "dark" ? "#94a3b8" : "#6b7280", wordBreak: "break-word" }}><span style={dim}>[{ts}] Step {d.step}: </span><span style={{ color: theme === "dark" ? "#d1fae5" : "#065f46" }}>{d.response_preview?.slice(0, 200)}{d.response_preview?.length > 200 ? "…" : ""}</span></span>);
  if (ev.event === "TOOL_CALL") return (<span style={{ wordBreak: "break-word" }}><span style={dim}>[{ts}] </span><span style={{ color: "#fb923c", fontWeight: "700" }}>{d.tool}</span><span style={dim}>(</span><span style={{ color: "#fde68a" }}>{d.arguments?.slice(0, 100)}</span><span style={dim}>)</span>{d.observation && <><br /><span style={{ color: "#86efac" }}>→ {d.observation?.slice(0, 250)}</span></>}</span>);
  if (ev.event === "AGENT_END") return (<span style={val}><span style={dim}>[{ts}] </span>Done in <strong style={{ color: "#22d3ee" }}>{d.steps} step{d.steps !== 1 ? "s" : ""}</strong></span>);
  return <span style={{ color: "#94a3b8" }}>{JSON.stringify(d).slice(0, 100)}</span>;
}

// ─────────────────────────────────────────────────────────────────────────────
//  IMAGE PREVIEW BADGE (in input bar)
// ─────────────────────────────────────────────────────────────────────────────

function ImagePreviewBadge({ preview, onRemove, theme }) {
  const t = THEMES[theme];
  if (!preview) return null;
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: "10px",
      padding: "8px 12px", marginBottom: "8px",
      background: t.previewBg, border: "1px solid rgba(124,58,237,0.25)", borderRadius: "10px",
    }}>
      <img src={preview} alt="preview"
        style={{ width: "44px", height: "44px", borderRadius: "7px", objectFit: "cover" }} />
      <div style={{ flex: 1, fontSize: "12px", color: "#a78bfa", lineHeight: "1.4" }}>
        📸 <strong>Ảnh đính kèm</strong> — AI sẽ nhận diện địa điểm khi bạn gửi
      </div>
      <button onClick={onRemove} style={{
        background: "rgba(248,113,113,0.12)", border: "1px solid rgba(248,113,113,0.28)",
        borderRadius: "7px", padding: "4px 10px", cursor: "pointer",
        color: "#f87171", display: "flex", alignItems: "center", gap: "4px",
        fontSize: "11.5px", fontFamily: "inherit",
      }}>
        <Icon.X /> Xoá
      </button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  MESSAGE
// ─────────────────────────────────────────────────────────────────────────────

function TypingDots() {
  return (
    <div style={{ display: "flex", gap: "5px", alignItems: "center", padding: "2px 0" }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#7c3aed", animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
      ))}
    </div>
  );
}

function Message({ msg, theme }) {
  const isUser = msg.role === "user";
  const t = THEMES[theme];
  const citations = isUser ? {} : parseCitations(msg.events);
  const images = isUser ? [] : parseImages(msg.events);
  const hasCitations = Object.keys(citations).length > 0;

  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: "20px", animation: "fadeUp 0.3s ease" }}>
      {!isUser && (
        <div style={{
          width: "32px", height: "32px", borderRadius: "50%",
          background: "linear-gradient(135deg, #7c3aed, #06b6d4)",
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0, marginRight: "10px", marginTop: "2px",
          boxShadow: "0 0 12px rgba(124,58,237,0.3)",
        }}><Icon.Plane /></div>
      )}

      <div style={{ maxWidth: "74%", minWidth: "60px" }}>
        {!isUser && <ThinkingBlock events={msg.events} theme={theme} />}

        {/* Image gallery — ảnh địa điểm nằm trên bubble */}
        {images.length > 0 && <ImageGallery images={images} theme={theme} />}

        {/* Message bubble */}
        <div style={{
          background: isUser ? "linear-gradient(135deg, #7c3aed, #5b21b6)" : t.msgBg,
          border: isUser ? "none" : `1px solid ${t.msgBorder}`,
          borderRadius: isUser ? "18px 18px 4px 18px" : "4px 18px 18px 18px",
          padding: "12px 16px",
          color: isUser ? "#f0f0ff" : t.text,
          fontSize: "14.5px", lineHeight: "1.65",
          boxShadow: isUser ? "0 4px 20px rgba(124,58,237,0.3)" : theme === "dark" ? "0 2px 12px rgba(0,0,0,0.3)" : "0 2px 12px rgba(0,0,0,0.07)",
        }}>
          {/* User image preview inside bubble */}
          {isUser && msg.imagePreview && (
            <div style={{ marginBottom: "8px" }}>
              <img src={msg.imagePreview} alt="ảnh đính kèm"
                style={{ maxWidth: "200px", maxHeight: "155px", borderRadius: "8px", objectFit: "cover", display: "block" }} />
            </div>
          )}

          {isUser ? (
            <span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>
          ) : msg.loading ? (
            <TypingDots />
          ) : (
            <div className={`md-body md-${theme}`}
              dangerouslySetInnerHTML={{ __html: renderMd(msg.content, citations) }} />
          )}
        </div>

        {/* Citation footnotes — như NotebookLM */}
        {!isUser && !msg.loading && hasCitations && (
          <CitationPanel citations={citations} theme={theme} />
        )}

        {msg.took_ms && !isUser && (
          <div style={{ fontSize: "11px", color: t.textDim, marginTop: "4px", paddingLeft: "4px" }}>
            {(msg.took_ms / 1000).toFixed(2)}s
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  MAIN APP
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const MODEL_OPTIONS = [
  { value: "openai", label: "OpenAI" },
  { value: "qwen3_4b", label: "Qwen3-4B" },
];

async function normalizeImageForVision(file) {
  const toDataUrl = (blob) => new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = (ev) => resolve(ev.target.result);
    fr.onerror = reject;
    fr.readAsDataURL(blob);
  });

  const fileDataUrl = await toDataUrl(file);
  const img = new Image();
  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = reject;
    img.src = fileDataUrl;
  });

  const maxSide = 1280;
  const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
  const w = Math.max(1, Math.round(img.width * scale));
  const h = Math.max(1, Math.round(img.height * scale));

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, 0, 0, w, h);

  const jpegDataUrl = canvas.toDataURL("image/jpeg", 0.9);
  return {
    preview: jpegDataUrl,
    mediaType: "image/jpeg",
    base64: jpegDataUrl.split(",")[1],
  };
}

export default function App() {
  const [theme, setTheme] = useState(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  );
  const t = THEMES[theme];

  // ── Thinking mode toggle ──────────────────────────────────────────────────
  // Khi bật: model suy nghĩ sâu hơn nhưng tool calling bị tắt (model 4B giới hạn).
  // Khi tắt (default): tool calling hoạt động bình thường — tìm vé, khách sạn, v.v.
  const [thinkingEnabled, setThinkingEnabled] = useState(false);
  const [selectedModel, setSelectedModel] = useState("openai");

  const [messages, setMessages] = useState([{
    role: "assistant",
    content: "Xin chào! Tôi là **TravelBuddy** 🌏 — trợ lý du lịch thông minh của bạn.\n\nTôi có thể giúp bạn:\n- Tìm **chuyến bay** giữa các thành phố\n- Tìm **khách sạn** phù hợp ngân sách\n- Tính **chi phí** tổng cộng\n- 📸 **Upload ảnh** địa điểm để nhận diện\n\nHãy cho tôi biết bạn muốn đi đâu! ✈️",
    events: [],
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());

  // Image state
  const [imagePreview, setImagePreview] = useState(null);
  const [imageBase64, setImageBase64] = useState(null);
  const [imageMediaType, setImageMediaType] = useState("image/jpeg");
  const [identifyingImage, setIdentifyingImage] = useState(false);

  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  // ── Image selection ──────────────────────────────────────────────────────
  const handleImageSelect = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const normalized = await normalizeImageForVision(file);
      setImageMediaType(normalized.mediaType);
      setImagePreview(normalized.preview);
      setImageBase64(normalized.base64);
    } catch {
      setImageMediaType(file.type || "image/jpeg");
      const reader = new FileReader();
      reader.onload = (ev) => {
        const dataUrl = ev.target.result;
        setImagePreview(dataUrl);
        setImageBase64(dataUrl.split(",")[1]);
      };
      reader.readAsDataURL(file);
    }
    e.target.value = "";
  }, []);

  const clearImage = useCallback(() => { setImagePreview(null); setImageBase64(null); }, []);

  // ── Send message ──────────────────────────────────────────────────────────
  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if ((!text && !imageBase64) || loading) return;
    setInput("");
    setLoading(true);

    let finalMessage = text;
    const capturedPreview = imagePreview;
    const capturedBase64 = imageBase64;
    const capturedMT = imageMediaType;
    clearImage();

    // Vision identify if image attached
    if (capturedBase64) {
      setIdentifyingImage(true);
      try {
        const vr = await fetch(`${API_BASE}/vision/identify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: capturedBase64, media_type: capturedMT }),
        });
        if (vr.ok) {
          const vd = await vr.json();
          const identified = vd.result || "";
          if (identified) {
            finalMessage = identified + "\n\n" + (text || "Bạn có thể tư vấn chuyến đi đến đây cho tôi không?");
          } else {
            finalMessage = text || "Đây là ảnh địa điểm nào? Bạn có thể tư vấn không?";
          }
        } else {
          let reason = "Khong nhan dien duoc anh";
          try {
            const errBody = await vr.json();
            reason = errBody?.detail || reason;
          } catch {}
          finalMessage = [
            text || "Tôi muốn đến địa điểm trong ảnh",
            "",
            `Luu y he thong: Vision nhan dien anh that bai (${reason}).`,
            "Hay uu tien giup nguoi dung xac dinh dia diem tu mo ta anh va de xuat cach gui lai anh JPG/PNG ro net neu can.",
          ].join("\n");
        }
      } catch {
        finalMessage = [
          text || "Tôi muốn đến địa điểm trong ảnh",
          "",
          "Luu y he thong: Khong ket noi duoc dich vu nhan dien anh.",
          "Hay giup nguoi dung xac dinh dia diem bang cach hoi them dac diem nhan dang trong anh.",
        ].join("\n");
      }
      setIdentifyingImage(false);
    }

    // Add user message
    setMessages(prev => [...prev, {
      role: "user",
      content: text || "(Đính kèm ảnh)",
      imagePreview: capturedPreview,
    }]);

    const _id = Date.now();
    setMessages(prev => [...prev, { role: "assistant", content: "", loading: true, events: [], _id }]);

    const collectedEvents = [];
    try {
      const url = `${API_BASE}/session/${sessionId}/stream?message=${encodeURIComponent(finalMessage)}&enable_thinking=${thinkingEnabled}&model_choice=${encodeURIComponent(selectedModel)}`;
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
              setMessages(prev => prev.map(m =>
                m._id === _id ? { ...m, loading: false, content: ev.data.final_answer, events: [...collectedEvents] } : m
              ));
            } else {
              setMessages(prev => prev.map(m =>
                m._id === _id ? { ...m, events: [...collectedEvents] } : m
              ));
            }
          } catch { }
        }
      }
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m._id === _id ? { ...m, loading: false, content: `❌ Lỗi kết nối: ${err.message}\n\nKiểm tra backend tại \`${API_BASE}\``, events: collectedEvents } : m
      ));
    }
    setLoading(false);
    inputRef.current?.focus();
  }, [input, loading, sessionId, imagePreview, imageBase64, imageMediaType, clearImage, thinkingEnabled, selectedModel]);

  const clearChat = () => {
    fetch(`${API_BASE}/session/${sessionId}`, { method: "DELETE" }).catch(() => { });
    clearImage();
    setMessages([{ role: "assistant", content: "Cuộc hội thoại đã được xóa. Tôi có thể giúp gì cho bạn? ✈️", events: [] }]);
  };

  const handleKey = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

  const suggestions = [
    "Tìm vé từ Hà Nội đến Đà Nẵng",
    "Tôi muốn đi Phú Quốc 2 đêm, budget 5 triệu",
    "Khách sạn Hồ Chí Minh dưới 800k/đêm",
  ];

  const canSend = !loading && (!!input.trim() || !!imageBase64);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,300;0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        body{background:#080812;}
        @keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
        @keyframes bounce{0%,80%,100%{transform:scale(0.7);opacity:0.5}40%{transform:scale(1);opacity:1}}
        @keyframes pulse{0%,100%{opacity:0.4}50%{opacity:1}}
        @keyframes spin{to{transform:rotate(360deg)}}

        ::-webkit-scrollbar{width:4px;height:4px}
        ::-webkit-scrollbar-track{background:transparent}
        ::-webkit-scrollbar-thumb{background:rgba(124,58,237,0.3);border-radius:2px}

        /* Citation badge — inline superscript */
        a.cite-badge, span.cite-badge{
          display:inline-flex;align-items:center;justify-content:center;
          background:linear-gradient(135deg,rgba(124,58,237,0.22),rgba(6,182,212,0.18));
          border:1px solid rgba(124,58,237,0.38); border-radius:4px;
          padding:0 5px; font-size:10px; font-weight:800;
          color:#a78bfa; text-decoration:none;
          margin:0 1px; vertical-align:super; line-height:1.6;
          transition:background 0.15s,color 0.15s; cursor:pointer;
          font-family:'JetBrains Mono',monospace;
        }
        a.cite-badge:hover{background:rgba(124,58,237,0.42);color:#fff;}
        span.cite-badge[aria-disabled="true"]{opacity:0.65;cursor:default;}

        /* Markdown shared */
        .md-body{font-family:'Be Vietnam Pro',sans-serif}
        .md-body h1,.md-body h2,.md-body h3{margin:10px 0 4px;font-weight:600}
        .md-body ul,.md-body ol{padding-left:20px;margin:6px 0}
        .md-body li{margin:3px 0}
        .md-body p{margin:4px 0}
        .md-body code{background:rgba(255,255,255,0.1);padding:1px 5px;border-radius:3px;font-family:'JetBrains Mono',monospace;font-size:12.5px}
        .md-body strong{font-weight:600}
        .md-body em{font-style:italic}

        /* Dark */
        .md-dark .md-table-wrap{overflow-x:auto;margin:10px 0;border-radius:8px;border:1px solid rgba(255,255,255,0.08)}
        .md-dark .md-table{width:100%;border-collapse:collapse;font-size:13.5px}
        .md-dark .md-table th{background:rgba(124,58,237,0.2);color:#e2e8f0;font-weight:600;padding:8px 12px;text-align:left;font-size:12.5px;letter-spacing:0.03em}
        .md-dark .md-table td{padding:7px 12px;border-top:1px solid rgba(255,255,255,0.06);color:#cbd5e1}
        .md-dark .md-table tr:nth-child(even) td{background:rgba(255,255,255,0.03)}
        .md-dark .md-table tr:hover td{background:rgba(124,58,237,0.08)}
        .md-dark .md-link{color:#38bdf8;text-decoration:none}.md-dark .md-link:hover{text-decoration:underline}
        .md-dark h1,.md-dark h2,.md-dark h3{color:#e2e8f0}
        .md-dark strong{color:#e2e8f0}.md-dark em{color:#a5b4fc}
        .md-dark code{color:#67e8f9;background:rgba(103,232,249,0.08)}

        /* Light */
        .md-light .md-table-wrap{overflow-x:auto;margin:10px 0;border-radius:8px;border:1px solid rgba(0,0,0,0.1)}
        .md-light .md-table{width:100%;border-collapse:collapse;font-size:13.5px}
        .md-light .md-table th{background:rgba(124,58,237,0.08);color:#374151;font-weight:600;padding:8px 12px;text-align:left;font-size:12.5px;letter-spacing:0.03em}
        .md-light .md-table td{padding:7px 12px;border-top:1px solid rgba(0,0,0,0.06);color:#374151}
        .md-light .md-table tr:nth-child(even) td{background:rgba(0,0,0,0.02)}
        .md-light .md-table tr:hover td{background:rgba(124,58,237,0.04)}
        .md-light .md-link{color:#2563eb;text-decoration:none}.md-light .md-link:hover{text-decoration:underline}
        .md-light h1,.md-light h2,.md-light h3{color:#111827}
        .md-light strong{color:#111827}.md-light em{color:#6d28d9}
        .md-light code{color:#0369a1;background:rgba(3,105,161,0.08)}

        textarea::placeholder{color:#6b7280 !important}
      `}</style>

      {/* Hidden file input */}
      <input ref={fileInputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={handleImageSelect} />

      <div style={{ height: "100vh", display: "flex", flexDirection: "column", fontFamily: "'Be Vietnam Pro',sans-serif", background: t.bg, color: t.text, transition: "background 0.3s, color 0.3s" }}>

        {/* ── Header ── */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "13px 24px", background: t.surface, borderBottom: `1px solid ${t.surfaceBorder}`, backdropFilter: "blur(20px)", flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ width: "38px", height: "38px", borderRadius: "12px", background: "linear-gradient(135deg, #7c3aed 0%, #0ea5e9 100%)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 20px rgba(124,58,237,0.35)" }}><Icon.Plane /></div>
            <div>
              <div style={{ fontWeight: "600", fontSize: "16px", color: t.textBright, letterSpacing: "-0.01em" }}>TravelBuddy</div>
              <div style={{ fontSize: "11px", color: t.textDim, letterSpacing: "0.05em" }}>AI TRAVEL AGENT · LANGGRAPH</div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "11px", color: "#22d3ee" }}>
              <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#22d3ee", animation: "pulse 2s infinite" }} />ONLINE
            </div>

            <button onClick={() => setTheme(th => th === "dark" ? "light" : "dark")} style={{ background: t.inputBg, border: `1px solid ${t.inputBorder}`, borderRadius: "8px", padding: "6px 10px", color: t.textDim, cursor: "pointer", display: "flex", alignItems: "center", gap: "5px", fontSize: "12px", transition: "all 0.2s", fontFamily: "inherit" }}>
              {theme === "dark" ? <Icon.Sun /> : <Icon.Moon />}{theme === "dark" ? "Sáng" : "Tối"}
            </button>
            <button onClick={clearChat} style={{ background: t.inputBg, border: `1px solid ${t.inputBorder}`, borderRadius: "8px", padding: "6px 10px", color: t.textDim, cursor: "pointer", display: "flex", alignItems: "center", gap: "5px", fontSize: "12px", transition: "all 0.2s", fontFamily: "inherit" }}
              onMouseEnter={e => { e.currentTarget.style.color = "#f87171"; e.currentTarget.style.borderColor = "rgba(248,113,113,0.4)"; }}
              onMouseLeave={e => { e.currentTarget.style.color = t.textDim; e.currentTarget.style.borderColor = t.inputBorder; }}>
              <Icon.Trash /> Xóa
            </button>
          </div>
        </div>

        {/* ── Thinking mode notice banner ── */}
        {thinkingEnabled && (
          <div style={{
            background: "linear-gradient(90deg, rgba(139,92,246,0.12), rgba(6,182,212,0.08))",
            borderBottom: "1px solid rgba(139,92,246,0.2)",
            padding: "7px 24px",
            fontSize: "12px",
            color: "#a78bfa",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            flexShrink: 0,
          }}>
            <Icon.Brain />
            <span><strong>Thinking mode BẬT</strong> — model suy nghĩ sâu trước khi trả lời. Tool calling (tìm vé, khách sạn) tạm tắt vì model 4B không hỗ trợ cả hai cùng lúc.</span>
          </div>
        )}

        {/* ── Messages ── */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px 16px" }}>
          <div style={{ maxWidth: "780px", margin: "0 auto" }}>
            {messages.map((msg, i) => <Message key={i} msg={msg} theme={theme} />)}

            {/* Identifying image spinner */}
            {identifyingImage && (
              <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "12px", animation: "fadeUp 0.3s ease" }}>
                <div style={{ background: t.msgBg, border: `1px solid ${t.msgBorder}`, borderRadius: "14px", padding: "10px 16px", fontSize: "13px", color: t.textDim, display: "flex", alignItems: "center", gap: "8px" }}>
                  <div style={{ width: "14px", height: "14px", border: "2px solid #7c3aed", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                  🔍 Đang nhận diện địa điểm từ ảnh…
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* ── Suggestion chips ── */}
        {messages.length <= 1 && (
          <div style={{ display: "flex", gap: "8px", justifyContent: "center", padding: "0 16px 10px", flexWrap: "wrap" }}>
            {suggestions.map((s, i) => (
              <button key={i} onClick={() => { setInput(s); inputRef.current?.focus(); }} style={{ background: t.inputBg, border: `1px solid ${t.chipBorder}`, borderRadius: "20px", padding: "7px 14px", color: t.chipText, fontSize: "12.5px", cursor: "pointer", transition: "all 0.2s", fontFamily: "inherit" }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(124,58,237,0.5)"; e.currentTarget.style.color = "#c4b5fd"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = t.chipBorder; e.currentTarget.style.color = t.chipText; }}>
                {s}
              </button>
            ))}
            <button onClick={() => fileInputRef.current?.click()} style={{ background: t.inputBg, border: `1px solid ${t.chipBorder}`, borderRadius: "20px", padding: "7px 14px", color: t.chipText, fontSize: "12.5px", cursor: "pointer", transition: "all 0.2s", fontFamily: "inherit", display: "flex", alignItems: "center", gap: "5px" }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(124,58,237,0.5)"; e.currentTarget.style.color = "#c4b5fd"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = t.chipBorder; e.currentTarget.style.color = t.chipText; }}>
              <Icon.Scan /> Nhận diện địa điểm từ ảnh
            </button>
          </div>
        )}

        {/* ── Input bar ── */}
        <div style={{ padding: "12px 16px 20px", background: t.surface, borderTop: `1px solid ${t.surfaceBorder}`, backdropFilter: "blur(20px)", flexShrink: 0 }}>
          <div style={{ maxWidth: "780px", margin: "0 auto" }}>

            <ImagePreviewBadge preview={imagePreview} onRemove={clearImage} theme={theme} />

            <div style={{ display: "flex", gap: "10px", alignItems: "flex-end", background: t.inputBg, border: `1px solid ${loading ? "rgba(124,58,237,0.4)" : imagePreview ? "rgba(124,58,237,0.35)" : t.inputBorder}`, borderRadius: "14px", padding: "10px 10px 10px 12px", transition: "border-color 0.2s", boxShadow: loading ? "0 0 0 1px rgba(124,58,237,0.2), 0 0 20px rgba(124,58,237,0.08)" : "none" }}>

              {/* Attach image button */}
              <button onClick={() => fileInputRef.current?.click()} disabled={loading} title="Đính kèm ảnh địa điểm" style={{ width: "34px", height: "34px", borderRadius: "9px", flexShrink: 0, background: imagePreview ? "rgba(124,58,237,0.18)" : t.inputBg, border: `1px solid ${imagePreview ? "rgba(124,58,237,0.45)" : t.inputBorder}`, cursor: loading ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", color: imagePreview ? "#a78bfa" : t.textDim, transition: "all 0.2s" }}
                onMouseEnter={e => { if (!loading) { e.currentTarget.style.color = "#a78bfa"; e.currentTarget.style.borderColor = "rgba(124,58,237,0.4)"; } }}
                onMouseLeave={e => { if (!imagePreview) { e.currentTarget.style.color = t.textDim; e.currentTarget.style.borderColor = t.inputBorder; } }}>
                <Icon.ImageIcon />
              </button>

              {/* Thinking toggle moved next to image button */}
              <button
                onClick={() => setThinkingEnabled(v => !v)}
                disabled={loading}
                title={thinkingEnabled
                  ? "Thinking ON — model suy nghĩ sâu, tool calling TẮT. Click để tắt."
                  : "Thinking OFF — tool calling BẬT (tìm vé, khách sạn…). Click để bật thinking."}
                style={{
                  height: "34px",
                  borderRadius: "9px",
                  flexShrink: 0,
                  background: thinkingEnabled
                    ? "linear-gradient(135deg, rgba(139,92,246,0.25), rgba(6,182,212,0.15))"
                    : t.inputBg,
                  border: thinkingEnabled
                    ? "1px solid rgba(139,92,246,0.55)"
                    : `1px solid ${t.inputBorder}`,
                  padding: "0 9px",
                  color: thinkingEnabled ? "#c4b5fd" : t.textDim,
                  cursor: loading ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "5px",
                  fontSize: "11.5px",
                  fontFamily: "inherit",
                }}
              >
                <Icon.Brain />
                {thinkingEnabled ? "ON" : "OFF"}
              </button>

              {/* Model selector */}
              <select
                value={selectedModel}
                onChange={e => setSelectedModel(e.target.value)}
                disabled={loading}
                title="Chọn model"
                style={{
                  height: "34px",
                  borderRadius: "9px",
                  border: `1px solid ${t.inputBorder}`,
                  background: t.inputBg,
                  color: t.text,
                  padding: "0 9px",
                  fontSize: "12px",
                  fontFamily: "inherit",
                  flexShrink: 0,
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                {MODEL_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>

              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder={imagePreview ? "Thêm câu hỏi về địa điểm này… (Enter để gửi)" : "Hỏi về chuyến bay, khách sạn, ngân sách… (Enter để gửi)"}
                disabled={loading}
                rows={1}
                style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: t.text, fontSize: "14.5px", fontFamily: "inherit", resize: "none", lineHeight: "1.5", maxHeight: "120px", overflowY: "auto", opacity: loading ? 0.5 : 1 }}
                onInput={e => { e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px"; }}
              />

              <button onClick={sendMessage} disabled={!canSend} style={{ width: "38px", height: "38px", borderRadius: "10px", flexShrink: 0, background: !canSend ? "rgba(124,58,237,0.15)" : "linear-gradient(135deg, #7c3aed, #0ea5e9)", border: "none", cursor: !canSend ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", color: !canSend ? t.textDim : "white", transition: "all 0.2s", boxShadow: !canSend ? "none" : "0 4px 15px rgba(124,58,237,0.4)" }}>
                {loading
                  ? <div style={{ width: "16px", height: "16px", border: `2px solid ${t.textDimmer}`, borderTopColor: "#7c3aed", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                  : <Icon.Send />}
              </button>
            </div>

            <div style={{ textAlign: "center", fontSize: "11px", color: t.textDimmer, marginTop: "8px" }}>
              Shift+Enter xuống dòng · 📸 Đính kèm ảnh để AI nhận diện địa điểm · Model: {MODEL_OPTIONS.find(m => m.value === selectedModel)?.label || selectedModel} · Session:{" "}
              <code style={{ color: t.textDim, fontSize: "10px", fontFamily: "'JetBrains Mono',monospace" }}>{sessionId.slice(0, 8)}…</code>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
