import { useState, useRef, useEffect } from "react";

const C = {
  bg: "#F5F6FA", surface: "#FFFFFF", sidebar: "#FFFFFF", sidebarBorder: "#E8ECF1",
  accent: "#4A7BF7", accentLight: "#EEF2FF", text: "#1A2138", textSecondary: "#6B7A99",
  textMuted: "#9CA8BE", border: "#E8ECF1",
  blue: "#4A7BF7", blueBg: "#EEF2FF", green: "#22A06B", greenBg: "#E9F7EF",
  yellow: "#CF8806", yellowBg: "#FFF8E6", red: "#DE350B", redBg: "#FFEBE6",
  orange: "#D97008", orangeBg: "#FFF4E5", purple: "#6554C0", purpleBg: "#F3F0FF",
};

function SvgIcon({ name, size = 20, color = C.textSecondary }) {
  const p = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1.5" fill={color} opacity="0.9"/><rect x="14" y="3" width="7" height="7" rx="1.5" fill={color} opacity="0.6"/><rect x="3" y="14" width="7" height="7" rx="1.5" fill={color} opacity="0.6"/><rect x="14" y="14" width="7" height="7" rx="1.5" fill={color} opacity="0.4"/></>,
    inspections: <><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" stroke={color} fill="none" strokeWidth="1.8"/><rect x="9" y="3" width="6" height="4" rx="1" stroke={color} fill="none" strokeWidth="1.8"/><path d="M9 14l2 2 4-4" stroke={color} fill="none" strokeWidth="1.8"/></>,
    cars: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke={color} fill="none" strokeWidth="1.8"/><path d="M14 2v6h6" stroke={color} fill="none" strokeWidth="1.8"/><line x1="8" y1="13" x2="16" y2="13" stroke={color} strokeWidth="1.8"/><line x1="8" y1="17" x2="13" y2="17" stroke={color} strokeWidth="1.8"/></>,
    notifications: <><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" stroke={color} fill="none" strokeWidth="1.8"/><path d="M13.73 21a2 2 0 0 1-3.46 0" stroke={color} fill="none" strokeWidth="1.8"/></>,
    reports: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke={color} fill="none" strokeWidth="1.8"/><path d="M14 2v6h6" stroke={color} fill="none" strokeWidth="1.8"/><path d="M8 18v-4" stroke={color} strokeWidth="1.8"/><path d="M12 18v-6" stroke={color} strokeWidth="1.8"/><path d="M16 18v-2" stroke={color} strokeWidth="1.8"/></>,
    settings: <><circle cx="12" cy="12" r="3" stroke={color} fill="none" strokeWidth="1.8"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" stroke={color} fill="none" strokeWidth="1.8"/></>,
    anchor: <><circle cx="12" cy="5" r="3" stroke={color} fill="none" strokeWidth="1.8"/><line x1="12" y1="22" x2="12" y2="8" stroke={color} strokeWidth="1.8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3" stroke={color} fill="none" strokeWidth="1.8"/></>,
    alert: <><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke={color} fill="none" strokeWidth="1.8"/><line x1="12" y1="9" x2="12" y2="13" stroke={color} strokeWidth="1.8"/><circle cx="12" cy="17" r="0.5" fill={color}/></>,
    clock: <><circle cx="12" cy="12" r="10" stroke={color} fill="none" strokeWidth="1.8"/><polyline points="12 6 12 12 16 14" stroke={color} fill="none" strokeWidth="1.8"/></>,
    shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke={color} fill="none" strokeWidth="1.8"/></>,
    eye: <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke={color} fill="none" strokeWidth="1.8"/><circle cx="12" cy="12" r="3" stroke={color} fill="none" strokeWidth="1.8"/></>,
    pending: <><rect x="3" y="3" width="18" height="18" rx="2" stroke={color} fill="none" strokeWidth="1.8"/><path d="M9 12h6" stroke={color} strokeWidth="1.8"/><path d="M12 9v6" stroke={color} strokeWidth="1.8"/></>,
    target: <><circle cx="12" cy="12" r="10" stroke={color} fill="none" strokeWidth="1.8"/><circle cx="12" cy="12" r="6" stroke={color} fill="none" strokeWidth="1.8"/><circle cx="12" cy="12" r="2" fill={color}/></>,
    calendar: <><rect x="3" y="4" width="18" height="18" rx="2" stroke={color} fill="none" strokeWidth="1.8"/><line x1="16" y1="2" x2="16" y2="6" stroke={color} strokeWidth="1.8"/><line x1="8" y1="2" x2="8" y2="6" stroke={color} strokeWidth="1.8"/><line x1="3" y1="10" x2="21" y2="10" stroke={color} strokeWidth="1.8"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round">{p[name]}</svg>;
}

