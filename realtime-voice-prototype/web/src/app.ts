import { MicrophoneStream } from "./audio/microphone";
import { RemoteTextToSpeech } from "./audio/remote-tts";
import { VoiceSessionSocket } from "./realtime/socket-client";
import { SessionStateStore } from "./realtime/session-state";
import type { TrainingConfig } from "./realtime/training-config";
import { DEFAULT_TRAINING_CONFIG } from "./realtime/training-config";
import { Controls } from "./ui/controls";
import { InterviewRoom } from "./ui/interview-room";
import { StatusPanel } from "./ui/status";
import { ActivityFeed } from "./ui/transcript";

export class VoicePrototypeApp {
  private readonly state = new SessionStateStore();
  private readonly socket = new VoiceSessionSocket("ws://localhost:8000/ws/voice", this.state);
  private readonly tts = new RemoteTextToSpeech("http://localhost:8000/api/tts", (phase) => {
    if (phase === "preparing") {
      this.state.ttsPlaybackPreparing();
    } else if (phase === "speaking") {
      this.state.ttsPlaybackStarted();
    } else {
      this.state.ttsPlaybackEnded();
    }
  });
  private readonly microphone = new MicrophoneStream((chunk) => {
    if (!this.tts.isBlockingInput()) {
      this.socket.sendAudio(chunk);
    }
  });
  private trainingConfig: TrainingConfig = { ...DEFAULT_TRAINING_CONFIG };

  constructor(private readonly root: HTMLElement) {
    this.socket.onAssistantDone((text) => void this.tts.speak(text));
    this.socket.onAssistantCancelled(() => this.tts.cancel());
    window.addEventListener("hashchange", () => this.render());
  }

  render(): void {
    const route = location.hash === "#/debug" ? "debug" : "room";
    this.root.innerHTML = `
      <main class="${route === "debug" ? "shell debug-shell" : "room-shell"}">
        ${
          route === "debug"
            ? `
        <header class="topbar">
          <div>
            <p class="eyebrow">V0 / \u5b9e\u65f6\u9762\u8bd5</p>
            <h1>\u9762\u8bd5\u8bad\u7ec3\u5ba4</h1>
          </div>
          <a class="debug-link" href="#/room">\u56de\u5230\u9762\u8bd5\u5ba4</a>
        </header>
        <section class="console" aria-label="\u5b9e\u65f6\u5bf9\u8bdd\u63a7\u5236\u53f0">
          <div id="status-panel"></div>
          <div id="controls"></div>
          <div id="activity-feed"></div>
        </section>
        `
            : `<div id="interview-room"></div>`
        }
      </main>
    `;

    const actions: {
      onConfigChange: (config: TrainingConfig) => void;
      onStart: () => Promise<void>;
      onStop: () => Promise<void>;
      onManualTurnEnd: () => Promise<void>;
      onTtsEnabledChange: (enabled: boolean) => void;
      ttsEnabled: boolean;
      ttsSupported: boolean;
    } = {
      onConfigChange: (config) => {
        this.trainingConfig = config;
      },
      onStart: async () => {
        try {
          this.tts.reset();
          await this.socket.startSession(this.trainingConfig);
          await this.microphone.start();
          this.socket.beginAudio();
          this.state.recordingStarted();
        } catch (error) {
          this.socket.stopSession();
          this.state.audioError(error instanceof Error ? error.message : "\u9ea6\u514b\u98ce\u542f\u52a8\u5931\u8d25\u3002");
        }
      },
      onStop: async () => {
        this.tts.reset();
        await this.microphone.stop();
        this.socket.stopSession();
      },
      onManualTurnEnd: async () => {
        this.tts.reset();
        this.socket.endAudio();
        this.state.manualTurnEnded();
      },
      onTtsEnabledChange: (enabled) => {
        this.tts.setEnabled(enabled);
      },
      ttsEnabled: this.tts.isEnabled(),
      ttsSupported: this.tts.isSupported(),
    };

    if (route === "debug") {
      new StatusPanel(this.required("#status-panel"), this.state).render();
      new ActivityFeed(this.required("#activity-feed"), this.state).render();
      new Controls(this.required("#controls"), this.state, actions).render();
    } else {
      new InterviewRoom(this.required("#interview-room"), this.state, actions).render();
    }
  }

  private required(selector: string): HTMLElement {
    const element = this.root.querySelector<HTMLElement>(selector);
    if (!element) {
      throw new Error(`Required element missing: ${selector}`);
    }
    return element;
  }
}
