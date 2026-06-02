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
        : "<li>\u4f1a\u8bdd\u4e8b\u4ef6\u4f1a\u663e\u793a\u5728\u8fd9\u91cc\u3002</li>";

      const finalTranscripts = snapshot.finalTranscripts.length
        ? snapshot.finalTranscripts.map((text) => `<p class="utterance user">${escapeMarkup(text)}</p>`).join("")
        : '<p class="placeholder">\u786e\u8ba4\u540e\u7684\u7528\u6237\u56de\u7b54\u4f1a\u663e\u793a\u5728\u8fd9\u91cc\u3002</p>';

      const assistantMessages = snapshot.assistantMessages.length
        ? snapshot.assistantMessages.map((text) => `<p class="utterance assistant">${escapeMarkup(text)}</p>`).join("")
        : '<p class="placeholder">\u6bcf\u8f6e\u5b8c\u6210\u540e\uff0cAI \u7684\u56de\u590d\u4f1a\u663e\u793a\u5728\u8fd9\u91cc\u3002</p>';

      const assistantDraft = snapshot.assistantDraft
        ? `<p class="utterance assistant streaming">${escapeMarkup(snapshot.assistantDraft)}</p>`
        : "";

      const listeningText = snapshot.recording ? "\u6b63\u5728\u8046\u542c..." : "";
      const turnHint = snapshot.turnHint ? `<p class="turn-hint">${escapeMarkup(snapshot.turnHint)}</p>` : "";
      const turnState = snapshot.turnState ? `<p class="turn-state">\u5f53\u524d\u8f6e\u6b21\u72b6\u6001\uff1a${escapeMarkup(snapshot.turnState)}</p>` : "";

      this.host.innerHTML = `
        <section class="transcript">
          <h2>\u5b9e\u65f6\u8f6c\u5199</h2>
          ${turnState}
          ${turnHint}
          <p class="partial">${escapeMarkup(snapshot.partialTranscript || listeningText)}</p>
          <div class="final">${finalTranscripts}</div>
        </section>
        <section class="transcript">
          <h2>AI \u56de\u590d</h2>
          <div class="final">${assistantMessages}${assistantDraft}</div>
        </section>
        <section class="feed">
          <h2>\u4f1a\u8bdd\u4e8b\u4ef6</h2>
          <ol>${events}</ol>
        </section>
      `;
    });
  }
}
