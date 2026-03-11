# Agent: PRISM Creative Note Field

Resolve GitHub Issue #4: Campo de observacao adicional (prompt humano) no briefing.

## Contexto

O sistema gera angulos criativos baseado em Q1/Q2/Q3 + script, mas nao tem como o humano dar uma DIRECAO CRIATIVA especifica. Exemplo: "explorar angulo da guerra" ou "tom ironico" ou "focar no numero R$300/mes".

## O que fazer

### 1. Frontend: adicionar campo no HTML

Em AMBOS os fluxos (rot-step-briefing E tl-step-briefing), adicionar textarea entre Q3 e convidados:

```html
<div class="tl-field">
  <div class="tl-label">OBSERVACAO CRIATIVA (OPCIONAL)</div>
  <textarea class="tl-textarea" id="rot-creative-note" rows="2"
    placeholder="Ex: explorar angulo da guerra, tom ironico, focar no R$300/mes, nao usar vermelho..."></textarea>
  <div style="font-size:10px;color:var(--text-muted);margin-top:4px;font-family:var(--font-mono)">
    Direcao extra para a IA. Quando preenchido, tem prioridade sobre escolhas automaticas.
  </div>
</div>
```

IDs:
- Roteiro: `rot-creative-note`
- Live: `tl-creative-note`

### 2. JS: incluir no payload

Em `rotGenerate()` e `tlGenerate()`:
```js
const creativeNote = document.getElementById('rot-creative-note')?.value?.trim() || '';
// Adicionar ao briefing:
briefing.creative_note = creativeNote;
```

Em `rotGenerateTitlesFromReview()`:
```js
const creativeNote = document.getElementById('rot-creative-note')?.value?.trim() || '';
// Adicionar ao body do fetch:
body.creative_note = creativeNote;
```

### 3. Backend: thumb_live.py

Em `generate_angles()`, apos montar `briefing_block`, se `creative_note` presente:

```python
creative_note = briefing.get('creative_note', '').strip()
if creative_note:
    briefing_block += (
        f"\n\n=== HUMAN CREATIVE DIRECTION (HIGHEST PRIORITY — override automatic choices when conflict) ===\n"
        f"{creative_note}\n"
        f"=== END CREATIVE DIRECTION ==="
    )
```

### 4. Backend: dashboard.py

Em `_handle_generate_titles()`, adicionar `creative_note` ao prompt:

```python
creative_note = body.get("creative_note", "")
if creative_note:
    video_context_parts.append(f"DIRECAO CRIATIVA DO PRODUTOR (PRIORIDADE ALTA): {creative_note}")
```

### 5. NAO alterar

- Prompt de geracao de imagem (generate_one_thumb): nao precisa mudar, os angulos ja vao refletir a nota
- Estrutura de steps: campo fica no Step 2 existente
- Backend endpoints: campo e opcional, nao quebra compatibilidade

## Validacao

1. Gerar SEM observacao: resultado igual ao atual (nao regride)
2. Gerar COM "explorar angulo da guerra, elemento de conflito/explosao":
   - Angulos devem ter elementos visuais de guerra
   - Titulo deve referenciar guerra ou Ormuz
3. Gerar COM "tom ironico, Julio debochado":
   - expressao_host deve ser "ironico"
4. Gerar COM "focar no R$300/mes":
   - Pelo menos 1 titulo com R$300
5. Gerar COM "nao usar vermelho, ultimo video ja era vermelho":
   - cor_dominante NAO deve ser vermelho/crimson

## Criterios de aceite

- [ ] Campo presente nos dois fluxos (Roteiro + Live)
- [ ] Opcional, nao bloqueia geracao
- [ ] Marcado como HIGHEST PRIORITY no prompt
- [ ] Influencia angulos criativos
- [ ] Influencia geracao de titulos
- [ ] Nao quebra geracao sem o campo
