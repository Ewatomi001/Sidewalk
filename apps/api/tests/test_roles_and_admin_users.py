import pytest


@pytest.mark.asyncio
async def test_role_permissions_matrix(
    client,
    regular_user_headers,
    moderator_headers,
    admin_headers,
    sample_user,
    sample_report,
):
    # Regular user: denied moderation and admin user management
    res = await client.get("/admin/users", headers=regular_user_headers)
    assert res.status_code == 403

    res = await client.post(
        f"/moderation/reports/{sample_report.id}/resolve",
        headers=regular_user_headers,
    )
    assert res.status_code == 403

    # Moderator: can moderate, cannot manage users
    res = await client.post(
        f"/moderation/reports/{sample_report.id}/resolve",
        headers=moderator_headers,
    )
    assert res.status_code in (200, 204)

    res = await client.get("/admin/users", headers=moderator_headers)
    assert res.status_code == 403

    res = await client.patch(
        f"/admin/users/{sample_user.id}",
        json={"role": "moderator"},
        headers=moderator_headers,
    )
    assert res.status_code == 403

    # Admin: can list users, promote moderator, and deactivate account
    res = await client.get("/admin/users", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1

    res = await client.patch(
        f"/admin/users/{sample_user.id}",
        json={"role": "moderator", "is_active": False},
        headers=admin_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["role"] == "moderator"
    assert body["is_active"] is False