// --- Gauge ---
function DefGauge({ actual, target, maxScale }) {
  const size = 180, cx = size / 2, cy = size / 2 + 10, r = 68, sw = 14;
  const actualR = Math.min(actual / maxScale, 1);
  const targetR = Math.min(target / maxScale, 1);
  const ptc = (a) => ({ x: cx + r * Math.cos(a), y: cy - r * Math.sin(a) });
  const bgS = ptc(Math.PI), bgE = ptc(0);
  const bgPath = `M ${bgS.x} ${bgS.y} A ${r} ${r} 0 0 1 ${bgE.x} ${bgE.y}`;
  const vAngle = Math.PI - actualR * Math.PI;
  const vEnd = ptc(vAngle);
  const vPath = `M ${bgS.x} ${bgS.y} A ${r} ${r} 0 ${actualR > 0.5 ? 1 : 0} 1 ${vEnd.x} ${vEnd.y}`;
  const tAngle = Math.PI - targetR * Math.PI;
  const tIn = { x: cx + (r - sw / 2 - 6) * Math.cos(tAngle), y: cy - (r - sw / 2 - 6) * Math.sin(tAngle) };
  const tOut = { x: cx + (r + sw / 2 + 6) * Math.cos(tAngle), y: cy - (r + sw / 2 + 6) * Math.sin(tAngle) };
  const over = actual > target;
  const vc = over ? C.red : C.green;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg width={size} height={size / 2 + 30} viewBox={`0 0 ${size} ${size / 2 + 30}`}>
        <path d={bgPath} fill="none" stroke="#F0F2F5" strokeWidth={sw} strokeLinecap="round" />
        {actual > 0 && <path d={vPath} fill="none" stroke={vc} strokeWidth={sw} strokeLinecap="round" />}
        <line x1={tIn.x} y1={tIn.y} x2={tOut.x} y2={tOut.y} stroke={C.text} strokeWidth="2.5" strokeLinecap="round" />
        <text x={tOut.x + (tAngle > Math.PI / 2 ? -4 : 4)} y={tOut.y - 8} textAnchor={tAngle > Math.PI / 2 ? "end" : "start"} fill={C.textMuted} fontSize="10" fontWeight="500">Target: {target}</text>
        <text x={cx} y={cy - 12} textAnchor="middle" fill={vc} fontSize="32" fontWeight="800">{actual.toFixed(1)}</text>
        <text x={cx} y={cy + 6} textAnchor="middle" fill={C.textSecondary} fontSize="11" fontWeight="500">DEFs / Inspection</text>
        <text x={cx - r - 2} y={cy + 20} textAnchor="middle" fill={C.textMuted} fontSize="10">0</text>
        <text x={cx + r + 2} y={cy + 20} textAnchor="middle" fill={C.textMuted} fontSize="10">{maxScale}</text>
      </svg>
      <div style={{ marginTop: 4, padding: "4px 12px", borderRadius: 6, background: over ? C.redBg : C.greenBg, fontSize: 12, fontWeight: 600, color: over ? C.red : C.green }}>
        {over ? `${(actual - target).toFixed(1)} above target` : actual === target ? "On target" : `${(target - actual).toFixed(1)} below target`}
      </div>
    </div>
  );
}

