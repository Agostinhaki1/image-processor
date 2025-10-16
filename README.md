# Image Processor Service

Microserviço para processar imagens do Instagram com texto sobreposto.

## Endpoints

- `GET /` - Informações da API
- `GET /health` - Health check
- `POST /process-slide` - Processar slide
- `GET /download/<filename>` - Baixar imagem gerada

## Deploy

Deploy automático via Easypanel conectado ao GitHub.
```

---

### **PASSO 5: CONFIGURAR NO EASYPANEL**

Depois de criar o repositório no GitHub:

1. **No Easypanel, em "Source":**
   - Repository: `https://github.com/seu-usuario/image-processor`
   - Branch: `main`
   - Build Method: `Dockerfile`

2. **Em "Domains":**
   - Clique em **Add Domain**
   - Escolha: **Generate Domain** (vai gerar algo como `image-processor.easypanel.host`)
   - **OU** use domínio customizado

3. **Em "Resources":**
   - **CPU:** 0.5 (pode aumentar depois)
   - **Memory:** 512 MB (pode aumentar depois)

4. **Em "Environment Variables"** (se precisar):
```
   FLASK_ENV=production
   PYTHONUNBUFFERED=1
