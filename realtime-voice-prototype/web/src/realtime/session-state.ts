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
  ttsPhase: "idle" | "preparing" | "speaking";
  turnState?: string;
  turnHint?: string;
  events: string[];
}

type Listener = (snapshot: SessionSnapshot) => void;

const TURN_STATE_LABELS: Record<string, string> = {
  listening: "\u6b63\u5728\u8046\u542c",
  processing: "\u6b63\u5728\u6574\u7406\u672c\u8f6e\u56de\u7b54",
  waiting_for_more: "\u5224\u65ad\u4f60\u53ef\u80fd\u8fd8\u60f3\u7ee7\u7eed\u8bf4",
  hint: "\u6700\u540e\u7b49\u5f85\u4e2d",
};

function turnStateLabel(state: string): string {
  return TURN_STATE_LABELS[state] ?? state;
}

export class SessionStateStore {
  private snapshot: SessionSnapshot = {
    status: "idle",
    recording: false,
    partialTranscript: "",
    finalTranscripts: [],
    assistantDraft: "",
    assistantMessages: [],
    ttsPhase: "idle",
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
    this.snapshot = {
      ...this.snapshot,
      recording: true,
      assistantDraft: "",
      ttsPhase: "idle",
      turnState: turnStateLabel("listening"),
      turnHint: undefined,
    };
    this.addEvent("\u9ea6\u514b\u98ce\u5df2\u5f00\u542f\uff0c\u6b63\u5728\u53d1\u9001\u97f3\u9891\u3002");
  }

  recordingStopped(): void {
    this.snapshot = {
      ...this.snapshot,
      recording: false,
      turnState: turnStateLabel("processing"),
      turnHint: undefined,
    };
    this.addEvent("\u5f53\u524d\u8fd9\u4e00\u8f6e\u5df2\u7ed3\u675f\uff0c\u6b63\u5728\u7b49\u5f85\u6700\u7ec8\u8f6c\u5199\u3002");
  }

  manualTurnEnded(): void {
    this.snapshot = {
      ...this.snapshot,
      turnState: turnStateLabel("processing"),
      turnHint: undefined,
    };
    this.addEvent("\u5df2\u8bf7\u6c42\u624b\u52a8\u7ed3\u675f\u5f53\u524d\u8fd9\u4e00\u8f6e\u3002");
  }

  receivePartialTranscript(text: string): void {
    this.snapshot = { ...this.snapshot, partialTranscript: text };
    this.emit();
  }

  receiveFinalTranscript(text: string): void {
    const finalTranscripts = text ? [...this.snapshot.finalTranscripts, text] : this.snapshot.finalTranscripts;
    this.snapshot = { ...this.snapshot, partialTranscript: "", finalTranscripts };
    this.addEvent(text ? "\u5df2\u6536\u5230\u672c\u8f6e\u6700\u7ec8\u8f6c\u5199\u3002" : "\u672c\u8f6e\u6ca1\u6709\u8bc6\u522b\u5230\u6709\u6548\u8bed\u97f3\u3002");
  }

  receiveAssistantTextDelta(text: string): void {
    this.snapshot = { ...this.snapshot, assistantDraft: this.snapshot.assistantDraft + text };
    this.emit();
  }

  receiveAssistantTextDone(text: string): void {
    const finalText = text || this.snapshot.assistantDraft;
    const assistantMessages = finalText ? [...this.snapshot.assistantMessages, finalText] : this.snapshot.assistantMessages;
    this.snapshot = {
      ...this.snapshot,
      assistantDraft: "",
      assistantMessages,
      ttsPhase: "idle",
      turnState: turnStateLabel("listening"),
      turnHint: undefined,
    };
    this.addEvent(finalText ? "AI \u56de\u590d\u5df2\u5b8c\u6210\u3002" : "AI \u6ca1\u6709\u751f\u6210\u6709\u6548\u56de\u590d\u3002");
  }

  receiveAssistantCancelled(reason: string): void {
    this.snapshot = {
      ...this.snapshot,
      assistantDraft: "",
      ttsPhase: "idle",
      turnState: turnStateLabel("listening"),
      turnHint: undefined,
    };
    this.addEvent(`AI \u56de\u590d\u5df2\u53d6\u6d88\uff1a${reason}`);
  }

  receiveTurnState(state: string, hint?: string): void {
    this.snapshot = {
      ...this.snapshot,
      turnState: turnStateLabel(state),
      turnHint: hint || undefined,
    };
    this.emit();
  }

  audioError(message: string): void {
    this.snapshot = { ...this.snapshot, recording: false, ttsPhase: "idle", error: message };
    this.addEvent(message);
  }

  ttsPlaybackPreparing(): void {
    this.snapshot = {
      ...this.snapshot,
      ttsPhase: "preparing",
      turnState: "AI \u6b63\u5728\u51c6\u5907\u8bed\u97f3",
      turnHint: "\u6211\u4f1a\u7b49 AI \u8bf4\u5b8c\u540e\u518d\u7ee7\u7eed\u542c\u4f60\u56de\u7b54\u3002",
    };
    this.emit();
  }

  ttsPlaybackStarted(): void {
    this.snapshot = {
      ...this.snapshot,
      ttsPhase: "speaking",
      turnState: "AI \u6b63\u5728\u8bf4\u8bdd",
      turnHint: "\u6211\u4f1a\u7b49 AI \u8bf4\u5b8c\u540e\u518d\u7ee7\u7eed\u542c\u4f60\u56de\u7b54\u3002",
    };
    this.emit();
  }

  ttsPlaybackEnded(): void {
    const shouldListen = this.snapshot.status === "ready" && this.snapshot.recording;
    this.snapshot = {
      ...this.snapshot,
      ttsPhase: "idle",
      turnState: shouldListen ? turnStateLabel("listening") : this.snapshot.turnState,
      turnHint: undefined,
    };
    this.emit();
  }

  resetTranscript(): void {
    this.snapshot = {
      ...this.snapshot,
      recording: false,
      partialTranscript: "",
      finalTranscripts: [],
      assistantDraft: "",
      assistantMessages: [],
      ttsPhase: "idle",
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
