# Agent: PRISM Publish Actions (Drive + YouTube)

Resolve GitHub Issue #3: Botoes de publicacao na review (Drive + YouTube).

## Contexto

Apos gerar thumb e escolher titulo na tela de review (Step 3), o usuario precisa fazer download manual, abrir Drive, subir arquivo, abrir YouTube Studio, trocar thumb e titulo. Precisa de botoes para publicar direto.

## Arquivos

- `prism-os/nutella-creator/static/index.html`: frontend (rot-step-review)
- `prism-os/nutella-creator/dashboard.py`: novos endpoints
- Novo: `prism-os/nutella-creator/youtube_publish.py` (modulo YouTube Data API)
- MCP google-contele: `create_drive_file`, `update_drive_file`

## O que fazer

### 1. Upload pro Google Drive

**Quando mostrar**: se o item veio da planilha e tem pasta Drive associada (campo `drive_folder` ou similar no item da planilha).

**Endpoint**: `POST /api/upload-drive`
```json
{
  "image_path": "output/thumb_live_roteiro-xxx_a.png",
  "folder_id": "1abc...",
  "filename": "thumb-titulo-do-video.png"
}
```

**Implementacao**:
- Usar MCP google-contele `create_drive_file` OU Google Drive API direta
- Upload da imagem aprovada na pasta do video
- Retornar link publico do arquivo

### 2. Atualizar YouTube (Titulo e/ou Thumbnail)

**Quando mostrar**: se o video tem URL YouTube (de qualquer fonte: planilha, Step 1 URL).

**Pre-requisito**: OAuth token com scope `youtube.force-ssl` (YouTube Data API v3).
- Verificar se ja existe token/credentials em `.env` ou `credentials/`
- Se nao tiver, mostrar mensagem "Configure YouTube API" com instrucoes

**Endpoint titulo**: `POST /api/youtube-update-title`
```json
{
  "video_id": "prZ3y8ZkX60",
  "new_title": "O prejuizo que o aumento do diesel vai gerar no seu caixa"
}
```

**Endpoint thumbnail**: `POST /api/youtube-update-thumb`
```json
{
  "video_id": "prZ3y8ZkX60",
  "image_path": "output/thumb_live_roteiro-xxx_a.png"
}
```

**Implementacao**:
- Extrair video_id da URL YouTube (regex: `v=([a-zA-Z0-9_-]{11})` ou `youtu.be/([a-zA-Z0-9_-]{11})`)
- YouTube Data API v3:
  - Titulo: `videos.update` com `snippet.title`
  - Thumbnail: `thumbnails.set` com media upload
- Thumbnail max 2MB, 1280x720, JPG/PNG
- Se imagem for maior que 2MB, redimensionar com Pillow antes do upload

### 3. Frontend (rot-step-review)

Adicionar apos o banner de aprovacao:

```html
<div id="rot-publish-actions" style="display:none;margin-top:16px">
  <!-- Drive -->
  <div id="rot-drive-row" style="display:none;margin-bottom:8px">
    <button class="btn btn-primary btn-sm" id="rot-btn-drive" onclick="rotUploadDrive()">
      Enviar pro Drive
    </button>
    <span id="rot-drive-status"></span>
  </div>
  <!-- YouTube -->
  <div id="rot-yt-row" style="display:none">
    <button class="btn btn-sm" onclick="rotUpdateYtTitle()"
            style="border-color:var(--red);color:var(--red)">
      Atualizar Titulo no YT
    </button>
    <button class="btn btn-sm" onclick="rotUpdateYtThumb()"
            style="border-color:var(--red);color:var(--red);margin-left:8px">
      Atualizar Thumb no YT
    </button>
    <span id="rot-yt-status"></span>
  </div>
</div>
```

Logica:
- Apos `rotApprove()`, mostrar `rot-publish-actions`
- Se tem `rotSelectedItem` com drive folder: mostrar drive row
- Se tem `rotVideoUrl` com YouTube URL: mostrar yt row
- Cada botao funciona independente com status individual

### 4. Tambem aplicar na tela de Thumb Live (tl-step-review)

A mesma funcionalidade deve existir na tela de lives, nao so no roteiro.
Reaproveitar os endpoints, so conectar os botoes.

## Validacao

### Drive
1. Selecionar video da planilha que tem pasta Drive
2. Gerar thumb, aprovar
3. Clicar "Enviar pro Drive"
4. Verificar no Google Drive que o arquivo apareceu na pasta correta
5. Verificar que o link retornado funciona

### YouTube Titulo
1. Usar video de teste (canal de testes ou video nao-listado)
2. Gerar titulo, aprovar
3. Clicar "Atualizar Titulo no YT"
4. Verificar no YouTube Studio que o titulo mudou
5. Testar com video que NAO tem URL: botao nao deve aparecer

### YouTube Thumb
1. Gerar thumb, aprovar
2. Clicar "Atualizar Thumb no YT"
3. Verificar no YouTube Studio que a miniatura mudou
4. Testar com imagem > 2MB: deve redimensionar automaticamente

### Fallbacks
1. Sem credenciais YouTube: mostrar mensagem amigavel, nao quebrar
2. Sem pasta Drive: botao Drive nao aparece
3. Sem URL YouTube: botoes YT nao aparecem
4. Erro de API: mostrar toast com erro, nao travar a tela

## Criterios de aceite

- [ ] Botao "Enviar pro Drive" funciona quando item tem pasta associada
- [ ] Botao "Atualizar Titulo no YT" atualiza titulo do video no YouTube
- [ ] Botao "Atualizar Thumb no YT" faz upload da miniatura no YouTube
- [ ] Cada botao funciona independente (pode atualizar so titulo, so thumb, ou ambos)
- [ ] Botoes so aparecem quando o contexto permite (tem URL, tem pasta)
- [ ] Erros sao tratados com mensagem amigavel
- [ ] Imagens > 2MB sao redimensionadas antes do upload YouTube
- [ ] Funciona tanto no fluxo Roteiro quanto no fluxo Live
