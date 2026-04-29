"""
plan_schema.py — JSON schema do output do mode "plan" do Prism Studio Planejador.

Usado em:
- studio_chat.py : _call_pro_json() passa este schema como responseSchema do Gemini Pro
- dashboard.py : /api/live-plan/generate retorna este shape pro frontend
- plan_schema_validator() : sanity check antes de devolver pro usuario

14 campos. Cada um tem proposito operacional (nao decorativo).
"""

# Schema compativel com Gemini API responseSchema (subset OpenAPI 3.0)
# Tipo, campos obrigatorios e descricao orientam o modelo a preencher direito.

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "plan_summary": {
            "type": "string",
            "description": "Resumo executivo do plano em 2-3 frases. Lider le isso e entende o que vai virar o video.",
        },
        "competitive_landscape": {
            "type": "object",
            "description": "Cruzamento com canal: o que ja foi feito, gap identificado, referencia de top organic.",
            "properties": {
                "similar_videos_in_channel": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "video_id": {"type": "string"},
                            "published_at": {"type": "string"},
                            "organic_apv_pct": {"type": "number"},
                            "organic_views": {"type": "integer"},
                            "leads_contele": {"type": "integer"},
                            "lesson": {"type": "string", "description": "O que esse video ensina pro plano (tema funciona, formato vence, anti-padrao, etc)"},
                        },
                        "required": ["title", "lesson"],
                    },
                    "description": "Top 3-5 videos do canal sobre tema similar. Se nao houver, lista vazia.",
                },
                "gap_identified": {
                    "type": "string",
                    "description": "Gap de mercado/canal que esse video preenche. Se nao tem gap claro, explica por que vale a pena mesmo assim.",
                },
                "reference_top_organic": {
                    "type": "string",
                    "description": "1 frase: qual video do canal e referencia de execucao pra esse plano. Ex: 'replicar estrutura de Live 298 Planilha pro Sistema'",
                },
            },
            "required": ["gap_identified"],
        },
        "hook": {
            "type": "object",
            "description": "Estrutura do hook (primeiros 30s). Aplicar youtube-principles-2026.md secao 5.",
            "properties": {
                "first_3s": {"type": "string", "description": "Primeira frase do video. Pergunta retorica ou afirmacao chocante."},
                "promise_with_number": {"type": "string", "description": "Promessa concreta com numero. Ex: 'Vou te mostrar 3 indicadores que reduzem 30% do CPK'"},
                "credibility": {"type": "string", "description": "1 frase de credenciamento do Julio. Max 30s acumulado."},
                "outline": {"type": "string", "description": "Roteiro do video em 1 frase: 'vamos cobrir 1) X, 2) Y, 3) Z + bonus na ponta'."},
            },
            "required": ["first_3s", "promise_with_number"],
        },
        "structure": {
            "type": "object",
            "description": "Estrutura de blocos do video. Aplicar template-roteiro-live-julio.md.",
            "properties": {
                "format": {"type": "string", "enum": ["aulao", "live_tematica", "gravado_tema_produto", "short_cluster"], "description": "Template aplicado (decision tree do template-roteiro)"},
                "duration_minutes": {"type": "integer", "description": "Duracao planejada em minutos"},
                "blocks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "start_minute": {"type": "integer"},
                            "end_minute": {"type": "integer"},
                            "purpose": {"type": "string", "description": "O que esse bloco entrega"},
                            "key_points": {"type": "array", "items": {"type": "string"}, "description": "3-5 pontos chave"},
                        },
                        "required": ["name", "purpose"],
                    },
                },
            },
            "required": ["format", "duration_minutes", "blocks"],
        },
        "guest_suggestions": {
            "type": "array",
            "description": "0-3 sugestoes de convidado especialista. So sugerir se tema pede convidado. Pode ser vazio.",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "credential": {"type": "string", "description": "Por que esse convidado e relevante. Ex: '20 anos perito em ARLA, ja apareceu em Live 245'"},
                    "source": {"type": "string", "enum": ["historico_canal", "backlog_ideias", "sugestao_pro"], "description": "De onde veio a sugestao"},
                    "contact": {"type": "string", "description": "Contato se conhecido. Vazio se nao"},
                },
                "required": ["name", "credential", "source"],
            },
        },
        "seo": {
            "type": "object",
            "properties": {
                "primary_keyword": {"type": "string"},
                "secondary_keywords": {"type": "array", "items": {"type": "string"}},
                "title_options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3 opcoes de titulo seguindo padroes do canal: separador `:`, pergunta, ou numero (sem R$/%)",
                },
                "description_first_2_lines": {"type": "string", "description": "2 primeiras linhas da descricao YouTube. Aparecem no search."},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "5-10 tags especificas"},
                "hashtags": {"type": "array", "items": {"type": "string"}, "description": "3 hashtags max"},
            },
            "required": ["primary_keyword", "title_options"],
        },
        "polls": {
            "type": "array",
            "description": "Enquetes da Comunidade YouTube ANTES da publicacao do video pra esquentar audiencia.",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "publish_days_before": {"type": "integer", "description": "Quantos dias antes da live publicar a enquete"},
                },
                "required": ["question", "options"],
            },
        },
        "ctas": {
            "type": "array",
            "description": "CTAs ao longo do video. Mid-roll (50%), peak (80%), final (95%). 1-3 CTAs total. Cada CTA tem 1 acao clara.",
            "items": {
                "type": "object",
                "properties": {
                    "moment": {"type": "string", "enum": ["mid", "peak", "final"]},
                    "action": {"type": "string", "description": "1 acao concreta. Ex: 'baixar checklist gratuito', 'agendar demo Contele Fleet', 'inscrever no curso'"},
                    "wording": {"type": "string", "description": "Como Julio fala isso na voz dele"},
                },
                "required": ["moment", "action"],
            },
        },
        "thumbnail_brief": {
            "type": "object",
            "description": "Brief pra Prism gerar a thumb. Aplicar diretivas do soul-canal-fpt.md secao 4.",
            "properties": {
                "main_text": {"type": "string", "description": "Texto principal da thumb. Max 4 palavras, alto contraste."},
                "secondary_text": {"type": "string", "description": "Texto secundario opcional. Pode ser vazio."},
                "expression": {"type": "string", "enum": ["pensativo", "assertivo", "ironico", "explicando", "surpreso", "confiante", "serio", "sorrindo"]},
                "composition": {"type": "string", "description": "Descricao da composicao. Ex: 'closeup Julio esquerda, dashboard de carro direita'"},
                "palette": {
                    "type": "object",
                    "properties": {
                        "primary": {"type": "string", "description": "Cor dominante. Ex: 'preto cinematografico'"},
                        "accent": {"type": "string", "description": "Cor de destaque. Ex: 'vermelho #E63946'"},
                        "justification": {"type": "string", "description": "Por que essa paleta vence pra esse tema (cruzar com dado)"},
                    },
                },
                "use_real_photo": {"type": "boolean", "description": "Foto real do Julio (true) vs Prism AI (false). Aplicar regra soul-canal-fpt.md: foto real pra retencao/produto, Prism pra descoberta/topo de funil"},
            },
            "required": ["main_text", "expression", "composition"],
        },
        "risks": {
            "type": "array",
            "description": "Riscos ou tensoes do plano. Vazio se tudo OK.",
            "items": {
                "type": "object",
                "properties": {
                    "risk": {"type": "string"},
                    "mitigation": {"type": "string"},
                },
                "required": ["risk"],
            },
        },
        "sources": {
            "type": "array",
            "description": "Fontes consultadas (knowledge docs, datasets, vídeos referencia). Pra rastreabilidade.",
            "items": {"type": "string"},
        },
        "slot_recommendation": {
            "type": "object",
            "description": "Sugestao de slot na grade do canal. Cruzar com calendario FPT em runtime.",
            "properties": {
                "date": {"type": "string", "description": "Data sugerida no formato DD/MM/YYYY"},
                "live_number": {"type": "integer", "description": "Numero da live (sequencial, baseado no ultimo publicado)"},
                "justification": {"type": "string", "description": "Por que essa data: slot vago, alinhamento sazonal, gap tematico, etc"},
                "alternative_dates": {"type": "array", "items": {"type": "string"}, "description": "Outras datas viaveis como fallback"},
            },
            "required": ["date", "justification"],
        },
        "duplicate_warnings": {
            "type": "array",
            "description": "Temas no calendario/backlog que se sobrepoem ao plano. Vazio se nao ha colisao.",
            "items": {
                "type": "object",
                "properties": {
                    "conflicting_title": {"type": "string"},
                    "where": {"type": "string", "enum": ["calendario_2026", "backlog_lives", "backlog_videos", "publicado_recente"]},
                    "overlap_pct": {"type": "integer", "description": "0-100, quao parecidos sao os temas"},
                    "recommendation": {"type": "string", "description": "Manter? Reformular angulo? Cancelar?"},
                },
                "required": ["conflicting_title", "where", "recommendation"],
            },
        },
        "idea_pulled_from": {
            "type": "object",
            "description": "Se o plano aproveitou ideia do backlog da planilha, registra origem. Null se ideia foi gerada do zero pelo agente.",
            "properties": {
                "source": {"type": "string", "enum": ["backlog_lives", "backlog_videos", "comentario_youtube", "ticket_interno", "gerado_pelo_agente"]},
                "row_reference": {"type": "string", "description": "Aba!linha pra rastreabilidade. Ex: '[LIVES] 💡 IDEIAS!A11'"},
                "original_text": {"type": "string", "description": "Texto original da ideia"},
            },
        },
    },
    "required": [
        "plan_summary",
        "competitive_landscape",
        "hook",
        "structure",
        "seo",
        "thumbnail_brief",
        "slot_recommendation",
    ],
}


