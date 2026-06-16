import { useRef } from "react";
import { SiteHeader } from "../components/SiteChrome";
import {
  useAssistant, MessageList, Composer, Suggestions, ChatHistory,
  THEMES, ASSISTANT_CSS,
} from "../components/assistant/core";

/* ════════════════════════════════════════════════════════════════════════════
   Trang Trợ lý AI (/assistant) — chat đầy đủ, dùng chung engine với widget nổi.
═══════════════════════════════════════════════════════════════════════════════ */

const theme = "light"; // giao diện sáng cố định, đồng nhất với toàn site

export default function AssistantPage() {
  const t = THEMES[theme];
  const chat = useAssistant();
  const fileInputRef = useRef(null);

  return (
    <>
      {/* Nạp đúng font Nunito + Inter để header SiteHeader đồng nhất với các trang khác */}
      <style dangerouslySetInnerHTML={{ __html: `
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
        body { font-family:'Inter',-apple-system,sans-serif; margin:0; }
        @media (max-width:760px){ .tb-history-aside{ display:none !important; } }
      ` }} />
      <style dangerouslySetInnerHTML={{ __html: ASSISTANT_CSS }} />
      <SiteHeader active="ai" />
      <input ref={fileInputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={chat.handleImageSelect} />

      <div style={{ display: "flex", height: "calc(100vh - 64px)", background: t.bg, fontFamily: "'Be Vietnam Pro',sans-serif", color: t.text }}>

        {/* SIDEBAR — lịch sử hội thoại */}
        <aside className="tb-history-aside" style={{ width: "270px", flexShrink: 0, borderRight: `1px solid ${t.surfaceBorder}`, background: t.surface, padding: "16px 12px", display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: t.textDim, textTransform: "uppercase", letterSpacing: "0.05em", padding: "0 4px 10px" }}>Lịch sử trò chuyện</div>
          <ChatHistory chat={chat} theme={theme} />
        </aside>

        {/* MAIN — chat */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
          <div className="tb-scroll" style={{ flex: 1, overflowY: "auto", padding: "24px 16px" }}>
            <div style={{ maxWidth: "820px", margin: "0 auto" }}>
              <MessageList messages={chat.messages} theme={theme} identifyingImage={chat.identifyingImage} />
            </div>
          </div>

          {chat.messages.length <= 1 && (
            <Suggestions theme={theme} onPick={(s) => chat.sendMessage(s)} />
          )}

          <div style={{ padding: "12px 16px 18px", background: t.surface, borderTop: `1px solid ${t.surfaceBorder}`, flexShrink: 0 }}>
            <div style={{ maxWidth: "820px", margin: "0 auto" }}>
              <Composer chat={chat} theme={theme} fileInputRef={fileInputRef} compact />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
