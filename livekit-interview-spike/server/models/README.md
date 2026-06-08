# Server Model Directory

This directory is for deployment-time model assets used by RAG services.

Do not commit model weights to git. Download or mount models on each deployment target.

Expected layout:

```text
server/
  models/
    bge-m3/
      config.json
      pytorch_model.bin
      tokenizer.json
      ...
```

`docker-compose.rag.yml` mounts `./server/models/bge-m3` into the embedding service.
