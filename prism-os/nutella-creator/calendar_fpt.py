"""
calendar_fpt.py — Helper Google Sheets pro calendario [FLEET] do canal FPT.

Le em runtime a planilha "[FLEET] Calendario e Ideias de Lives e Videos":
- Calendario 2026 (lives publicadas + agendadas)
- Backlog de ideias (livres)
- Backlog de videos gravados (comentarios + tickets)

Spreadsheet ID: 1xhDthK2RoJpWD1OrpcQYA1ettta8FcBFYFvDzSwzZuw
Token OAuth: token_sheets_marco.pickle (gerado por reauth_sheets_marco.py)

Uso:
  from calendar_fpt import CalendarFPT
  cal = CalendarFPT()
  cal.last_published_live()       # {'number': 327, 'date': '22/04', 'title': '...'}
  cal.upcoming_planned_lives(4)   # lista [{date, number, title, ...}]
  cal.ideas_backlog()             # lista [{idea, contact, status, sheet_row}]
  cal.slot_gaps(4)                # lista de quartas sem live agendada nas proximas N semanas
"""

import pickle
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SPREADSHEET_ID = "1xhDthK2RoJpWD1OrpcQYA1ettta8FcBFYFvDzSwzZuw"

# Em producao (Railway), boot.py decodifica SHEETS_TOKEN_B64 -> /tmp/token_sheets.pickle
# e define SHEETS_TOKEN_PATH no env. Local dev usa o pickle do diretorio.
import os
TOKEN_PATH = Path(
    os.environ.get("SHEETS_TOKEN_PATH")
    or (Path(__file__).parent / "token_sheets_marco.pickle")
)

# Aba ranges (validados via get_spreadsheet_info)
RANGE_CALENDAR_2026 = "[LIVES] [2026] CALENDÁRIO!A1:K55"
RANGE_IDEAS_LIVES = "[LIVES] 💡 IDEIAS!A1:J63"
RANGE_IDEAS_VIDEOS = "[VIDEOS GRAVADOS] 💡 IDEIAS!A1:M50"

# Header rows (1-indexed)
HEADER_ROW_CALENDAR = 3       # row 4 in Sheets (0-indexed = 3 after split)
HEADER_ROW_IDEAS_LIVES = 3    # row 4
HEADER_ROW_IDEAS_VIDEOS = 1   # row 2

CURRENT_YEAR = 2026


