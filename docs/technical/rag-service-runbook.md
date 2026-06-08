# RAG 服务测试与运维手册

更新时间：2026-06-08

本文档用于你自己测试 RAG：怎么启动服务、怎么指定资料切分入库、怎么检查是否入库、怎么验证检索、怎么删除数据、怎么重建。

当前商用目标架构：

```text
面试主服务
-> Qdrant 向量库
-> TEI Embedding Service
-> BAAI/bge-m3
```

当前本机实际配置：

```text
Qdrant: http://localhost:6333
Embedding: http://localhost:8080/v1
Collection: interview_methodology
Model source: BAAI/bge-m3
TEI served model name: /models/bge-m3
Dimension: 1024
```

## 1. 启动 RAG 服务

### 1.1 WSL 启动

你现在使用的是 WSL + Docker，推荐在 WSL 里运行：

```bash
cd /mnt/d/面试训练/livekit-interview-spike
docker compose -f docker-compose.rag.yml up -d
```

查看服务状态：

```bash
cd /mnt/d/面试训练/livekit-interview-spike
docker compose -f docker-compose.rag.yml ps
```

查看 embedding 日志：

```bash
cd /mnt/d/面试训练/livekit-interview-spike
docker compose -f docker-compose.rag.yml logs -f embedding-service
```

查看 Qdrant 日志：

```bash
cd /mnt/d/面试训练/livekit-interview-spike
docker compose -f docker-compose.rag.yml logs -f qdrant
```

停止服务：

```bash
cd /mnt/d/面试训练/livekit-interview-spike
docker compose -f docker-compose.rag.yml down
```

### 1.2 Ubuntu 服务器启动

服务器上同样运行：

```bash
cd /你的项目目录/livekit-interview-spike
docker compose -f docker-compose.rag.yml up -d
```

生产环境不要把 `6333` 和 `8080` 裸露到公网。建议只允许内网访问，或者放到反向代理和安全组后面。

## 2. 环境变量

Windows 本地 Python 服务连接 WSL Docker 时，`.env` 使用：

```env
RAG_VECTOR_STORE=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=interview_methodology

RAG_EMBEDDING_PROVIDER=openai_compatible
RAG_EMBEDDING_BASE_URL=http://localhost:8080/v1
RAG_EMBEDDING_API_KEY=local
RAG_EMBEDDING_MODEL=/models/bge-m3
RAG_EMBEDDING_DIMENSION=1024

RAG_CHUNK_SIZE=900
RAG_CHUNK_OVERLAP=120
RAG_RETRIEVAL_LIMIT=6
```

如果未来面试主服务也放进 Docker 网络里，改成容器名：

```env
QDRANT_URL=http://qdrant:6333
RAG_EMBEDDING_BASE_URL=http://embedding-service/v1
```

## 3. 模型目录

当前 compose 挂载的是：

```text
livekit-interview-spike/server/models/bge-m3
```

容器内路径是：

```text
/models/bge-m3
```

必须能看到：

```text
server/models/bge-m3/config.json
server/models/bge-m3/pytorch_model.bin
server/models/bge-m3/tokenizer.json
```

如果缺文件，重新下载：

```powershell
cd D:\面试训练\livekit-interview-spike\server
modelscope download --model BAAI/bge-m3 --local_dir models\bge-m3
```

模型文件不要提交到 git，`server/models/.gitignore` 已经忽略。

## 4. 资料格式

入库资料使用 JSONL，每行一条：

```json
{"source_id":"star-bei-001","title":"STAR 与 BEI 行为事件采证","content":"方法论正文","source_type":"internal_note","license_note":"项目内部整理的方法论卡片","metadata":{"strategy_categories":["evidence_probe"],"role_families":["general"],"competency_archetypes":["execution_delivery"],"evidence_categories":["action","result"]}}
```

关键字段：

- `source_id`：稳定唯一 ID，不要随便改。
- `title`：资料标题。
- `content`：要切分和向量化的正文。
- `source_type`：资料类型，比如 `internal_note`、`book_note`、`paper`、`article`。
- `license_note`：授权和来源说明。
- `metadata.strategy_categories`：适用策略类型。
- `metadata.role_families`：适用职业族。
- `metadata.competency_archetypes`：适用能力原型。
- `metadata.evidence_categories`：适用证据类型。

当前示例资料：

```text
server/data/methodology.example.jsonl
```

当前文档解析测试资料：

