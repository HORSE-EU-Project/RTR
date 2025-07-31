# LLM Models Directory

This directory contains the GGUF model files for the LLM server using the optimized `ghcr.io/abetlen/llama-cpp-python:server` image.

## Required Model

The LLM server expects a model file named `gemma-2b-it.Q4_K_M.gguf` by default.

## Downloading Models

You can download compatible GGUF models from Hugging Face. Here are some examples:

### Gemma 2B Instruct (Recommended)
```bash
# Navigate to the models directory
cd llm_server/models

# Download from Hugging Face
wget https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf -O gemma-2b-it.Q4_K_M.gguf
```

### Alternative Models

#### Phi-3 Mini (Smaller, faster)
```bash
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf -O gemma-2b-it.Q4_K_M.gguf
```

#### Llama 2 7B Chat (Larger, more capable)
```bash
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf -O gemma-2b-it.Q4_K_M.gguf
```

## Model Configuration

To use a different model, update the `MODEL` environment variable in the docker-compose.yml:

```yaml
environment:
  - MODEL=/models/your-model-name.gguf
```

## Server Configuration

The optimized image uses these settings:
- **Internal Port**: 8080 (to avoid conflict with RTR API)
- **External Port**: 8081 (mapped from host)
- **API**: OpenAI-compatible endpoints
- **Health check**: `/health`
- **Chat completions**: `/v1/chat/completions`
- **Completions**: `/v1/completions`

## Testing the Server

Once started with `docker-compose up --build`:

### Health Check
```bash
curl http://localhost:8081/health
```

### Chat Completion (Recommended)
```bash
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Block IP address 192.168.1.100"}
    ],
    "max_tokens": 100
  }'
```

### Legacy Completion
```bash
curl -X POST http://localhost:8081/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is cybersecurity?", 
    "max_tokens": 50
  }'
```

## Model Requirements

- **Format**: GGUF format only
- **Quantization**: Q4_K_M recommended for balance of speed and quality
- **Size**: Model should fit in available RAM (2GB+ recommended for 2B parameter models)
- **CPU**: Multi-core CPU recommended for better performance

## Benefits of This Setup

✅ **Plug-and-Play**: No compilation or complex setup  
✅ **CPU Optimized**: Built on llama.cpp for efficient CPU inference  
✅ **OpenAI Compatible**: Standard API endpoints  
✅ **Pre-optimized**: Ready-to-use with best practices  
✅ **Health Checks**: Built-in monitoring and health endpoints
