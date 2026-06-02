import type { SessionStateStore } from "../realtime/session-state";
import type { TrainingConfig } from "../realtime/training-config";
import { DEFAULT_TRAINING_CONFIG, TRAINING_OPTIONS } from "../realtime/training-config";

interface Actions {
  onConfigChange: (config: TrainingConfig) => void;
  onStart: () => Promise<void>;
  onStop: () => Promise<void>;
  onManualTurnEnd: () => Promise<void>;
  onTtsEnabledChange: (enabled: boolean) => void;
  ttsEnabled: boolean;
  ttsSupported: boolean;
}

const STATUS_TEXT: Record<string, string> = {
  idle: "\u51c6\u5907\u5f00\u59cb",
  connecting: "\u6b63\u5728\u8fde\u63a5",
  ready: "\u6b63\u5728\u8046\u542c",
  ended: "\u672c\u8f6e\u5df2\u7ed3\u675f",
  error: "\u8fde\u63a5\u5f02\u5e38",
};

export class InterviewRoom {
  constructor(
    private readonly host: HTMLElement,
    private readonly state: SessionStateStore,
    private readonly actions: Actions,
  ) {}

  render(): void {
    this.host.innerHTML = `
      <section class="room-panel" aria-label="\u6b63\u5f0f\u9762\u8bd5\u8bad\u7ec3">
        <header class="room-header">
          <div>
            <p class="eyebrow">AI INTERVIEW ROOM</p>
            <h1>\u9762\u8bd5\u8bad\u7ec3\u5ba4</h1>
          </div>
          <div class="room-header-actions">
            <a class="debug-link" href="#/debug">\u8c03\u8bd5\u53f0</a>
          </div>
        </header>

        <section class="training-dock" aria-label="\u8bad\u7ec3\u6761\u4ef6">
          ${this.selectField("jobId", "\u5c97\u4f4d", TRAINING_OPTIONS.jobs)}
          ${this.selectField("modeId", "\u6a21\u5f0f", TRAINING_OPTIONS.modes)}
          ${this.selectField("competencyId", "\u80fd\u529b", TRAINING_OPTIONS.competencies)}
          <label class="tts-toggle">
            <span>AI \u8bed\u97f3</span>
            <input
              type="checkbox"
              data-tts-toggle
              ${this.actions.ttsEnabled ? "checked" : ""}
              ${this.actions.ttsSupported ? "" : "disabled"}
            />
          </label>
        </section>

        <section class="voice-room">
          <div class="voice-orb-wrap">
            <div class="voice-orb" aria-hidden="true">
              <span class="voice-core"></span>
              <span class="voice-ring ring-one"></span>
              <span class="voice-ring ring-two"></span>
              <span class="voice-wave wave-one"></span>
              <span class="voice-wave wave-two"></span>
              <span class="voice-wave wave-three"></span>
            </div>
          </div>
          <p class="focus-status">\u51c6\u5907\u5f00\u59cb</p>
          <p class="focus-hint">\u5f00\u59cb\u540e\u76f4\u63a5\u8bf4\u8bdd\uff0c\u9875\u9762\u4f1a\u5c3d\u91cf\u4fdd\u6301\u5b89\u9759\u3002</p>
          <div class="interviewer-card">
            <p class="prompt-label">\u9762\u8bd5\u5b98</p>
            <p class="prompt-text">\u5f00\u59cb\u540e\uff0cAI \u4f1a\u6839\u636e\u4f60\u7684\u56de\u7b54\u7ee7\u7eed\u8ffd\u95ee\u3002</p>
          </div>
          <details class="transcript-peek">
            <summary>\u67e5\u770b\u8f6c\u5199</summary>
            <p class="peek-text"></p>
          </details>
        </section>

        <footer class="room-controls">
          <button class="start primary-action" type="button">\u5f00\u59cb\u8bad\u7ec3</button>
          <button class="finish" type="button">\u6211\u8bf4\u5b8c\u4e86</button>
          <button class="stop" type="button">\u7ed3\u675f</button>
        </footer>
      </section>
    `;

    const start = this.host.querySelector<HTMLButtonElement>(".start");
    const stop = this.host.querySelector<HTMLButtonElement>(".stop");
    const finish = this.host.querySelector<HTMLButtonElement>(".finish");
    const ttsToggle = this.host.querySelector<HTMLInputElement>("[data-tts-toggle]");
    const configInputs = Array.from(this.host.querySelectorAll<HTMLSelectElement>("[data-config-key]"));

    start?.addEventListener("click", () => void this.actions.onStart());
    stop?.addEventListener("click", () => void this.actions.onStop());
    finish?.addEventListener("click", () => void this.actions.onManualTurnEnd());
    ttsToggle?.addEventListener("change", () => this.actions.onTtsEnabledChange(ttsToggle.checked));
    configInputs.forEach((input) => {
      input.addEventListener("change", () => this.actions.onConfigChange(this.currentConfig()));
    });
    this.actions.onConfigChange(this.currentConfig());

    this.state.subscribe((snapshot) => {
      const panel = this.host.querySelector<HTMLElement>(".room-panel");
      const status = this.host.querySelector<HTMLElement>(".focus-status");
      const hint = this.host.querySelector<HTMLElement>(".focus-hint");
      const prompt = this.host.querySelector<HTMLElement>(".prompt-text");
      const peek = this.host.querySelector<HTMLElement>(".peek-text");

      panel?.setAttribute("data-status", snapshot.status);
      panel?.setAttribute("data-voice-mode", this.voiceMode(snapshot));
      if (status) status.textContent = snapshot.turnState || STATUS_TEXT[snapshot.status];
      if (hint) hint.textContent = this.hintText(snapshot);
      if (prompt) prompt.textContent = this.promptText(snapshot);
      if (peek) peek.textContent = snapshot.partialTranscript || snapshot.finalTranscripts.at(-1) || "\u6682\u65e0\u8f6c\u5199\u3002";

      if (start) start.disabled = snapshot.status === "connecting" || snapshot.status === "ready";
      if (stop) stop.disabled = snapshot.status !== "ready";
      if (finish) finish.disabled = snapshot.status !== "ready" || !snapshot.recording;
      configInputs.forEach((input) => {
        input.disabled = snapshot.status === "connecting" || snapshot.status === "ready";
      });
    });
  }

