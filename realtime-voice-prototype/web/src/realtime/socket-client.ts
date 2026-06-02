import type { ClientEvent, ServerEvent } from "./events";
import { SessionStateStore } from "./session-state";
import type { TrainingConfig } from "./training-config";

export class VoiceSessionSocket {
  private socket?: WebSocket;
  private readyResolver?: () => void;
  private readyRejecter?: (error: Error) => void;
  private assistantDeltaListeners = new Set<(text: string) => void>();
  private assistantDoneListeners = new Set<(text: string) => void>();
  private assistantCancelledListeners = new Set<() => void>();

  constructor(
    private readonly endpoint: string,
    private readonly state: SessionStateStore,
  ) {}

  startSession(config: TrainingConfig): Promise<void> {
    const ready = new Promise<void>((resolve, reject) => {
      this.readyResolver = resolve;
      this.readyRejecter = reject;
    });

    if (this.socket?.readyState === WebSocket.OPEN) {
      this.send({ type: "session.start", ...config });
      return ready;
    }

    this.state.update("connecting", "\u6b63\u5728\u8fde\u63a5\u672c\u5730\u9762\u8bd5\u4f1a\u8bdd...");
    this.socket = new WebSocket(this.endpoint);

    this.socket.addEventListener("open", () => this.send({ type: "session.start", ...config }));
    this.socket.addEventListener("message", (message) => {
      this.receive(JSON.parse(message.data as string) as ServerEvent);
    });
    this.socket.addEventListener("error", () => {
      const error = new Error("WebSocket connection failed.");
      this.state.update("error", "\u8fde\u63a5\u5931\u8d25\uff0c\u8bf7\u786e\u8ba4\u540e\u7aef\u670d\u52a1\u5df2\u542f\u52a8\u3002", {
        error: error.message,
      });
      this.readyRejecter?.(error);
      this.readyResolver = undefined;
      this.readyRejecter = undefined;
    });
    this.socket.addEventListener("close", () => {
      if (this.state.current().status !== "ended") {
        this.state.update("ended", "\u5b9e\u65f6\u8fde\u63a5\u5df2\u5173\u95ed\u3002");
      }
      this.readyRejecter?.(new Error("Realtime connection closed before the session became ready."));
      this.readyResolver = undefined;
      this.readyRejecter = undefined;
      this.socket = undefined;
    });
    return ready;
  }

  stopSession(): void {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      this.state.update("ended", "\u5f53\u524d\u6ca1\u6709\u8fdb\u884c\u4e2d\u7684\u4f1a\u8bdd\u3002");
      return;
    }
    this.state.resetTranscript();
    this.send({ type: "session.stop" });
  }

  beginAudio(): void {
    this.send({ type: "audio.begin" });
  }

  endAudio(): void {
    this.send({ type: "audio.end" });
  }

  onAssistantDone(listener: (text: string) => void): () => void {
    this.assistantDoneListeners.add(listener);
    return () => this.assistantDoneListeners.delete(listener);
  }

  onAssistantDelta(listener: (text: string) => void): () => void {
    this.assistantDeltaListeners.add(listener);
    return () => this.assistantDeltaListeners.delete(listener);
  }

  onAssistantCancelled(listener: () => void): () => void {
    this.assistantCancelledListeners.add(listener);
    return () => this.assistantCancelledListeners.delete(listener);
  }

  sendAudio(chunk: ArrayBuffer): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(chunk);
    }
  }

  private send(event: ClientEvent): void {
    this.socket?.send(JSON.stringify(event));
  }

  private receive(event: ServerEvent): void {
    if (event.type === "session.ready") {
      this.state.update("ready", "\u4f1a\u8bdd\u5df2\u5c31\u7eea\uff0c\u53ef\u4ee5\u5f00\u59cb\u8bb2\u8bdd\u5e76\u67e5\u770b\u5b9e\u65f6\u8f6c\u5199\u3002", {
        sessionId: event.session_id,
        error: undefined,
      });
      this.readyResolver?.();
      this.readyResolver = undefined;
      this.readyRejecter = undefined;
      return;
    }

    if (event.type === "session.ended") {
      this.state.update("ended", "\u4f1a\u8bdd\u5df2\u7ed3\u675f\uff0c\u4e34\u65f6\u72b6\u6001\u5df2\u6e05\u7a7a\u3002", {
        sessionId: undefined,
      });
      this.socket?.close();
      return;
    }

    if (event.type === "transcript.partial") {
      this.state.receivePartialTranscript(event.text);
      return;
    }

    if (event.type === "transcript.final") {
      this.state.receiveFinalTranscript(event.text);
      return;
    }

    if (event.type === "assistant.text.delta") {
      this.state.receiveAssistantTextDelta(event.text);
      this.assistantDeltaListeners.forEach((listener) => listener(event.text));
      return;
    }

    if (event.type === "assistant.text.done") {
      this.state.receiveAssistantTextDone(event.text);
      this.assistantDoneListeners.forEach((listener) => listener(event.text));
      return;
    }

    if (event.type === "assistant.cancelled") {
      this.state.receiveAssistantCancelled(event.reason);
      this.assistantCancelledListeners.forEach((listener) => listener());
      return;
    }

    if (event.type === "turn.state") {
      this.state.receiveTurnState(event.state, event.hint_text);
      return;
    }

    this.state.update("error", event.message, { error: event.message });
    this.readyRejecter?.(new Error(event.message));
    this.readyResolver = undefined;
    this.readyRejecter = undefined;
  }
}
