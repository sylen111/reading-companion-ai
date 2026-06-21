"use client";

import { useEffect, useState, useRef } from "react";

type Annotation = {
  id: string;
  text: string;
  start: number;
  end: number;
  type: string;
  explanation: string;
};

type Message = {
  role: "user" | "assistant" | "system";
  content: string;
};

export default function Page() {
  const [article, setArticle] = useState("");
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [activeAnnotation, setActiveAnnotation] = useState<Annotation | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");

  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const chatBoxRef = useRef<HTMLDivElement | null>(null);

  // =========================
  // Auto analyze
  // =========================
  useEffect(() => {
    if (!article || article.length < 20) return;

    const timer = setTimeout(async () => {
      try {
        const res = await fetch("http://localhost:8000/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ article }),
        });

        const data = await res.json();
        setAnnotations(data.annotations || []);
      } catch (err) {
        console.error(err);
      }
    }, 1200);

    return () => clearTimeout(timer);
  }, [article]);

  useEffect(() => {
    setAnnotations([]);
    setActiveAnnotation(null);
  }, [article]);

  useEffect(() => {
  const chatBox = chatBoxRef.current;
  const end = chatEndRef.current;

  if (!chatBox || !end) return;

  const isNearBottom =
    chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight < 120;

  if (isNearBottom) {
    end.scrollIntoView({ behavior: "smooth" });
  }
}, [messages]);

  // =========================
  // Click annotation
  // =========================
  const handleAnnotationClick = async (ann: Annotation) => {
    setActiveAnnotation(ann);

    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        annotation: ann,
        question: "Explain this expression.",
        chat_history: messages,
      }),
    });

    const data = await res.json();

    setMessages((prev) => [
      ...prev,
      {
        role: "system",
        content: `Selected: "${ann.text}" (${ann.type})`,
      },
      {
        role: "assistant",
        content: data.answer,
      },
    ]);
  };

  // =========================
  // Highlight renderer
  // =========================
  function renderHighlightedText(text: string, anns: Annotation[]) {
    if (!anns.length) return text;

    const sorted = [...anns].sort((a, b) => a.start - b.start);
    const result: any[] = [];
    let cursor = 0;

    sorted.forEach((ann, i) => {
      if (cursor < ann.start) {
        result.push(<span key={`t-${i}`}>{text.slice(cursor, ann.start)}</span>);
      }

      result.push(
        <span
          key={`h-${i}`}
          className="highlight"
          onClick={() => handleAnnotationClick(ann)}
        >
          {text.slice(ann.start, ann.end)}
        </span>
      );

      cursor = ann.end;
    });

    result.push(<span key="end">{text.slice(cursor)}</span>);

    return result;
  }

  // =========================
  // Chat
  // =========================
  const sendMessage = async () => {
    if (!question || !activeAnnotation) return;

    const userMsg: Message = {
      role: "user",
      content: question,
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setQuestion("");

    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        annotation: activeAnnotation,
        question,
        chat_history: newMessages,
      }),
    });

    const data = await res.json();

    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: data.answer },
    ]);
  };

  // =========================
  // UI
  // =========================
  return (
    <main className="shell">
      <div className="workspace">

        {/* TOP */}
        <div className="topbar">
          <div>
            <p className="eyebrow">Demo</p>
            <h1>Reading Companion AI</h1>
          </div>

          <div className="status">Test</div>
        </div>

        {/* GRID */}
        <div className="main-grid">

          {/* LEFT */}
          <section className="composer" style={{ minHeight: 0 }}>
            <textarea
              value={article}
              onChange={(e) => setArticle(e.target.value)}
              placeholder="Paste your article..."
            />

            <label>Annotations</label>
            <div className="panel annotations-panel">
              {renderHighlightedText(article, annotations)}
            </div>
          </section>

          {/* RIGHT */}
          <section className="output">

            {/* CHAT PANEL */}
            <div className="panel" style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>

              <div className="panel-title">
                <h2>Chat Assistant</h2>
              </div>

              {/* CHAT HISTORY */}
              <div className="chat-box" ref={chatBoxRef}>
                {messages.map((m, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                        marginBottom: 10,
                      }}
                    >
                      <div
                        style={{
                          maxWidth: "75%",
                          padding: "10px 12px",
                          borderRadius: 10,
                          background:
                            m.role === "user"
                              ? "var(--lightgreen)"
                              : m.role === "system"
                              ? "#eef2ff"
                              : "#f3f4f6",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        {m.content}
                      </div>
                    </div>
                  ))
                }
                <div ref={chatEndRef} />
              </div>

              {/* INPUT (GPT STYLE FIXED BOTTOM) */}
              <div className="chat-input-row">
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask anything..."
                  onKeyDown={(e) => {
                    if (e.key === "Enter") sendMessage();
                  }}
                />

                <button className="primary-button" onClick={sendMessage}>
                  Send
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}