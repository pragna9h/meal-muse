import { useEffect, useState } from "react";

interface ChatInputProps {
  onSubmit: (message: string) => Promise<void>;
  isLoading: boolean;

}

export default function ChatInput({
  onSubmit,
  isLoading,
}: ChatInputProps) {
  const [message, setMessage] = useState("");

  const [loadingDots, setLoadingDots] = useState(".");

  useEffect(() => {
    if (!isLoading) {
      setLoadingDots(".");
      return;
    }

    const interval = window.setInterval(() => {
      setLoadingDots((current) => {
        if (current === ".") return "..";
        if (current === "..") return "...";
        return ".";
      });
    }, 400);

    return () => window.clearInterval(interval);
  }, [isLoading]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedMessage = message.trim();

    if (!trimmedMessage || isLoading) {
      return;
    }

    await onSubmit(trimmedMessage);
  }

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <div className="search-icon" aria-hidden="true">
        ⌕
      </div>

      <textarea
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="What would you like to cook?"
        rows={1}
        disabled={isLoading}
      />

      {message && !isLoading && (
        <button
            type="button"
            className="clear-button"
            onClick={() => setMessage("")}
            aria-label="Clear prompt"
        >
            <span className="clear-icon">×</span>
        </button>
        )}

      <button type="submit" className="submit-button" disabled={isLoading || !message.trim()}>
        {isLoading ? `Thinking${loadingDots}` : "Ask MealMuse"}
        {!isLoading && <span className="button-arrow">→</span>}
      </button>
    </form>
  );
}