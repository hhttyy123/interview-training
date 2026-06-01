import type { SessionStateStore } from "../realtime/session-state";

function escapeMarkup(text: string): string {
  return text.replace(/[&<>"']/g, (character) => {
    const substitutions: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return substitutions[character];
  });
}

export class ActivityFeed {
  constructor(
    private readonly host: HTMLElement,
    private readonly state: SessionStateStore,
  ) {}

  render(): void {
    this.state.subscribe((snapshot) => {
      const events = snapshot.events.length
        ? snapshot.events.map((event) => `<li>${escapeMarkup(event)}</li>`).join("")
        : "<li>Session events will appear here.</li>";

      const finalTranscripts = snapshot.finalTranscripts.length
        ? snapshot.finalTranscripts.map((text) => `<p class="utterance user">${escapeMarkup(text)}</p>`).join("")
        : '<p class="placeholder">Confirmed user turns will appear here.</p>';

      const assistantMessages = snapshot.assistantMessages.length
        ? snapshot.assistantMessages.map((text) => `<p class="utterance assistant">${escapeMarkup(text)}</p>`).join("")
        : '<p class="placeholder">Assistant replies will appear here after each completed turn.</p>';

      const assistantDraft = snapshot.assistantDraft
        ? `<p class="utterance assistant streaming">${escapeMarkup(snapshot.assistantDraft)}</p>`
        : "";

      const listeningText = snapshot.recording ? "Listening..." : "";
      const turnHint = snapshot.turnHint ? `<p class="turn-hint">${escapeMarkup(snapshot.turnHint)}</p>` : "";
      const turnState = snapshot.turnState ? `<p class="turn-state">Turn state: ${escapeMarkup(snapshot.turnState)}</p>` : "";

      this.host.innerHTML = `
        <section class="transcript">
          <h2>Live transcript</h2>
          ${turnState}
          ${turnHint}
          <p class="partial">${escapeMarkup(snapshot.partialTranscript || listeningText)}</p>
          <div class="final">${finalTranscripts}</div>
        </section>
        <section class="transcript">
          <h2>AI reply</h2>
          <div class="final">${assistantMessages}${assistantDraft}</div>
        </section>
        <section class="feed">
          <h2>Session events</h2>
          <ol>${events}</ol>
        </section>
      `;
    });
  }
}