class CalendarFPT:
    """Read-only client pro calendario FPT em runtime."""

    def __init__(self, token_path: Path = TOKEN_PATH):
        self.token_path = token_path
        self._service = None
        self._cache = {}

    def _get_service(self):
        if self._service:
            return self._service
        if not self.token_path.exists():
            raise FileNotFoundError(
                f"Token Sheets nao encontrado em {self.token_path}. "
                f"Rodar reauth_sheets_marco.py pra gerar."
            )
        with open(self.token_path, "rb") as f:
            creds = pickle.load(f)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(self.token_path, "wb") as f:
                    pickle.dump(creds, f)
            else:
                raise RuntimeError("Token Sheets invalido. Reautenticar.")
        self._service = build("sheets", "v4", credentials=creds)
        return self._service

    def _read(self, range_name: str) -> list[list]:
        if range_name in self._cache:
            return self._cache[range_name]
        svc = self._get_service()
        resp = svc.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=range_name
        ).execute()
        rows = resp.get("values", [])
        self._cache[range_name] = rows
        return rows

    def _parse_date_dd_mm(self, date_str: str, year: int = CURRENT_YEAR) -> datetime | None:
        """Parse 'DD/MM' or 'DD/MM/YYYY' to datetime."""
        if not date_str or date_str.strip() in ("-", ""):
            return None
        s = date_str.strip()
        try:
            if len(s.split("/")) == 2:
                return datetime.strptime(f"{s}/{year}", "%d/%m/%Y")
            return datetime.strptime(s, "%d/%m/%Y")
        except ValueError:
            return None

    def calendar_2026(self) -> list[dict]:
        """
        Retorna todas as linhas do calendario 2026 estruturadas.
        Headers: [Data, NumLive, Formato, Titulo, Direcionamento, Convidado,
                 Categoria, EtapaFunil, Produto, DataEspecial, Status]
        """
        rows = self._read(RANGE_CALENDAR_2026)
        if len(rows) <= HEADER_ROW_CALENDAR:
            return []
        # Header at index HEADER_ROW_CALENDAR (row 4 1-indexed = idx 3 0-indexed)
        # Data starts at idx 3
        headers_keys = ["date", "live_number", "format", "title", "direction",
                        "guest", "category", "funnel_stage", "product",
                        "special_date", "status"]
        data = []
        for idx, row in enumerate(rows[HEADER_ROW_CALENDAR:], start=HEADER_ROW_CALENDAR + 1):
            if not row or not row[0]:
                continue
            entry = {"sheet_row": idx, "raw": row}
            for col_idx, key in enumerate(headers_keys):
                entry[key] = row[col_idx] if col_idx < len(row) else ""
            entry["parsed_date"] = self._parse_date_dd_mm(entry["date"])
            data.append(entry)
        return data

    def last_published_live(self) -> dict | None:
        """
        Ultima live com status 'Realizada'/'Publicada'. Retorna dict ou None.
        """
        cal = self.calendar_2026()
        published = [r for r in cal if r["status"].strip() in ("Realizada", "Publicado", "Publicada")]
        if not published:
            return None
        # Ordenar por numero da live (mais recente)
        published.sort(key=lambda r: int(r["live_number"]) if r["live_number"].isdigit() else 0, reverse=True)
        last = published[0]
        return {
            "number": int(last["live_number"]) if last["live_number"].isdigit() else None,
            "date": last["date"],
            "title": last["title"],
            "guest": last["guest"],
            "product": last["product"],
            "sheet_row": last["sheet_row"],
        }

    def upcoming_planned_lives(self, weeks: int = 4) -> list[dict]:
        """
        Lives agendadas/em planejamento nas proximas N semanas (status != Realizada).
        """
        cal = self.calendar_2026()
        today = datetime.now()
        cutoff = today + timedelta(weeks=weeks)
        upcoming = []
        for r in cal:
            if not r["parsed_date"]:
                continue
            status = r["status"].strip()
            if status in ("Realizada", "Publicado", "Publicada"):
                continue
            if r["parsed_date"] < today - timedelta(days=2):
                # Passado mas nao publicada — pode estar atrasada, manter
                pass
            if r["parsed_date"] > cutoff:
                continue
            upcoming.append({
                "date": r["date"],
                "live_number": int(r["live_number"]) if r["live_number"].isdigit() else None,
                "title": r["title"],
                "direction": r["direction"],
                "guest": r["guest"],
                "product": r["product"],
                "status": status,
                "sheet_row": r["sheet_row"],
            })
        upcoming.sort(key=lambda r: r["live_number"] or 0)
        return upcoming

    def slot_gaps(self, weeks_ahead: int = 4) -> list[dict]:
        """
        Lista quartas-feiras nas proximas N semanas que NAO tem live agendada.
        FPT publica as quartas. Considera slot vago se nao houver entry no calendario.
        """
        cal = self.calendar_2026()
        scheduled_dates = {r["parsed_date"].date() for r in cal if r["parsed_date"]}

        today = datetime.now()
        # Achar proxima quarta-feira
        # weekday(): Monday=0 ... Sunday=6. Wednesday=2
        days_until_wed = (2 - today.weekday()) % 7
        if days_until_wed == 0:
            days_until_wed = 7
        next_wed = today + timedelta(days=days_until_wed)

        gaps = []
        for i in range(weeks_ahead):
            wed = next_wed + timedelta(weeks=i)
            if wed.date() not in scheduled_dates:
                gaps.append({
                    "date": wed.strftime("%d/%m/%Y"),
                    "weekday": "Quarta-feira",
                    "weeks_ahead": i + 1,
                })
        return gaps

    def ideas_backlog(self) -> dict:
        """
        Backlog de ideias livres (aba [LIVES] 💡 IDEIAS).
        Retorna {ideas_lives: [...], ideas_videos: [...]}
        """
        out = {"ideas_lives": [], "ideas_videos": []}

        # Ideas lives
        try:
            rows = self._read(RANGE_IDEAS_LIVES)
            # Header at row 4 (idx 3): Ideia, Data, Contato, Direcionamento, EtapaFunil, Produto, Origem, Convidado, Cliente, PalavraChave
            headers = ["idea", "date", "contact", "direction", "funnel_stage",
                       "product", "origin", "guest", "client", "keyword"]
            for idx, row in enumerate(rows[HEADER_ROW_IDEAS_LIVES + 1:], start=HEADER_ROW_IDEAS_LIVES + 2):
                if not row or not row[0]:
                    continue
                entry = {"sheet_row": idx, "sheet_ref": f"[LIVES] 💡 IDEIAS!A{idx}"}
                for col_idx, key in enumerate(headers):
                    entry[key] = row[col_idx] if col_idx < len(row) else ""
                # Ideia "ativa" = nao tem status "Efetuado" ainda
                entry["used"] = entry["contact"].strip().lower() == "efetuado"
                out["ideas_lives"].append(entry)
        except Exception as e:
            out["ideas_lives_error"] = str(e)

        # Ideas videos (formato bem mais sujo, faz best-effort)
        try:
            rows = self._read(RANGE_IDEAS_VIDEOS)
            # Header at row 2 (idx 1): Autor, Data, Acao, Comentario, TituloVideo, LinkVideo, Status, Titulo, ...
            # Tem 2 secoes: comentarios (cols A-G) + tickets internos (cols J+)
            headers_comments = ["author", "date", "action", "comment",
                                "video_title", "video_link", "status", "edit_title"]
            for idx, row in enumerate(rows[HEADER_ROW_IDEAS_VIDEOS + 1:], start=HEADER_ROW_IDEAS_VIDEOS + 2):
                if not row or not row[0]:
                    continue
                entry = {"sheet_row": idx, "sheet_ref": f"[VIDEOS GRAVADOS] 💡 IDEIAS!A{idx}"}
                for col_idx, key in enumerate(headers_comments):
                    entry[key] = row[col_idx] if col_idx < len(row) else ""
                if entry["action"].strip().lower() in ("selecionado", "pronto"):
                    out["ideas_videos"].append(entry)
        except Exception as e:
            out["ideas_videos_error"] = str(e)

        return out

    def to_context_summary(self, weeks_ahead: int = 4) -> str:
        """
        Constroi summary compacto pro system prompt do Gemini Pro.
        ~1500 chars max. Inclui: ultima live, proximas N semanas, gaps, top 8 ideias livres.
        """
        try:
            last = self.last_published_live()
            upcoming = self.upcoming_planned_lives(weeks_ahead)
            gaps = self.slot_gaps(weeks_ahead)
            backlog = self.ideas_backlog()
        except Exception as e:
            return f"## CALENDARIO FPT (erro de leitura)\n\nErro: {e}\n"

        lines = ["## CALENDARIO FPT (em runtime via Google Sheets)", ""]

        if last:
            lines.append(f"**Ultima live publicada**: #{last['number']} ({last['date']}) — {last['title']}")
            if last.get("product"):
                lines.append(f"  Produto vinculado: {last['product']}")
            lines.append("")

        lines.append(f"**Proximas {weeks_ahead} semanas (lives agendadas/em planejamento)**:")
        if upcoming:
            for u in upcoming:
                num = f"#{u['live_number']}" if u['live_number'] else "(sem #)"
                title = u['title'] or "(sem titulo)"
                lines.append(f"  - {u['date']} {num}: {title} | status: {u['status']} | guest: {u.get('guest', '-')}")
        else:
            lines.append("  (nenhuma agendada)")
        lines.append("")

        lines.append(f"**Slots vagos (quartas sem live agendada)**:")
        if gaps:
            for g in gaps:
                lines.append(f"  - {g['date']} ({g['weekday']}) — semana +{g['weeks_ahead']}")
        else:
            lines.append("  (todas as quartas das proximas semanas tem live)")
        lines.append("")

        # Top 8 ideias nao usadas
        ideas = [i for i in backlog.get("ideas_lives", []) if not i.get("used")][:8]
        lines.append(f"**Backlog ativo (top 8 ideias livres pra live)**:")
        if ideas:
            for i in ideas:
                idea_text = i.get('idea', '')[:120]
                ref = i.get('sheet_ref', '')
                guest = i.get('guest', '').strip()
                guest_str = f" | guest: {guest}" if guest and guest != "-" else ""
                lines.append(f"  - [{ref}] {idea_text}{guest_str}")
        else:
            lines.append("  (vazio ou nao lido)")
        lines.append("")

        # Top 5 videos selecionados
        v_ideas = backlog.get("ideas_videos", [])[:5]
        if v_ideas:
            lines.append(f"**Backlog videos gravados (top 5 comentarios selecionados)**:")
            for v in v_ideas:
                comment = v.get('comment', '')[:100]
                lines.append(f"  - [{v.get('sheet_ref', '')}] {comment}")
            lines.append("")

        return "\n".join(lines)


# Helper functions standalone (uso fora de classe)

def get_calendar_summary(weeks_ahead: int = 4) -> str:
    """Convenience: retorna o summary direto pro prompt do Pro."""
    try:
        cal = CalendarFPT()
        return cal.to_context_summary(weeks_ahead)
    except FileNotFoundError as e:
        return f"## CALENDARIO FPT\n\n(token Sheets nao configurado: {e})\n"
    except Exception as e:
        return f"## CALENDARIO FPT\n\n(erro: {e})\n"


def get_last_live_number() -> int | None:
    """Convenience: numero da ultima live publicada. None se erro."""
    try:
        last = CalendarFPT().last_published_live()
        return last["number"] if last else None
    except Exception:
        return None
