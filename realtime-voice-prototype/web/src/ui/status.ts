import type { ConnectionStatus, SessionStateStore } from "../realtime/session-state";

const labels: Record<ConnectionStatus, string> = {
  idle: "\u672a\u8fde\u63a5",
  connecting: "\u8fde\u63a5\u4e2d",
  ready: "\u4f1a\u8bdd\u5df2\u5c31\u7eea",
  ended: "\u4f1a\u8bdd\u5df2\u7ed3\u675f",
  error: "\u8fde\u63a5\u5f02\u5e38",
};

export class StatusPanel {
  constructor(
    private readonly host: HTMLElement,
    private readonly state: SessionStateStore,
  ) {}

  render(): void {
    this.state.subscribe((snapshot) => {
      this.host.innerHTML = `
        <div class="status-card ${snapshot.status}">
          <div>
            <p class="label">\u4f1a\u8bdd\u72b6\u6001</p>
            <strong>${labels[snapshot.status]}</strong>
          </div>
          <span class="signal" aria-hidden="true"></span>
        </div>
        <p class="session-id">${snapshot.sessionId ? `\u4f1a\u8bdd ID: ${snapshot.sessionId}` : "\u7b49\u5f85\u5f00\u59cb\u4e00\u8f6e\u65b0\u4f1a\u8bdd"}</p>
      `;
    });
  }
}
