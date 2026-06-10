# Production Deploy

这份 README 只讲一件事：

```text
怎么把 AI 面试训练项目，按你现在这台已经在跑其他项目的服务器方式，上线成一个可用版本。
```

这次采用的是你当前最合适的上线方式：

- 不新起第二套 Nginx
- 不改成新子域名
- 继续复用 `catal.online`
- 用路径区分这个项目
- 先不上 RAG
- 先把主链路跑通

当前对外访问路径固定为：

```text
前端：https://catal.online/ai-interview-studio-2606/
后端：https://catal.online/ai-interview-gateway-2606/
LiveKit：wss://catal.online/ai-interview-realtime-2606
```

---

## 1. 先明确你现在的服务器结构

你现在服务器根目录大致是这种结构：

```text
docker-compose.yml
nginx/
wechat/
my_blog/
mysql_data/
chem_project/
ai_chem/
```

这次上线不会推翻你现有结构，只是在这套结构上继续加服务。

新增的服务名是：

```text
ai-interview-web
ai-interview-token-api
ai-interview-agent
ai-interview-livekit
```

---

## 2. 这次上线你到底要改哪些东西

真正要改的核心只有 4 个东西：

```text
1. docker-compose.yml
2. nginx/nginx.conf
3. .env.production
4. ai_interview/livekit/livekit.yaml
```

其中前两个你已经有“完整版本”了，后两个我也已经给你生成好了。

---

## 3. 哪些文件我已经帮你准备好了

### 3.1 已经改好的完整 `docker-compose.yml`

你桌面这个文件已经被我改好了：

```text
C:\Users\44818\Desktop\docker-compose.yml
```

这个文件里已经包含了新增服务：

- `ai-interview-web`
- `ai-interview-token-api`
- `ai-interview-agent`
- `ai-interview-livekit`

也就是说，你不用自己再拼服务块。

### 3.2 已经改好的完整 `nginx.conf`

你桌面这个文件也已经被我改好了：

```text
C:\Users\44818\Desktop\nginx.conf
```

这个文件里已经包含了 3 个路径转发：

- `/ai-interview-studio-2606/`
- `/ai-interview-gateway-2606/`
- `/ai-interview-realtime-2606/`

所以你也不用自己再手写 `location`。

### 3.3 已经生成好的生产环境变量文件

我已经给你生成好了这份文件：

```text
livekit-interview-spike/deploy/generated/.env.production
```

里面已经写好了你这次上线要用的核心配置，包括：

- `WEB_IMAGE`
- `SERVER_IMAGE`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `LIVEKIT_URL`
- `DEEPSEEK_API_KEY`
- `BOCHA_API_KEY`
- `TAVILY_API_KEY`
- `CORS_ALLOW_ORIGINS`
- `PRO_FOLLOWUP_RAG_ENABLED=false`

这份文件是直接给服务器用的。

### 3.4 已经生成好的 LiveKit 生产配置

我也已经给你生成好了：

```text
livekit-interview-spike/deploy/generated/livekit.yaml
```

这个文件就是服务器上的 LiveKit 配置文件。

---

## 4. 这次为什么先不上 RAG

原因很简单：你服务器空间不够，当前不适合先上本地 embedding 模型。

所以这次我已经按“低空间上线版”处理好了：

```text
默认不启动 qdrant
默认不启动 embedding-service
默认关闭 RAG
```

也就是说，这次你不需要：

- 下载 `bge-m3`
- 部署 Qdrant
- 部署 embedding service
- 处理向量库初始化

你先把主流程跑起来：

- 公司搜索
- 岗位 JD
- 实时面试
- 追问
- 结果报告

这样最稳。

---

## 5. 本地要先做什么

这一步是在你自己的电脑上完成，不是在服务器上完成。

### 5.1 打开 WSL

进入你的项目目录：

```bash
cd /mnt/d/面试训练/livekit-interview-spike
```

### 5.2 登录阿里云 ACR

执行：

```bash
docker login --username=yourname crpi-zapnyuqlrws037uw.cn-shanghai.personal.cr.aliyuncs.com
```

这里的 `yourname` 换成你自己的阿里云镜像仓库登录用户名。

### 5.3 设置镜像构建变量