```text
server/data/docs/star-bei-test.md
server/data/docs/pressure-attribution-test.txt
server/data/docs/business-case-test.md
server/data/docs/technical-deep-dive-test.docx
server/data/docs/methodology-text-layer-test.pdf
server/data/docs/pdf-parse-smoke-test.pdf
```

其中 `methodology-text-layer-test.pdf` 是带真实文本层的 PDF，可用于验证 PDF 正文抽取。`pdf-parse-smoke-test.pdf` 是空白页烟雾测试文件，只用于确认 PDF 文件读取链路，不适合验证正文抽取质量。真实业务 PDF 请优先使用带文本层的 PDF，不建议使用纯扫描图片 PDF。

当前评测集：

```text
server/data/methodology.eval.jsonl
```

## 5. 指定切分参数入库

基础入库：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_methodology.py --file data\methodology.example.jsonl
```

指定切分大小和重叠：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_methodology.py --file data\methodology.example.jsonl --chunk-size 900 --chunk-overlap 120
```

指定更小切分，适合短方法论卡片：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_methodology.py --file data\methodology.example.jsonl --chunk-size 500 --chunk-overlap 80
```

指定更大切分，适合章节笔记：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_methodology.py --file data\methodology.example.jsonl --chunk-size 1200 --chunk-overlap 180
```

指定 batch size：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_methodology.py --file data\methodology.example.jsonl --batch-size 16
```

成功输出类似：

```text
Ingested 5 sources / 5 chunks into Qdrant collection 'interview_methodology'.
```

## 6. 直接导入 md / txt / pdf / docx

支持格式：

```text
.txt
.md
.markdown
.pdf
.docx
```

导入单个 Markdown 文件：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_documents.py --path data\docs\star.md --strategy-categories evidence_probe,clarification --role-families general --competency-archetypes execution_delivery --evidence-categories action,result,metric
```

导入整个目录：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_documents.py --path data\docs --strategy-categories evidence_probe,depth_probe --role-families general --chunk-size 900 --chunk-overlap 120
```

导入当前准备好的测试文档目录：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_documents.py --path data\docs --source-type internal_note --license-note "项目测试资料" --strategy-categories evidence_probe,depth_probe,pressure,reflection --role-families general,engineering,product_business --competency-archetypes execution_delivery,analytical_reasoning,technical_depth,commercial_judgment --evidence-categories action,result,metric,decision,risk,technical_depth,business_judgment --chunk-size 900 --chunk-overlap 120
```

导入 PDF：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_documents.py --path data\docs\interview-method.pdf --source-type book_note --license-note "用户整理笔记，仅内部使用" --strategy-categories evidence_probe --role-families general
```

导入当前测试 PDF：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_documents.py --path data\docs\methodology-text-layer-test.pdf --source-type internal_note --license-note "项目 PDF 测试资料" --strategy-categories evidence_probe,depth_probe,pressure --role-families general,engineering,product_business --competency-archetypes execution_delivery,analytical_reasoning,technical_depth,commercial_judgment --evidence-categories action,result,metric,decision,risk,technical_depth,business_judgment
```

导入 Word / docx：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_documents.py --path data\docs\interview-method.docx --source-type internal_note --license-note "用户提供资料" --strategy-categories evidence_probe,reflection --role-families general
```

参数说明：

- `--path`：文件或目录路径。
- `--source-type`：资料类型，比如 `internal_note`、`book_note`、`paper`。
- `--license-note`：来源和授权说明。
- `--strategy-categories`：逗号分隔的策略类型。
- `--role-families`：逗号分隔的职业族，默认 `general`。
- `--competency-archetypes`：逗号分隔的能力原型。
- `--evidence-categories`：逗号分隔的证据类型。
- `--chunk-size`：切分大小。
- `--chunk-overlap`：切分重叠。

注意：`.doc` 老 Word 格式暂不支持，请先另存为 `.docx`。

## 7. 检查是否入库

### 6.1 用 Python 检查 collection 数量

```powershell
cd D:\面试训练\livekit-interview-spike\server
python -c "from dotenv import load_dotenv; load_dotenv('../.env'); from interview.followup.rag.qdrant_store import qdrant_store_from_env; s=qdrant_store_from_env(); print(s.collection_name, s.client.count(s.collection_name, exact=True).count)"
```

如果输出：

```text
interview_methodology 5
```

说明当前 collection 有 5 条 chunk。

### 6.2 查看前几条 payload

```powershell
cd D:\面试训练\livekit-interview-spike\server
python -c "from dotenv import load_dotenv; load_dotenv('../.env'); from interview.followup.rag.qdrant_store import qdrant_store_from_env; s=qdrant_store_from_env(); points,_=s.client.scroll(collection_name=s.collection_name, limit=5, with_payload=True); [print(p.payload.get('source_id'), p.payload.get('title')) for p in points]"
```

## 8. 检验是否能检索

运行评测集：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\evaluate_methodology_retrieval.py --file data\methodology.eval.jsonl
```