// --- Date Range Picker Dropdown ---
function DateRangePicker({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const [custom, setCustom] = useState(false);
  const [fromDate, setFromDate] = useState("2024-03");
  const [toDate, setToDate] = useState("2025-02");
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) { setOpen(false); setCustom(false); } };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const presets = [
    { key: "3m", label: "Last 3 Months" },
    { key: "6m", label: "Last 6 Months" },
    { key: "12m", label: "Last 12 Months" },
    { key: "24m", label: "Last 24 Months" },
    { key: "ytd", label: "Year to Date" },
    { key: "custom", label: "Custom Range..." },
  ];

  const displayLabel = () => {
    if (value.key === "custom") return `${value.from} to ${value.to}`;
    return presets.find(p => p.key === value.key)?.label || "Last 12 Months";
  };

  const handlePreset = (key) => {
    if (key === "custom") {
      setCustom(true);
      return;
    }
    onChange({ key });
    setOpen(false);
    setCustom(false);
  };

  const handleCustomApply = () => {
    onChange({ key: "custom", from: fromDate, to: toDate });
    setOpen(false);
    setCustom(false);
  };

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button onClick={() => setOpen(!open)} style={{
        display: "flex", alignItems: "center", gap: 6, padding: "5px 10px",
        borderRadius: 6, border: `1px solid ${C.border}`, background: C.surface,
        fontSize: 11, fontWeight: 500, color: C.textSecondary, cursor: "pointer",
        transition: "border-color 0.15s",
      }}
        onMouseEnter={e => e.currentTarget.style.borderColor = C.accent}
        onMouseLeave={e => { if (!open) e.currentTarget.style.borderColor = C.border; }}
      >
        <SvgIcon name="calendar" size={13} color={C.textSecondary} />
        {displayLabel()}
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke={C.textMuted} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", right: 0, zIndex: 50,
          background: "#fff", borderRadius: 10, border: `1px solid ${C.border}`,
          boxShadow: "0 6px 20px rgba(0,0,0,0.1)", minWidth: custom ? 280 : 180,
          overflow: "hidden",
        }}>
          {!custom ? (
            <div style={{ padding: "6px 0" }}>
              {presets.map(p => (
                <button key={p.key} onClick={() => handlePreset(p.key)} style={{
                  display: "block", width: "100%", textAlign: "left", padding: "8px 14px",
                  border: "none", background: value.key === p.key ? C.accentLight : "transparent",
                  color: value.key === p.key ? C.accent : C.text, fontSize: 12, fontWeight: value.key === p.key ? 600 : 400,
                  cursor: "pointer", transition: "background 0.1s",
                }}
                  onMouseEnter={e => { if (value.key !== p.key) e.currentTarget.style.background = "#F5F6FA"; }}
                  onMouseLeave={e => { if (value.key !== p.key) e.currentTarget.style.background = "transparent"; }}
                >
                  {p.label}
                </button>
              ))}
            </div>
          ) : (
            <div style={{ padding: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: C.text, marginBottom: 12 }}>Custom Date Range</div>
              <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 10, fontWeight: 600, color: C.textMuted, display: "block", marginBottom: 4 }}>FROM</label>
                  <input type="month" value={fromDate} onChange={e => setFromDate(e.target.value)}
                    style={{ width: "100%", padding: "6px 8px", borderRadius: 6, border: `1px solid ${C.border}`, fontSize: 12, color: C.text, boxSizing: "border-box" }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 10, fontWeight: 600, color: C.textMuted, display: "block", marginBottom: 4 }}>TO</label>
                  <input type="month" value={toDate} onChange={e => setToDate(e.target.value)}
                    style={{ width: "100%", padding: "6px 8px", borderRadius: 6, border: `1px solid ${C.border}`, fontSize: 12, color: C.text, boxSizing: "border-box" }} />
                </div>
              </div>
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <button onClick={() => setCustom(false)} style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${C.border}`, background: "#fff", fontSize: 11, color: C.textSecondary, cursor: "pointer" }}>Back</button>
                <button onClick={handleCustomApply} style={{ padding: "6px 12px", borderRadius: 6, border: "none", background: C.accent, fontSize: 11, fontWeight: 600, color: "#fff", cursor: "pointer" }}>Apply</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// --- Yearly Trend bar chart ---
function YearlyTrend({ data, targetLine }) {
  const maxVal = Math.max(...data.map(d => d.value), targetLine || 0, 1);
  const chartH = 140;
  const gap = Math.max(2, Math.min(4, 300 / data.length - 20));
  const barW = Math.max(10, Math.min(22, (500 - data.length * gap) / data.length));

  return (
    <div style={{ position: "relative", height: chartH + 28 }}>
      {targetLine != null && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 24 + (targetLine / maxVal) * chartH, borderTop: `2px dashed ${C.red}`, zIndex: 2, opacity: 0.5 }}>
          <span style={{ position: "absolute", right: 0, top: -16, fontSize: 10, color: C.red, fontWeight: 600 }}>Avg target</span>
        </div>
      )}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "center", gap, height: chartH, paddingBottom: 4 }}>
        {data.map((d, i) => {
          const h = Math.max(2, (d.value / maxVal) * (chartH - 20));
          const isCurrent = i === data.length - 1;
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
              {d.value > 0 && <span style={{ fontSize: 9, fontWeight: 600, color: C.text }}>{d.value}</span>}
              <div style={{
                width: barW, height: h,
                background: isCurrent ? C.accent : d.value === 0 ? "#E8ECF1" : "#93B4F8",
                borderRadius: "3px 3px 0 0", transition: "height 0.4s ease",
              }} />
              <span style={{ fontSize: data.length > 18 ? 7 : 9, color: C.textMuted, fontWeight: isCurrent ? 600 : 400 }}>{d.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Repeat Defs ---
function RepeatDefs({ data }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {data.map((d, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: i < data.length - 1 ? `1px solid ${C.border}` : "none" }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8, flexShrink: 0,
            background: d.count >= 3 ? C.redBg : d.count >= 2 ? C.yellowBg : C.blueBg,
            border: `1px solid ${d.count >= 3 ? "#FECACA" : d.count >= 2 ? "#FDE68A" : "#BFDBFE"}`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 14, fontWeight: 800, color: d.count >= 3 ? C.red : d.count >= 2 ? C.yellow : C.blue,
          }}>{d.count}x</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: C.text, fontFamily: "monospace" }}>{d.code}</span>
              <span style={{ fontSize: 12, color: C.textSecondary }}>{d.description}</span>
            </div>
            <div style={{ display: "flex", gap: 4, marginTop: 4, flexWrap: "wrap" }}>
              {d.vessels.map((v, vi) => <span key={vi} style={{ fontSize: 10, padding: "1px 6px", borderRadius: 4, background: "#F0F2F5", color: C.textSecondary, fontWeight: 500 }}>{v}</span>)}
            </div>
          </div>
          <div style={{ fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 4, flexShrink: 0, background: d.count >= 3 ? C.redBg : C.yellowBg, color: d.count >= 3 ? C.red : C.yellow }}>
            {d.count >= 3 ? "Systemic" : "Recurring"}
          </div>
        </div>
      ))}
    </div>
  );
}

// --- HBar chart ---
function HBarChart({ data }) {
  const mx = Math.max(...data.map(d => d.value), 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {data.map((d, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ width: 48, fontSize: 12, fontWeight: 600, color: C.text, textAlign: "right", fontFamily: "monospace", flexShrink: 0 }}>{d.code}</span>
          <div style={{ flex: 1, height: 22, background: "#F0F2F5", borderRadius: 4, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${(d.value / mx) * 100}%`, background: C.accent, borderRadius: 4, transition: "width 0.6s ease", display: "flex", alignItems: "center", justifyContent: "flex-end", paddingRight: 8, minWidth: 28 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: "#fff" }}>{d.value}</span>
            </div>
          </div>
          <span style={{ fontSize: 11, color: C.textSecondary, width: 90, flexShrink: 0 }}>{d.desc}</span>
        </div>
      ))}
    </div>
  );
}

