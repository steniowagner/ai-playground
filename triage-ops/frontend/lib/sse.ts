import type { StreamEvent } from "./types";

type EventHandler = (event: StreamEvent) => void;

function parseBlock(block: string): StreamEvent | null {
  const data = block
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n");

  if (!data) return null;

  try {
    return JSON.parse(data) as StreamEvent;
  } catch {
    return null;
  }
}

export async function consumeEventStream(
  url: string,
  body: unknown,
  onEvent: EventHandler,
): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `Request failed (${response.status}).`);
  }

  if (!response.body) throw new Error("The server returned an empty stream.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, "\n");

    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const event = parseBlock(block);
      if (event) onEvent(event);
    }

    if (done) break;
  }

  if (buffer.trim()) {
    const event = parseBlock(buffer);
    if (event) onEvent(event);
  }
}