重点看：

```text
hit@1
hit@3
hit@5
mrr
```

当前示例集跑通时应该接近：

```text
hit@1: 1.000
hit@3: 1.000
hit@5: 1.000
mrr: 1.000
```

注意：示例集很小，不能代表商用真实质量。商用前应该扩充到至少 50-100 条真实追问场景。

## 9. 手动检索一个 query

可以临时新增一条评测 JSONL，例如 `server/data/my.eval.jsonl`：

```json
{"query_id":"my-test-001","query":"候选人说指标提升了，但没有说明归因，应该如何追问？","expected_source_ids":["pressure-attribution-001"],"strategy_category":"pressure","role_family":"general","competency_archetypes":["analytical_reasoning"],"evidence_categories":["metric","result","risk"]}
```

然后运行：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\evaluate_methodology_retrieval.py --file data\my.eval.jsonl
```

## 10. 删除数据

### 9.1 删除整个 collection

这会删除 `interview_methodology` 里的全部向量数据：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python -c "from dotenv import load_dotenv; load_dotenv('../.env'); from interview.followup.rag.qdrant_store import qdrant_store_from_env; s=qdrant_store_from_env(); s.client.delete_collection(s.collection_name); print('deleted', s.collection_name)"
```

删除后检查：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python -c "from dotenv import load_dotenv; load_dotenv('../.env'); from interview.followup.rag.qdrant_store import qdrant_store_from_env; s=qdrant_store_from_env(); print(s.client.collection_exists(s.collection_name))"
```

应该输出：

```text
False
```

### 9.2 删除后重新入库

```powershell
cd D:\面试训练\livekit-interview-spike\server
python scripts\ingest_methodology.py --file data\methodology.example.jsonl
```

### 9.3 删除 Qdrant Docker volume

如果你要彻底清空 Qdrant 持久化数据，在 WSL 里运行：

```bash
cd /mnt/d/面试训练/livekit-interview-spike
docker compose -f docker-compose.rag.yml down -v
```

注意：`down -v` 会删除 compose 管理的 volume，所有 Qdrant 数据会丢失。

## 11. 常见问题

### 10.1 `config.json not found`

说明模型目录挂载成功了，但目录里没有模型文件。

检查：

```powershell
cd D:\面试训练\livekit-interview-spike\server
dir models\bge-m3\config.json
```

没有就重新下载模型。

### 10.2 `Could not download model artifacts`

说明 TEI 容器直接下载 HuggingFace 模型失败。

当前方案不依赖容器下载，而是本地模型目录挂载。确认 compose 里有：

```yaml
- ./server/models/bge-m3:/models/bge-m3:ro
```

### 10.3 `Header content-range is missing`

说明镜像站响应和 TEI 下载器不兼容。不要反复重启，改用本地模型目录挂载。

### 10.4 `QdrantClient object has no attribute search`

这是 qdrant-client 版本差异。当前代码已经兼容新版 `query_points()`。

### 10.5 评测全 miss

优先检查：

```text
collection 是否有数据
payload 里是否有 strategy_categories / role_families / competency_archetypes / evidence_categories
过滤条件是否过严
```

查看 payload：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python -c "from dotenv import load_dotenv; load_dotenv('../.env'); from interview.followup.rag.qdrant_store import qdrant_store_from_env; s=qdrant_store_from_env(); points,_=s.client.scroll(collection_name=s.collection_name, limit=5, with_payload=True); [print(p.payload) for p in points]"
```

## 12. 当前还没接入什么

当前 RAG 服务、入库、检索评测已经跑通。

还没有默认接入实时面试主流程。

下一步应该做：

```text
增加 RAG 开关
-> 在追问生成前检索方法论
-> 写入 QuestionPlan.methodology_notes
-> 观察追问质量和延迟
-> 再决定是否默认开启
```
