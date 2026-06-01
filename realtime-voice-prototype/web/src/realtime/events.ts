import type { TrainingConfig } from "./training-config";

export type ClientEvent =
  | ({ type: "session.start" } & Partial<TrainingConfig>)
  | { type: "session.stop" }
  | { type: "audio.begin" }
  | { type: "audio.end" };

export type ServerEvent =
  | { type: "session.ready"; session_id: string }
  | { type: "session.ended"; session_id: string }
  | { type: "session.error"; message: string }
  | { type: "transcript.partial"; text: string }
  | { type: "transcript.final"; text: string }
  | { type: "assistant.text.delta"; text: string }
  | { type: "assistant.text.done"; text: string }
  | { type: "assistant.cancelled"; reason: string }
  | {
      type: "turn.state";
      state: string;
      wait_ms?: number;
      hint_after_ms?: number;
      hint_text?: string;
      reason?: string;
    };
