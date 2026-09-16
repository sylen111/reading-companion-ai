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
  const [bookId, setBookId] = useState<string | null>(null);
  const [bookTitle, setBookTitle] = useState("");
  const [pages, setPages] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(0);

  const [article, setArticle] = useState("");
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [activeAnnotation, setActiveAnnotation] = useState<Annotation | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");

  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const chatBoxRef = useRef<HTMLDivElement | null>(null);

  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

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
        book_id: bookId,
        use_annotation: true,
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

    const userMsg: Message = {
      role: "user",
      content: question,
    };

    const newMessages = [
      ...messages,
      userMsg,
    ].filter(
      (message) =>
        message.role &&
        typeof message.content === "string"
    );
    setMessages(newMessages);
    setQuestion("");

    console.log("Sending chat history:", newMessages);

    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        annotation: activeAnnotation,
        question,
        chat_history: newMessages,
        book_id: bookId,
        use_annotation: false,
      }),
    });

    const data = await res.json();

    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: data.answer },
    ]);
  };

  // =========================
  // upload book
  // =========================

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetch(
        "http://localhost:8000/books/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!res.ok) {
        throw new Error("Upload failed");
      }

      const data = await res.json();

      console.log("Uploaded:", data);

      setBookId(data.book_id);
      setBookTitle(data.filename);
      setPages(data.pages || []);
      setCurrentPage(0);

      setArticle(data.pages?.[0] || "");

      setMessages([]);
      setActiveAnnotation(null);

      setShowUpload(false);
      setSelectedFile(null);

    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
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

          <button
            className="primary-button" onClick={() => setShowUpload(true)}>
            Upload Book
          </button>
        </div>

        {/* GRID */}
        <div className="main-grid">

          {/* LEFT */}
          <section className="composer" style={{ minHeight: 0 }}>

          <div className="reader-header">
            <div>
              <h2>{bookTitle || "No book selected"}</h2>
              {pages.length > 0 && (
                <span>
                  Page {currentPage + 1} / {pages.length}
                </span>
              )}
            </div>
          </div>

          <div className="panel annotations-panel reader-content">
            {pages.length > 0
              ? renderHighlightedText(article, annotations)
              : "Upload a book to start reading."
            }
          </div>

          <div className="reader-navigation">
            <button
              disabled={currentPage === 0}
              onClick={() => {
                const newPage = currentPage - 1;
                setCurrentPage(newPage);
                setArticle(pages[newPage]);
              }}
            >
              ← Previous
            </button>

            <button
              disabled={pages.length === 0 || currentPage === pages.length - 1}
              onClick={() => {
                const newPage = currentPage + 1;
                setCurrentPage(newPage);
                setArticle(pages[newPage]);
              }}
            >
              Next →
            </button>
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

        {showUpload && (
          <div className="modal-overlay">
            <div className="upload-modal">
              <h2>Upload Book</h2>

              <p>
                Upload a text file to start reading.
              </p>

              <input
                className="upload-file"
                type="file"
                accept=".txt"
                onChange={(e) => {
                  setSelectedFile(e.target.files?.[0] || null);
                }}
              />

              <div className="modal-actions">
                <button onClick={() => setShowUpload(false)}>
                  Cancel
                </button>

                <button
                  className="primary-button"
                  disabled={!selectedFile || uploading}
                  onClick={handleUpload}
                >
                  {uploading ? "Uploading..." : "Upload"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}