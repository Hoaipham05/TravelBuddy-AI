import { useState, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  useAssistant, MessageList, Composer, Suggestions, ChatHistory,
  THEMES, Icon, ASSISTANT_CSS,
} from "./core";

/* ════════════════════════════════════════════════════════════════════════════
   Floating AI assistant — nút nổi góc phải dưới, hiện trên MỌI trang (trừ
   /login và /assistant). Click → mở panel chat gọn dùng chung engine.
   (Đáp ứng spec 6.2.1 — floating button trên mọi trang.)
═══════════════════════════════════════════════════════════════════════════════ */

const HIDE_ON = ["/login", "/assistant"];

export default function AssistantWidget() {
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [view, setView] = useState("chat"); // 'chat' | 'history'
  const theme = "light";
  const t = THEMES[theme];
  const chat = useAssistant();
  const fileInputRef = useRef(null);

  if (HIDE_ON.some(p => location.pathname === p)) return null;
  // chỉ hiện khi đã đăng nhập
  const token = localStorage.getItem("tb_token") || sessionStorage.getItem("tb_token");
  if (!token) return null;

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: ASSISTANT_CSS }} />
      <input ref={fileInputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={chat.handleImageSelect} />

      {/* Panel */}
      {open && (
        <div style={{
          position: "fixed", bottom: "92px", right: "24px", zIndex: 9000,
          width: "min(410px, calc(100vw - 32px))", height: "min(620px, calc(100vh - 130px))",
          display: "flex", flexDirection: "column", background: t.bg,
          borderRadius: "18px", overflow: "hidden", fontFamily: "'Be Vietnam Pro',sans-serif",
          color: t.text, boxShadow: "0 24px 70px rgba(15,23,42,0.28)", border: `1px solid ${t.surfaceBorder}`,
          animation: "tb-pop 0.22s ease",
        }}>
          {/* header */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "11px 14px", background: "linear-gradient(135deg, #0ea5e9, #0284c7)", flexShrink: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "9px", color: "#fff" }}>
              <div style={{ width: "30px", height: "30px", borderRadius: "9px", background: "rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center" }}><Icon.Plane /></div>
              <div>
                <div style={{ fontWeight: 800, fontFamily: "'Nunito',sans-serif", fontSize: "14px" }}>TravelBuddy AI</div>
                <div style={{ fontSize: "10.5px", opacity: 0.9 }}>Trợ lý du lịch · luôn sẵn sàng</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: "4px" }}>
              <button title={view === "history" ? "Về cuộc trò chuyện" : "Lịch sử trò chuyện"} onClick={() => setView(v => v === "history" ? "chat" : "history")} style={{ ...iconBtn, background: view === "history" ? "rgba(255,255,255,0.34)" : "rgba(255,255,255,0.18)" }}><Icon.History /></button>
              <button title="Mở toàn màn hình" onClick={() => navigate("/assistant")} style={iconBtn}><Icon.Scan /></button>
              <button title="Đóng" onClick={() => setOpen(false)} style={iconBtn}><Icon.X /></button>
            </div>
          </div>

          {view === "history" ? (
            /* history list */
            <div style={{ flex: 1, overflow: "hidden", padding: "14px 12px", background: t.surface }}>
              <ChatHistory chat={chat} theme={theme} onSelect={() => setView("chat")} />
            </div>
          ) : (
            <>
              {/* messages */}
              <div className="tb-scroll" style={{ flex: 1, overflowY: "auto", padding: "16px 12px" }}>
                <MessageList messages={chat.messages} theme={theme} identifyingImage={chat.identifyingImage} />
              </div>

              {chat.messages.length <= 1 && (
                <Suggestions theme={theme} onPick={(s) => chat.sendMessage(s)}
                  items={["Lịch trình Đà Nẵng 3 ngày", "Thời tiết Đà Lạt tuần này", "Đi Nhật cần visa không?"]} />
              )}

              {/* composer (compact: ẩn thinking/model để gọn) */}
              <div style={{ padding: "10px 12px 12px", background: t.surface, borderTop: `1px solid ${t.surfaceBorder}`, flexShrink: 0 }}>
                <Composer chat={chat} theme={theme} fileInputRef={fileInputRef} compact />
              </div>
            </>
          )}
        </div>
      )}

      {/* FAB */}
      <button onClick={() => setOpen(o => !o)} title="Trợ lý AI TravelBuddy" style={{
        position: "fixed", bottom: "24px", right: "24px", zIndex: 9001,
        width: "60px", height: "60px", borderRadius: "50%", border: "none", cursor: "pointer",
        background: "linear-gradient(135deg, #0ea5e9, #0284c7)", color: "#fff",
        display: "flex", alignItems: "center", justifyContent: "center",
        boxShadow: "0 10px 30px rgba(14,165,233,0.45)", transition: "transform 0.18s",
      }}
        onMouseEnter={e => e.currentTarget.style.transform = "scale(1.07)"}
        onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}>
        {open ? <Icon.X /> : <span style={{ fontSize: "26px", lineHeight: 1 }}>🤖</span>}
        {!open && <span style={{ position: "absolute", top: "6px", right: "8px", width: "11px", height: "11px", background: "#22c55e", borderRadius: "50%", border: "2px solid #fff" }} />}
      </button>
    </>
  );
}

const iconBtn = {
  width: "28px", height: "28px", borderRadius: "8px", border: "none",
  background: "rgba(255,255,255,0.18)", color: "#fff", cursor: "pointer",
  display: "flex", alignItems: "center", justifyContent: "center",
};
