from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ee_status.users.models import User


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.username}/"