执行：

```bash
export ACR_REGISTRY=crpi-zapnyuqlrws037uw.cn-shanghai.personal.cr.aliyuncs.com
export ACR_NAMESPACE=chemtutor
export IMAGE_VERSION=v1
export VITE_API_BASE_URL=https://catal.online/ai-interview-gateway-2606
export VITE_BASE_PATH=/ai-interview-studio-2606/
```

解释一下这几个变量：

- `ACR_REGISTRY`：你的阿里云镜像仓库地址
- `ACR_NAMESPACE`：你的命名空间
- `IMAGE_VERSION`：这次发版的版本号
- `VITE_API_BASE_URL`：前端上线后请求的后端地址
- `VITE_BASE_PATH`：前端部署在主域名下的子路径

### 5.4 构建并推送镜像

执行：

```bash
bash deploy/scripts/acr-build-push.sh
```

它会构建并推送两个镜像：

```text
interview-web
interview-server
```

其中：

- `interview-web` 是前端
- `interview-server` 是后端镜像，`token_server.py` 和 `agent.py` 共用它

### 5.5 如果你以后要发新版

只需要改版本号：

```bash
export IMAGE_VERSION=v2
```

然后重新执行：

```bash
bash deploy/scripts/acr-build-push.sh
```

---

## 6. 服务器上要准备什么目录

登录服务器后，进入你平时放 `docker-compose.yml` 的根目录。

然后只需要创建这个目录：

```text
ai_interview/livekit/
```

如果没有，就执行：

```bash
mkdir -p ai_interview/livekit
```

这次先不上 RAG，所以你现在不需要准备：

```text
ai_interview/models/bge-m3/
ai_interview/data/qdrant/
ai_interview/data/tei/
```

---

## 7. 服务器上到底要上传哪些文件

这一步最关键。

你只需要把下面 4 个文件上传到服务器对应位置。

### 7.1 上传 `docker-compose.yml`

本地来源：

```text
C:\Users\44818\Desktop\docker-compose.yml
```

上传到服务器：

```text
服务器根目录/docker-compose.yml
```

直接覆盖服务器原来的那个同名文件。

### 7.2 上传 `nginx.conf`

本地来源：

```text
C:\Users\44818\Desktop\nginx.conf
```

上传到服务器：

```text
服务器根目录/nginx/nginx.conf
```

直接覆盖服务器原来的那个同名文件。

### 7.3 上传 `.env.production`

本地来源：

```text
livekit-interview-spike/deploy/generated/.env.production
```

上传到服务器：

```text
服务器根目录/.env.production
```

### 7.4 上传 `livekit.yaml`

本地来源：

```text
livekit-interview-spike/deploy/generated/livekit.yaml
```

上传到服务器：

```text
服务器根目录/ai_interview/livekit/livekit.yaml
```

---

## 8. 上传完以后怎么启动

进入服务器根目录后，先拉镜像：

```bash
docker compose --env-file .env.production pull ai-interview-web ai-interview-token-api ai-interview-agent ai-interview-livekit
```

然后启动：

```bash
docker compose --env-file .env.production up -d ai-interview-web ai-interview-token-api ai-interview-agent ai-interview-livekit nginx
```

查看状态：

```bash
docker compose --env-file .env.production ps
```

你应该至少看到这些服务是 `Up`：

```text
ai-interview-web
ai-interview-token-api
ai-interview-agent
ai-interview-livekit
nginx
```

---

## 9. 启动后怎么查日志

### 9.1 看后端 API

```bash
docker compose --env-file .env.production logs -f ai-interview-token-api
```

### 9.2 看面试 Agent

```bash
docker compose --env-file .env.production logs -f ai-interview-agent
```

### 9.3 看 LiveKit

```bash
docker compose --env-file .env.production logs -f ai-interview-livekit
```

### 9.4 看 Nginx

```bash
docker compose --env-file .env.production logs -f nginx
```

---

## 10. 上线后怎么验证到底成没成功

### 10.1 先看前端能不能打开

浏览器访问：

```text
https://catal.online/ai-interview-studio-2606/
```

如果页面能打开，说明前端路径转发没问题。

### 10.2 再看后端健康检查

浏览器访问：

