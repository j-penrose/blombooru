from __future__ import annotations

from typing import Optional

KEYBINDING_ACTIONS: dict[str, dict] = {
    "media_nav_prev": {
        "context": "media_viewer",
        "label_key": "admin.keybindings.actions.media_nav_prev",
        "default": {"code": "ArrowLeft", "key": "ArrowLeft"},
    },
    "media_nav_next": {
        "context": "media_viewer",
        "label_key": "admin.keybindings.actions.media_nav_next",
        "default": {"code": "ArrowRight", "key": "ArrowRight"},
    },
    "media_fullscreen": {
        "context": "media_viewer",
        "label_key": "admin.keybindings.actions.media_fullscreen",
        "default": {"code": "KeyF", "key": "f"},
    },
    "fullscreen_zoom_in": {
        "context": "fullscreen_viewer",
        "label_key": "admin.keybindings.actions.fullscreen_zoom_in",
        "default": {"code": "KeyG", "key": "g"},
    },
    "fullscreen_zoom_out": {
        "context": "fullscreen_viewer",
        "label_key": "admin.keybindings.actions.fullscreen_zoom_out",
        "default": {"code": "KeyH", "key": "h"},
    },
    "fullscreen_move_up": {
        "context": "fullscreen_viewer",
        "label_key": "admin.keybindings.actions.fullscreen_move_up",
        "default": {"code": "ArrowUp", "key": "ArrowUp"},
    },
    "fullscreen_move_down": {
        "context": "fullscreen_viewer",
        "label_key": "admin.keybindings.actions.fullscreen_move_down",
        "default": {"code": "ArrowDown", "key": "ArrowDown"},
    },
    "fullscreen_move_left": {
        "context": "fullscreen_viewer",
        "label_key": "admin.keybindings.actions.fullscreen_move_left",
        "default": {"code": "ArrowLeft", "key": "ArrowLeft"},
    },
    "fullscreen_move_right": {
        "context": "fullscreen_viewer",
        "label_key": "admin.keybindings.actions.fullscreen_move_right",
        "default": {"code": "ArrowRight", "key": "ArrowRight"},
    },
    "gallery_nav_up": {
        "context": "gallery_nav",
        "label_key": "admin.keybindings.actions.gallery_nav_up",
        "default": {"code": "ArrowUp", "key": "ArrowUp"},
    },
    "gallery_nav_down": {
        "context": "gallery_nav",
        "label_key": "admin.keybindings.actions.gallery_nav_down",
        "default": {"code": "ArrowDown", "key": "ArrowDown"},
    },
    "gallery_nav_left": {
        "context": "gallery_nav",
        "label_key": "admin.keybindings.actions.gallery_nav_left",
        "default": {"code": "ArrowLeft", "key": "ArrowLeft"},
    },
    "gallery_nav_right": {
        "context": "gallery_nav",
        "label_key": "admin.keybindings.actions.gallery_nav_right",
        "default": {"code": "ArrowRight", "key": "ArrowRight"},
    },
    "tag_suggestion_prev": {
        "context": "tag_autocomplete",
        "label_key": "admin.keybindings.actions.tag_suggestion_prev",
        "default": {"code": "ArrowUp", "key": "ArrowUp"},
    },
    "tag_suggestion_next": {
        "context": "tag_autocomplete",
        "label_key": "admin.keybindings.actions.tag_suggestion_next",
        "default": {"code": "ArrowDown", "key": "ArrowDown"},
    },
}

def get_default_keybindings() -> dict[str, dict]:
    """Return a mapping of action_id -> default binding spec."""
    return {action_id: info["default"].copy() for action_id, info in KEYBINDING_ACTIONS.items()}

def merge_with_defaults(saved: dict) -> dict[str, dict]:
    """Merge saved bindings (from settings.json) over the built-in defaults."""
    defaults = get_default_keybindings()
    result: dict[str, dict] = {}

    for action_id, default_spec in defaults.items():
        saved_spec = saved.get(action_id)
        if isinstance(saved_spec, dict) and "code" in saved_spec:
            merged = {**default_spec, **saved_spec}
            result[action_id] = {"code": merged["code"], "key": merged.get("key", merged["code"])}
        else:
            result[action_id] = default_spec.copy()

    return result

DISALLOWED_CODES = {"Tab", "Enter", "NumpadEnter", "Escape", "CapsLock", "ContextMenu"}

def validate_binding(
    action_id: str,
    binding: dict,
    current_bindings: dict,
    updating_action_id: Optional[str] = None,
) -> None:
    """Validate a candidate binding for *action_id*."""
    if action_id not in KEYBINDING_ACTIONS:
        raise ValueError(f"Unknown action: {action_id!r}")

    action_info = KEYBINDING_ACTIONS[action_id]
    code = binding.get("code", "")

    if not code:
        raise ValueError("Binding must include a 'code' field.")

    if code in DISALLOWED_CODES:
        raise ValueError(f"disallowed:{code}")

    # In-context conflict detection
    context = action_info["context"]
    for other_id, other_binding in current_bindings.items():
        if other_id == (updating_action_id or action_id):
            continue
        other_info = KEYBINDING_ACTIONS.get(other_id)
        if other_info is None:
            continue
        if other_info["context"] != context:
            continue
        if other_binding.get("code") == code:
            raise ValueError(f"conflict:{other_id}")
