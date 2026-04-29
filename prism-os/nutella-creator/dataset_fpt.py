"""
dataset_fpt.py — Helper pra ler dataset classificado do canal FPT em runtime.

Lê dataset_classified_with_leads.json (gerado pelo Pulse FPT em assistant-sexta-feira).
Expõe summaries compactos pro prompt do Pro + tools de drill-down (top videos, busca por keyword, etc).

Path canonical (local): /Users/marcofassa/Documents/assistant-sexta-feira/output/fpt-canal-julio/dataset_classified_with_leads.json

Em runtime Railway, o dataset precisa ser sincronizado pra prism-os via cron ou copia manual.
Fallback: se nao encontra, retorna placeholder e Pro nao tem dado granular do canal.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

# Path canonical (local dev). Em prod, sobrescrever via env var ou copia pra prism-os/data/
DATASET_CANDIDATES = [
    Path.home() / "Documents" / "assistant-sexta-feira" / "output" / "fpt-canal-julio" / "dataset_classified_with_leads.json",
    Path(__file__).parent / "data" / "dataset_classified_with_leads.json",
]


class DatasetFPT:
    """Read-only client pro dataset classificado do canal FPT."""

    def __init__(self):
        self._dataset = None
        self._path_used = None

    def _load(self) -> list[dict]:
        if self._dataset is not None:
            return self._dataset
        for path in DATASET_CANDIDATES:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Dataset vem como dict com chave "videos"
                    if isinstance(data, dict) and "videos" in data:
                        data = data["videos"]
                    if not isinstance(data, list):
                        continue
                    self._dataset = data
                    self._path_used = path
                    return data
                except Exception:
                    continue
        self._dataset = []
        return []

    def cluster_field_name(self) -> str:
        """Nome do campo de cluster no dataset (varia entre versoes)."""
        if not self._dataset:
            return "cluster"
        sample = self._dataset[0]
        for k in ("cluster_topic", "cluster", "topic_cluster", "tema_cluster"):
            if k in sample:
                return k
        return "cluster"

    def is_loaded(self) -> bool:
        self._load()
        return bool(self._dataset)

    def all_videos(self) -> list[dict]:
        return self._load()

    def organic_videos(self) -> list[dict]:
        """Filtra so organico_puro (exclui misto e ad_boosted)."""
        return [v for v in self._load() if v.get("traffic_class") == "organico_puro"]

    def top_organic_by_metric(self, metric: str, n: int = 10) -> list[dict]:
        """
        Top N videos organicos por metrica:
        - 'organic_views', 'organic_APV_pct', 'subsGained',
        - 'subs_per_1k_organic', 'lead_per_1k_organic_views', 'leads_contele'
        """
        videos = self.organic_videos()
        videos.sort(key=lambda v: v.get(metric, 0) or 0, reverse=True)
        return videos[:n]

    def search_by_keyword(self, keyword: str, organic_only: bool = True, n: int = 10) -> list[dict]:
        """Busca videos cujo titulo contem a keyword (case insensitive)."""
        kw = keyword.lower()
        pool = self.organic_videos() if organic_only else self.all_videos()
        matches = [v for v in pool if kw in (v.get("title", "") or "").lower()]
        # Ordena por organic_views desc
        matches.sort(key=lambda v: v.get("organic_views", 0) or 0, reverse=True)
        return matches[:n]

    def cluster_summary(self) -> dict:
        """
        Resumo por cluster tematico. Retorna {cluster_name: {n, avg_apv, avg_views, total_subs, total_leads}}.
        Cluster info vem direto dos campos do dataset (tools/cluster_topics.py do Pulse FPT).
        """
        videos = self.organic_videos()
        by_cluster = defaultdict(lambda: {"n": 0, "apv_sum": 0, "views_sum": 0, "subs_sum": 0, "leads_sum": 0})
        for v in videos:
            cluster = v.get("cluster_topic") or v.get("cluster") or "uncategorized"
            agg = by_cluster[cluster]
            agg["n"] += 1
            agg["apv_sum"] += v.get("organic_APV_pct", 0) or 0
            agg["views_sum"] += v.get("organic_views", 0) or 0
            agg["subs_sum"] += v.get("subsGained", 0) or 0
            agg["leads_sum"] += v.get("leads_contele", 0) or 0
        out = {}
        for cluster, agg in by_cluster.items():
            n = agg["n"] or 1
            out[cluster] = {
                "n": agg["n"],
                "avg_apv_pct": round(agg["apv_sum"] / n, 1),
                "avg_views": int(agg["views_sum"] / n),
                "total_subs": agg["subs_sum"],
                "total_leads": agg["leads_sum"],
            }
        return out

    def to_context_summary(self) -> str:
        """
        Constroi summary compacto pro system prompt. Max ~3000 chars.
        Inclui: contagem geral, top 5 organicos por subs, top 5 por leads, top clusters.
        """
        if not self.is_loaded():
            return "## DATASET FPT (nao disponivel)\n\nDataset_classified_with_leads.json nao encontrado em runtime. Sem dado granular do canal.\n"

        all_v = self.all_videos()
        organic = self.organic_videos()

        lines = ["## DATASET FPT (canal classificado por trafego)", ""]
        lines.append(f"Total: {len(all_v)} videos | organico_puro: {len(organic)} | path: {self._path_used.name if self._path_used else '?'}")
        lines.append("")

        # Top 5 organicos por subs ganhos
        top_subs = self.top_organic_by_metric("subsGained", 5)
        lines.append("**Top 5 organicos por subs ganhos**:")
        for v in top_subs:
            t = (v.get("title") or "")[:70]
            lines.append(
                f"  - {t} | subs:{v.get('subsGained', 0)} | APV:{v.get('organic_APV_pct', 0):.0f}% | "
                f"views_org:{v.get('organic_views', 0)} | leads:{v.get('leads_contele', 0)}"
            )
        lines.append("")

        # Top 5 organicos por leads
        top_leads = [v for v in organic if (v.get("leads_contele") or 0) > 0]
        top_leads.sort(key=lambda v: v.get("lead_per_1k_organic_views", 0) or 0, reverse=True)
        lines.append("**Top 5 organicos por leads/1k views (eficiencia conversao)**:")
        for v in top_leads[:5]:
            t = (v.get("title") or "")[:70]
            lines.append(
                f"  - {t} | leads/1k:{v.get('lead_per_1k_organic_views', 0):.2f} | "
                f"leads:{v.get('leads_contele', 0)} | views_org:{v.get('organic_views', 0)}"
            )
        lines.append("")

        # Top clusters
        clusters = self.cluster_summary()
        if clusters:
            sorted_clusters = sorted(clusters.items(), key=lambda kv: kv[1]["total_subs"], reverse=True)[:8]
            lines.append("**Top 8 clusters tematicos (por total de subs ganhos)**:")
            for name, agg in sorted_clusters:
                lines.append(
                    f"  - {name} | n:{agg['n']} | avg_APV:{agg['avg_apv_pct']}% | "
                    f"avg_views:{agg['avg_views']} | subs:{agg['total_subs']} | leads:{agg['total_leads']}"
                )
            lines.append("")

        return "\n".join(lines)


# Conveniencia
def get_dataset_summary() -> str:
    try:
        return DatasetFPT().to_context_summary()
    except Exception as e:
        return f"## DATASET FPT (erro)\n\n{e}\n"


def search_dataset(keyword: str, n: int = 5) -> list[dict]:
    """Busca videos por keyword. Pra tool calling do Pro."""
    try:
        return DatasetFPT().search_by_keyword(keyword, n=n)
    except Exception:
        return []
