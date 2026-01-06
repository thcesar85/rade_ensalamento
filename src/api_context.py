# src/api_context.py
# Contexto global simples para compartilhar IES selecionada

_CONTEXT = {
    "id": None,
    "entity_code": None,
    "entity_name": None,
    "api_key": None,
}

def set_api_context(
    *,
    id=None,
    entity_code=None,
    entity_name=None,
    api_key=None,
) -> None:
    _CONTEXT["id"] = id
    _CONTEXT["entity_code"] = entity_code
    _CONTEXT["entity_name"] = entity_name
    _CONTEXT["api_key"] = f"Bearer {api_key}" if api_key else None


def get_api_token() -> str | None:
    """Retorna o token já formatado com Bearer."""
    return _CONTEXT.get("api_key")

def get_selected_ies() -> str | None:
    """Retorna o código da IES selecionada."""
    return _CONTEXT.get("entity_code")