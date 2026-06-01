import { describe, expect, it } from "vitest";
import { SessionStateStore } from "../src/realtime/session-state";

describe("SessionStateStore", () => {
  it("notifies listeners with status transitions", () => {
    const store = new SessionStateStore();
    const statuses: string[] = [];
    store.subscribe((snapshot) => statuses.push(snapshot.status));

    store.update("connecting", "connecting");
    store.update("ready", "ready", { sessionId: "session-1" });

    expect(statuses).toEqual(["idle", "connecting", "ready"]);
    expect(store.current().sessionId).toBe("session-1");
  });

  it("accumulates streaming assistant text into a final message", () => {
    const store = new SessionStateStore();

    store.receiveAssistantTextDelta("hello, ");
    store.receiveAssistantTextDelta("continue");
    expect(store.current().assistantDraft).toBe("hello, continue");

    store.receiveAssistantTextDone("hello, continue");
    expect(store.current().assistantDraft).toBe("");
    expect(store.current().assistantMessages).toEqual(["hello, continue"]);
  });

  it("tracks turn hints and clears assistant draft when cancelled", () => {
    const store = new SessionStateStore();

    store.receiveAssistantTextDelta("draft");
    store.receiveTurnState("hint", "If there is nothing to add, I will continue.");
    expect(store.current().turnState).toBe("hint");
    expect(store.current().turnHint).toBe("If there is nothing to add, I will continue.");

    store.receiveAssistantCancelled("user started speaking");
    expect(store.current().assistantDraft).toBe("");
    expect(store.current().turnState).toBe("listening");
    expect(store.current().turnHint).toBeUndefined();
  });
});