// --- Stat card ---
function StatCard({ icon, value, label, iconBg, iconColor, pulse, subtitle }) {
  return (
    <div style={{ background: C.surface, borderRadius: 10, border: `1px solid ${C.border}`, padding: "18px 18px 14px", display: "flex", alignItems: "flex-start", gap: 14, transition: "box-shadow 0.2s", cursor: "default" }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.05)"}
      onMouseLeave={e => e.currentTarget.style.boxShadow = "none"}>
      <div style={{ width: 42, height: 42, borderRadius: 10, background: iconBg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, position: "relative" }}>
        <SvgIcon name={icon} size={20} color={iconColor} />
        {pulse && <div style={{ position: "absolute", top: -2, right: -2, width: 10, height: 10, borderRadius: "50%", background: C.red, border: "2px solid #fff" }} />}
      </div>
      <div>
        <div style={{ fontSize: 28, fontWeight: 700, color: C.text, lineHeight: 1 }}>{value}</div>
        <div style={{ fontSize: 13, color: C.textSecondary, marginTop: 3 }}>{label}</div>
        {subtitle && <div style={{ fontSize: 11, color: C.textMuted, marginTop: 2 }}>{subtitle}</div>}
      </div>
    </div>
  );
}

// --- Alert strip ---
function AlertStrip({ items }) {
  const active = items.filter(i => i.count > 0);
  if (!active.length) return null;
  return (
    <div style={{ background: C.redBg, border: "1px solid #FFD2CC", borderRadius: 10, padding: "12px 18px", display: "flex", alignItems: "center", gap: 16, marginBottom: 18 }}>
      <div style={{ width: 32, height: 32, borderRadius: 8, background: C.red, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <SvgIcon name="alert" size={16} color="#fff" />
      </div>
      <div style={{ flex: 1, display: "flex", gap: 20, flexWrap: "wrap" }}>
        {active.map((item, i) => <span key={i} style={{ fontSize: 13, color: "#AB1300", fontWeight: 500 }}><strong>{item.count}</strong> {item.label}</span>)}
      </div>
      <button style={{ background: C.red, color: "#fff", border: "none", borderRadius: 6, padding: "6px 14px", fontSize: 12, fontWeight: 600, cursor: "pointer" }}>Review</button>
    </div>
  );
}

// --- Inspections table ---
function InspectionsTable({ data }) {
  const tBadge = (t) => { const m = { PSC: { bg: C.blueBg, c: C.blue }, RS: { bg: C.yellowBg, c: C.yellow }, Audit: { bg: C.purpleBg, c: C.purple } }; const s = m[t] || m.PSC; return <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 4, background: s.bg, color: s.c }}>{t}</span>; };
  const sBadge = (st) => { const m = { Completed: { bg: C.greenBg, c: C.green }, "In Progress": { bg: C.blueBg, c: C.blue }, Overdue: { bg: C.redBg, c: C.red } }; const s = m[st] || { bg: C.blueBg, c: C.blue }; return <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 12, background: s.bg, color: s.c }}>{st}</span>; };
  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead><tr>{["Vessel", "Type", "Date", "DEFs", "Status"].map(h => <th key={h} style={{ textAlign: "left", padding: "8px 12px", fontSize: 11, fontWeight: 600, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.04em", borderBottom: `1px solid ${C.border}` }}>{h}</th>)}</tr></thead>
      <tbody>{data.map((r, i) => (
        <tr key={i} style={{ cursor: "pointer" }} onMouseEnter={e => e.currentTarget.style.background = "#FAFBFC"} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
          <td style={{ padding: "10px 12px", fontSize: 13, fontWeight: 600, color: C.text }}>{r.vessel}</td>
          <td style={{ padding: "10px 12px" }}>{tBadge(r.type)}</td>
          <td style={{ padding: "10px 12px", fontSize: 12, color: C.textSecondary, fontFamily: "monospace" }}>{r.date}</td>
          <td style={{ padding: "10px 12px", fontSize: 13, fontWeight: 700, color: r.defs > 0 ? C.yellow : C.green }}>{r.defs}</td>
          <td style={{ padding: "10px 12px" }}>{sBadge(r.status)}</td>
        </tr>
      ))}</tbody>
    </table>
  );
}

// --- Nav item ---
function NavItem({ icon, label, active, badge, onClick }) {
  return (
    <button onClick={onClick} style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "9px 14px", border: "none", borderRadius: 8, cursor: "pointer", background: active ? C.accentLight : "transparent", color: active ? C.accent : C.textSecondary, fontSize: 14, fontWeight: active ? 600 : 400, textAlign: "left", transition: "all 0.15s" }}
      onMouseEnter={e => { if (!active) e.currentTarget.style.background = "#F5F6FA"; }}
      onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}>
      <SvgIcon name={icon} size={19} color={active ? C.accent : C.textSecondary} />
      <span style={{ flex: 1 }}>{label}</span>
      {badge > 0 && <span style={{ fontSize: 10, fontWeight: 700, background: C.red, color: "#fff", padding: "1px 6px", borderRadius: 8, minWidth: 16, textAlign: "center" }}>{badge}</span>}
    </button>
  );
}

