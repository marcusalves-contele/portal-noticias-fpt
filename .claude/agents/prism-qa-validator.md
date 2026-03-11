# Agent: PRISM QA Validator

Agente de testes e validacao do PRISM OS. Executa cenarios de teste end-to-end para garantir que o sistema funciona corretamente apos mudancas.

## Como executar

Rodar o dashboard e testar cada cenario manualmente via API (curl) ou browser.

```bash
cd prism-os/nutella-creator
python3 dashboard.py --no-open  # porta 8765
```

## Testes obrigatorios

### T1: Fluxo Roteiro 3 Steps (navegacao)

1. Abrir http://127.0.0.1:8765, clicar "Thumb de Roteiro"
2. **Step 1**: deve mostrar 3 abas (Planilha, URL YouTube, Colar roteiro)
   - [ ] Planilha: clicar "Buscar", selecionar item -> navega pro Step 2
   - [ ] URL: colar URL, clicar "Selecionar video" -> navega pro Step 2
   - [ ] Texto: colar roteiro + titulo, clicar "Selecionar video" -> navega pro Step 2
3. **Step 2**: deve mostrar header do video selecionado + briefing separado
   - [ ] Audio upload funciona (auto-trigger transcricao)
   - [ ] Q1/Q2/Q3 editaveis
   - [ ] Botao "Auto-preencher" aparece se tem URL ou texto
   - [ ] Botao voltar retorna pro Step 1
4. **Step 3**: thumbs renderizam corretamente
   - [ ] Thumbs A e B aparecem (nao so spinners)
   - [ ] Download links funcionam
   - [ ] Secao de titulo aparece apos thumbs prontas
   - [ ] Botao voltar retorna pro Step 2

### T2: Qualidade dos angulos criativos

Testar via API direta:

```bash
curl -s -X POST http://127.0.0.1:8765/api/thumb-generate \
  -H 'Content-Type: application/json' \
  -d '{"briefing": {"title": "Test", "channel": "fleet", "q1": "gestores", "q2": "urgencia", "q3": "live sobre X", "script": "Texto com numeros e dados especificos..."}, "divergence": 7}'
```

Criterios:
- [ ] `differentials_found` presente na resposta de angulos (verificar logs do server)
- [ ] Titulos das thumbs contem dados especificos do script (numeros, nomes, fatos)
- [ ] Titulos NAO sao genericos (rejeitar: "GESTAO DE FROTA", "COMO ECONOMIZAR", "DICAS PARA")
- [ ] Expressao do host combina com o tom do video
- [ ] Angulos A e B sao visualmente distintos

### T3: Qualidade dos titulos

```bash
curl -s -X POST http://127.0.0.1:8765/api/generate-titles \
  -H 'Content-Type: application/json' \
  -d '{"q1": "gestores de frota", "q2": "urgencia", "q3": "diesel +75 centavos", "channel": "fleet", "script": "texto com dados..."}'
```

Criterios:
- [ ] 3 titulos retornados com strategies ctr/seo/authority
- [ ] Pelo menos 2 dos 3 contem dado especifico do script
- [ ] Nenhum titulo generico
- [ ] Todos abaixo de 60 caracteres
- [ ] JSON valido sem truncamento

### T4: Fluxo Thumb Live (regressao)

1. Clicar "Thumb de Live"
2. Buscar da planilha, selecionar live
3. Preencher briefing (ou auto-fill)
4. Gerar thumbs
- [ ] Funciona igual antes (nao quebrou)
- [ ] Review mostra thumbs corretamente
- [ ] Aprovacao funciona

### T5: Edge cases

- [ ] Gerar sem script (so Q1/Q2/Q3): deve funcionar, angulos baseados no briefing
- [ ] Gerar sem Q1/Q2/Q3 (so script): deve funcionar, modelo extrai do script
- [ ] Script muito longo (>6000 chars): deve truncar sem erro
- [ ] Planilha vazia: mensagem amigavel
- [ ] URL YouTube invalida: toast de erro, nao trava

## Como reportar

Para cada teste, registrar:
- PASS / FAIL
- Screenshot ou output relevante se FAIL
- Sugestao de fix se obvio

Salvar resultado em `prism-os/nutella-creator/output/qa-report-{data}.md`
