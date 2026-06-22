"""Testes unitários para blog.py — Portal FPT."""
import sys
import os
from unittest.mock import patch, MagicMock

# Adiciona o diretório pai ao path para importar blog
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import blog


class TestCreateWordpressPostStatus:
    """Bug 1: create_wordpress_post deve usar o status recebido, não 'publish' hardcoded."""

    def test_create_wordpress_post_usa_status_pending(self):
        """Quando status='pending' é passado, o post deve ser criado como pending."""
        post_response = {
            "id": 123,
            "link": "https://noticias.frotaparatodos.com.br/titulo-do-post/",
        }
        content = {
            "title": "Titulo do Post",
            "content_html": "<p>Conteudo</p>",
            "excerpt": "Resumo",
            "slug": "titulo-do-post",
        }

        with patch("blog.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 201
            mock_resp.json.return_value = post_response
            mock_post.return_value = mock_resp

            blog.create_wordpress_post(
                content=content,
                media_id=1,
                wp_url="https://noticias.frotaparatodos.com.br",
                wp_user="admin",
                wp_password="senha",
                categories=[1],
                video_id="abc123",
                blog="fpt_portal",
                status="pending",
            )

        call_kwargs = mock_post.call_args
        post_data = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert post_data["status"] == "pending", f"Esperava 'pending', got '{post_data['status']}'"

    def test_create_wordpress_post_default_status_publish(self):
        """Sem status passado, padrão deve ser 'publish' para não quebrar fleet/teams."""
        post_response = {"id": 1, "link": "https://blog.contelerastreador.com.br/post/"}
        content = {
            "title": "Post Fleet",
            "content_html": "<p>Conteudo</p>",
            "excerpt": "Resumo",
            "slug": "post-fleet",
        }

        with patch("blog.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 201
            mock_resp.json.return_value = post_response
            mock_post.return_value = mock_resp

            blog.create_wordpress_post(
                content=content,
                media_id=1,
                wp_url="https://blog.contelerastreador.com.br",
                wp_user="Admin",
                wp_password="senha",
                categories=[839],
                video_id="abc123",
                blog="fleet",
            )

        call_kwargs = mock_post.call_args
        post_data = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert post_data["status"] == "publish"


class TestGetBlogPromptFptPortal:
    """Bug 2: get_blog_prompt deve usar CTA de frotaparatodos.com.br para fpt_portal."""

    def test_fpt_portal_usa_cta_frotaparatodos(self):
        """CTA no prompt do fpt_portal deve apontar para frotaparatodos.com.br."""
        prompt = blog.get_blog_prompt(
            blog="fpt_portal",
            titulo="Gestao de Frotas do Zero",
            duracao="45min",
            transcricao="Hoje vamos falar sobre gestao de frotas...",
        )
        assert "frotaparatodos.com.br" in prompt, "CTA deve apontar para frotaparatodos.com.br"
        assert "contelerastreador.com.br" not in prompt, "CTA NAO deve apontar para contelerastreador"

    def test_fpt_portal_usa_autor_julio(self):
        """fpt_portal deve usar Julio Cesar como autor."""
        prompt = blog.get_blog_prompt(
            blog="fpt_portal",
            titulo="Reducao de CPK",
            duracao="30min",
            transcricao="Fala gestores...",
        )
        assert "Julio Cesar" in prompt

    def test_fleet_nao_foi_alterado(self):
        """fleet deve continuar usando CTA de contelerastreador.com.br."""
        prompt = blog.get_blog_prompt(
            blog="fleet",
            titulo="Titulo Fleet",
            duracao="20min",
            transcricao="Transcricao...",
        )
        assert "contelerastreador.com.br" in prompt


class TestFptPortalConfig:
    """Bug 3 + nova config: WP_CONFIG e WHATSAPP_GROUPS devem ter entrada fpt_portal."""

    def test_wp_config_tem_fpt_portal(self):
        """WP_CONFIG deve ter entrada fpt_portal."""
        assert "fpt_portal" in blog.WP_CONFIG

    def test_wp_config_fpt_portal_status_pending(self):
        """fpt_portal deve ter status 'pending' para curadoria humana."""
        assert blog.WP_CONFIG["fpt_portal"]["status"] == "pending"

    def test_wp_config_fpt_portal_url_correto(self):
        """URL do fpt_portal deve apontar para noticias.frotaparatodos.com.br."""
        assert blog.WP_CONFIG["fpt_portal"]["url"] == "https://noticias.frotaparatodos.com.br"

    def test_whatsapp_groups_tem_fpt_portal(self):
        """WHATSAPP_GROUPS deve ter grupo para fpt_portal."""
        assert "fpt_portal" in blog.WHATSAPP_GROUPS

    def test_whatsapp_groups_fpt_portal_tem_vip_group(self):
        """fpt_portal deve notificar o grupo VIP | Frota Para Todos."""
        assert "120363040705704064@g.us" in blog.WHATSAPP_GROUPS["fpt_portal"]
