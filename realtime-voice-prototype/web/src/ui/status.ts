import type { ConnectionStatus, SessionStateStore } from "../realtime/session-state";

const labels: Record<ConnectionStatus, string> = {
  idle: "未连接",
  connecting: "连接中",
  ready: "会话已就绪",
  ended: "会话已结束",
  error: "连接异常",
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
            <p class="label">SESSION STATUS</p>
            <strong>${labels[snapshot.status]}</strong>
          </div>
          <span class="signal" aria-hidden="true"></span>
        </div>
        <p class="session-id">${snapshot.sessionId ? `ID: ${snapshot.sessionId}` : "等待开始一轮新会话"}</p>
      `;
    });
  }
}
