# Agent: PRISM Briefing Separation

Resolve GitHub Issue #1: Separar Briefing (Q1/Q2/Q3) de Script/Transcricao no fluxo Thumb Roteiro.

## Contexto

No fluxo "Thumb de Roteiro" do PRISM OS, existem dois conceitos distintos que estao misturados na UI:

1. **Script/Transcricao**: conteudo completo do video (roteiro escrito OU transcricao de video gravado). Vem do Step 1 (planilha, URL YouTube, ou texto colado). Armazenado em `rotScriptText`.
2. **Briefing (Q1/Q2/Q3)**: respostas humanas curtas e direcionadas sobre publico-alvo, objetivo e conteudo. Preenchido por Marco, Julio ou roteirista via texto ou audio.

O audio upload no Step 2 serve SOMENTE para preencher Q1/Q2/Q3 (briefing via voz), NAO para transcricao do video.

## Arquivos

- `prism-os/nutella-creator/static/index.html`: frontend (Step 2 HTML + JS, rot-step-briefing)
- `prism-os/nutella-creator/thumb_live.py`: backend (`generate_angles` ja recebe `briefing.script` separado de Q1/Q2/Q3)
- `prism-os/nutella-creator/dashboard.py`: endpoints

## O que fazer

### 1. Reestruturar Step 2 (rot-step-briefing) no HTML

Dividir visualmente em duas secoes claras:

**Secao A: Contexto do Video (read-only ou informativo)**
- Mostrar se tem script/transcricao carregado (badge "Roteiro carregado" ou "Transcricao carregada" ou "Sem contexto")
- Se tem, mostrar preview colapsavel (primeiras 3 linhas + "ver mais")
- Botao "Auto-preencher briefing" que usa o script como INPUT para sugerir Q1/Q2/Q3 via Gemini
- Esta secao e somente informativa, o usuario nao edita aqui

**Secao B: Briefing (editavel)**
- Label claro: "BRIEFING: Preenchido por voce (texto ou audio)"
- Audio upload (transcreve e preenche Q1/Q2/Q3 automaticamente)
- Q1, Q2, Q3 text areas
- Deve ficar claro que audio = atalho para preencher Q1/Q2/Q3, nao e transcricao do video

### 2. Atualizar JS

- `rotGoToBriefing()`: montar a secao de contexto com `rotScriptText` (preview colapsavel)
- Garantir que `rotAutoBriefing()` mostra loading no lugar correto
- Garantir que `rotGenerate()` envia AMBOS: `script: rotScriptText` + `q1/q2/q3` separados no briefing

### 3. NAO alterar

- Backend: `thumb_live.py` e `dashboard.py` ja tratam script separado de Q1/Q2/Q3
- Step 1 (rot-step-source): ja funciona corretamente
- Step 3 (rot-step-review): ja funciona

## Validacao

1. Abrir dashboard (`python3 dashboard.py --no-open`, porta 8765)
2. Ir em "Thumb de Roteiro"
3. **Cenario A**: Buscar da planilha um item com URL YouTube
   - Step 1: selecionar item -> deve navegar pro Step 2
   - Step 2: deve mostrar "Transcricao carregada" (se auto-transcreveu) com preview
   - Briefing deve estar separado embaixo
   - Preencher Q1/Q2/Q3 manualmente ou via audio
   - Gerar thumb -> verificar que AMBOS (script + Q1/Q2/Q3) foram enviados (checar logs do server)

4. **Cenario B**: Colar roteiro via texto
   - Step 1: colar roteiro + titulo -> selecionar
   - Step 2: deve mostrar "Roteiro carregado" com preview do texto colado
   - Preencher briefing separadamente
   - Gerar e validar

5. **Cenario C**: URL YouTube sem transcricao disponivel
   - Step 2: deve mostrar "Sem contexto do video"
   - Briefing preenchido manualmente funciona normalmente

6. Verificar no terminal que o payload enviado para `/api/thumb-generate` contem `briefing.script` (texto longo) E `briefing.q1/q2/q3` (respostas curtas) como campos DISTINTOS.

## Criterios de aceite

- [ ] Step 2 tem duas secoes visuais distintas: "Contexto do Video" e "Briefing"
- [ ] Audio upload esta claramente na secao de Briefing, nao na secao de contexto
- [ ] Preview do script/transcricao e colapsavel
- [ ] Botao auto-preencher esta na secao de contexto e preenche campos do briefing
- [ ] Payload de geracao contem `script` + `q1/q2/q3` como campos separados
- [ ] Todos os 3 cenarios funcionam sem erros
