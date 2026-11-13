"""Shared read helpers for private member blocking.

Blocking is stored in `skillkind_member_block` as DIRECTIONAL rows
(`blocker_id` -> `blocked_id`) and is never disclosed to the blocked member.

Two rules follow from that:

* Communication authorization is SYMMETRIC: a row in EITHER direction means
  neither member may initiate or continue contact.
* Content hiding and the private block list are DIRECTIONAL: only the member who
  created a row sees its effect, and only their own blocked ids are returned.

Every helper here accepts an existing async session (from `rx.asession()`), runs
parameterized SQL against the migrated indexes, and NEVER commits or rolls back:
transaction control belongs to the caller. Return values are booleans or plain
member-id collections, so nothing ever reveals who blocked whom.
"""

import logging

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

MEMBER_BLOCK_TABLE = "skillkind_member_block"

# One neutral sentence for EVERY refused interaction. It never says whether the
# viewer blocked the other member or the other way round.
BLOCK_UNAVAILABLE_MESSAGE = "This connection isn't available."


def not_blocked_author_sql(
    author_expr: str, viewer_param: str = "sid", alias: str = "mb"
) -> str:
    """Directional content-hiding fragment: hide rows the VIEWER blocked.

    `author_expr` is a SQL column reference (never user text) and
    `viewer_param` is the bound signed-in member id.
    """
    return (
        f"NOT EXISTS (SELECT 1 FROM {MEMBER_BLOCK_TABLE} {alias}"
        f" WHERE {alias}.blocker_id = :{viewer_param}"
        f"   AND {alias}.blocked_id = {author_expr})"
    )


def not_blocked_pair_sql(
    first_expr: str, second_expr: str, alias: str = "mb"
) -> str:
    """Symmetric communication fragment: hide rows blocked in EITHER direction."""
    return (
        f"NOT EXISTS (SELECT 1 FROM {MEMBER_BLOCK_TABLE} {alias}"
        f" WHERE ({alias}.blocker_id = {first_expr}"
        f"        AND {alias}.blocked_id = {second_expr})"
        f"    OR ({alias}.blocker_id = {second_expr}"
        f"        AND {alias}.blocked_id = {first_expr}))"
    )


# Symmetric existence probe. LIMIT 1 keeps it an index-only lookup: the first
# branch uses uq_member_block_blocker_blocked, the second
# ix_member_block_blocked_blocker.
_BLOCK_EXISTS_SQL = text(
    """
    SELECT 1
    FROM skillkind_member_block
    WHERE (blocker_id = :first_id AND blocked_id = :second_id)
       OR (blocker_id = :second_id AND blocked_id = :first_id)
    LIMIT 1
    """
)

# Directional list, newest first (ix_member_block_blocker_created).
_BLOCKED_BY_SQL = text(
    """
    SELECT blocked_id
    FROM skillkind_member_block
    WHERE blocker_id = :blocker_id
    ORDER BY created_at DESC, blocked_id DESC
    """
)

# Restricted directional probe over a candidate set (authors on one screen).
_BLOCKED_SUBSET_SQL = text(
    """
    SELECT blocked_id
    FROM skillkind_member_block
    WHERE blocker_id = :blocker_id
      AND blocked_id IN :candidate_ids
    """
).bindparams(bindparam("candidate_ids", expanding=True))


def normalize_member_id(value: int | str | None) -> int:
    """Coerce a member id to a positive int. Anything unusable becomes 0.

    0 means "not a real member" (signed-out visitor, missing id) and is never
    treated as one side of a block relationship.
    """
    try:
        member_id = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return member_id if member_id > 0 else 0


def normalize_member_ids(
    values: list[int] | set[int] | tuple[int, ...],
) -> list[int]:
    """De-duplicate a candidate id collection, dropping invalid ids."""
    seen: set[int] = set()
    cleaned: list[int] = []
    for value in values or []:
        member_id = normalize_member_id(value)
        if member_id and member_id not in seen:
            seen.add(member_id)
            cleaned.append(member_id)
    return cleaned


def is_valid_block_pair(
    first_id: int | str | None, second_id: int | str | None
) -> bool:
    """True only for two DISTINCT, authenticated member ids."""
    first = normalize_member_id(first_id)
    second = normalize_member_id(second_id)
    return bool(first and second and first != second)


async def are_members_blocked(
    asession: AsyncSession,
    first_id: int | str | None,
    second_id: int | str | None,
) -> bool:
    """Is there a block in EITHER direction between these two members?

    Use this for every communication authorization check (help offers, community
    replies, contact requests, job threads, contact and non-contact messages).
    The result deliberately does not say which side blocked the other.
    Unauthenticated ids and self-pairs are never blocked.
    """
    if not is_valid_block_pair(first_id, second_id):
        return False
    first = normalize_member_id(first_id)
    second = normalize_member_id(second_id)
    try:
        result = await asession.execute(
            _BLOCK_EXISTS_SQL, {"first_id": first, "second_id": second}
        )
        return result.first() is not None
    except Exception as exc:
        logging.exception(f"Block pair lookup failed: {exc}")
        # Fail safe: treat an unreadable block table as "blocked" so a block is
        # never silently bypassed.
        return True


async def blocked_member_ids(
    asession: AsyncSession, blocker_id: int | str | None
) -> list[int]:
    """Member ids this subscriber blocked, newest block first.

    Directional on purpose: it powers hiding blocked authors from the blocker's
    own views and rendering their private block list. It never includes members
    who blocked them.
    """
    blocker = normalize_member_id(blocker_id)
    if not blocker:
        return []
    try:
        result = await asession.execute(
            _BLOCKED_BY_SQL, {"blocker_id": blocker}
        )
        return [int(row[0]) for row in result.all() if row[0] is not None]
    except Exception as exc:
        logging.exception(f"Blocked member list lookup failed: {exc}")
        return []


async def blocked_member_id_set(
    asession: AsyncSession, blocker_id: int | str | None
) -> set[int]:
    """Set form of :func:`blocked_member_ids` for fast membership tests."""
    return set(await blocked_member_ids(asession, blocker_id))


async def blocked_ids_within(
    asession: AsyncSession,
    blocker_id: int | str | None,
    candidate_ids: list[int] | set[int] | tuple[int, ...],
) -> set[int]:
    """Which of `candidate_ids` has this subscriber blocked?

    Cheaper than loading the whole block list when only the authors visible on
    one screen matter. Returns an empty set when there is nothing to check.
    """
    blocker = normalize_member_id(blocker_id)
    candidates = normalize_member_ids(candidate_ids)
    candidates = [member_id for member_id in candidates if member_id != blocker]
    if not blocker or not candidates:
        return set()
    try:
        result = await asession.execute(
            _BLOCKED_SUBSET_SQL,
            {"blocker_id": blocker, "candidate_ids": candidates},
        )
        return {int(row[0]) for row in result.all() if row[0] is not None}
    except Exception as exc:
        logging.exception(f"Blocked subset lookup failed: {exc}")
        return set()


async def has_blocked_member(
    asession: AsyncSession,
    blocker_id: int | str | None,
    blocked_id: int | str | None,
) -> bool:
    """Did THIS subscriber block that member? (Only ever asked by the blocker.)

    Used to render an accurate Block / Unblock action for the viewer's own row.
    Never expose the result to the blocked side.
    """
    if not is_valid_block_pair(blocker_id, blocked_id):
        return False
    return normalize_member_id(blocked_id) in await blocked_ids_within(
        asession, blocker_id, [normalize_member_id(blocked_id)]
    )
