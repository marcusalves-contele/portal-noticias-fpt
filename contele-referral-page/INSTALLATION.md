# Instalação e Configuração - Landing Page Contele

## Passos para Deploy

### 1. Instalar Dependências

```bash
npm install
```

Isso instalará as novas dependências adicionadas:
- `tailwindcss@^3.4.17`
- `postcss@^8.4.49`
- `autoprefixer@^10.4.20`

### 2. Configurar Variável de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# URL do webhook n8n para receber as indicações
VITE_N8N_WEBHOOK_URL=https://primary-production-2349.up.railway.app/webhook/referral-submission
```

### 3. Testar Localmente

```bash
npm run dev
```

Acesse: http://localhost:3000

### 4. Build para Produção

```bash
npm run build
```

Isso irá:
1. Compilar TypeScript com `strict: true`
2. Processar Tailwind CSS com PostCSS
3. Gerar bundle otimizado em `dist/`

### 5. Preview do Build

```bash
npm run preview
```

## Arquivos Criados/Modificados na Revisão

### Arquivos Novos:
- `tailwind.config.js` - Configuração do Tailwind com cores personalizadas
- `postcss.config.js` - Processamento de CSS
- `index.css` - Imports do Tailwind e custom animations
- `INSTALLATION.md` - Este arquivo

### Arquivos Modificados:
- `package.json` - Adicionadas dependências Tailwind
- `tsconfig.json` - Ativado strict mode
- `vite.config.ts` - Removidas variáveis de ambiente não utilizadas
- `index.html` - Removido Tailwind CDN, melhorado SEO
- `index.tsx` - Import do CSS, modernizado código
- `components/ReferralForm.tsx` - Validações robustas, acessibilidade
- Todos os componentes - Removido `import React`

## Verificações de Qualidade

### TypeScript Strict Mode
Verifique se não há erros de tipo:
```bash
npx tsc --noEmit
```

### Tailwind Classes
Todas as classes `contele-*` agora estão definidas:
- `contele-blue` → #013D8F
- `contele-light` → #0052CC
- `contele-accent` → #22C55E (green-500)

### Acessibilidade
- Labels com `htmlFor` e `id`
- Ícones com `aria-hidden="true"`
- Inputs com `aria-label` descritivos
- Fieldset/legend para radio buttons
- Estados de erro com `role="alert"` e `aria-live="assertive"`

## Próximos Passos (Opcional)

1. Adicionar Google Analytics
2. Adicionar Meta Tags Open Graph para compartilhamento
3. Implementar tracking de conversão
4. Adicionar testes com Vitest ou Jest
5. Configurar CI/CD no Railway/Vercel