```text
https://catal.online/ai-interview-gateway-2606/health
```

如果能返回健康检查结果，说明 API 是通的。

### 10.3 再实际跑一轮

最少要测这些：

1. 打开配置流程页面
2. 完成公司信息配置
3. 完成岗位配置
4. 进入面试房间
5. 听到 AI 开场
6. 用户说话后能转写
7. AI 能继续追问
8. 面试结束后能生成结果页

---

## 11. 出问题时优先查哪里

### 11.1 前端打不开，或者是白屏

先看：

```bash
docker compose --env-file .env.production logs -f ai-interview-web
docker compose --env-file .env.production logs -f nginx
```

常见原因：

- 前端镜像不是最新版
- `VITE_BASE_PATH` 配错
- Nginx 没正确转发 `/ai-interview-studio-2606/`

### 11.2 `/health` 打不开

看：

```bash
docker compose --env-file .env.production logs -f ai-interview-token-api
```

常见原因：

- `.env.production` 没传上去
- `SERVER_IMAGE` 写错
- token API 没有启动成功

### 11.3 页面能打开，但进不了实时房间

看：

```bash
docker compose --env-file .env.production logs -f ai-interview-livekit
docker compose --env-file .env.production logs -f ai-interview-agent
```

常见原因：

- `LIVEKIT_API_KEY` 和 `LIVEKIT_API_SECRET` 不一致
- `ai_interview/livekit/livekit.yaml` 没传对
- LiveKit 服务没起来
- 服务器端口没放通

### 11.4 页面能打开，但接口跨域报错

检查服务器上的 `.env.production` 里是否正确：

```env
CORS_ALLOW_ORIGINS=https://catal.online
```

---

## 12. 这次为什么不改代码里的 localhost

因为那些本来就是本地开发默认值，保留它们反而是对的。

当前代码里保留的本地默认包括：

```text
http://127.0.0.1:8787
ws://localhost:7880
http://localhost:6333
http://localhost:8080/v1
```

它们只在本地开发时兜底使用。

服务器上线时，真正生效的是：

- 前端构建时传入的 `VITE_API_BASE_URL`
- 前端构建时传入的 `VITE_BASE_PATH`
- 服务器上的 `.env.production`
- Nginx 的路径转发

所以：

- 本地测试不会坏
- 服务器上线也不会误用 localhost

---

## 13. 这次最短执行顺序

如果你只想按最短路径做，直接照这个顺序：

1. 本地打开 WSL，进入 `livekit-interview-spike`
2. 登录阿里云 ACR
3. 设置 `ACR_REGISTRY`、`ACR_NAMESPACE`、`IMAGE_VERSION`
4. 设置 `VITE_API_BASE_URL` 和 `VITE_BASE_PATH`
5. 执行 `bash deploy/scripts/acr-build-push.sh`
6. 用 Xftp 把桌面上的 `docker-compose.yml` 上传覆盖服务器根目录同名文件
7. 用 Xftp 把桌面上的 `nginx.conf` 上传覆盖服务器 `nginx/nginx.conf`
8. 把 `deploy/generated/.env.production` 上传到服务器根目录
9. 把 `deploy/generated/livekit.yaml` 上传到服务器 `ai_interview/livekit/livekit.yaml`
10. 用 Xshell 进入服务器根目录
11. 执行 `docker compose --env-file .env.production pull ai-interview-web ai-interview-token-api ai-interview-agent ai-interview-livekit`
12. 执行 `docker compose --env-file .env.production up -d ai-interview-web ai-interview-token-api ai-interview-agent ai-interview-livekit nginx`
13. 打开 `https://catal.online/ai-interview-studio-2606/`
14. 访问 `https://catal.online/ai-interview-gateway-2606/health`
15. 实际跑一轮面试流程

---

## 14. 以后如果你要补 RAG

等你以后服务器空间够了，再做这几件事：

1. 下载并准备 embedding 模型
2. 启动 `qdrant`
3. 启动 `embedding-service`
4. 打开 `PRO_FOLLOWUP_RAG_ENABLED`
5. 执行资料入库

但这些都不是这次上线必须做的。

这次最重要的目标只有一个：

```text
先把不带 RAG 的完整可用版本，稳定上线。
```
