import { describe, expect, it } from "vitest";
import { SessionStateStore } from "../src/realtime/session-state";

describe("SessionStateStore", () => {
  it("notifies listeners with status transitions", () => {
    const store = new SessionStateStore();
    const statuses: string[] = [];
    store.subscribe((snapshot) => statuses.push(snapshot.status));

    store.update("connecting", "\u8fde\u63a5\u4e2d");
    store.update("ready", "\u4f1a\u8bdd\u5df2\u5c31\u7eea", { sessionId: "session-1" });

    expect(statuses).toEqual(["idle", "connecting", "ready"]);
    expect(store.current().sessionId).toBe("session-1");
  });

  it("accumulates streaming assistant text into a final message", () => {
    const store = new SessionStateStore();

    store.receiveAssistantTextDelta("\u4f60\u597d\uff0c");
    store.receiveAssistantTextDelta("\u7ee7\u7eed\u8bf4");
    expect(store.current().assistantDraft).toBe("\u4f60\u597d\uff0c\u7ee7\u7eed\u8bf4");

    store.receiveAssistantTextDone("\u4f60\u597d\uff0c\u7ee7\u7eed\u8bf4");
    expect(store.current().assistantDraft).toBe("");
    expect(store.current().assistantMessages).toEqual(["\u4f60\u597d\uff0c\u7ee7\u7eed\u8bf4"]);
  });

  it("tracks turn hints and clears assistant draft when cancelled", () => {
    const store = new SessionStateStore();

    store.receiveAssistantTextDelta("\u8349\u7a3f");
    store.receiveTurnState("hint", "\u5982\u679c\u4f60\u6ca1\u6709\u66f4\u591a\u8981\u8865\u5145\u7684\uff0c\u6211\u5c06\u7ee7\u7eed\u4e0b\u4e00\u9898\u3002");
    expect(store.current().turnState).toBe("\u6700\u540e\u7b49\u5f85\u4e2d");
    expect(store.current().turnHint).toBe("\u5982\u679c\u4f60\u6ca1\u6709\u66f4\u591a\u8981\u8865\u5145\u7684\uff0c\u6211\u5c06\u7ee7\u7eed\u4e0b\u4e00\u9898\u3002");

    store.receiveAssistantCancelled("\u7528\u6237\u91cd\u65b0\u5f00\u53e3");
    expect(store.current().assistantDraft).toBe("");
    expect(store.current().turnState).toBe("\u6b63\u5728\u8046\u542c");
    expect(store.current().turnHint).toBeUndefined();
  });
});
