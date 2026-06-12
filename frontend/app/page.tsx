"use client";

import { useState } from "react";

export default function Home() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const askAI = async () => {
    if (!input.trim()) return;

    setLoading(true);
    setResponse("");

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/ask?q=${encodeURIComponent(input)}`
      );

      const data = await res.json();
      setResponse(data.response);
    } catch (err) {
      setResponse("Error connecting to backend");
    }

    setLoading(false);
  };

  return (
    <main style={{ padding: 20, maxWidth: 700, margin: "0 auto" }}>
      <h1>Reading Companion AI</h1>

      <textarea
        rows={4}
        style={{ width: "100%", marginTop: 20 }}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask something..."
      />

      <button onClick={askAI} style={{ marginTop: 10 }}>
        Ask AI
      </button>

      <div style={{ marginTop: 20 }}>
        {loading ? (
          <p>Thinking...</p>
        ) : (
          <pre style={{ whiteSpace: "pre-wrap" }}>{response}</pre>
        )}
      </div>
    </main>
  );
}