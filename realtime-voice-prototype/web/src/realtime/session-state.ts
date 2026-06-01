export type ConnectionStatus = "idle" | "connecting" | "ready" | "ended" | "error";

export interface SessionSnapshot {
  status: ConnectionStatus;
  sessionId?: string;
  error?: string;
  recording: boolean;
  partialTranscript: string;
  finalTranscripts: string[];
  assistantDraft: string;
  assistantMessages: string[];
  turnState?: string;
  turnHint?: string;
  events: string[];
}

type Listener = (snapshot: SessionSnapshot) => void;

export class SessionStateStore {
  private snapshot: SessionSnapshot = {
    status: "idle",
    recording: false,
    partialTranscript: "",
    finalTranscripts: [],
    assistantDraft: "",
    assistantMessages: [],
    turnState: undefined,
    turnHint: undefined,
    events: [],
  };
  private readonly listeners = new Set<Listener>();

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    listener(this.snapshot);
    return () => this.listeners.delete(listener);
  }

  update(status: ConnectionStatus, entry: string, changes: Partial<SessionSnapshot> = {}): void {
    this.snapshot = {
      ...this.snapshot,
      ...changes,
      status,
      events: [entry, ...this.snapshot.events].slice(0, 8),
    };
    this.emit();
  }

  current(): SessionSnapshot {
    return this.snapshot;
  }

  recordingStarted(): void {
    this.snapshot = { ...this.snapshot, recording: true, assistantDraft: "", turnState: "listening", turnHint: undefined };
    this.addEvent("麦克风已开启，正在发送音频。");
  }

  recordingStopped(): void {
    this.snapshot = { ...this.snapshot, recording: false, turnState: "processing", turnHint: undefined };
    this.addEvent("本轮音频结束，正在等待最终转写。");
  }

  manualTurnEnded(): void {
    this.snapshot = { ...this.snapshot, turnState: "processing", turnHint: undefined };
    this.addEvent("Manual turn end requested.");
  }

  receivePartialTranscript(text: string): void {
    this.snapshot = { ...this.snapshot, partialTranscript: text };
    this.emit();
  }

  receiveFinalTranscript(text: string): void {
    const finalTranscripts = text ? [...this.snapshot.finalTranscripts, text] : this.snapshot.finalTranscripts;
    this.snapshot = { ...this.snapshot, partialTranscript: "", finalTranscripts };
    this.addEvent(text ? "已收到本轮最终转写。" : "本轮没有识别到有效语音。");
  }

  receiveAssistantTextDelta(text: string): void {
    this.snapshot = { ...this.snapshot, assistantDraft: this.snapshot.assistantDraft + text };
    this.emit();
  }

  receiveAssistantTextDone(text: string): void {
    const finalText = text || this.snapshot.assistantDraft;
    const assistantMessages = finalText ? [...this.snapshot.assistantMessages, finalText] : this.snapshot.assistantMessages;
    this.snapshot = { ...this.snapshot, assistantDraft: "", assistantMessages, turnState: "listening", turnHint: undefined };
    this.addEvent(finalText ? "AI 回复已完成。" : "AI 没有生成回复。");
  }

  receiveAssistantCancelled(reason: string): void {
    this.snapshot = { ...this.snapshot, assistantDraft: "", turnState: "listening", turnHint: undefined };
    this.addEvent(`AI reply cancelled: ${reason}`);
  }

  receiveTurnState(state: string, hint?: string): void {
    this.snapshot = { ...this.snapshot, turnState: state, turnHint: hint || undefined };
    this.emit();
  }

  audioError(message: string): void {
    this.snapshot = { ...this.snapshot, recording: false, error: message };
    this.addEvent(message);
  }

  resetTranscript(): void {
    this.snapshot = {
      ...this.snapshot,
      recording: false,
      partialTranscript: "",
      finalTranscripts: [],
      assistantDraft: "",
      assistantMessages: [],
      turnState: undefined,
      turnHint: undefined,
    };
    this.emit();
  }

  private addEvent(entry: string): void {
    this.snapshot = { ...this.snapshot, events: [entry, ...this.snapshot.events].slice(0, 8) };
    this.emit();
  }

  private emit(): void {
    for (const listener of this.listeners) {
      listener(this.snapshot);
    }
  }
}
