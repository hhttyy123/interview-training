# 服务器部署思路与上线检查

更新时间：2026-06-09

本文档面向当前 `livekit-interview-spike` 版本，目标是按你已有习惯上线：本地或 WSL 构建镜像，推送到阿里云容器镜像服务 ACR，再用 Xshell 登录服务器执行 `docker compose pull && docker compose up -d`。

## 1. 推荐上线形态

当前项目不要用“服务器手动开多个窗口”的方式上线。生产版本建议拆成这些服务：

```text
browser
-> existing nginx on catal.online
-> ai-interview-web: 前端静态站点
-> ai-interview-token-api: FastAPI token_server.py
-> ai-interview-livekit: LiveKit Server
-> ai-interview-agent: agent.py 常驻进程
-> optional rag profile:
-> ai-interview-qdrant: 向量库
-> ai-interview-embedding: TEI + BGE-M3
```

其中 `ai-interview-qdrant`、`ai-interview-embedding`、`ai-interview-livekit` 可以直接用官方镜像；`ai-interview-web`、`ai-interview-token-api`、`ai-interview-agent` 使用本项目自己的镜像。

当前已准备生产模板：

- `livekit-interview-spike/deploy/docker-compose.prod.yml`
- `livekit-interview-spike/deploy/docker-compose.existing-server.snippet.yml`
- `livekit-interview-spike/deploy/Dockerfile.web`
- `livekit-interview-spike/deploy/Dockerfile.server`
- `livekit-interview-spike/deploy/nginx/nginx.conf`
- `livekit-interview-spike/deploy/nginx/interview-location-snippet.conf`
- `livekit-interview-spike/deploy/caddy/Caddyfile`
- `livekit-interview-spike/deploy/livekit/livekit.yaml`
- `livekit-interview-spike/deploy/.env.production.example`
- `livekit-interview-spike/deploy/scripts/acr-build-push.sh`
- `livekit-interview-spike/deploy/scripts/server-pull-up.sh`
- `livekit-interview-spike/deploy/scripts/server-pull-up-existing-root.sh`
- `livekit-interview-spike/deploy/scripts/smoke-test.sh`

真实密钥文件不进入 Git。当前生成位置：

- `livekit-interview-spike/deploy/generated/.env.production`
- `livekit-interview-spike/deploy/generated/livekit.yaml`

上传服务器时分别放到服务器根目录 `.env.production` 和 `ai_interview/livekit/livekit.yaml`。

## 2. 和你之前部署习惯的对应关系

你的旧流程是：

```text
本地/WSL 构建镜像
-> docker login 阿里云 ACR
-> docker push 到 ACR
-> Xshell 登录服务器
-> docker compose pull
-> docker compose up -d
-> 浏览器/F12/日志排错
```

这个项目也建议沿用这条链路，只是镜像会从一个变成多个：

```text
crpi-xxx.cn-shanghai.personal.cr.aliyuncs.com/你的命名空间/interview-web:版本号
crpi-xxx.cn-shanghai.personal.cr.aliyuncs.com/你的命名空间/interview-api:版本号
crpi-xxx.cn-shanghai.personal.cr.aliyuncs.com/你的命名空间/interview-agent:版本号
```

不建议把 `server/models/bge-m3` 打进 Git；模型可以在服务器上单独下载或用 Xftp 上传到服务器挂载目录。

## 3. 服务器目录建议

服务器上建议固定目录：

```text
/opt/interview-training/
  docker-compose.prod.yml
  .env.production
  nginx/
    nginx.conf
    certs/
  livekit/
    livekit.yaml
  data/
    qdrant/
    tei/
  models/
    bge-m3/
  scripts/
```

`models/bge-m3` 必须包含：

```text
config.json
pytorch_model.bin
tokenizer.json
1_Pooling/config.json
```

## 4. 环境变量清单

生产环境必须单独准备 `.env.production`：

