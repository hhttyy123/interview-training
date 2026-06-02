import type { SessionStateStore } from "../realtime/session-state";
import type { TrainingConfig } from "../realtime/training-config";
import { DEFAULT_TRAINING_CONFIG, TRAINING_OPTIONS } from "../realtime/training-config";

interface Actions {
  onConfigChange: (config: TrainingConfig) => void;
  onStart: () => Promise<void>;
  onStop: () => Promise<void>;
  onManualTurnEnd: () => Promise<void>;
}

export class Controls {
  private static keydownHandler?: (event: KeyboardEvent) => void;

  constructor(
    private readonly host: HTMLElement,
    private readonly state: SessionStateStore,
    private readonly actions: Actions,
  ) {}

  render(): void {
    this.host.innerHTML = `
      <section class="training-config" aria-label="\u8bad\u7ec3\u914d\u7f6e">
        <div class="config-heading">
          <p class="label">\u8bad\u7ec3\u8bbe\u7f6e</p>
          <strong>\u5b9e\u65f6\u9762\u8bd5\u8bad\u7ec3\u5ba4</strong>
        </div>
        ${this.selectField("jobId", "\u5c97\u4f4d", TRAINING_OPTIONS.jobs)}
        ${this.selectField("modeId", "\u6a21\u5f0f", TRAINING_OPTIONS.modes)}
        ${this.selectField("competencyId", "\u80fd\u529b\u70b9", TRAINING_OPTIONS.competencies)}
        ${this.selectField("strategyId", "\u8ffd\u95ee\u65b9\u5f0f", TRAINING_OPTIONS.strategies)}
      </section>
      <div class="controls">
        <button class="start" type="button">\u5f00\u59cb\u4f1a\u8bdd</button>
        <button class="stop" type="button">\u7ed3\u675f\u4f1a\u8bdd</button>
      </div>
      <div class="controls speech-controls">
        <button class="finish" type="button" title="\u6309 Enter \u53ef\u624b\u52a8\u7ed3\u675f\u5f53\u524d\u8fd9\u4e00\u8f6e\u3002">\u6211\u8bf4\u5b8c\u4e86</button>
      </div>
    `;
    const start = this.host.querySelector<HTMLButtonElement>(".start");
    const stop = this.host.querySelector<HTMLButtonElement>(".stop");
    const finish = this.host.querySelector<HTMLButtonElement>(".finish");
    const configInputs = Array.from(this.host.querySelectorAll<HTMLSelectElement>("[data-config-key]"));

    start?.addEventListener("click", () => void this.actions.onStart());
    stop?.addEventListener("click", () => void this.actions.onStop());
    finish?.addEventListener("click", () => void this.actions.onManualTurnEnd());
    if (Controls.keydownHandler) {
      document.removeEventListener("keydown", Controls.keydownHandler);
    }
    Controls.keydownHandler = (event: KeyboardEvent) => {
      if (event.key === "Enter" && this.state.current().status === "ready") {
        event.preventDefault();
        void this.actions.onManualTurnEnd();
      }
    };
    document.addEventListener("keydown", Controls.keydownHandler);
    configInputs.forEach((input) => {
      input.addEventListener("change", () => this.actions.onConfigChange(this.currentConfig()));
    });
    this.actions.onConfigChange(this.currentConfig());

    this.state.subscribe((snapshot) => {
      if (start) start.disabled = snapshot.status === "connecting" || snapshot.status === "ready";
      if (stop) stop.disabled = snapshot.status !== "ready";
      if (finish) finish.disabled = snapshot.status !== "ready" || !snapshot.recording;
      configInputs.forEach((input) => {
        input.disabled = snapshot.status === "connecting" || snapshot.status === "ready";
      });
    });
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
      strategyId: valueFor("strategyId"),
    };
  }
}
