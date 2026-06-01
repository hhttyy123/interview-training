import { MicrophoneStream } from "./audio/microphone";
import { VoiceSessionSocket } from "./realtime/socket-client";
import { SessionStateStore } from "./realtime/session-state";
import type { TrainingConfig } from "./realtime/training-config";
import { DEFAULT_TRAINING_CONFIG } from "./realtime/training-config";
import { Controls } from "./ui/controls";
import { StatusPanel } from "./ui/status";
import { ActivityFeed } from "./ui/transcript";

export class VoicePrototypeApp {
  private readonly state = new SessionStateStore();
  private readonly socket = new VoiceSessionSocket("ws://localhost:8000/ws/voice", this.state);
  private readonly microphone = new MicrophoneStream((chunk) => this.socket.sendAudio(chunk));
  private trainingConfig: TrainingConfig = { ...DEFAULT_TRAINING_CONFIG };

  constructor(private readonly root: HTMLElement) {}

  render(): void {
    this.root.innerHTML = `
      <main class="shell">
        <header class="hero">
          <p class="eyebrow">V0 / Realtime Conversation Lab</p>
          <h1>Realtime interview<br />without turn buttons</h1>
          <p class="intro">
            Start one session and speak naturally. The backend listens continuously,
            detects turn completion, waits when you may still be thinking, and lets you
            force-end a turn only when needed.
          </p>
        </header>
        <section class="console" aria-label="realtime conversation console">
          <div id="status-panel"></div>
          <div id="controls"></div>
          <div id="activity-feed"></div>
        </section>
      </main>
    `;

    new StatusPanel(this.required("#status-panel"), this.state).render();
    new ActivityFeed(this.required("#activity-feed"), this.state).render();
    new Controls(this.required("#controls"), this.state, {
      onConfigChange: (config) => {
        this.trainingConfig = config;
      },
      onStart: async () => {
        try {
          await this.socket.startSession(this.trainingConfig);
          await this.microphone.start();
          this.socket.beginAudio();
          this.state.recordingStarted();
        } catch (error) {
          this.socket.stopSession();
          this.state.audioError(error instanceof Error ? error.message : "Microphone could not start.");
        }
      },
      onStop: async () => {
        await this.microphone.stop();
        this.socket.stopSession();
      },
      onManualTurnEnd: async () => {
        this.socket.endAudio();
        this.state.manualTurnEnded();
      },
    }).render();
  }

  private required(selector: string): HTMLElement {
    const element = this.root.querySelector<HTMLElement>(selector);
    if (!element) {
      throw new Error(`Required element missing: ${selector}`);
    }
    return element;
  }
}