# Lista dos campos obrigatorios pra checklist visual no frontend
PLAN_REQUIRED_FIELDS = PLAN_SCHEMA["required"]

# Numero total de campos expostos
PLAN_TOTAL_FIELDS = len(PLAN_SCHEMA["properties"])


def validate_plan(plan: dict) -> tuple[bool, list[str]]:
    """
    Sanity check do plano gerado pelo Pro.
    Retorna (ok, list_of_missing_or_invalid).
    Nao tenta corrigir, so reporta.
    """
    issues = []

    for field in PLAN_REQUIRED_FIELDS:
        if field not in plan:
            issues.append(f"Campo obrigatorio ausente: {field}")
            continue
        val = plan[field]
        if val is None or val == "" or val == [] or val == {}:
            issues.append(f"Campo obrigatorio vazio: {field}")

    # Checks especificos
    if "structure" in plan:
        struct = plan["structure"]
        if "blocks" in struct and not struct["blocks"]:
            issues.append("structure.blocks vazio")
        if "format" in struct and struct["format"] not in ("aulao", "live_tematica", "gravado_tema_produto", "short_cluster"):
            issues.append(f"structure.format invalido: {struct.get('format')}")

    if "seo" in plan:
        titles = plan["seo"].get("title_options", [])
        if len(titles) < 3:
            issues.append(f"seo.title_options deve ter 3+ opcoes, tem {len(titles)}")

    if "thumbnail_brief" in plan:
        thumb = plan["thumbnail_brief"]
        text = thumb.get("main_text", "")
        if text and len(text.split()) > 4:
            issues.append(f"thumbnail_brief.main_text tem {len(text.split())} palavras, max 4")

    return len(issues) == 0, issues
