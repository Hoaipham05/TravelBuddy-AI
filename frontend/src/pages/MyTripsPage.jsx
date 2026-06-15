import { useState, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { SiteHeader, SiteFooter } from "../components/SiteChrome";
import { toast, confirmDialog } from "../components/dialog";

/* ════════════════════════════════════════════════════════════
   TravelBuddy — Kế hoạch của tôi (My Trips)
   Liệt kê toàn bộ kế hoạch đã lưu trong localStorage `tb_saved_trips`.
   Phân biệt rõ: 📝 Bản lưu tạm  vs  ✅ Đã xuất PDF.
═══════════════════════════════════════════════════════════════ */

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Inter',-apple-system,sans-serif; background:#F0F9FF; color:#0F172A; -webkit-font-smoothing:antialiased; }

.mt-wrap { background:#F0F9FF; min-height:calc(100vh - 64px); }
.mt-main { max-width:1080px; margin:0 auto; padding:2.5rem 2rem 3.5rem; }

/* hero */
.mt-hero { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin-bottom:1.75rem; }
.mt-eyebrow { font-size:0.75rem; font-weight:800; letter-spacing:0.08em; text-transform:uppercase; color:#0EA5E9; }
.mt-title { font-family:'Nunito',sans-serif; font-weight:900; font-size:2rem; letter-spacing:-0.02em; margin-top:0.25rem; }
.mt-sub { font-size:0.9375rem; color:#64748B; margin-top:0.375rem; }
.mt-new-btn { display:inline-flex; align-items:center; gap:0.45rem; padding:0.625rem 1.125rem; border:none; border-radius:9px; font-family:'Nunito',sans-serif; font-weight:700; font-size:0.9rem; cursor:pointer; background:#0284C7; color:#fff; transition:background 0.13s ease; }
.mt-new-btn:hover { background:#0369A1; }
.mt-new-btn:active { background:#075985; }

/* filter tabs */
.mt-tabs { display:flex; gap:0.5rem; margin-bottom:1.75rem; flex-wrap:wrap; }
.mt-tab { display:inline-flex; align-items:center; gap:0.4rem; padding:0.5rem 1rem; border-radius:100px; border:1.5px solid #E2E8F0; background:#fff; font-size:0.8125rem; font-weight:700; color:#64748B; cursor:pointer; transition:all 0.15s; }
.mt-tab:hover { border-color:#0EA5E9; }
.mt-tab.on { background:linear-gradient(135deg,#0EA5E9,#0284C7); color:#fff; border-color:transparent; box-shadow:0 4px 12px rgba(14,165,233,0.28); }
.mt-tab .cnt { font-size:0.6875rem; font-weight:800; padding:0.05rem 0.45rem; border-radius:100px; background:rgba(255,255,255,0.35); }
.mt-tab:not(.on) .cnt { background:#F1F5F9; color:#64748B; }

/* list */
.mt-list { display:flex; flex-direction:column; gap:0.75rem; }
.mt-row { display:flex; align-items:center; gap:1.25rem; background:#fff; border:1px solid rgba(226,232,240,0.9); border-left-width:5px; border-radius:13px; padding:1rem 1.25rem; box-shadow:0 2px 10px rgba(15,23,42,0.05); transition:box-shadow 0.15s, transform 0.15s; }
.mt-row:hover { box-shadow:0 8px 22px rgba(15,23,42,0.1); transform:translateY(-1px); }
.mt-row.saved { border-left-color:#F59E0B; }
.mt-row.exported { border-left-color:#10B981; }

.mt-status { flex-shrink:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:0.3rem; width:78px; text-align:center; }
.mt-status .tag { font-size:0.75rem; font-weight:800; line-height:1.25; }
.mt-row.saved .mt-status .tag { color:#B45309; }
.mt-row.exported .mt-status .tag { color:#059669; }
.mt-status-sep { flex-shrink:0; width:1px; align-self:stretch; background:#EEF2F7; }

.mt-row-main { flex:1; min-width:0; }
.mt-row-dest { font-family:'Nunito',sans-serif; font-weight:800; font-size:1.0625rem; color:#0F172A; }
.mt-row-meta { display:flex; flex-wrap:wrap; gap:0.25rem 0.875rem; font-size:0.8125rem; color:#64748B; margin-top:0.2rem; }
.mt-row-meta b { color:#0369A1; font-weight:700; }
.mt-row-meta .dot { color:#CBD5E1; }

.mt-row-cost { flex-shrink:0; text-align:right; min-width:120px; }
.mt-row-cost .n { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.1875rem; color:#0284C7; }
.mt-row-cost .l { font-size:0.6875rem; color:#94A3B8; }

.mt-row-actions { flex-shrink:0; display:flex; gap:0.5rem; }
.mt-act { display:inline-flex; align-items:center; justify-content:center; gap:0.35rem; padding:0.5rem 0.875rem; border-radius:10px; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; cursor:pointer; border:1.5px solid #E2E8F0; background:#fff; color:#0284C7; transition:all 0.15s; }
.mt-act:hover { border-color:#0EA5E9; background:#F0F9FF; }
.mt-act.primary { background:#0284C7; color:#fff; border-color:transparent; transition:none; }
.mt-act.primary:hover { background:#0284C7; box-shadow:none; }
.mt-act.danger { color:#DC2626; padding:0.5rem 0.7rem; }
.mt-act.danger:hover { border-color:#FCA5A5; background:#FEF2F2; }

/* empty */
.mt-empty { text-align:center; padding:4rem 1.5rem; background:#fff; border-radius:20px; border:1px dashed #CBD5E1; }
.mt-empty .ic { font-size:3.25rem; }
.mt-empty h3 { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.25rem; margin:0.75rem 0 0.375rem; }
.mt-empty p { font-size:0.9375rem; color:#64748B; margin-bottom:1.5rem; }

@media (max-width:760px) {
  .mt-row { flex-wrap:wrap; gap:0.75rem 1rem; }
  .mt-status-sep { display:none; }
  .mt-row-cost { text-align:left; min-width:0; }
  .mt-row-actions { width:100%; }
  .mt-act.primary { flex:1; }
}
@media (max-width:600px) { .mt-main { padding:1.75rem 1.25rem 2.5rem; } .mt-title { font-size:1.625rem; } }
`;

const STATUS = {
  saved:    { label: "Bản lưu" },
  exported: { label: "Đã xuất PDF" },
};

const pad = (n) => String(n).padStart(2, "0");
const fmtVND = (n) => (n || 0).toLocaleString("vi-VN") + "đ";
const fmtDate = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
};
const fmtDateTime = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())} · ${fmtDate(iso)}`;
};

function loadTrips() {
  try {
    const arr = JSON.parse(localStorage.getItem("tb_saved_trips") || "[]");
    return Array.isArray(arr) ? arr : [];
  } catch { return []; }
}

export default function MyTripsPage() {
  const navigate = useNavigate();
  const [trips, setTrips] = useState(loadTrips);
  const [filter, setFilter] = useState("all");

  const counts = useMemo(() => ({
    all: trips.length,
    saved: trips.filter((t) => t.status !== "exported").length,
    exported: trips.filter((t) => t.status === "exported").length,
  }), [trips]);

  const shown = useMemo(() => {
    const list = filter === "all" ? trips
      : filter === "exported" ? trips.filter((t) => t.status === "exported")
      : trips.filter((t) => t.status !== "exported");
    // mới lưu nhất lên đầu
    return list.slice().sort((a, b) => new Date(b.savedAt || 0) - new Date(a.savedAt || 0));
  }, [trips, filter]);

  const persist = useCallback((next) => {
    setTrips(next);
    localStorage.setItem("tb_saved_trips", JSON.stringify(next));
  }, []);

  const reopen = (t) => {
    const draft = {
      tripId: t.id, step: 4,
      form: t.form, itinerary: t.itinerary || {}, notes: t.notes || {},
      packChecked: t.packChecked || {}, customPack: t.customPack || [],
    };
    localStorage.setItem("tb_trip_draft", JSON.stringify(draft));
    navigate("/plan");
  };

  const removeTrip = async (t) => {
    const ok = await confirmDialog(`Xoá kế hoạch “${t.destName}”? Hành động này không thể hoàn tác.`, {
      title: "Xoá kế hoạch?", okText: "Xoá", cancelText: "Huỷ", danger: true,
    });
    if (!ok) return;
    persist(trips.filter((x) => x.id !== t.id));
    toast("Đã xoá kế hoạch");
  };

  const TABS = [
    { key: "all", label: "Tất cả" },
    { key: "saved", label: "Bản lưu" },
    { key: "exported", label: "Đã xuất PDF" },
  ];

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />
      <SiteHeader active="plan" />

      <div className="mt-wrap">
        <main className="mt-main">
          <div className="mt-hero">
            <div>
              <div className="mt-eyebrow">Tài khoản của bạn</div>
              <h1 className="mt-title">Kế hoạch của tôi</h1>
              <p className="mt-sub">Toàn bộ lịch trình bạn đã lưu. Mở lại để xem, chỉnh sửa hoặc xuất PDF bất cứ lúc nào.</p>
            </div>
            <button className="mt-new-btn" onClick={() => navigate("/plan")}>+ Lập kế hoạch mới</button>
          </div>

          {trips.length > 0 && (
            <div className="mt-tabs">
              {TABS.map((t) => (
                <button key={t.key} className={"mt-tab" + (filter === t.key ? " on" : "")} onClick={() => setFilter(t.key)}>
                  {t.label} <span className="cnt">{counts[t.key]}</span>
                </button>
              ))}
            </div>
          )}

          {shown.length === 0 ? (
            <div className="mt-empty">
              <div className="ic">🗺️</div>
              <h3>{trips.length === 0 ? "Chưa có kế hoạch nào" : "Không có kế hoạch ở mục này"}</h3>
              <p>{trips.length === 0
                ? "Hãy tạo lịch trình đầu tiên — sau khi lưu hoặc xuất PDF, kế hoạch sẽ xuất hiện tại đây."
                : "Thử chọn bộ lọc khác hoặc tạo kế hoạch mới."}</p>
              <button className="mt-new-btn" onClick={() => navigate("/plan")}>+ Bắt đầu lập kế hoạch</button>
            </div>
          ) : (
            <div className="mt-list">
              {shown.map((t) => {
                const st = t.status === "exported" ? "exported" : "saved";
                const meta = STATUS[st];
                return (
                  <div key={t.id} className={"mt-row " + st}>
                    <div className="mt-status">
                      <span className="tag">{meta.label}</span>
                    </div>
                    <div className="mt-status-sep" />
                    <div className="mt-row-main">
                      <div className="mt-row-dest">{t.originName || "—"} → {t.destName || "Kế hoạch"}</div>
                      <div className="mt-row-meta">
                        <span><b>{t.days || 0}</b> ngày</span><span className="dot">·</span>
                        <span><b>{t.travelers || 1}</b> người</span><span className="dot">·</span>
                        <span><b>{t.totalPlaces || 0}</b> địa điểm</span><span className="dot">·</span>
                        <span>📅 {fmtDate(t.startDate)}</span><span className="dot">·</span>
                        <span>Lưu {fmtDateTime(t.savedAt)}</span>
                      </div>
                    </div>
                    <div className="mt-row-cost">
                      <div className="n">{fmtVND(t.totalCost)}</div>
                      <div className="l">tổng dự kiến</div>
                    </div>
                    <div className="mt-row-actions">
                      <button className="mt-act primary" onClick={() => reopen(t)}>Mở lại</button>
                      <button className="mt-act danger" onClick={() => removeTrip(t)} title="Xoá">🗑</button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </main>
      </div>

      <SiteFooter />
    </>
  );
}
