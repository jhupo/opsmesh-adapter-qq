"""Smoke test for initialized qq modular package skeleton."""

import qq
import qq.api
import qq.event
import qq.message
import qq.transport


def test_qq_skeleton_import() -> None:
    assert qq.__version__ is not None
    for subpkg in (qq.api, qq.event, qq.message, qq.transport):
        assert subpkg.__doc__
