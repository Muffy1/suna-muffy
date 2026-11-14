import pytest

from core.analytics import conversation_analytics_worker
from core.services import db


@pytest.mark.asyncio
async def test_claim_pending_queue_items_commits_claim_with_mutation_helper(monkeypatch):
    calls = []

    async def fake_execute_mutate(sql, params):
        calls.append((sql, params))
        return [
            {
                "id": "queue-1",
                "thread_id": "thread-1",
                "agent_run_id": "run-1",
                "account_id": "account-1",
                "attempts": 0,
            }
        ]

    async def fake_execute(sql, params=None):
        raise AssertionError("claiming queue items must use execute_mutate() so the UPDATE commits")

    monkeypatch.setattr(db, "execute_mutate", fake_execute_mutate)
    monkeypatch.setattr(db, "execute", fake_execute)

    rows = await conversation_analytics_worker.claim_pending_queue_items(limit=1)

    assert rows == [
        {
            "id": "queue-1",
            "thread_id": "thread-1",
            "agent_run_id": "run-1",
            "account_id": "account-1",
            "attempts": 0,
        }
    ]
    assert len(calls) == 1
    sql, params = calls[0]
    assert "UPDATE conversation_analytics_queue" in sql
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert params == {"limit": 1, "max_attempts": conversation_analytics_worker.MAX_ATTEMPTS}
