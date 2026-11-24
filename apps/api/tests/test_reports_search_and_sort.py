from datetime import UTC, datetime, timedelta
import pytest


@pytest.mark.asyncio
async def test_reports_search_date_range_and_sort(client, report_factory):
    now = datetime.now(UTC)
    r1 = await report_factory(
        title="Broken curb on Maple Ave",
        address="102 Maple Avenue",
        category="sidewalk",
        status="open",
        created_at=now - timedelta(days=3),
    )
    r2 = await report_factory(
        title="Flooded crosswalk",
        address="55 Elm Street",
        category="drainage",
        status="open",
        created_at=now - timedelta(days=1),
    )

    # Search by title
    res = await client.get("/reports", params={"q": "crosswalk"})
    assert res.status_code == 200
    assert [item["id"] for item in res.json()["items"]] == [str(r2.id)]

    # Search by address
    res = await client.get("/reports", params={"q": "maple avenue"})
    assert res.status_code == 200
    assert [item["id"] for item in res.json()["items"]] == [str(r1.id)]

    # Date range filter
    res = await client.get(
        "/reports",
        params={"created_from": (now - timedelta(days=2)).isoformat()},
    )
    assert res.status_code == 200
    assert [item["id"] for item in res.json()["items"]] == [str(r2.id)]

    # Ascending sort
    res = await client.get("/reports", params={"sort": "created_at"})
    assert res.status_code == 200
    assert [item["id"] for item in res.json()["items"]] == [str(r1.id), str(r2.id)]

    # Invalid sort field rejected
    res = await client.get("/reports", params={"sort": "password_hash"})
    assert res.status_code == 422