```env
LIVEKIT_URL=wss://catal.online/ai-interview-realtime-2606
LIVEKIT_API_KEY=replace_with_real_key
LIVEKIT_API_SECRET=replace_with_real_secret
LIVEKIT_AGENT_NAME=interview-coach
LIVEKIT_ROOM=interview-spike-room
LIVEKIT_TOKEN_TTL_SECONDS=3600

CORS_ALLOW_ORIGINS=https://catal.online

DEEPSEEK_API_KEY=replace_with_deepseek_key
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com

COMPANY_SEARCH_PROVIDER=bocha
BOCHA_API_KEY=replace_with_bocha_key

QDRANT_URL=http://ai-interview-qdrant:6333
QDRANT_COLLECTION=interview_methodology
RAG_EMBEDDING_PROVIDER=openai_compatible
RAG_EMBEDDING_BASE_URL=http://ai-interview-embedding/v1
RAG_EMBEDDING_API_KEY=local
RAG_EMBEDDING_MODEL=/models/bge-m3
RAG_EMBEDDING_DIMENSION=1024
RAG_EMBEDDING_TIMEOUT_SECONDS=120

PRO_FOLLOWUP_ENABLED=true
PRO_FOLLOWUP_RAG_ENABLED=false
PRO_FOLLOWUP_FALLBACK_TO_LEGACY=true
PRO_FOLLOWUP_DEBUG=false
```

低空间上线建议保持：

```env
PRO_FOLLOWUP_RAG_ENABLED=false
```

这样即使暂时不部署 `ai-interview-qdrant` 和 `ai-interview-embedding`，主流程也能正常上线。

前端构建时需要：

```env
VITE_API_BASE_URL=https://catal.online/ai-interview-gateway-2606
VITE_BASE_PATH=/ai-interview-studio-2606/
```

否则浏览器会默认请求本机 `http://127.0.0.1:8787`，服务器部署后一定会失败。

## 5. 三档追问模式上线建议

当前已接入三档模式，入口在配置流程第 4 步“选择面试风格”：

```text
极速稳定：旧版追问提示词，不跑 answer_gap，不跑 RAG。推荐当前上线试运行。
平衡策略：answer_gap + 策略卡，不跑 RAG。标注开发中，用于内部对比。
专业增强：answer_gap + 策略卡 + RAG。标注效果待优化，用于调试，不建议默认给真实用户。
```

上线默认建议：

```text
默认选择：极速稳定
调试人员可切换：平衡策略 / 专业增强
RAG 总开关：先关闭，等检索 raw/filtered 和延迟稳定后再考虑默认开启
```

## 6. 端口和域名

当前采用同域名非常规路径，避免和主域名已有项目冲突：

```text
https://catal.online/ai-interview-studio-2606/       -> 前端
https://catal.online/ai-interview-gateway-2606/      -> token-api
wss://catal.online/ai-interview-realtime-2606        -> LiveKit WebSocket
```

如果 `catal.online` 已经有项目和 Nginx 在运行，不要再启动一个新的 Nginx 绑定 `80/443`。当前 `docker-compose.prod.yml` 已把内置 `nginx` 放进 `edge` profile，默认不会启动。应把 `deploy/nginx/interview-location-snippet.conf` 合并进现有 Nginx 的 `catal.online` HTTPS `server` 块，并确保现有 Nginx 能访问 `ai-interview-web`、`ai-interview-token-api`、`ai-interview-livekit` 这几个容器。

如果并入你现有的服务器根目录结构，优先使用 `deploy/docker-compose.existing-server.snippet.yml`。它使用 `chem-network`，服务名是 `ai-interview-web`、`ai-interview-token-api`、`ai-interview-agent`、`ai-interview-livekit`、`ai-interview-qdrant`、`ai-interview-embedding`，避免和现有 `blog`、`mysql`、`ai-chem-backend` 等服务冲突。

服务器安全组至少需要：

```text
80/tcp
443/tcp
7880/tcp
7881/tcp
7882/udp
```

如果使用 TURN，还需要按 TURN 配置开放对应 UDP/TCP 端口。不要把下面服务裸露公网：

```text
6333  Qdrant
8080  Embedding service
```

## 7. 上线步骤

### 7.1 本地或 WSL 构建并推送镜像

```bash
cd /mnt/d/面试训练/livekit-interview-spike
docker login --username=yourname crpi-xxx.cn-shanghai.personal.cr.aliyuncs.com
export ACR_REGISTRY=crpi-xxx.cn-shanghai.personal.cr.aliyuncs.com
export ACR_NAMESPACE=your_namespace
export IMAGE_VERSION=v1
export VITE_API_BASE_URL=https://catal.online/ai-interview-gateway-2606
export VITE_BASE_PATH=/ai-interview-studio-2606/
bash deploy/scripts/acr-build-push.sh
```

