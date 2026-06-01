import type { ClientEvent, ServerEvent } from "./events";
import { SessionStateStore } from "./session-state";
import type { TrainingConfig } from "./training-config";

export class VoiceSessionSocket {
  private socket?: WebSocket;
  private readyResolver?: () => void;
  private readyRejecter?: (error: Error) => void;

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

    this.state.update("connecting", "Connecting to the local interview session...");
    this.socket = new WebSocket(this.endpoint);

    this.socket.addEventListener("open", () => this.send({ type: "session.start", ...config }));
    this.socket.addEventListener("message", (message) => {
      this.receive(JSON.parse(message.data as string) as ServerEvent);
    });
    this.socket.addEventListener("error", () => {
      const error = new Error("WebSocket connection failed.");
      this.state.update("error", "Connection failed. Confirm the backend server is running.", {
        error: error.message,
      });
      this.readyRejecter?.(error);
      this.readyResolver = undefined;
      this.readyRejecter = undefined;
    });
    this.socket.addEventListener("close", () => {
      if (this.state.current().status !== "ended") {
        this.state.update("ended", "Realtime connection closed.");
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
      this.state.update("ended", "There is no active session.");
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
      this.state.update("ready", "Session ready. I am listening.", {
        sessionId: event.session_id,
        error: undefined,
      });
      this.readyResolver?.();
      this.readyResolver = undefined;
      this.readyRejecter = undefined;
      return;
    }

    if (event.type === "session.ended") {
      this.state.update("ended", "Session ended and transient state was cleared.", {
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
      return;
    }

    if (event.type === "assistant.text.done") {
      this.state.receiveAssistantTextDone(event.text);
      return;
    }

    if (event.type === "assistant.cancelled") {
      this.state.receiveAssistantCancelled(event.reason);
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
