import reflex as rx

REVIEW_REMINDER_SQL = """
INSERT INTO skillkind_member_notification
(recipient_id, actor_id, kind, title, body, help_post_id, target_route)
SELECT :sid, CASE WHEN ct.poster_id = :sid THEN ct.helper_id ELSE ct.poster_id END,
       'community_like',
       CASE WHEN ct.poster_id = :sid THEN 'Review helper' ELSE 'Review your help' END,
       '', ct.post_id, CONCAT('community:reviews:', ct.id)
FROM skillkind_completed_task ct
JOIN skillkind_subscriber poster ON poster.id = ct.poster_id
JOIN skillkind_subscriber helper ON helper.id = ct.helper_id
JOIN skillkind_help_post p ON p.id = ct.post_id AND p.author_id = ct.poster_id
WHERE ((ct.poster_id = :sid AND ct.poster_confirmed)
    OR (ct.helper_id = :sid AND ct.helper_confirmed))
  AND poster.is_active AND helper.is_active AND ct.poster_id <> ct.helper_id
  AND NOT EXISTS (SELECT 1 FROM skillkind_member_block mb
      WHERE (mb.blocker_id = ct.poster_id AND mb.blocked_id = ct.helper_id)
         OR (mb.blocker_id = ct.helper_id AND mb.blocked_id = ct.poster_id))
  AND NOT EXISTS (SELECT 1 FROM skillkind_review r
      WHERE r.completed_task_id = ct.id AND r.reviewer_id = :sid)
  AND NOT EXISTS (SELECT 1 FROM skillkind_member_notification n
      WHERE n.recipient_id = :sid AND n.kind = 'community_like'
        AND n.help_post_id = ct.post_id
        AND n.actor_id = CASE WHEN ct.poster_id = :sid THEN ct.helper_id ELSE ct.poster_id END
        AND n.target_route = CONCAT('community:reviews:', ct.id))
ON CONFLICT DO NOTHING
"""


def review_task_id(route: str) -> int:
    parts = route.split(":")
    return (
        int(parts[2])
        if len(parts) == 3
        and parts[:2] == ["community", "reviews"]
        and parts[2].isdigit()
        else 0
    )


def concise_text(
    kind: str, name: str, route: str, title: str, comment_id: int = 0
) -> str:
    name = name.strip() or "A member"
    if review_task_id(route):
        return (
            f"Review your help with {name}"
            if title == "Review your help"
            else f"Review {name}'s help"
        )
    if route == "contacts:request":
        return f"{name} sent you a contact request"
    if route == "contacts:accepted":
        return f"{name} accepted your contact request"
    if "review" in title.lower() and kind == "community_like":
        return f"{name} added a review"
    if route == "community" and kind in ("help_offer", "help_confirmed"):
        return f"{name} updated your event"
    phrases = {
        "inbox_message": "sent you a message",
        "help_offer": "sent you an offer to help",
        "direct_help_request": "sent you a help request",
        "direct_request": "sent you a help request",
        "help_confirmed": "confirmed help with you",
        "request_accepted": "accepted your help request",
        "request_declined": "declined your help request",
        "community_reply": "replied to your comment (forum)"
        if comment_id
        else "replied to your post (forum)",
        "community_like": "liked your comment (forum)"
        if comment_id
        else "liked your post (forum)",
        "schedule_proposed": "proposed a new time",
        "schedule_confirmed": "confirmed the new time",
        "schedule_declined": "declined the new time",
        "cancellation_proposed": "requested a cancellation",
        "cancellation_accepted": "confirmed the cancellation",
        "cancellation_declined": "declined the cancellation",
        "no_show_reported": "reported a missed meeting",
    }
    if kind == "job_expired":
        return "Your help request has expired"
    if kind == "job_renewed":
        return "Your help request was renewed"
    return f"{name} {phrases.get(kind, 'updated your help request')}"
