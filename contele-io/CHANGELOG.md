# Changelog: contele-io

Registro de mudancas no site institucional contele.io / contele.com.br (Express, server.js + public/).

---

## 17/06/2026: hospeda manual de marca FPT em /brand-fpt (feat/manual-marca-html-fpt)

- **Contexto**: a versao visual (humana) do manual de marca FPT/Fleet so existia no site PESSOAL do Marco (marcofassa-cto.web.app/brand-fpt/), cruzando a fronteira "CTO pessoal x Contele". No growth so tinha o markdown (`manual-marca/fleet-fpt/`, PR #161).
- **Migracao**: HTML completo + 4 thumbs movidos pra `public/brand-fpt/` (self-contained: CSS/JS inline, so Google Fonts externo). Agora servido em **https://contele.com.br/brand-fpt/** (e contele.io/brand-fpt/).
- **Rota**: como `express.static` usa `index:false`, a rota de diretorio `/brand-fpt` precisou ser explicita (`sendFile` do index.html, mesmo padrao de `/privacy`). `/brand-fpt` -> 301 -> `/brand-fpt/` (redirect do static) -> 200.
- **Assets**: paths das imagens reescritos pra absolutos (`/brand-fpt/thumbs/...`) pra renderizar em qualquer forma de URL.
- **Validado local**: smoke test (porta 3987) `/brand-fpt` 200 + title correto + 4 thumbs image/png 200 + home intacta.
- Referenciado no contele-os (card no menu Growth + ponteiro no CLAUDE.md).
- Pendencia: apendice de agentes embutido no HTML ainda cita a URL antiga; sync via `brand-fpt-agent.md` -> regenerar HTML (regra de ouro do proprio doc).