当前使用两个镜像：`interview-web` 和 `interview-server`。`interview-server` 同时用于 `token-api` 和 `agent`，避免重复构建 Python 依赖。

### 7.2 Xshell 登录服务器拉取并启动

```bash
cd /opt/interview-training
cp .env.production.example .env.production
vim .env.production
vim nginx/nginx.conf
vim livekit/livekit.yaml
chmod +x scripts/*.sh
bash scripts/server-pull-up.sh
```

默认只启动主链路服务，不启动 RAG 相关容器。

如果以后空间够了，再启动 RAG profile：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml --profile rag up -d ai-interview-qdrant ai-interview-embedding
```

### 7.3 查看日志

```bash
docker compose -f docker-compose.prod.yml logs -f ai-interview-token-api
docker compose -f docker-compose.prod.yml logs -f ai-interview-agent
docker compose -f docker-compose.prod.yml logs -f ai-interview-livekit
```

如果启用了 RAG，再看：

```bash
docker compose -f docker-compose.prod.yml logs -f ai-interview-qdrant
docker compose -f docker-compose.prod.yml logs -f ai-interview-embedding
```

### 7.4 Smoke test

```bash
cd /opt/interview-training
export APP_URL=https://catal.online/ai-interview-studio-2606
export API_URL=https://catal.online/ai-interview-gateway-2606
export LIVEKIT_URL=wss://catal.online/ai-interview-realtime-2606
bash scripts/smoke-test.sh
```

## 8. 上线检查表

### P0 必须通过

- 前端 `npm exec tsc -- --noEmit` 通过。
- 后端项目 Python 文件 `py_compile` 通过。
- 前端 API 地址已使用 `VITE_API_BASE_URL`，不能硬编码 `127.0.0.1`。
- `CORS_ALLOW_ORIGINS` 只包含正式前端域名。
- `LIVEKIT_URL` 使用 `wss://` 正式域名。
- LiveKit 不能继续使用 `--dev` 配置。
- `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` 使用正式强密钥。
- `DEEPSEEK_API_KEY`、`BOCHA_API_KEY` 放在服务器 `.env.production`，不提交 Git。
- Qdrant volume 持久化。
- BGE-M3 模型文件在服务器挂载目录，不提交 Git。
- Qdrant 和 Embedding 不暴露公网。
- `token-api`、`agent` 崩溃后能自动重启。
- 默认追问模式使用“极速稳定”，不要把专业增强作为默认上线模式。

### P1 强烈建议

- 增加生产 `docker-compose.prod.yml`。
- 增加 `web.Dockerfile`、`server.Dockerfile`、`agent.Dockerfile`。
- 增加 Nginx/Caddy 反向代理配置。
- 增加 `/health` 扩展检查：DeepSeek、Bocha、Qdrant、Embedding、LiveKit。
- 增加一键 smoke test 脚本。
- 增加日志保留和滚动策略。
- 增加基础限流，尤其是 `/token`、`/tts`、`/company-card`。

## 9. 当前项目检查结果

已经具备：

- 前端构建脚本：`web/package.json`
- 后端依赖：`server/requirements.txt`
- RAG compose：`docker-compose.rag.yml`
- 本地 LiveKit/Qdrant compose：`docker-compose.yml`
- RAG runbook：`docs/technical/rag-service-runbook.md`
- 追问三档模式：已接入配置页和 agent 主流程
- RAG 调试面板和总开关：已接入
- 生产 Dockerfile、compose、Nginx、LiveKit、ACR 脚本、smoke test：已准备在 `deploy/`

仍需补齐：

- 替换真实域名。
- 替换正式证书文件。
- 替换正式 LiveKit key/secret。
- 在服务器放置 BGE-M3 模型目录。
- 服务器实际拉取镜像并做一次完整面试链路验收。

## 10. 首次上线建议范围

第一版不要追求“专业增强全开”。建议先上线：

```text
公司搜索
岗位 JD 分析
基础实时语音面试
极速稳定追问
面试报告
调试台
```

暂时内部灰度：

```text
平衡策略
专业增强
RAG 默认开启
```

这样能先验证真实用户是否能顺利完成一次面试，再逐步打开复杂追问能力。
