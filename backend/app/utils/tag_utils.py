import fnmatch
import re
import time
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from ..models import Tag, TagImplication
from ..utils.logger import logger

def resolve_aliases(db: Session, raw_names: List[str]) -> Dict[str, Tuple[str, str]]:
    """Build an alias lookup map for a list of (already lowercased) tag names."""
    from ..models import TagAlias

    if not raw_names:
        return {}

    aliases = db.query(TagAlias).filter(TagAlias.alias_name.in_(raw_names)).all()
    return {
        a.alias_name: (a.target_tag.name, a.target_tag.category)
        for a in aliases
    }

def expand_implications(db: Session, tag_set: Dict[int, object], implications: Optional[List[object]] = None) -> None:
    """Recursively expand tag implications into *tag_set*, mutating it in place."""
    from ..models import TagImplication

    if implications is None:
        implications = db.query(TagImplication).all()
    if not implications:
        return

    changed = True
    while changed:
        changed = False
        current_names = {t.name for t in tag_set.values()}

        for imp in implications:
            triggered = any(t.id in tag_set for t in imp.target_tags)
            if not triggered and imp.target_tag_patterns:
                triggered = any(
                    fnmatch.fnmatch(tag_name, pattern)
                    for tag_name in current_names
                    for pattern in imp.target_tag_patterns
                )

            if triggered:
                for implied_tag in imp.implied_tags:
                    if implied_tag.id not in tag_set:
                        tag_set[implied_tag.id] = implied_tag
                        changed = True


def resolve_implications(db: Session, tags: list[str], max_depth: int = 10) -> list[str]:
    """Get all implications for a given set of tags"""

    start_time = time.perf_counter()

    TargetTag = aliased(Tag)

    def all_patterns_match(tag_names: set[str], patterns: list[str]) -> bool:
        """Return true if all patterns can be matches"""

        matches = 0
        regexes = [re.compile(fnmatch.translate(pat)) for pat in patterns]
        for regex in regexes:
            for tag_name in tag_names:
                if regex.match(tag_name):
                    matches += 1
                    break
        return matches >= len(regexes)


    def get_implied_tags(
            tag_names: set[str],
            tag_ids: set[int],
            implications_to_skip: set[int]
        ) -> tuple[set[int], set[str], set[int]]:
        # Tag ids for implications that apply
        ids: set[int] = set()

        # Tag names for implications that apply
        names: set[str] = set()

        # Select implied tag id & name as well as implication id and patterns for all non-evaluated implications that
        # have an exact target tag match OR don't have any target tags at all
        stmt_by_target_tags = (
            select(Tag.id, Tag.name, TagImplication.id, TagImplication.target_tag_patterns)
            .join(TagImplication.implied_tags)
            .where(
                ~TagImplication.id.in_(implications_to_skip),
                ~TagImplication.target_tags.of_type(TargetTag).any(
                    ~TargetTag.id.in_(tag_ids)
                )
            )
        )
        res = db.execute(stmt_by_target_tags).all()

        # Evaluation status for all implications
        evaluated_implications: dict[int, bool] = {}

        for (implied_tag_id, implied_tag_name, imp_id, patterns) in res:
            eval_status = evaluated_implications.get(imp_id)
            if eval_status is None:
                # The current implication id has not been evaluated before
                eval_status = evaluated_implications[imp_id] = (
                    all_patterns_match(tag_names, patterns)
                    if patterns is not None
                    else True
                )

            if not eval_status:
                # Pattern(s) does not match for this implication
                continue

            ids.add(implied_tag_id)
            names.add(implied_tag_name)

        return (
            ids,
            names,
            set(
                implication_id
                for implication_id, applies in evaluated_implications.items()
                if applies
            )
        )


    # The set of all tags ids (those given + implied)
    all_ids = set(db.scalars(select(Tag.id).where(Tag.name.in_(tags))).all())

    # The set of all tags names (those given + implied)
    all_names = set(tags)

    # The set of all implications (ids) that have been applied
    applied_implications: set[int] = set()

    final_depth: int = 0
    for depth in range(max_depth):
        ids, names, applied_implication_ids = get_implied_tags(all_names, all_ids, applied_implications)
        if ids.issubset(all_ids):
            break
        applied_implications |= applied_implication_ids
        all_names |= names
        all_ids |= ids
        final_depth = depth


    logger.debug(f"Implication lookup finished in {time.perf_counter() - start_time:.3f}s (depth={final_depth}) ")
    return list(all_names - set(tags))
