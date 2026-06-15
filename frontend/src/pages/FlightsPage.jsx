import { useState, useEffect, useMemo, useCallback } from "react";
import { SiteHeader, SiteFooter } from "../components/SiteChrome";
import { toast } from "../components/dialog";

/* ════════════════════════════════════════════════════════════
   TravelBuddy — Vé máy bay (Flights)
   Tìm chuyến bay nội địa VN. Data đồng bộ thật từ BE:
     /api/travel/airports         → danh sách sân bay
     /api/travel/flights/search   → chuyến bay + lịch giá (giá thật nếu có,
                                      nếu chưa thì BE trả ước tính, cờ estimated)
═══════════════════════════════════════════════════════════════ */

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
body { font-family:'Inter',-apple-system,sans-serif; background:#F0F9FF; color:#0F172A; -webkit-font-smoothing:antialiased; }
:root {
  --sky:#0EA5E9; --ocean:#0284C7; --deep:#0369A1; --deepest:#075985;
  --sunset:#F97316; --coral:#FB7185; --green:#10B981; --amber:#F59E0B;
  --muted:#64748B; --border:#E2E8F0;
}

.fl-wrap { min-height:calc(100vh - 64px); }

/* ─── HERO + SEARCH ─── */
.fl-hero { background:linear-gradient(125deg,var(--deepest),var(--ocean) 60%,var(--sky)); padding:2.5rem 2rem 5.5rem; position:relative; overflow:hidden; }
.fl-hero::before { content:''; position:absolute; inset:0; background-image:radial-gradient(circle,rgba(255,255,255,0.08) 1.5px,transparent 1.5px); background-size:26px 26px; }
.fl-hero-in { max-width:1100px; margin:0 auto; position:relative; z-index:2; }
.fl-hero h1 { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.875rem; color:#fff; letter-spacing:-0.02em; }
.fl-hero p { color:rgba(255,255,255,0.82); font-size:0.9375rem; margin-top:0.3rem; }

.fl-search { max-width:1100px; margin:-4rem auto 0; position:relative; z-index:5; background:#fff; border-radius:18px; box-shadow:0 16px 44px rgba(15,23,42,0.13); border:1px solid rgba(226,232,240,0.7); padding:1.25rem 1.25rem 1.375rem; }
.fl-trip { display:flex; gap:0.375rem; margin-bottom:1rem; }
.fl-trip button { display:inline-flex; align-items:center; gap:0.4rem; padding:0.4rem 0.9rem; border-radius:100px; border:1.5px solid var(--border); background:#fff; font-family:inherit; font-size:0.8125rem; font-weight:700; color:var(--muted); cursor:pointer; transition:all 0.15s; }
.fl-trip button.on { background:#EFF8FF; border-color:var(--sky); color:var(--ocean); }

.fl-row { display:flex; gap:0.75rem; align-items:flex-end; flex-wrap:wrap; }
.fl-field { display:flex; flex-direction:column; gap:0.3rem; flex:1; min-width:140px; }
.fl-field label { font-size:0.6875rem; font-weight:800; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; }
.fl-field select, .fl-field input { width:100%; padding:0.7rem 0.75rem; border:1.5px solid var(--border); border-radius:11px; font-family:inherit; font-size:0.9375rem; font-weight:600; color:#0F172A; background:#FAFBFC; outline:none; transition:all 0.15s; }
.fl-field select:focus, .fl-field input:focus { border-color:var(--sky); background:#fff; box-shadow:0 0 0 3px rgba(14,165,233,0.1); }
.fl-od { flex:2.4; display:flex; align-items:flex-end; gap:0.5rem; min-width:300px; }
.fl-od .fl-field { flex:1; }
.fl-swap { flex-shrink:0; width:40px; height:43px; border:1.5px solid var(--border); border-radius:11px; background:#fff; color:var(--ocean); cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.15s; }
.fl-swap:hover { border-color:var(--sky); background:#F0F9FF; transform:rotate(180deg); }
.fl-go { flex-shrink:0; }
.fl-go button { height:43px; padding:0 1.5rem; border:none; border-radius:11px; background:var(--ocean); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; cursor:pointer; display:inline-flex; align-items:center; gap:0.5rem; transition:background 0.15s; white-space:nowrap; }
.fl-go button:hover { background:var(--deep); }
.fl-go button:disabled { opacity:0.6; cursor:not-allowed; }

/* ─── BODY ─── */
.fl-body { max-width:1100px; margin:1.75rem auto 0; padding:0 2rem 3.5rem; }
.fl-estbar { display:flex; align-items:center; gap:0.6rem; background:#FFFBEB; border:1px solid #FDE68A; color:#92400E; border-radius:12px; padding:0.7rem 1rem; font-size:0.8125rem; margin-bottom:1.25rem; }
.fl-estbar b { font-weight:800; }

/* price calendar */
.fl-cal-wrap { background:#fff; border:1px solid var(--border); border-radius:16px; padding:0.875rem 1rem; margin-bottom:1.5rem; box-shadow:0 4px 16px rgba(15,23,42,0.05); }
.fl-cal-head { font-size:0.75rem; font-weight:800; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.6rem; padding-left:0.15rem; }
.fl-cal { display:flex; gap:0.5rem; overflow-x:auto; padding-bottom:0.35rem; scrollbar-width:thin; }
.fl-cal-day { flex-shrink:0; min-width:86px; border:1.5px solid var(--border); border-radius:12px; padding:0.55rem 0.4rem; text-align:center; cursor:pointer; background:#fff; transition:all 0.15s; }
.fl-cal-day:hover { border-color:var(--sky); }
.fl-cal-day.on { border-color:var(--ocean); background:#EFF8FF; box-shadow:0 0 0 2px rgba(2,132,199,0.18); }
.fl-cal-day .wd { font-size:0.6875rem; font-weight:700; color:var(--muted); }
.fl-cal-day .dm { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.875rem; margin:0.1rem 0; }
.fl-cal-day .pr { font-size:0.75rem; font-weight:800; color:var(--ocean); }
.fl-cal-day.cheap .pr { color:var(--green); }
.fl-cal-day .cheaptag { font-size:0.5625rem; font-weight:800; color:var(--green); text-transform:uppercase; letter-spacing:0.03em; }

/* thời tiết trong từng ngày của lịch giá */
.fl-cal-day .wx { font-size:0.75rem; font-weight:700; color:#334155; margin:0.1rem 0; white-space:nowrap; }

/* card chi tiết thời tiết (trong sidebar bộ lọc) */
.fl-wxd { background:linear-gradient(135deg,#EFF8FF,#F0FDFA); border:1px solid #BAE6FD; border-radius:13px; padding:0.875rem; }
.fl-wxd-top { display:flex; align-items:center; gap:0.6rem; }
.fl-wxd-top .emo { font-size:2rem; line-height:1; }
.fl-wxd-top .cond { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; color:#0F172A; }
.fl-wxd-top .dt { font-size:0.6875rem; color:var(--muted); font-weight:600; }
.fl-wxd-temps { margin:0.6rem 0 0.5rem; display:flex; align-items:baseline; gap:0.35rem; }
.fl-wxd-temps b { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.75rem; color:var(--deep); }
.fl-wxd-temps span { font-size:0.875rem; color:var(--muted); font-weight:600; }
.fl-wxd-rows { display:flex; flex-direction:column; gap:0.25rem; font-size:0.8125rem; color:#334155; }
.fl-wxd-rows b { font-weight:800; color:#0F172A; }
.fl-wxd-hint { font-size:0.6875rem; color:var(--muted); line-height:1.4; margin-top:0.2rem; }
.fl-wxd-tip { margin-top:0.6rem; padding-top:0.6rem; border-top:1px solid #BAE6FD; font-size:0.75rem; color:var(--deep); line-height:1.4; }
.fl-wxd-none { font-size:0.8125rem; color:var(--muted); line-height:1.5; background:#F8FAFC; border:1px dashed var(--border); border-radius:11px; padding:0.7rem; }

/* layout */
.fl-grid { display:grid; grid-template-columns:236px 1fr; gap:1.5rem; align-items:start; }
.fl-aside { position:sticky; top:80px; background:#fff; border:1px solid var(--border); border-radius:16px; padding:1.125rem; box-shadow:0 4px 16px rgba(15,23,42,0.05); }
.fl-aside h3 { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.9375rem; margin-bottom:0.875rem; }
.fl-aside .grp { border-top:1px solid var(--border); padding-top:0.875rem; margin-top:0.875rem; }
.fl-aside .grp-t { font-size:0.6875rem; font-weight:800; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.6rem; }
.fl-chk { display:flex; align-items:center; gap:0.6rem; padding:0.35rem 0; cursor:pointer; font-size:0.875rem; }
.fl-chk input { width:17px; height:17px; accent-color:var(--ocean); cursor:pointer; }
.fl-chk .al-dot { width:10px; height:10px; border-radius:3px; flex-shrink:0; }
.fl-chk .cnt { margin-left:auto; font-size:0.75rem; color:var(--muted); }

/* sort bar */
.fl-sort { display:flex; align-items:center; gap:0.5rem; margin-bottom:1rem; flex-wrap:wrap; }
.fl-sort .lbl { font-size:0.8125rem; color:var(--muted); font-weight:600; }
.fl-seg { display:inline-flex; background:#EEF2F7; border-radius:10px; padding:0.2rem; }
.fl-seg button { border:none; background:none; padding:0.4rem 0.8rem; border-radius:8px; font-family:inherit; font-size:0.8125rem; font-weight:700; color:var(--muted); cursor:pointer; transition:all 0.15s; }
.fl-seg button.on { background:#fff; color:var(--ocean); box-shadow:0 1px 4px rgba(15,23,42,0.1); }
.fl-count { margin-left:auto; font-size:0.8125rem; color:var(--muted); }

/* flight card */
.fl-card { background:#fff; border:1px solid var(--border); border-radius:16px; padding:1.125rem 1.25rem; display:grid; grid-template-columns:150px 1fr auto; gap:1.25rem; align-items:center; transition:border-color 0.15s, box-shadow 0.15s; }
.fl-card + .fl-card { margin-top:0.75rem; }
.fl-card:hover { border-color:#CBD5E1; box-shadow:0 8px 22px rgba(15,23,42,0.08); }
.fl-air { display:flex; align-items:center; gap:0.6rem; min-width:0; }
.fl-air-logo { width:40px; height:40px; border-radius:11px; flex-shrink:0; display:flex; align-items:center; justify-content:center; color:#fff; font-family:'Nunito',sans-serif; font-weight:900; font-size:0.8125rem; }
.fl-air-name { font-family:'Nunito',sans-serif; font-weight:800; font-size:0.875rem; line-height:1.2; }
.fl-air-no { font-size:0.75rem; color:var(--muted); }

.fl-timeline { display:flex; align-items:center; gap:0.875rem; }
.fl-pt { text-align:center; }
.fl-pt .t { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.25rem; line-height:1; }
.fl-pt .c { font-size:0.75rem; color:var(--muted); font-weight:700; margin-top:0.25rem; }
.fl-mid { flex:1; text-align:center; min-width:90px; }
.fl-mid .dur { font-size:0.75rem; color:var(--muted); font-weight:700; }
.fl-line { position:relative; height:2px; background:var(--border); margin:0.35rem 0; }
.fl-line::after { content:'✈'; position:absolute; right:-2px; top:50%; transform:translateY(-50%); font-size:0.75rem; color:var(--sky); background:#fff; padding-left:2px; }
.fl-mid .stops { font-size:0.6875rem; font-weight:800; color:var(--green); }

.fl-buy { text-align:right; }
.fl-buy .pr { font-family:'Nunito',sans-serif; font-weight:900; font-size:1.375rem; color:var(--deep); white-space:nowrap; }
.fl-buy .pp { font-size:0.6875rem; color:var(--muted); }
.fl-buy .tot { font-size:0.6875rem; color:var(--muted); margin-top:0.1rem; }
.fl-buy button { margin-top:0.5rem; border:none; border-radius:10px; padding:0.5rem 1.1rem; background:linear-gradient(135deg,var(--sunset),#FB923C); color:#fff; font-family:'Nunito',sans-serif; font-weight:800; font-size:0.8125rem; cursor:pointer; display:inline-flex; align-items:center; gap:0.35rem; transition:filter 0.15s; }
.fl-buy button:hover { filter:brightness(0.95); }

.fl-leg-title { font-family:'Nunito',sans-serif; font-weight:800; font-size:1.0625rem; margin:0.5rem 0 0.875rem; display:flex; align-items:center; gap:0.5rem; }
.fl-leg-title .badge { font-size:0.6875rem; font-weight:800; padding:0.15rem 0.55rem; border-radius:100px; background:#EFF8FF; color:var(--ocean); }

/* states */
.fl-loading, .fl-empty { text-align:center; padding:3.5rem 1rem; color:var(--muted); background:#fff; border:1px solid var(--border); border-radius:16px; }
.fl-spin { width:34px; height:34px; border:3px solid var(--border); border-top-color:var(--sky); border-radius:50%; animation:fl-spin 0.7s linear infinite; margin:0 auto 0.875rem; }
@keyframes fl-spin { to { transform:rotate(360deg); } }
.fl-empty .ic { font-size:2.75rem; }

@media (max-width:880px) {
  .fl-grid { grid-template-columns:1fr; }
  .fl-aside { position:static; }
  .fl-card { grid-template-columns:1fr; gap:0.875rem; }
  .fl-air { order:1; }
  .fl-timeline { order:2; }
  .fl-buy { order:3; text-align:left; display:flex; align-items:center; justify-content:space-between; }
  .fl-buy button { margin-top:0; }
}
@media (max-width:600px) {
  .fl-hero, .fl-body { padding-left:1.25rem; padding-right:1.25rem; }
  .fl-od { min-width:0; flex-basis:100%; }
  .fl-search { padding:1rem; }
}
`;

/* ─── meta ─── */
const AIRLINE = {
  VN: { color: "#16654E" }, // Vietnam Airlines
  VJ: { color: "#E8112D" }, // VietJet
  QH: { color: "#1A9E5E" }, // Bamboo
};
const alMeta = (code) => AIRLINE[code] || { color: "#0EA5E9" };

const CABINS = [
  { v: "economy", l: "Phổ thông" },
  { v: "premium_economy", l: "Phổ thông đặc biệt" },
  { v: "business", l: "Thương gia" },
  { v: "first", l: "Hạng nhất" },
];

const WD = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
const pad = (n) => String(n).padStart(2, "0");
const todayStr = () => new Date().toISOString().slice(0, 10);
const addDays = (str, n) => { const d = new Date(str + "T00:00:00"); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
const fmtVND = (n) => (n || 0).toLocaleString("vi-VN") + "đ";
const hhmm = (iso) => (iso ? iso.slice(11, 16) : "--:--");
const fmtDur = (m) => `${Math.floor((m || 0) / 60)}h${(m || 0) % 60 ? " " + ((m || 0) % 60) + "m" : ""}`;
const calLabel = (str) => { const d = new Date(str + "T00:00:00"); return { wd: WD[d.getDay()], dm: `${pad(d.getDate())}/${pad(d.getMonth() + 1)}` }; };

/* WMO weather code → emoji + nhãn tiếng Việt */
const wmo = (code) => {
  const m = {
    0: ["☀️", "Nắng"], 1: ["🌤️", "Ít mây"], 2: ["⛅", "Có mây"], 3: ["☁️", "Nhiều mây"],
    45: ["🌫️", "Sương mù"], 48: ["🌫️", "Sương mù"],
    51: ["🌦️", "Mưa phùn"], 53: ["🌦️", "Mưa phùn"], 55: ["🌦️", "Mưa phùn"],
    61: ["🌧️", "Mưa nhẹ"], 63: ["🌧️", "Mưa"], 65: ["🌧️", "Mưa to"],
    66: ["🌧️", "Mưa lạnh"], 67: ["🌧️", "Mưa lạnh"],
    71: ["🌨️", "Tuyết"], 73: ["🌨️", "Tuyết"], 75: ["🌨️", "Tuyết"], 77: ["🌨️", "Mưa tuyết"],
    80: ["🌦️", "Mưa rào"], 81: ["🌧️", "Mưa rào"], 82: ["⛈️", "Mưa rào lớn"],
    85: ["🌨️", "Tuyết rào"], 86: ["🌨️", "Tuyết rào"],
    95: ["⛈️", "Dông"], 96: ["⛈️", "Dông kèm mưa đá"], 99: ["⛈️", "Dông kèm mưa đá"],
  };
  return m[code] || ["🌡️", "—"];
};

/* ─── icons ─── */
const IconSwap = () => (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M7 4v13M7 4L4 7M7 4l3 3M17 20V7M17 20l-3-3M17 20l3-3" /></svg>);
const IconSearch = () => (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>);
const IconExt = () => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17L17 7M17 7H8M17 7v9" /></svg>);

/* ════════════════════════════════════════════════════════════ */
export default function FlightsPage() {
  const [airports, setAirports] = useState([]);
  const [tripType, setTripType] = useState("oneway");
  const [from, setFrom] = useState("HAN");
  const [to, setTo] = useState("SGN");
  const [departDate, setDepartDate] = useState(todayStr());
  const [returnDate, setReturnDate] = useState(addDays(todayStr(), 3));
  const [adults, setAdults] = useState(1);
  const [cabin, setCabin] = useState("economy");

  const [loading, setLoading] = useState(false);
  const [outbound, setOutbound] = useState(null);
  const [inbound, setInbound] = useState(null);
  const [weather, setWeather] = useState(null);

  /* fetch airports once */
  useEffect(() => {
    fetch("/api/travel/airports")
      .then((r) => r.json())
      .then((d) => setAirports(d.items || []))
      .catch(() => {});
  }, []);

  const search = useCallback(async (opts = {}) => {
    const o = opts.from ?? from;
    const d = opts.to ?? to;
    const dep = opts.departDate ?? departDate;
    if (o === d) { toast("Điểm đi và điểm đến phải khác nhau"); return; }
    setLoading(true);
    try {
      const qs = (orig, dest, date) =>
        `/api/travel/flights/search?origin=${orig}&destination=${dest}&depart_date=${date}&cabin_class=${cabin}&adults=${adults}`;
      const outRes = await fetch(qs(o, d, dep)).then((r) => r.json());
      setOutbound(outRes);
      // thời tiết tại điểm đến — khớp khoảng ngày của lịch giá, chỉ từ hôm nay trở đi
      const cal = (outRes.price_calendar || []).filter((c) => c.date >= todayStr());
      const wFrom = cal.length ? cal[0].date : dep;
      const wTo = cal.length ? cal[cal.length - 1].date : dep;
      fetch(`/api/travel/weather/by-airport?iata=${d}&date_from=${wFrom}&date_to=${wTo}`)
        .then((r) => r.json()).then(setWeather).catch(() => setWeather(null));
      if ((opts.tripType ?? tripType) === "round") {
        const ret = await fetch(qs(d, o, opts.returnDate ?? returnDate)).then((r) => r.json());
        setInbound(ret);
      } else {
        setInbound(null);
      }
    } catch {
      toast("Không tải được chuyến bay. Kiểm tra kết nối máy chủ.");
    } finally {
      setLoading(false);
    }
  }, [from, to, departDate, returnDate, cabin, adults, tripType]);

  /* auto search on first load */
  useEffect(() => { search(); /* eslint-disable-next-line */ }, []);

  const doSwap = () => { setFrom(to); setTo(from); };
  const pickDate = (dstr) => { setDepartDate(dstr); search({ departDate: dstr }); };

  const airOpt = (a) => `${a.city} (${a.iata_code})`;
  const cityOf = (code) => airports.find((a) => a.iata_code === code)?.city || code;

  // chỉ giữ ngày hôm nay & tương lai (bỏ ngày quá khứ)
  const calDays = useMemo(
    () => (outbound?.price_calendar || []).filter((c) => c.date >= todayStr()),
    [outbound]
  );
  const cheapest = useMemo(
    () => (calDays.length ? Math.min(...calDays.map((c) => c.min_price)) : null),
    [calDays]
  );

  const wxByDate = useMemo(() => {
    const m = {};
    (weather?.items || []).forEach((w) => { m[w.forecast_date] = w; });
    return m;
  }, [weather]);
  const destCity = weather?.destination?.city || cityOf(to);

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />
      <SiteHeader active="flight" />

      <div className="fl-wrap">
        {/* HERO */}
        <section className="fl-hero">
          <div className="fl-hero-in">
            <h1>Vé máy bay giá rẻ ✈️</h1>
            <p>So sánh giá VietJet, Bamboo Airways, Vietnam Airlines — đặt vé nội địa nhanh chóng.</p>
          </div>
        </section>

        {/* SEARCH CARD */}
        <div className="fl-search">
          <div className="fl-trip">
            <button className={tripType === "oneway" ? "on" : ""} onClick={() => setTripType("oneway")}>Một chiều</button>
            <button className={tripType === "round" ? "on" : ""} onClick={() => setTripType("round")}>Khứ hồi</button>
          </div>

          <div className="fl-row">
            <div className="fl-od">
              <div className="fl-field">
                <label>Điểm đi</label>
                <select value={from} onChange={(e) => setFrom(e.target.value)}>
                  {airports.map((a) => <option key={a.iata_code} value={a.iata_code}>{airOpt(a)}</option>)}
                </select>
              </div>
              <button className="fl-swap" onClick={doSwap} title="Đổi chiều"><IconSwap /></button>
              <div className="fl-field">
                <label>Điểm đến</label>
                <select value={to} onChange={(e) => setTo(e.target.value)}>
                  {airports.map((a) => <option key={a.iata_code} value={a.iata_code}>{airOpt(a)}</option>)}
                </select>
              </div>
            </div>

            <div className="fl-field" style={{ maxWidth: 150 }}>
              <label>Ngày đi</label>
              <input type="date" value={departDate} min={todayStr()} onChange={(e) => setDepartDate(e.target.value)} />
            </div>
            {tripType === "round" && (
              <div className="fl-field" style={{ maxWidth: 150 }}>
                <label>Ngày về</label>
                <input type="date" value={returnDate} min={departDate} onChange={(e) => setReturnDate(e.target.value)} />
              </div>
            )}
            <div className="fl-field" style={{ maxWidth: 110 }}>
              <label>Số khách</label>
              <select value={adults} onChange={(e) => setAdults(Number(e.target.value))}>
                {[1, 2, 3, 4, 5, 6].map((n) => <option key={n} value={n}>{n} người</option>)}
              </select>
            </div>
            <div className="fl-field" style={{ maxWidth: 170 }}>
              <label>Hạng ghế</label>
              <select value={cabin} onChange={(e) => setCabin(e.target.value)}>
                {CABINS.map((c) => <option key={c.v} value={c.v}>{c.l}</option>)}
              </select>
            </div>
            <div className="fl-go">
              <button onClick={() => search()} disabled={loading}><IconSearch /> {loading ? "Đang tìm…" : "Tìm chuyến bay"}</button>
            </div>
          </div>
        </div>

        {/* BODY */}
        <div className="fl-body">
          {loading && !outbound ? (
            <div className="fl-loading"><div className="fl-spin" />Đang tìm chuyến bay phù hợp…</div>
          ) : outbound ? (
            <>
              {/* price calendar (kèm thời tiết theo ngày) */}
              {calDays.length > 0 && (
                <div className="fl-cal-wrap">
                  <div className="fl-cal-head">Lịch giá rẻ — {cityOf(from)} → {cityOf(to)}</div>
                  <div className="fl-cal">
                    {calDays.map((c) => {
                      const { wd, dm } = calLabel(c.date);
                      const isCheap = cheapest != null && c.min_price === cheapest;
                      const wx = wxByDate[c.date];
                      return (
                        <div key={c.date}
                          className={"fl-cal-day" + (c.date === departDate ? " on" : "") + (isCheap ? " cheap" : "")}
                          onClick={() => pickDate(c.date)}>
                          <div className="wd">{wd}</div>
                          <div className="dm">{dm}</div>
                          {wx && <div className="wx" title={wmo(wx.weather_code)[1]}>{wmo(wx.weather_code)[0]} {Math.round(wx.temp_max_c)}°</div>}
                          <div className="pr">{(c.min_price / 1000).toLocaleString("vi-VN")}k</div>
                          {isCheap && <div className="cheaptag">Rẻ nhất</div>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {tripType === "round" && (
                <div className="fl-leg-title">Chuyến đi <span className="badge">{cityOf(from)} → {cityOf(to)}</span></div>
              )}
              <FlightResults data={outbound} adults={adults}
                weatherDay={wxByDate[departDate] || null} weatherCity={destCity} weatherDateStr={departDate} />

              {tripType === "round" && inbound && (
                <>
                  <div className="fl-leg-title" style={{ marginTop: "1.75rem" }}>Chuyến về <span className="badge">{cityOf(to)} → {cityOf(from)}</span></div>
                  <FlightResults data={inbound} adults={adults} />
                </>
              )}
            </>
          ) : (
            <div className="fl-empty"><div className="ic">🔎</div><p>Chọn hành trình và bấm “Tìm chuyến bay”.</p></div>
          )}
        </div>
      </div>

      <SiteFooter />
    </>
  );
}

/* ─── results: filter + sort + list (own state, dùng cho mỗi chiều) ─── */
function FlightResults({ data, adults, weatherDay, weatherCity, weatherDateStr }) {
  const offers = data?.offers || [];
  const [sort, setSort] = useState("price");
  const [offAir, setOffAir] = useState(() => new Set());

  const airlines = useMemo(() => {
    const m = new Map();
    offers.forEach((o) => { if (!m.has(o.airline_iata)) m.set(o.airline_iata, { code: o.airline_iata, name: o.airline_name, count: 0 }); m.get(o.airline_iata).count++; });
    return [...m.values()];
  }, [offers]);

  const shown = useMemo(() => {
    let list = offers.filter((o) => !offAir.has(o.airline_iata));
    list = list.slice();
    if (sort === "price") list.sort((a, b) => a.price_amount - b.price_amount);
    else if (sort === "duration") list.sort((a, b) => a.duration_minutes - b.duration_minutes);
    else if (sort === "depart") list.sort((a, b) => a.depart_at.localeCompare(b.depart_at));
    return list;
  }, [offers, offAir, sort]);

  const toggleAir = (code) => setOffAir((p) => { const n = new Set(p); n.has(code) ? n.delete(code) : n.add(code); return n; });

  const openBooking = (o) => {
    if (o.booking_url) window.open(o.booking_url, "_blank", "noopener");
    else toast("Chưa có liên kết đặt vé cho hãng này");
  };

  return (
    <div className="fl-grid">
      <aside className="fl-aside">
        <h3>Bộ lọc</h3>
        <div className="grp" style={{ borderTop: "none", marginTop: 0, paddingTop: 0 }}>
          <div className="grp-t">Hãng bay</div>
          {airlines.map((a) => (
            <label key={a.code} className="fl-chk">
              <input type="checkbox" checked={!offAir.has(a.code)} onChange={() => toggleAir(a.code)} />
              <span className="al-dot" style={{ background: alMeta(a.code).color }} />
              {a.name}
              <span className="cnt">{a.count}</span>
            </label>
          ))}
        </div>

        {weatherDay !== undefined && (
          <div className="grp">
            <div className="grp-t">Thời tiết ngày đi</div>
            {weatherDay ? (() => {
              const [emo, label] = wmo(weatherDay.weather_code);
              const { wd, dm } = calLabel(weatherDay.forecast_date);
              const rain = weatherDay.precipitation_probability_max ?? 0;
              const tip = rain >= 70 ? "🌂 Mưa nhiều — nhớ mang ô / áo mưa."
                : weatherDay.temp_max_c >= 35 ? "🧴 Nắng nóng — mang nước & kem chống nắng."
                : "👍 Thời tiết khá thuận lợi để bay.";
              return (
                <div className="fl-wxd">
                  <div className="fl-wxd-top">
                    <span className="emo">{emo}</span>
                    <div>
                      <div className="cond">{label}</div>
                      <div className="dt">{wd}, {dm} · {weatherCity}</div>
                    </div>
                  </div>
                  <div className="fl-wxd-temps"><b>{Math.round(weatherDay.temp_max_c)}°</b><span>cao nhất · {Math.round(weatherDay.temp_min_c)}° thấp nhất</span></div>
                  <div className="fl-wxd-rows">
                    <div>💧 Khả năng mưa <b>{rain}%</b></div>
                    <div>💨 Gió <b>{Math.round(weatherDay.wind_speed_max_kmh)} km/h</b></div>
                    <div className="fl-wxd-hint">Nhiệt độ cao nhất thường vào buổi trưa; mưa/dông hay xảy ra buổi chiều.</div>
                  </div>
                  <div className="fl-wxd-tip">{tip}</div>
                </div>
              );
            })() : (
              <div className="fl-wxd-none">Chưa có dự báo cho ngày này — Open-Meteo chỉ dự báo trong khoảng ~16 ngày tới.</div>
            )}
          </div>
        )}
      </aside>

      <div>
        <div className="fl-sort">
          <span className="lbl">Sắp xếp:</span>
          <div className="fl-seg">
            <button className={sort === "price" ? "on" : ""} onClick={() => setSort("price")}>Rẻ nhất</button>
            <button className={sort === "duration" ? "on" : ""} onClick={() => setSort("duration")}>Nhanh nhất</button>
            <button className={sort === "depart" ? "on" : ""} onClick={() => setSort("depart")}>Sớm nhất</button>
          </div>
          <span className="fl-count">{shown.length} chuyến</span>
        </div>

        {shown.length === 0 ? (
          <div className="fl-empty"><div className="ic">😕</div><p>Không có chuyến bay khớp bộ lọc.</p></div>
        ) : shown.map((o) => (
          <div key={o.flight_number + o.depart_at} className="fl-card">
            <div className="fl-air">
              <div className="fl-air-logo" style={{ background: alMeta(o.airline_iata).color }}>{o.airline_iata}</div>
              <div>
                <div className="fl-air-name">{o.airline_name}</div>
                <div className="fl-air-no">{o.flight_number}</div>
              </div>
            </div>

            <div className="fl-timeline">
              <div className="fl-pt"><div className="t">{hhmm(o.depart_at)}</div><div className="c">{o.route_key?.split("-")[0]}</div></div>
              <div className="fl-mid">
                <div className="dur">{fmtDur(o.duration_minutes)}</div>
                <div className="fl-line" />
                <div className="stops">{o.stops > 0 ? `${o.stops} điểm dừng` : "Bay thẳng"}</div>
              </div>
              <div className="fl-pt"><div className="t">{hhmm(o.arrive_at)}</div><div className="c">{o.route_key?.split("-")[1]}</div></div>
            </div>

            <div className="fl-buy">
              <div className="pr">{fmtVND(o.price_amount)}</div>
              <div className="pp">/ người</div>
              {adults > 1 && <div className="tot">Tổng {adults} khách: {fmtVND(o.price_amount * adults)}</div>}
              <button onClick={() => openBooking(o)}>Chọn <IconExt /></button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