// --- Target modal ---
function TargetModal({ target, onSave, onClose }) {
  const [val, setVal] = useState(target.toString());
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.3)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }} onClick={onClose}>
      <div style={{ background: "#fff", borderRadius: 12, padding: 28, width: 340, boxShadow: "0 8px 30px rgba(0,0,0,0.12)" }} onClick={e => e.stopPropagation()}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: C.text, margin: "0 0 4px" }}>KPI Target Settings</h3>
        <p style={{ fontSize: 13, color: C.textSecondary, margin: "0 0 20px" }}>Set the acceptable average deficiencies per inspection for your fleet.</p>
        <label style={{ fontSize: 12, fontWeight: 600, color: C.textSecondary, display: "block", marginBottom: 6 }}>Target: Avg DEFs per Inspection</label>
        <input type="number" step="0.5" min="0" max="20" value={val} onChange={e => setVal(e.target.value)}
          style={{ width: "100%", padding: "10px 12px", borderRadius: 8, border: `1px solid ${C.border}`, fontSize: 14, color: C.text, boxSizing: "border-box", outline: "none" }}
          onFocus={e => e.currentTarget.style.borderColor = C.accent} onBlur={e => e.currentTarget.style.borderColor = C.border} />
        <p style={{ fontSize: 11, color: C.textMuted, margin: "6px 0 20px" }}>Industry benchmark for PSC: ~2.0 deficiencies per inspection. Lower is better.</p>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{ padding: "8px 16px", borderRadius: 8, border: `1px solid ${C.border}`, background: "#fff", fontSize: 13, fontWeight: 500, color: C.textSecondary, cursor: "pointer" }}>Cancel</button>
          <button onClick={() => { onSave(parseFloat(val) || 2); onClose(); }} style={{ padding: "8px 16px", borderRadius: 8, border: "none", background: C.accent, fontSize: 13, fontWeight: 600, color: "#fff", cursor: "pointer" }}>Save Target</button>
        </div>
      </div>
    </div>
  );
}

