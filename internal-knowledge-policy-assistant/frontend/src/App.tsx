import { FormEvent, useEffect, useRef, useState } from "react";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  error?: boolean;
};

type AskResponse = {
  content: string;
  sources: string[];
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

const suggestions = [
  "Is alcohol reimbursable?",
  "What is the remote work policy?",
  "How do I request production access?",
];

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [minScore, setMinScore] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const nextId = useRef(1);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function ask(rawQuestion: string) {
    const trimmedQuestion = rawQuestion.trim();
    if (!trimmedQuestion || isLoading) return;

    const userMessage: Message = {
      id: nextId.current++,
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/ask/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmedQuestion,
          top_k: topK,
          min_score: minScore,
        }),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(
          detail || `Request failed with status ${response.status}`,
        );
      }

      const answer = (await response.json()) as AskResponse;
      setMessages((current) => [
        ...current,
        {
          id: nextId.current++,
          role: "assistant",
          content: answer.content,
          sources: answer.sources,
        },
      ]);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Unknown error";
      setMessages((current) => [
        ...current,
        {
          id: nextId.current++,
          role: "assistant",
          content: `I couldn't reach the policy service. ${detail}`,
          error: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void ask(question);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-mark" aria-hidden="true">
          P
        </div>
        <div>
          <p className="eyebrow">Internal knowledge</p>
          <h1>Policy Assistant</h1>
        </div>
        <button
          className="settings-button"
          type="button"
          onClick={() => setShowSettings((current) => !current)}
          aria-expanded={showSettings}
        >
          Retrieval settings
        </button>
      </header>

      {showSettings && (
        <section className="settings-panel" aria-label="Retrieval settings">
          <label>
            <span>Top results</span>
            <input
              type="number"
              min="1"
              max="20"
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
          </label>
          <label>
            <span>Minimum score</span>
            <input
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={minScore}
              onChange={(event) => setMinScore(Number(event.target.value))}
            />
          </label>
        </section>
      )}

      <main className="conversation">
        {messages.length === 0 ? (
          <section className="welcome">
            <div className="welcome-icon" aria-hidden="true">
              ?
            </div>
            <p className="eyebrow">Grounded in your documents</p>
            <h2>What would you like to know?</h2>
            <p>
              Ask a direct question about expenses, access, remote work, or any
              other policy in the knowledge base.
            </p>
            <div className="suggestions">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => void ask(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </section>
        ) : (
          <div className="message-list" aria-live="polite">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <div className="message-label">
                  {message.role === "user" ? "You" : "Policy Assistant"}
                </div>
                <div className={`bubble${message.error ? " error" : ""}`}>
                  <p>{message.content}</p>
                  {message.sources && message.sources.length > 0 && (
                    <div className="sources">
                      <span>Sources</span>
                      <ul>
                        {message.sources.map((source) => (
                          <li key={source}>{source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </article>
            ))}
            {isLoading && (
              <article
                className="message assistant"
                aria-label="Generating answer"
              >
                <div className="message-label">Policy Assistant</div>
                <div className="bubble loading-dots">
                  <span />
                  <span />
                  <span />
                </div>
              </article>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </main>

      <footer className="composer-wrap">
        <form className="composer" onSubmit={submit}>
          <label className="sr-only" htmlFor="question">
            Ask a policy question
          </label>
          <textarea
            id="question"
            rows={1}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder="Ask a policy question…"
            disabled={isLoading}
          />
          <button type="submit" disabled={!question.trim() || isLoading}>
            Ask
          </button>
        </form>
        <p>
          Answers are generated from internal documents. Verify critical
          decisions.
        </p>
      </footer>
    </div>
  );
}

export default App;