  private hintText(snapshot: ReturnType<SessionStateStore["current"]>): string {
    if (snapshot.error) return snapshot.error;
    if (snapshot.turnHint) return snapshot.turnHint;
    if (snapshot.assistantDraft) return "AI \u6b63\u5728\u51c6\u5907\u4e0b\u4e00\u4e2a\u8ffd\u95ee\u3002";
    if (snapshot.status === "ready" && snapshot.recording) return "\u4f60\u53ef\u4ee5\u81ea\u7136\u505c\u987f\u601d\u8003\uff0c\u6211\u4f1a\u7b49\u5230\u786e\u8ba4\u4f60\u8bf4\u5b8c\u3002";
    if (snapshot.status === "connecting") return "\u6b63\u5728\u51c6\u5907\u672c\u5730\u5b9e\u65f6\u4f1a\u8bdd\u3002";
    if (snapshot.status === "ended") return "\u53ef\u4ee5\u518d\u5f00\u59cb\u4e00\u8f6e\u65b0\u8bad\u7ec3\u3002";
    return "\u9009\u597d\u8bad\u7ec3\u6761\u4ef6\u540e\uff0c\u5f00\u59cb\u4e00\u573a\u8bed\u97f3\u9762\u8bd5\u3002";
  }

  private promptText(snapshot: ReturnType<SessionStateStore["current"]>): string {
    const assistantText = snapshot.assistantMessages.at(-1);
    if (assistantText) return assistantText;
    if (snapshot.assistantDraft) return "AI \u6b63\u5728\u601d\u8003\u4e0b\u4e00\u4e2a\u95ee\u9898...";
    if (snapshot.status === "ready") return "\u6211\u6b63\u5728\u542c\u4f60\u56de\u7b54\u3002";
    return "\u5f00\u59cb\u540e\uff0cAI \u4f1a\u6839\u636e\u4f60\u7684\u56de\u7b54\u7ee7\u7eed\u8ffd\u95ee\u3002";
  }

  private voiceMode(snapshot: ReturnType<SessionStateStore["current"]>): string {
    if (snapshot.status === "error") return "error";
    if (snapshot.ttsPhase === "preparing") return "thinking";
    if (snapshot.ttsPhase === "speaking") return "speaking";
    if (snapshot.assistantDraft) return "thinking";
    if (snapshot.turnState?.includes("\u7b49\u5f85") || snapshot.turnState?.includes("\u53ef\u80fd\u8fd8\u60f3")) return "waiting";
    if (snapshot.partialTranscript) return "hearing";
    if (snapshot.status === "ready" && snapshot.recording) return "listening";
    if (snapshot.status === "connecting") return "connecting";
    return "idle";
  }

  private selectField(key: keyof TrainingConfig, label: string, options: readonly { id: string; label: string }[]): string {
    const defaultValue = DEFAULT_TRAINING_CONFIG[key];
    const optionHtml = options
      .map((option) => `<option value="${option.id}"${option.id === defaultValue ? " selected" : ""}>${option.label}</option>`)
      .join("");
    return `
      <label class="config-field">
        <span>${label}</span>
        <select data-config-key="${key}">${optionHtml}</select>
      </label>
    `;
  }

  private currentConfig(): TrainingConfig {
    const valueFor = (key: keyof TrainingConfig): string => {
      const input = this.host.querySelector<HTMLSelectElement>(`[data-config-key="${key}"]`);
      return input?.value ?? DEFAULT_TRAINING_CONFIG[key];
    };

    return {
      jobId: valueFor("jobId"),
      modeId: valueFor("modeId"),
      competencyId: valueFor("competencyId"),
      strategyId: DEFAULT_TRAINING_CONFIG.strategyId,
    };
  }
}