// === MAIN ===
export default function VIMSDashboard() {
  const [activeNav, setActiveNav] = useState("dashboard");
  const [vessel, setVessel] = useState("all");
  const [defTarget, setDefTarget] = useState(2.0);
  const [showTarget, setShowTarget] = useState(false);
  const [trendRange, setTrendRange] = useState({ key: "12m" });

  const totalDefs = 12, totalInsp = 4;
  const avgDef = totalDefs / totalInsp;

  const navItems = [
    { icon: "dashboard", label: "Dashboard", id: "dashboard" },
    { icon: "inspections", label: "Inspections", id: "inspections" },
    { icon: "cars", label: "CARs", id: "cars" },
    { icon: "notifications", label: "Notifications", id: "notifications", badge: 2 },
    { icon: "reports", label: "Reports", id: "reports" },
    { icon: "settings", label: "Settings", id: "settings" },
  ];

  // Full 24-month dataset - range picker slices from this
  const allMonthlyData = [
    { label: "Mar'23", value: 2 }, { label: "Apr'23", value: 0 }, { label: "May'23", value: 1 },
    { label: "Jun'23", value: 3 }, { label: "Jul'23", value: 1 }, { label: "Aug'23", value: 4 },
    { label: "Sep'23", value: 2 }, { label: "Oct'23", value: 0 }, { label: "Nov'23", value: 1 },
    { label: "Dec'23", value: 3 }, { label: "Jan'24", value: 2 }, { label: "Feb'24", value: 1 },
    { label: "Mar'24", value: 3 }, { label: "Apr'24", value: 1 }, { label: "May'24", value: 0 },
    { label: "Jun'24", value: 4 }, { label: "Jul'24", value: 2 }, { label: "Aug'24", value: 5 },
    { label: "Sep'24", value: 1 }, { label: "Oct'24", value: 0 }, { label: "Nov'24", value: 0 },
    { label: "Dec'24", value: 1 }, { label: "Jan'25", value: 2 }, { label: "Feb'25", value: 7 },
  ];

  // Slice data based on selected range
  const getTrendData = () => {
    const total = allMonthlyData.length;
    switch (trendRange.key) {
      case "3m": return allMonthlyData.slice(total - 3);
      case "6m": return allMonthlyData.slice(total - 6);
      case "12m": return allMonthlyData.slice(total - 12);
      case "24m": return allMonthlyData;
      case "ytd": return allMonthlyData.slice(total - 2); // Jan-Feb 2025
      case "custom": {
        // Simple month-based filtering using label matching
        const fromKey = trendRange.from; // "2024-03"
        const toKey = trendRange.to; // "2025-02"
        const monthMap = {
          "2023-03": 0, "2023-04": 1, "2023-05": 2, "2023-06": 3, "2023-07": 4, "2023-08": 5,
          "2023-09": 6, "2023-10": 7, "2023-11": 8, "2023-12": 9, "2024-01": 10, "2024-02": 11,
          "2024-03": 12, "2024-04": 13, "2024-05": 14, "2024-06": 15, "2024-07": 16, "2024-08": 17,
          "2024-09": 18, "2024-10": 19, "2024-11": 20, "2024-12": 21, "2025-01": 22, "2025-02": 23,
        };
        const startIdx = monthMap[fromKey] ?? 0;
        const endIdx = (monthMap[toKey] ?? total - 1) + 1;
        return allMonthlyData.slice(startIdx, endIdx);
      }
      default: return allMonthlyData.slice(total - 12);
    }
  };

  const trendData = getTrendData();
  const trendTotal = trendData.reduce((s, d) => s + d.value, 0);

  const getRangeLabel = () => {
    if (trendData.length === 0) return "";
    return `${trendData[0].label} — ${trendData[trendData.length - 1].label}`;
  };

  const repeatDefs = [
    { code: "01315", description: "Fire doors not self-closing", count: 3, vessels: ["Pacific Star", "Ocean Breeze", "Coral Voyager"] },
    { code: "14501", description: "ISM procedures not followed", count: 3, vessels: ["Pacific Star", "Atlantic Dawn", "Coral Voyager"] },
    { code: "10111", description: "Lifeboat davit maintenance", count: 2, vessels: ["Pacific Star", "Ocean Breeze"] },
    { code: "07105", description: "OWS logbook incomplete", count: 2, vessels: ["Ocean Breeze", "Coral Voyager"] },
  ];

  const defCodes = [
    { code: "01315", value: 7, desc: "Fire safety" }, { code: "14501", value: 5, desc: "ISM procedures" },
    { code: "10111", value: 4, desc: "Life-saving" }, { code: "09225", value: 3, desc: "Navigation" },
    { code: "07105", value: 2, desc: "Pollution prev." },
  ];

  const inspections = [
    { vessel: "MV Pacific Star", type: "PSC", date: "2025-02-26", defs: 7, status: "In Progress" },
    { vessel: "MV Ocean Breeze", type: "RS", date: "2025-02-14", defs: 3, status: "Completed" },
    { vessel: "MV Atlantic Dawn", type: "PSC", date: "2025-01-22", defs: 0, status: "Completed" },
    { vessel: "MV Coral Voyager", type: "Audit", date: "2025-01-10", defs: 2, status: "Completed" },
  ];

  const card = (extra) => ({ background: C.surface, borderRadius: 10, padding: 22, border: `1px solid ${C.border}`, ...extra });

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: C.bg }}>
      {showTarget && <TargetModal target={defTarget} onSave={setDefTarget} onClose={() => setShowTarget(false)} />}

      <aside style={{ width: 220, background: C.sidebar, borderRight: `1px solid ${C.sidebarBorder}`, display: "flex", flexDirection: "column", position: "fixed", top: 0, bottom: 0, left: 0, zIndex: 10 }}>
        <div style={{ padding: "20px 16px 16px", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: C.accent, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <SvgIcon name="anchor" size={18} color="#fff" />
          </div>
          <span style={{ fontSize: 18, fontWeight: 800, color: C.text }}>VIMS</span>
        </div>
        <nav style={{ padding: "8px 10px", display: "flex", flexDirection: "column", gap: 1, flex: 1 }}>
          {navItems.map(item => <NavItem key={item.id} {...item} active={activeNav === item.id} onClick={() => setActiveNav(item.id)} />)}
        </nav>
        <div style={{ padding: "12px 16px", borderTop: `1px solid ${C.sidebarBorder}` }}>
          <span style={{ fontSize: 11, color: C.textMuted }}>VIMS v0.1.0</span>
        </div>
      </aside>

      <main style={{ flex: 1, marginLeft: 220, padding: "24px 28px 40px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 22 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: C.text, margin: 0 }}>Dashboard</h1>
            <p style={{ fontSize: 13, color: C.textSecondary, margin: "2px 0 0" }}>Overview of inspections, CARs, and deficiencies</p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <select value={vessel} onChange={e => setVessel(e.target.value)} style={{ padding: "7px 32px 7px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.surface, fontSize: 13, color: C.text, cursor: "pointer", appearance: "none", backgroundImage: `url("data:image/svg+xml,%3Csvg width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%236B7A99' stroke-width='2.5' xmlns='http://www.w3.org/2000/svg'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E")`, backgroundRepeat: "no-repeat", backgroundPosition: "right 10px center" }}>
              <option value="all">All Vessels</option>
              <option value="1">MV Pacific Star</option>
              <option value="2">MV Ocean Breeze</option>
            </select>
            <div style={{ position: "relative", cursor: "pointer" }}>
              <SvgIcon name="notifications" size={20} color={C.textSecondary} />
              <div style={{ position: "absolute", top: -4, right: -4, width: 16, height: 16, borderRadius: "50%", background: C.red, border: "2px solid #fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: "#fff" }}>2</div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginLeft: 4 }}>
              <div style={{ width: 32, height: 32, borderRadius: "50%", background: C.accentLight, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: C.accent }}>CW</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.text, lineHeight: 1.2 }}>Carol W.</div>
                <div style={{ fontSize: 11, color: C.textMuted }}>DPA</div>
              </div>
            </div>
          </div>
        </div>

        <AlertStrip items={[{ count: 1, label: "Detention in last 3 years" }, { count: 1, label: "CAR missing evidence" }]} />

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 14 }}>
          <StatCard icon="inspections" value={4} label="Inspections (12 mo)" iconBg={C.blueBg} iconColor={C.blue} subtitle="Last: Feb 26" />
          <StatCard icon="cars" value={4} label="Open CARs" iconBg={C.greenBg} iconColor={C.green} />
          <StatCard icon="alert" value={0} label="Overdue CARs" iconBg={C.yellowBg} iconColor={C.yellow} subtitle="All on track" />
          <StatCard icon="shield" value={1} label="Detentions (3 yr)" iconBg={C.redBg} iconColor={C.red} pulse />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 22 }}>
          <StatCard icon="pending" value={3} label="Pending DEFs" iconBg={C.orangeBg} iconColor={C.orange} />
          <StatCard icon="eye" value={1} label="CARs Missing Evid." iconBg={C.redBg} iconColor={C.red} />
          <StatCard icon="clock" value={0} label="Overdue Actions" iconBg={C.blueBg} iconColor={C.blue} />
          <StatCard icon="inspections" value={1} label="PV Due" iconBg={C.purpleBg} iconColor={C.purple} subtitle="Next: Mar 15" />
        </div>

        {/* Gauge + Yearly Trend */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr", gap: 16, marginBottom: 16 }}>
          <div style={card()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text, margin: 0 }}>Avg DEFs / Inspection</h3>
              <button onClick={() => setShowTarget(true)} style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 4, fontSize: 11, fontWeight: 600, color: C.accent, padding: "4px 8px", borderRadius: 6 }}
                onMouseEnter={e => e.currentTarget.style.background = C.accentLight} onMouseLeave={e => e.currentTarget.style.background = "none"}>
                <SvgIcon name="target" size={14} color={C.accent} /> Set Target
              </button>
            </div>
            <DefGauge actual={avgDef} target={defTarget} maxScale={8} />
            <div style={{ display: "flex", justifyContent: "center", gap: 24, marginTop: 14, paddingTop: 14, borderTop: `1px solid ${C.border}` }}>
              <div style={{ textAlign: "center" }}><div style={{ fontSize: 18, fontWeight: 700, color: C.text }}>{totalInsp}</div><div style={{ fontSize: 11, color: C.textMuted }}>Inspections</div></div>
              <div style={{ width: 1, background: C.border }} />
              <div style={{ textAlign: "center" }}><div style={{ fontSize: 18, fontWeight: 700, color: C.text }}>{totalDefs}</div><div style={{ fontSize: 11, color: C.textMuted }}>Total DEFs</div></div>
              <div style={{ width: 1, background: C.border }} />
              <div style={{ textAlign: "center" }}><div style={{ fontSize: 18, fontWeight: 700, color: C.text }}>{defTarget}</div><div style={{ fontSize: 11, color: C.textMuted }}>Target</div></div>
            </div>
          </div>

          <div style={card()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text, margin: 0 }}>Deficiency Trend</h3>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 11, color: C.textMuted }}>{getRangeLabel()}</span>
                <DateRangePicker value={trendRange} onChange={setTrendRange} />
              </div>
            </div>
            <YearlyTrend data={trendData} targetLine={defTarget} />
            <div style={{ display: "flex", gap: 20, marginTop: 12, paddingTop: 12, borderTop: `1px solid ${C.border}` }}>
              <div><span style={{ fontSize: 20, fontWeight: 700, color: C.text }}>{trendTotal}</span><span style={{ fontSize: 12, color: C.textMuted, marginLeft: 6 }}>Total DEFs ({trendData.length} mo)</span></div>
              <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 12, height: 12, borderRadius: 2, background: C.accent }} />
                <span style={{ fontSize: 11, color: C.textMuted }}>Current</span>
                <div style={{ width: 12, height: 12, borderRadius: 2, background: "#93B4F8", marginLeft: 8 }} />
                <span style={{ fontSize: 11, color: C.textMuted }}>Previous</span>
              </div>
            </div>
          </div>
        </div>

        {/* Repeat DEFs + Top Codes */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
          <div style={card()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text, margin: 0 }}>Repeat Deficiencies</h3>
                <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 7px", borderRadius: 4, background: C.redBg, color: C.red }}>{repeatDefs.length} found</span>
              </div>
            </div>
            <RepeatDefs data={repeatDefs} />
          </div>
          <div style={card()}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text, margin: "0 0 16px" }}>Top Deficiency Codes</h3>
            <HBarChart data={defCodes} />
          </div>
        </div>

        {/* Recent Inspections */}
        <div style={card()}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: C.text, margin: 0 }}>Recent Inspections</h3>
            <button style={{ background: "none", border: "none", color: C.accent, fontSize: 12, fontWeight: 600, cursor: "pointer" }}>View All →</button>
          </div>
          <InspectionsTable data={inspections} />
        </div>
      </main>
    </div>
  );
}
