from fastapi import APIRouter, Depends, HTTPException

from ...auth import require_admin_mode
from ...config import settings
from ...keybindings import KEYBINDING_ACTIONS, validate_binding
from ...models import User
from ...schemas import KeybindingsResetRequest, KeybindingsUpdate

router = APIRouter()

def _action_list() -> list[dict]:
    """Serialise KEYBINDING_ACTIONS into a JSON-friendly list."""
    return [
        {
            "id": action_id,
            "context": info["context"],
            "label_key": info["label_key"],
            "default": info["default"],
        }
        for action_id, info in KEYBINDING_ACTIONS.items()
    ]

@router.get("/keybindings")
async def get_keybindings(current_user: User = Depends(require_admin_mode)):
    """Return the action registry and the current merged bindings."""
    return {
        "actions": _action_list(),
        "bindings": settings.KEYBINDINGS,
    }

@router.put("/keybindings")
async def update_keybindings(
    body: KeybindingsUpdate,
    current_user: User = Depends(require_admin_mode),
):
    """Update one or more keybindings.

    Validates all incoming bindings against in-context conflicts and persists
    the updated bindings into settings.json.
    """
    current = settings.KEYBINDINGS
    candidate_bindings = dict(current)
    for action_id, spec in body.bindings.items():
        candidate_bindings[action_id] = {"code": spec.code, "key": spec.key}

    # Validate all candidate bindings
    for action_id, spec in body.bindings.items():
        spec_dict = {"code": spec.code, "key": spec.key}
        try:
            validate_binding(action_id, spec_dict, candidate_bindings, updating_action_id=action_id)
        except ValueError as exc:
            msg = str(exc)
            if msg.startswith("conflict:"):
                conflicts_with = msg[len("conflict:"):]
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "conflict",
                        "action": action_id,
                        "conflicts_with": conflicts_with,
                    },
                )
            raise HTTPException(status_code=422, detail=msg)

    # Persist all updated bindings into settings.json
    saved = dict(settings.file_settings.get("keybindings") or {})
    for action_id, spec in body.bindings.items():
        saved[action_id] = {"code": spec.code, "key": spec.key}

    settings.save_settings({"keybindings": saved})

    return {"bindings": settings.KEYBINDINGS}

@router.post("/keybindings/reset")
async def reset_keybindings(
    body: KeybindingsResetRequest = None,
    current_user: User = Depends(require_admin_mode),
):
    """Reset one or all keybindings to their defaults in settings.json."""
    saved = dict(settings.file_settings.get("keybindings") or {})

    if body and body.action_id:
        saved.pop(body.action_id, None)
    else:
        saved = {}

    settings.save_settings({"keybindings": saved})

    return {"bindings": settings.KEYBINDINGS}
