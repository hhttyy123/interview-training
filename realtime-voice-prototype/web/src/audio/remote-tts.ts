export type TtsPlaybackPhase = "idle" | "preparing" | "speaking";

export class RemoteTextToSpeech {
  private enabled = true;
  private audio?: HTMLAudioElement;
  private objectUrl?: string;
  private abortController?: AbortController;
  private phase: TtsPlaybackPhase = "idle";
  private playbackToken = 0;

  constructor(
    private readonly endpoint = "http://localhost:8000/api/tts",
    private readonly onPlaybackChange: (phase: TtsPlaybackPhase) => void = () => undefined,
  ) {}

  isSupported(): boolean {
    return "fetch" in window && "Audio" in window && "URL" in window;
  }

  isEnabled(): boolean {
    return this.enabled && this.isSupported();
  }

  isBlockingInput(): boolean {
    return this.phase !== "idle";
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    if (!enabled) {
      this.cancel();
    }
  }

  async speak(text: string): Promise<void> {
    this.cancel();
    if (!this.isEnabled() || !text.trim()) {
      return;
    }

    const token = this.playbackToken;
    try {
      this.abortController = new AbortController();
      this.setPhase("preparing");
      const response = await fetch(this.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.trim() }),
        signal: this.abortController.signal,
      });
      if (!response.ok || token !== this.playbackToken) {
        this.setPhase("idle");
        return;
      }

      const blob = await response.blob();
      if (token === this.playbackToken) {
        this.objectUrl = URL.createObjectURL(blob);
        this.audio = new Audio(this.objectUrl);
        this.setPhase("speaking");
        await this.playCurrentAudio(token);
        this.setPhase("idle");
      }
    } catch {
      this.cancel();
    } finally {
      this.abortController = undefined;
      this.releaseObjectUrl();
    }
  }

  reset(): void {
    this.cancel();
  }

  cancel(): void {
    this.playbackToken += 1;
    this.abortController?.abort();
    this.abortController = undefined;
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
      this.audio = undefined;
    }
    this.setPhase("idle");
    this.releaseObjectUrl();
  }

  private playCurrentAudio(token: number): Promise<void> {
    const audio = this.audio;
    if (!audio) {
      return Promise.resolve();
    }

    return new Promise((resolve) => {
      const finish = () => {
        audio.removeEventListener("ended", finish);
        audio.removeEventListener("error", finish);
        if (token === this.playbackToken) {
          this.audio = undefined;
        }
        resolve();
      };
      audio.addEventListener("ended", finish);
      audio.addEventListener("error", finish);
      audio.play().catch(finish);
    });
  }

  private setPhase(phase: TtsPlaybackPhase): void {
    if (this.phase === phase) {
      return;
    }
    this.phase = phase;
    this.onPlaybackChange(phase);
  }

  private releaseObjectUrl(): void {
    if (this.objectUrl) {
      URL.revokeObjectURL(this.objectUrl);
      this.objectUrl = undefined;
    }
  }
}
