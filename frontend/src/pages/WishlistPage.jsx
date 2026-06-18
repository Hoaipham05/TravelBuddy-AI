import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { SiteHeader, SiteFooter } from "../components/SiteChrome";
import { toast, confirmDialog } from "../components/dialog";

/* ════════════════════════════════════════════════════════════
   TravelBuddy — Wishlist của tôi
   Chỉ chứa những bài chia sẻ "hữu ích" bạn đã lưu từ Cộng đồng.
   Khi bấm "Hữu ích" ở một bài chia sẻ, bài đó được lưu vào đây (BE).
     GET    /api/travel/community/saved
     DELETE /api/travel/community/saved/{id}
═══════════════════════════════════════════════════════════════ */

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Inter',-apple-system,sans-serif; background:#F0F9FF; color:#0F172A; -webkit-font-smoothing:antialiased; }

.wl-wrap { background:#F0F9FF; min-height:calc(100vh - 64px); }
.wl-main { max-width:1140px; margin:0 auto; padding:2.5rem 2rem 3.5rem; }

.wl-hero { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin-bottom:1.75rem; }
.wl-eyebrow { font-size:0.75rem; font-weight:800; letter-spacing:0.08em; text-transform:uppercase; color:#0EA5E9; }
.wl-title { font-family:'Nunito',sans-serif; font-weight:900; font-size:2rem; letter-spacing:-0.02em; margin-top:0.25rem;
  display:flex; align-items:center; gap:0.625rem; }
.wl-title .heart { color:#FB7185; }
.wl-sub { font-size:0.9375rem; color:#64748B; margin-top:0.375rem; max-width:580px; }
.wl-explore-btn { display:inline-flex; align-items:center; gap:0.45rem; padding:0.625rem 1.125rem; border:none;
  border-radius:10px; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9rem; cursor:pointer;
  background:linear-gradient(135deg,#0EA5E9,#0284C7); color:#fff; box-shadow:0 4px 14px rgba(14,165,233,0.32);
  transition:all 0.15s; }
.wl-explore-btn:hover { transform:translateY(-1px); box-shadow:0 7px 18px rgba(14,165,233,0.42); }

.wl-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1.25rem; }

.wl-card { background:#fff; border:1px solid rgba(226,232,240,0.9); border-radius:18px; overflow:hidden;
  box-shadow:0 2px 10px rgba(15,23,42,0.05); display:flex; flex-direction:column; transition:transform 0.18s, box-shadow 0.18s; }
.wl-card:hover { transform:translateY(-4px); box-shadow:0 16px 36px rgba(15,23,42,0.13); }
.wl-img { position:relative; height:160px; background:#E0F2FE center/cover no-repeat; }
.wl-badge { position:absolute; top:0.7rem; left:0.7rem; display:inline-flex; align-items:center; gap:0.3rem;
  padding:0.3rem 0.7rem; border-radius:100px; background:rgba(255,255,255,0.94); backdrop-filter:blur(6px);
  font-size:0.7rem; font-weight:800; color:#0369A1; font-family:'Nunito',sans-serif; }
.wl-rm { position:absolute; top:0.6rem; right:0.6rem; width:32px; height:32px; border-radius:50%; border:none;
  background:rgba(255,255,255,0.92); cursor:pointer; color:#64748B; font-size:1.1rem; display:flex; align-items:center;
  justify-content:center; box-shadow:0 3px 10px rgba(15,23,42,0.18); transition:all 0.15s; }
.wl-rm:hover { background:#FEF2F2; color:#DC2626; }
.wl-body { padding:1rem 1.125rem 1.125rem; display:flex; flex-direction:column; flex:1; }
.wl-author { font-size:0.75rem; color:#94A3B8; }
.wl-author b { color:#475569; font-weight:700; }
.wl-text { font-size:0.875rem; color:#334155; line-height:1.55; margin:0.4rem 0 0.7rem; flex:1;
  display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.wl-dest { display:inline-flex; align-items:center; gap:0.25rem; font-size:0.75rem; font-weight:700; color:#0284C7; margin-bottom:0.7rem; }
.wl-foot { display:flex; gap:0.5rem; }
.wl-foot button { flex:1; padding:0.5rem 0.6rem; border-radius:10px; font-family:'Nunito',sans-serif; font-weight:800;
  font-size:0.8rem; cursor:pointer; transition:all 0.15s; border:1.5px solid #E2E8F0; background:#fff; color:#0284C7; }
.wl-foot button.primary { border-color:transparent; background:linear-gradient(135deg,#0EA5E9,#0284C7); color:#fff; }
.wl-foot button:hover { box-shadow:0 4px 12px rgba(14,165,233,0.22); }

.wl-empty { text-align:center; padding:4rem 1.5rem; background:#fff; border-radius:20px; border:1px dashed #CBD5E1; }
.wl-empty .ic { font-size:3.25rem; }
.wl-empty h3 { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.25rem; margin:0.75rem 0 0.375rem; }
.wl-empty p { font-size:0.9375rem; color:#64748B; margin-bottom:1.5rem; max-width:460px; margin-left:auto; margin-right:auto; }

@media (max-width:920px) { .wl-grid { grid-template-columns:repeat(2,1fr); } }
@media (max-width:600px) {
  .wl-main { padding:1.75rem 1.25rem 2.5rem; }
  .wl-title { font-size:1.625rem; }
  .wl-grid { grid-template-columns:1fr; }
}
`;

const IconCompass = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16.2 7.8l-2.9 6.4-6.4 2.9 2.9-6.4 6.4-2.9z"/></svg>);

function getToken() { return localStorage.getItem("tb_token") || sessionStorage.getItem("tb_token"); }

export default function WishlistPage() {
  const navigate = useNavigate();
  const [saved, setSaved] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) { setLoading(false); return; }
    fetch("/api/travel/community/saved", { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.ok ? r.json() : { items: [] })
      .then((d) => setSaved((d.items || []).filter((it) => it.kind === "post")))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const removeSaved = useCallback(async (it) => {
    const ok = await confirmDialog("Gỡ bài này khỏi Wishlist?", {
      title: "Gỡ khỏi Wishlist?", okText: "Gỡ", cancelText: "Giữ lại", danger: true,
    });
    if (!ok) return;
    const token = getToken();
    setSaved((s) => s.filter((x) => x.id !== it.id));   // optimistic
    try {
      await fetch(`/api/travel/community/saved/${it.id}`, {
        method: "DELETE", headers: { Authorization: `Bearer ${token}` },
      });
      toast("Đã gỡ khỏi Wishlist");
    } catch { toast("Gỡ thất bại, thử lại sau"); }
  }, []);

  const planFromSaved = (it) => {
    const name = it.snapshot?.destination_name;
    if (name) { try { localStorage.setItem("tb_trip_draft", JSON.stringify({ step: 1, form: { destName: name } })); } catch {} }
    navigate("/plan");
  };

  const viewInCommunity = (it) => {
    const slug = it.snapshot?.destination_slug;
    if (slug) { try { localStorage.setItem("tb_community_dest", slug); } catch {} }
    navigate("/community");
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />
      <SiteHeader active="wishlist" />

      <div className="wl-wrap">
        <main className="wl-main">
          <div className="wl-hero">
            <div>
              <div className="wl-eyebrow">Tài khoản của bạn</div>
              <h1 className="wl-title"><span className="heart">❤</span> Wishlist của tôi</h1>
              <p className="wl-sub">Những bài chia sẻ <b>hữu ích</b> bạn đã lưu từ cộng đồng — mở lại bất cứ lúc nào để lên kế hoạch cho chuyến đi của bạn.</p>
            </div>
            <button className="wl-explore-btn" onClick={() => navigate("/community")}>
              👥 Khám phá cộng đồng
            </button>
          </div>

          {loading ? (
            <div className="wl-empty"><div className="ic">⏳</div><h3>Đang tải…</h3></div>
          ) : saved.length === 0 ? (
            <div className="wl-empty">
              <div className="ic">💙</div>
              <h3>Wishlist còn trống</h3>
              <p>Vào trang Cộng đồng, gặp bài chia sẻ nào hữu ích thì bấm <b>🤍 Hữu ích</b> — bài đó sẽ được lưu vào đây để bạn lên kế hoạch sau.</p>
              <button className="wl-explore-btn" onClick={() => navigate("/community")}><IconCompass /> Đến Cộng đồng</button>
            </div>
          ) : (
            <div className="wl-grid">
              {saved.map((it) => {
                const s = it.snapshot || {};
                const img = it.image_url || s.image_url;
                return (
                  <div key={it.id} className="wl-card">
                    {img && (
                      <div className="wl-img" style={{ backgroundImage: `url(${img})` }}>
                        {s.destination_name && <span className="wl-badge">📍 {s.destination_name}</span>}
                        <button className="wl-rm" onClick={() => removeSaved(it)} title="Gỡ khỏi Wishlist">×</button>
                      </div>
                    )}
                    <div className="wl-body">
                      {!img && (
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.4rem" }}>
                          {s.destination_name
                            ? <span className="wl-dest" style={{ margin: 0 }}>📍 {s.destination_name}</span>
                            : <span />}
                          <button className="wl-rm" style={{ position: "static", boxShadow: "none" }} onClick={() => removeSaved(it)}>×</button>
                        </div>
                      )}
                      <div className="wl-author">bởi <b>{s.author_name || "Traveler"}</b>{s.rating ? ` · ${"★".repeat(Math.round(s.rating))}` : ""}</div>
                      {s.excerpt && <p className="wl-text">“{s.excerpt}”</p>}
                      <div className="wl-foot">
                        <button onClick={() => viewInCommunity(it)}>Xem ở cộng đồng</button>
                        {s.destination_name && <button className="primary" onClick={() => planFromSaved(it)}>Lập kế hoạch</button>}
                      </div>
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
