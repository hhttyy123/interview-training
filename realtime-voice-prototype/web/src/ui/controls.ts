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
      <section class="training-config" aria-label="training configuration">
        <div class="config-heading">
          <p class="label">TRAINING SETUP</p>
          <strong>Realtime interview room</strong>
        </div>
        ${this.selectField("jobId", "Job", TRAINING_OPTIONS.jobs)}
        ${this.selectField("modeId", "Mode", TRAINING_OPTIONS.modes)}
        ${this.selectField("competencyId", "Competency", TRAINING_OPTIONS.competencies)}
        ${this.selectField("strategyId", "Follow-up", TRAINING_OPTIONS.strategies)}
      </section>
      <div class="controls">
        <button class="start" type="button">Start session</button>
        <button class="stop" type="button">End session</button>
      </div>
      <div class="controls speech-controls">
        <button class="finish" type="button" title="Press Enter to force the current turn to end.">I'm done</button>
      </div>
      <p class="privacy">The microphone stays on only during the active session. Audio and transcripts are not persisted.</p>
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
