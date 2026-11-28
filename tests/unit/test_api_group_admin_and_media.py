"""Unit tests for QQ Adapter, Gateway, Group Admin v2 APIs, Stream, and BDH."""

from collections.abc import Callable
from datetime import timedelta
import json
from typing import Any

from opsmesh.config import Config as GlobalConfig
from opsmesh.config import Env
from opsmesh.drivers import Driver, HTTPClientMixin, Request, Response
from opsmesh.exception import ActionNotAvailable
from pydantic import SecretStr
import pytest

from qq import (
    Adapter,
    BotConfig,
    Config,
    Gateway,
    MediaFileType,
    MessageSegment,
    SetMemberMuteState,
    parse_event,
)
from qq.typing import QQ_AUTH_URL


class _FakeDriver(Driver, HTTPClientMixin):
    def __init__(self, handler: Callable[[Request], Response]) -> None:
        super().__init__(Env(), GlobalConfig())
        self._handler = handler
        self.requests: list[Request] = []

    @property
    def type(self) -> str:
        return "fake"

    @property
    def logger(self) -> Any:
        return None

    def run(self, *args: Any, **kwargs: Any) -> None:
        return None

    async def request(self, setup: Request) -> Response:
        self.requests.append(setup)
        return self._handler(setup)

    async def stream_request(self, setup: Request, *, chunk_size: int = 1024):
        resp = await self.request(setup)
        yield resp

    def get_session(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


def _make_adapter(
    handler: Callable[[Request], Response],
    *,
    bdh_threshold: int = 2 * 1024 * 1024,
) -> tuple[_FakeDriver, Adapter, Gateway]:
    driver = _FakeDriver(handler)
    cfg = Config(
        qq_bots=[
            BotConfig(
                app_id="102000001",
                app_secret=SecretStr("secret_value"),
            )
        ],
        qq_bdh_threshold_bytes=bdh_threshold,
    )
    adapter = Adapter(driver, qq_config=cfg)
    gw = adapter._bot_gateways["qq:102000001"]
    return driver, adapter, gw


def _json_resp(data: Any, status: int = 200) -> Response:
    return Response(
        status,
        headers={"content-type": "application/json"},
        content=json.dumps(data),
    )


@pytest.mark.anyio
async def test_all_12_official_group_admin_v2_endpoints() -> None:
    def _route(req: Request) -> Response:
        url = str(req.url)
        if url == QQ_AUTH_URL:
            return _json_resp({"access_token": "tok_1", "expires_in": 7200})
        if req.method == "GET" and url.endswith("/v2/groups/G1/info"):
            return _json_resp(
                {
                    "group_openid": "G1",
                    "group_name": "Ops",
                    "group_member_num": 42,
                    "group_finger_memo": "memo",
                }
            )
        if req.method == "GET" and url.endswith("/v2/groups/G1/bot_state"):
            return _json_resp({"member_role": "admin", "allow_proactive_msg": True})
        if (req.method == "GET" and "/v2/groups/G1/members?" in url) or url.endswith(
            "/v2/groups/G1/members"
        ):
            if req.method == "GET":
                return _json_resp(
                    {
                        "members": [
                            {
                                "member_openid": "M1",
                                "member_role": "member",
                                "bot": False,
                            }
                        ],
                        "next_cursor": None,
                    }
                )
            return _json_resp(
                {
                    "members": [
                        {
                            "member_openid": "M1",
                            "join_timestamp": "2026-01-01T00:00:00Z",
                        }
                    ],
                    "next_index": 0,
                }
            )
        if req.method == "GET" and url.endswith("/v2/groups/G1/members/M1"):
            return _json_resp(
                {"member_openid": "M1", "username": "Alice", "member_role": "member"}
            )
        if req.method == "GET" and url.endswith("/v2/groups/G1/restrict_chat_setting"):
            return _json_resp(
                {
                    "global_rule": {
                        "mode": "none",
                        "schedule_rules": [],
                        "recurring_rules": [],
                    },
                    "members": [
                        {
                            "member_openid": "M1",
                            "mute_expire_at": "2026-01-01T01:00:00Z",
                            "username": "Alice",
                        }
                    ],
                }
            )
        if req.method == "POST" and url.endswith("/v2/groups/G1/restrict_chat_setting"):
            return _json_resp({})
        if req.method == "GET" and "/v2/groups/G1/join_request_list" in url:
            return _json_resp(
                {
                    "list": [{"join_request_id": "JR1", "member_openid": "M2"}],
                    "next_cursor": "",
                }
            )
        if req.method == "POST" and url.endswith(
            "/v2/groups/G1/approval_join_request/M2"
        ):
            return _json_resp({})
        if req.method == "POST" and url.endswith("/v2/groups/G1/batch_remove_members"):
            return _json_resp(
                {
                    "remove_members_result": "ok",
                    "add_to_member_blacklist_fail_openids": [],
                }
            )
        if req.method == "GET" and "/v2/groups/G1/member_blacklist" in url:
            return _json_resp(
                {"users": [{"member_openid": "M9", "bot": False}], "next_cursor": None}
            )
        if req.method == "POST" and url.endswith("/v2/groups/G1/member_blacklist"):
            return _json_resp({"fail_openids": []})
        if req.method == "DELETE" and url.endswith("/v2/groups/G1/messages/MSG1"):
            return _json_resp({})
        return _json_resp({"message": f"unexpected {req.method} {url}"}, status=404)

    driver, _adapter, gw = _make_adapter(_route)

    info = await gw.get_group_info("G1")
    assert info.group_name == "Ops"
    assert info.group_member_num == 42

    bot_state = await gw.get_group_bot_state("G1")
    assert bot_state.member_role == "admin"

    members = await gw.get_group_members("G1", limit=20)
    assert len(members.members) == 1

    post_members = await gw.post_group_members("G1", limit=10, start_index=0)
    assert len(post_members.members) == 1

    member = await gw.get_group_member("G1", "M1")
    assert member.username == "Alice"

    mute_setting = await gw.get_group_mute_setting("G1")
    assert len(mute_setting.members) == 1

    await gw.set_group_members_mute(
        "G1",
        [
            SetMemberMuteState(
                member_openid="M1",
                op="add",
                mute_expire_at=timedelta(minutes=10),
            )
        ],
    )

    reqs = await gw.get_group_join_request_list("G1")
    assert reqs.list[0].join_request_id == "JR1"

    await gw.approval_join_request("G1", "M2", op="approve", join_request_id="JR1")

    removed = await gw.batch_remove_group_members(
        "G1", ["M1"], add_to_member_blacklist=False
    )
    assert removed.remove_members_result == "ok"

    bl = await gw.get_group_member_blacklist("G1")
    assert bl.users[0].member_openid == "M9"

    bl_op = await gw.post_group_member_blacklist("G1", op="add", member_openids=["M9"])
    assert bl_op.fail_openids == []

    await gw.delete_group_message("G1", "MSG1")

    token_calls = [r for r in driver.requests if str(r.url) == QQ_AUTH_URL]
    assert len(token_calls) == 1

    with pytest.raises(ActionNotAvailable):
        await gw.invoke("nonexistent_action")


@pytest.mark.anyio
async def test_passive_reply_seq_and_message_stream_and_bdh_upload() -> None:
    sent_bodies: list[dict[str, Any]] = []
    bdh_parts_put: list[int] = []
    bdh_parts_finished: list[int] = []

    def _route(req: Request) -> Response:
        url = str(req.url)
        if url == QQ_AUTH_URL:
            return _json_resp({"access_token": "tok_1", "expires_in": 7200})
        if req.method == "POST" and url.endswith("/v2/groups/G1/messages"):
            body = (
                json.loads(req.content)
                if isinstance(req.content, (str, bytes))
                else (req.json or {})
            )
            sent_bodies.append(body)
            return _json_resp({"id": f"reply_{len(sent_bodies)}"})
        if req.method == "POST" and url.endswith("/v2/groups/G1/upload_prepare"):
            return _json_resp(
                {
                    "upload_id": "UP1",
                    "block_size": 40000,
                    "parts": [
                        {"index": 0, "presigned_url": "https://cos.myqcloud.com/p0"},
                        {"index": 1, "presigned_url": "https://cos.myqcloud.com/p1"},
                    ],
                    "upload_config": {
                        "concurrency": 2,
                        "retry_timeout": 30,
                        "retry_delay": 1,
                    },
                }
            )
        if req.method == "PUT" and "cos.myqcloud.com" in url:
            bdh_parts_put.append(len(req.content or b""))
            return Response(200, content="")
        if req.method == "POST" and url.endswith("/v2/groups/G1/upload_part_finish"):
            body = req.json or {}
            bdh_parts_finished.append(int(body["part_index"]))
            return _json_resp({})
        if req.method == "POST" and url.endswith("/v2/groups/G1/files"):
            return _json_resp({"file_uuid": "F1", "file_info": "FI_BDH_1", "ttl": 3600})
        return _json_resp({}, status=404)

    _driver, _adapter, gw = _make_adapter(_route, bdh_threshold=65536)
    ev = parse_event(
        "GROUP_AT_MESSAGE_CREATE",
        {
            "id": "IN_1",
            "group_openid": "G1",
            "content": "hi",
            "author": {"member_openid": "U1"},
        },
    )

    await gw.send(ev, "first")
    await gw.send(ev, "second")
    assert sent_bodies[0]["msg_id"] == "IN_1"
    assert sent_bodies[0]["msg_seq"] == 1
    assert sent_bodies[1]["msg_seq"] == 2

    async with gw.message_stream(ev) as stream:  # type: ignore[arg-type]
        await stream.append("chunk1 ")
        await stream.append("chunk2")
    assert sent_bodies[2]["stream"] == {"state": 1, "index": 1}
    assert sent_bodies[3]["stream"] == {"state": 1, "index": 2, "id": "reply_3"}
    assert sent_bodies[4]["stream"] == {"state": 10, "index": 3, "id": "reply_3"}

    big_bytes = b"A" * 70000
    await gw.send_group_message(
        "G1",
        MessageSegment.file(content=big_bytes, filename="big.bin"),
    )
    assert len(bdh_parts_put) == 2
    assert sorted(bdh_parts_finished) == [0, 1]
    assert sent_bodies[-1]["msg_type"] == 7
    assert sent_bodies[-1]["media"]["file_info"] == "FI_BDH_1"
    assert MediaFileType.FILE == 4
