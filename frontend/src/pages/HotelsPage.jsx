import { useState, useEffect, useMemo, useCallback } from "react";
import { SiteHeader, SiteFooter } from "../components/SiteChrome";
import { toast } from "../components/dialog";

/* ════════════════════════════════════════════════════════════
   TravelBuddy — Khách sạn (Hotels)
   Data đồng bộ thật từ BE:
     /api/travel/destinations  → danh sách điểm đến
     /api/travel/hotels        → khách sạn + giá thật (live SerpApi Google Hotels,
                                  cache 24h; KS seed sẵn nếu chưa có giá)
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
.ht-wrap { min-height:calc(100vh - 64px); }

/* ─── HERO + SEARCH ─── */
.ht-hero { background:linear-gradient(125deg,var(--deepest),var(--ocean) 60%,var(--sky)); padding:2.5rem 2rem 5.5rem; position:relative; overflow:hidden; }
.ht-hero::before { content:''; position:absolute; inset:0; background-image:radial-gradient(circle,rgba(255,255,255,0.08) 1.5px,transparent 1.5px); background-size:26px 26px; }
.ht-hero-in { max-width:1100px; margin:0 auto; position:relative; z-index:2; }
.ht-hero h1 { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.875rem; color:#fff; letter-spacing:-0.02em; }
.ht-hero p { color:rgba(255,255,255,0.82); font-size:0.9375rem; margin-top:0.3rem; }

.ht-search { max-width:1100px; margin:-4rem auto 0; position:relative; z-index:5; background:#fff; border-radius:18px; box-shadow:0 16px 44px rgba(15,23,42,0.13); border:1px solid rgba(226,232,240,0.7); padding:1.25rem; }
.ht-row { display:flex; gap:0.75rem; align-items:flex-end; flex-wrap:wrap; }
.ht-field { display:flex; flex-direction:column; gap:0.3rem; }
.ht-field.dest { flex:2; min-width:220px; }
.ht-field label { font-size:0.6875rem; font-weight:800; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; }
.ht-field select, .ht-field input { width:100%; padding:0.7rem 0.75rem; border:1.5px solid var(--border); border-radius:11px; font-family:inherit; font-size:0.9375rem; font-weight:600; color:#0F172A; background:#FAFBFC; outline:none; transition:all 0.15s; }
.ht-field select:focus, .ht-field input:focus { border-color:var(--sky); background:#fff; box-shadow:0 0 0 3px rgba(14,165,233,0.1); }
.ht-go button { height:43px; padding:0 1.5rem; border:none; border-radius:11px; background:var(--ocean); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; cursor:pointer; display:inline-flex; align-items:center; gap:0.5rem; transition:background 0.15s; white-space:nowrap; }
.ht-go button:hover { background:var(--deep); }
.ht-go button:disabled { opacity:0.6; cursor:not-allowed; }

/* ─── BODY ─── */
.ht-body { max-width:1100px; margin:1.75rem auto 0; padding:0 2rem 3.5rem; }
.ht-summary { display:flex; align-items:baseline; gap:0.5rem; flex-wrap:wrap; margin-bottom:1.25rem; }
.ht-summary .dest { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.375rem; }
.ht-summary .meta { font-size:0.875rem; color:var(--muted); }

.ht-grid { display:grid; grid-template-columns:240px 1fr; gap:1.5rem; align-items:start; }
.ht-aside { position:sticky; top:80px; background:#fff; border:1px solid var(--border); border-radius:16px; padding:1.125rem; box-shadow:0 4px 16px rgba(15,23,42,0.05); }
.ht-aside h3 { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; margin-bottom:0.875rem; }
.ht-aside .grp { border-top:1px solid var(--border); padding-top:0.875rem; margin-top:0.875rem; }
.ht-aside .grp-t { font-size:0.6875rem; font-weight:800; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.6rem; }
.ht-chk { display:flex; align-items:center; gap:0.6rem; padding:0.35rem 0; cursor:pointer; font-size:0.875rem; }
.ht-chk input { width:17px; height:17px; accent-color:var(--ocean); cursor:pointer; }
.ht-chk .stars { color:var(--amber); letter-spacing:-1px; }
.ht-chk .cnt { margin-left:auto; font-size:0.75rem; color:var(--muted); }

/* sort bar */
.ht-sort { display:flex; align-items:center; gap:0.5rem; margin-bottom:1rem; flex-wrap:wrap; }
.ht-sort .lbl { font-size:0.8125rem; color:var(--muted); font-weight:600; }
.ht-seg { display:inline-flex; background:#EEF2F7; border-radius:10px; padding:0.2rem; }
.ht-seg button { border:none; background:none; padding:0.4rem 0.8rem; border-radius:8px; font-family:inherit; font-size:0.8125rem; font-weight:700; color:var(--muted); cursor:pointer; transition:all 0.15s; }
.ht-seg button.on { background:#fff; color:var(--ocean); box-shadow:0 1px 4px rgba(15,23,42,0.1); }
.ht-count { margin-left:auto; font-size:0.8125rem; color:var(--muted); }

/* hotel card */
.ht-card { display:grid; grid-template-columns:230px 1fr auto; gap:1.25rem; background:#fff; border:1px solid var(--border); border-radius:16px; overflow:hidden; transition:border-color 0.15s, box-shadow 0.15s; }
.ht-card + .ht-card { margin-top:1rem; }
.ht-card:hover { border-color:#CBD5E1; box-shadow:0 10px 28px rgba(15,23,42,0.1); }
.ht-photo { position:relative; min-height:190px; background:linear-gradient(135deg,var(--sky),var(--deep)); display:flex; align-items:center; justify-content:center; font-size:2.5rem; color:#fff; }
.ht-photo img { width:100%; height:100%; object-fit:cover; position:absolute; inset:0; }
.ht-photo .ptype { position:absolute; top:0.6rem; left:0.6rem; z-index:2; font-size:0.625rem; font-weight:800; text-transform:uppercase; letter-spacing:0.03em; background:rgba(255,255,255,0.92); color:var(--deep); padding:0.2rem 0.55rem; border-radius:100px; }

.ht-info { padding:1.125rem 0; min-width:0; display:flex; flex-direction:column; }
.ht-stars { color:var(--amber); font-size:0.875rem; letter-spacing:-1px; margin-bottom:0.2rem; }
.ht-name { font-family:'Nunito',sans-serif; font-weight:800; font-size:1.0625rem; line-height:1.25; color:#0F172A; }
.ht-addr { font-size:0.8125rem; color:var(--muted); margin-top:0.3rem; display:flex; align-items:center; gap:0.3rem; }
.ht-amen { display:flex; flex-wrap:wrap; gap:0.35rem; margin-top:0.7rem; }
.ht-amen span { font-size:0.6875rem; font-weight:600; color:#334155; background:#F1F5F9; border-radius:7px; padding:0.2rem 0.5rem; }
.ht-amen .more { background:none; color:var(--ocean); }

.ht-rev { display:flex; align-items:center; gap:0.5rem; margin-top:auto; padding-top:0.7rem; }
.ht-score { background:var(--deep); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.875rem; padding:0.25rem 0.5rem; border-radius:8px 8px 8px 2px; }
.ht-rev .lbl { font-weight:700; font-size:0.8125rem; }
.ht-rev .cnt { font-size:0.75rem; color:var(--muted); }

.ht-buy { padding:1.125rem 1.25rem; border-left:1px dashed var(--border); display:flex; flex-direction:column; align-items:flex-end; justify-content:center; min-width:185px; text-align:right; }
.ht-buy .from { font-size:0.6875rem; color:var(--muted); }
.ht-buy .price { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.5rem; color:var(--deep); white-space:nowrap; }
.ht-buy .per { font-size:0.6875rem; color:var(--muted); }
.ht-buy .total { font-size:0.75rem; color:#334155; margin-top:0.2rem; }
.ht-buy .noprice { font-size:0.8125rem; color:var(--muted); font-weight:600; }
.ht-buy button { margin-top:0.65rem; border:none; border-radius:10px; padding:0.55rem 1.1rem; background:linear-gradient(135deg,var(--sunset),#FB923C); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; cursor:pointer; display:inline-flex; align-items:center; gap:0.35rem; transition:filter 0.15s; }
.ht-buy button:hover { filter:brightness(0.96); }
.ht-buy .src { font-size:0.5625rem; color:#94A3B8; margin-top:0.4rem; }

/* states */
.ht-loading, .ht-empty { text-align:center; padding:3.5rem 1rem; color:var(--muted); background:#fff; border:1px solid var(--border); border-radius:16px; }
.ht-spin { width:34px; height:34px; border:3px solid var(--border); border-top-color:var(--sky); border-radius:50%; animation:ht-spin 0.7s linear infinite; margin:0 auto 0.875rem; }
@keyframes ht-spin { to { transform:rotate(360deg); } }
.ht-empty .ic { font-size:2.75rem; }

@media (max-width:880px) {
  .ht-grid { grid-template-columns:1fr; }
  .ht-aside { position:static; }
  .ht-card { grid-template-columns:1fr; }
  .ht-photo { min-height:170px; }
  .ht-info { padding:1rem 1.25rem 0; }
  .ht-buy { border-left:none; border-top:1px dashed var(--border); align-items:flex-start; text-align:left; flex-direction:row; justify-content:space-between; width:100%; }
  .ht-buy button { margin-top:0; }
}
@media (max-width:600px) {
  .ht-hero, .ht-body { padding-left:1.25rem; padding-right:1.25rem; }
  .ht-field.dest { flex-basis:100%; }
}
`;

/* ─── helpers ─── */
const todayStr = () => new Date().toISOString().slice(0, 10);
const addDays = (s, n) => { const d = new Date(s + "T00:00:00"); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
const fmtVND = (n) => (n || 0).toLocaleString("vi-VN") + "đ";
const nightsBetween = (a, b) => Math.max(1, Math.round((new Date(b) - new Date(a)) / 86400000));
const starStr = (s) => (s ? "★".repeat(Math.round(s)) : "");
const scoreLabel = (r) => r >= 4.5 ? "Tuyệt vời" : r >= 4 ? "Rất tốt" : r >= 3.5 ? "Tốt" : r >= 3 ? "Khá" : "Ổn";
const starBucket = (s) => (s ? String(Math.round(s)) : "0");

/* ─── icons ─── */
const IconSearch = () => (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>);
const IconPin = () => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 21s7-5.5 7-11a7 7 0 10-14 0c0 5.5 7 11 7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>);
const IconExt = () => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17L17 7M17 7H8M17 7v9" /></svg>);

const PTYPE = { hotel: "Khách sạn", resort: "Resort", homestay: "Homestay", apartment: "Căn hộ", villa: "Villa", hostel: "Hostel", guesthouse: "Nhà nghỉ" };

export default function HotelsPage() {
  const [destinations, setDestinations] = useState([]);
  const [destination, setDestination] = useState("da-nang");
  const [checkin, setCheckin] = useState(addDays(todayStr(), 7));
  const [checkout, setCheckout] = useState(addDays(todayStr(), 9));
  const [adults, setAdults] = useState(2);

  const [loading, setLoading] = useState(false);
  const [hotels, setHotels] = useState([]);
  const [sort, setSort] = useState("price");
  const [offStars, setOffStars] = useState(() => new Set());

  /* destinations once */
  useEffect(() => {
    fetch("/api/travel/destinations?limit=50")
      .then((r) => r.json())
      .then((d) => setDestinations(d.items || []))
      .catch(() => {});
  }, []);

  const search = useCallback(async (opts = {}) => {
    const dest = opts.destination ?? destination;
    const ci = opts.checkin ?? checkin;
    const co = opts.checkout ?? checkout;
    if (new Date(co) <= new Date(ci)) { toast("Ngày trả phòng phải sau ngày nhận phòng"); return; }
    setLoading(true);
    try {
      const res = await fetch(`/api/travel/hotels?destination=${dest}&checkin=${ci}&checkout=${co}&adults=${adults}&limit=40`).then((r) => r.json());
      setHotels(res.items || []);
    } catch {
      toast("Không tải được khách sạn. Kiểm tra kết nối máy chủ.");
    } finally {
      setLoading(false);
    }
  }, [destination, checkin, checkout, adults]);

  useEffect(() => { search(); /* eslint-disable-next-line */ }, []);

  const nights = nightsBetween(checkin, checkout);
  const destName = destinations.find((d) => d.slug === destination)?.name || destination;

  /* star buckets present */
  const starOptions = useMemo(() => {
    const m = new Map();
    hotels.forEach((h) => { const b = starBucket(h.stars); m.set(b, (m.get(b) || 0) + 1); });
    return [...m.entries()].sort((a, b) => b[0].localeCompare(a[0])); // 5,4,3,...,0
  }, [hotels]);

  const shown = useMemo(() => {
    let list = hotels.filter((h) => !offStars.has(starBucket(h.stars)));
    list = list.slice();
    if (sort === "price") {
      list.sort((a, b) => {
        if (a.price_amount == null && b.price_amount == null) return (b.avg_rating || 0) - (a.avg_rating || 0);
        if (a.price_amount == null) return 1;
        if (b.price_amount == null) return -1;
        return a.price_amount - b.price_amount;
      });
    } else if (sort === "rating") list.sort((a, b) => (b.avg_rating || 0) - (a.avg_rating || 0));
    else if (sort === "stars") list.sort((a, b) => (b.stars || 0) - (a.stars || 0));
    return list;
  }, [hotels, offStars, sort]);

  const pricedCount = useMemo(() => hotels.filter((h) => h.price_amount != null).length, [hotels]);
  const toggleStar = (b) => setOffStars((p) => { const n = new Set(p); n.has(b) ? n.delete(b) : n.add(b); return n; });

  const openBooking = (h) => {
    if (h.booking_url) window.open(h.booking_url, "_blank", "noopener");
    else toast("Chưa có liên kết đặt phòng cho khách sạn này");
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />
      <SiteHeader active="hotel" />

      <div className="ht-wrap">
        <section className="ht-hero">
          <div className="ht-hero-in">
            <h1>Khách sạn tốt nhất 🏨</h1>
            <p>Hàng trăm lựa chọn từ homestay tới resort 5 sao — giá thật cập nhật từ Google Hotels.</p>
          </div>
        </section>

        <div className="ht-search">
          <div className="ht-row">
            <div className="ht-field dest">
              <label>Điểm đến</label>
              <select value={destination} onChange={(e) => setDestination(e.target.value)}>
                {destinations.map((d) => <option key={d.slug} value={d.slug}>{d.name}</option>)}
              </select>
            </div>
            <div className="ht-field" style={{ flex: 1, minWidth: 140 }}>
              <label>Nhận phòng</label>
              <input type="date" value={checkin} min={todayStr()} onChange={(e) => { setCheckin(e.target.value); if (new Date(checkout) <= new Date(e.target.value)) setCheckout(addDays(e.target.value, 2)); }} />
            </div>
            <div className="ht-field" style={{ flex: 1, minWidth: 140 }}>
              <label>Trả phòng</label>
              <input type="date" value={checkout} min={addDays(checkin, 1)} onChange={(e) => setCheckout(e.target.value)} />
            </div>
            <div className="ht-field" style={{ maxWidth: 120 }}>
              <label>Số khách</label>
              <select value={adults} onChange={(e) => setAdults(Number(e.target.value))}>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => <option key={n} value={n}>{n} người</option>)}
              </select>
            </div>
            <div className="ht-go">
              <button onClick={() => search()} disabled={loading}><IconSearch /> {loading ? "Đang tìm…" : "Tìm khách sạn"}</button>
            </div>
          </div>
        </div>

        <div className="ht-body">
          {loading && hotels.length === 0 ? (
            <div className="ht-loading"><div className="ht-spin" />Đang tìm khách sạn & cập nhật giá thật…</div>
          ) : hotels.length === 0 ? (
            <div className="ht-empty"><div className="ic">🏨</div><p>Không tìm thấy khách sạn. Thử điểm đến hoặc ngày khác.</p></div>
          ) : (
            <>
              <div className="ht-summary">
                <span className="dest">{destName}</span>
              </div>

              <div className="ht-grid">
                <aside className="ht-aside">
                  <h3>Bộ lọc</h3>
                  <div className="grp" style={{ borderTop: "none", marginTop: 0, paddingTop: 0 }}>
                    <div className="grp-t">Hạng sao</div>
                    {starOptions.map(([b, cnt]) => (
                      <label key={b} className="ht-chk">
                        <input type="checkbox" checked={!offStars.has(b)} onChange={() => toggleStar(b)} />
                        {b === "0" ? <span>Chưa xếp hạng</span> : <span className="stars">{"★".repeat(Number(b))}</span>}
                        <span className="cnt">{cnt}</span>
                      </label>
                    ))}
                  </div>
                </aside>

                <div>
                  <div className="ht-sort">
                    <span className="lbl">Sắp xếp:</span>
                    <div className="ht-seg">
                      <button className={sort === "price" ? "on" : ""} onClick={() => setSort("price")}>Giá thấp</button>
                      <button className={sort === "rating" ? "on" : ""} onClick={() => setSort("rating")}>Đánh giá cao</button>
                      <button className={sort === "stars" ? "on" : ""} onClick={() => setSort("stars")}>Hạng sao</button>
                    </div>
                    <span className="ht-count">{shown.length} khách sạn</span>
                  </div>

                  {shown.length === 0 ? (
                    <div className="ht-empty"><div className="ic">😕</div><p>Không có khách sạn khớp bộ lọc.</p></div>
                  ) : shown.map((h) => {
                    const amen = Array.isArray(h.amenities) ? h.amenities : [];
                    return (
                      <div key={h.id} className="ht-card">
                        <div className="ht-photo">
                          {h.property_type && <span className="ptype">{PTYPE[h.property_type] || h.property_type}</span>}
                          {h.primary_image_url ? <img src={h.primary_image_url} alt="" loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} /> : "🏨"}
                        </div>

                        <div className="ht-info">
                          {h.stars > 0 && <div className="ht-stars">{starStr(h.stars)}</div>}
                          <div className="ht-name">{h.name}</div>
                          {(h.area || h.address) && <div className="ht-addr"><IconPin /> {h.area || h.address}</div>}
                          {amen.length > 0 && (
                            <div className="ht-amen">
                              {amen.slice(0, 4).map((a, i) => <span key={i}>{a}</span>)}
                              {amen.length > 4 && <span className="more">+{amen.length - 4} tiện ích</span>}
                            </div>
                          )}
                          {h.avg_rating > 0 && (
                            <div className="ht-rev">
                              <span className="ht-score">{h.avg_rating.toFixed(1)}</span>
                              <span className="lbl">{scoreLabel(h.avg_rating)}</span>
                              {h.review_count > 0 && <span className="cnt">({h.review_count.toLocaleString("vi-VN")} đánh giá)</span>}
                            </div>
                          )}
                        </div>

                        <div className="ht-buy">
                          {h.price_amount != null ? (
                            <>
                              <div className="from">Chỉ từ</div>
                              <div className="price">{fmtVND(h.price_amount)}</div>
                              <div className="per">/ đêm</div>
                              <div className="total">{nights} đêm ≈ {fmtVND(h.price_amount * nights)}</div>
                              <button onClick={() => openBooking(h)}>Đặt phòng <IconExt /></button>
                              <div className="src">Giá/đêm đã gồm thuế & phí · Google Hotels</div>
                            </>
                          ) : (
                            <>
                              <div className="noprice">Chưa có giá cho ngày này</div>
                              <button onClick={() => openBooking(h)}>Xem chi tiết <IconExt /></button>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <SiteFooter />
    </>
  );
}
