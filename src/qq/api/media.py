"""Rich media single-step upload, BDH chunked upload, and SSRF-safe download."""

import base64
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
from opsmesh.drivers import Request

from qq.config import BotConfig, Config
from qq.event.models import PostFilesReturn, UploadPrepareReturn
from qq.exception import MediaError, MediaLimitExceeded, QQActionFailed
from qq.typing import MediaFileType, T_JsonDict
from qq.utils import validate_media_url, validate_qq_identifier

from .client import ApiClient
from .token import TokenManager

if TYPE_CHECKING:
    from qq.adapter import Adapter

_BDH_TRANSIENT_CODE = 40093001


class MediaService:
    """QQ v2 media upload (single-step + BDH multipart) and attachment download."""

    def __init__(self, adapter: "Adapter", client: ApiClient, config: Config) -> None:
        self._adapter = adapter
        self._client = client
        self._config = config

    async def post_files(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        target_id: str,
        is_c2c: bool,
        file_type: MediaFileType | int | None = None,
        url: str | None = None,
        file_data: bytes | str | None = None,
        upload_id: str | None = None,
        srv_send_msg: bool = False,
    ) -> PostFilesReturn:
        """Single-step media upload or BDH finalization via /files."""
        prefix = "users" if is_c2c else "groups"
        safe_id = validate_qq_identifier(target_id, "target_id")
        if upload_id is not None:
            body: T_JsonDict = {"upload_id": upload_id, "srv_send_msg": srv_send_msg}
        elif file_type is None:
            raise MediaError("file_type is required when upload_id is not provided.")
        else:
            body = {"file_type": int(file_type), "srv_send_msg": srv_send_msg}
            if url is not None:
                body["url"] = url
            elif file_data is not None:
                body["file_data"] = (
                    base64.b64encode(file_data).decode("ascii")
                    if isinstance(file_data, (bytes, bytearray))
                    else file_data
                )
            else:
                raise MediaError(
                    "Either url, file_data, or upload_id must be provided."
                )

        data = await self._client.request_json(
            "POST",
            f"/v2/{prefix}/{safe_id}/files",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body=body,
        )
        return PostFilesReturn.model_validate(data or {})

    async def upload_prepare(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        target_id: str,
        is_c2c: bool,
        file_type: MediaFileType | int,
        file_name: str,
        file_size: int,
        md5_hex: str,
        sha1_hex: str,
        md5_10m_hex: str | None = None,
    ) -> UploadPrepareReturn:
        """Step 1 of BDH chunked upload: POST /upload_prepare."""
        prefix = "users" if is_c2c else "groups"
        safe_id = validate_qq_identifier(target_id, "target_id")
        data = await self._client.request_json(
            "POST",
            f"/v2/{prefix}/{safe_id}/upload_prepare",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body={
                "file_type": int(file_type),
                "file_name": file_name,
                "file_size": file_size,
                "md5": md5_hex,
                "sha1": sha1_hex,
                "md5_10m": md5_10m_hex or md5_hex,
            },
        )
        return UploadPrepareReturn.model_validate(data or {})

    async def put_upload_part(self, *, presigned_url: str, chunk: bytes) -> str:
        """Step 2 of BDH chunked upload: PUT one part and return its MD5 hex."""
        resp = await self._adapter.request(
            Request(
                "PUT",
                presigned_url,
                content=chunk,
                timeout=self._config.qq_timeout,
            )
        )
        if not (200 <= resp.status_code < 300):
            raise MediaError(f"BDH part PUT failed with HTTP {resp.status_code}")
        return hashlib.md5(chunk, usedforsecurity=False).hexdigest()

    async def upload_part_finish(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        target_id: str,
        is_c2c: bool,
        upload_id: str,
        part_index: int,
        block_size: int,
        md5_hex: str,
    ) -> None:
        """Step 3 of BDH chunked upload: POST /upload_part_finish for one part."""
        prefix = "users" if is_c2c else "groups"
        safe_id = validate_qq_identifier(target_id, "target_id")
        await self._client.request_json(
            "POST",
            f"/v2/{prefix}/{safe_id}/upload_part_finish",
            bot_config=bot_config,
            token_manager=token_manager,
            json_body={
                "upload_id": upload_id,
                "part_index": part_index,
                "block_size": block_size,
                "md5": md5_hex,
            },
        )

    async def upload_bytes_or_path(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        target_id: str,
        is_c2c: bool,
        file_type: MediaFileType | int,
        raw_bytes: bytes | None = None,
        path: str | Path | None = None,
        filename: str = "file.bin",
    ) -> PostFilesReturn:
        """Automatically choose single-step or BDH chunked upload based on file size."""
        data_bytes = raw_bytes
        resolved_name = filename
        if data_bytes is None:
            if path is None:
                raise MediaError("upload_bytes_or_path requires raw_bytes or path.")
            file_path = Path(path)
            resolved_name = filename or file_path.name
            data_bytes = await anyio.to_thread.run_sync(file_path.read_bytes)

        if len(data_bytes) < self._config.qq_bdh_threshold_bytes:
            return await self.post_files(
                bot_config=bot_config,
                token_manager=token_manager,
                target_id=target_id,
                is_c2c=is_c2c,
                file_type=file_type,
                file_data=data_bytes,
            )

        return await self._upload_bdh(
            bot_config=bot_config,
            token_manager=token_manager,
            target_id=target_id,
            is_c2c=is_c2c,
            file_type=file_type,
            data_bytes=data_bytes,
            filename=resolved_name,
        )

    async def _upload_bdh(
        self,
        *,
        bot_config: BotConfig,
        token_manager: TokenManager,
        target_id: str,
        is_c2c: bool,
        file_type: MediaFileType | int,
        data_bytes: bytes,
        filename: str,
    ) -> PostFilesReturn:
        md5_hex = hashlib.md5(data_bytes, usedforsecurity=False).hexdigest()
        sha1_hex = hashlib.sha1(data_bytes, usedforsecurity=False).hexdigest()
        md5_10m_hex = hashlib.md5(
            data_bytes[: 10 * 1024 * 1024], usedforsecurity=False
        ).hexdigest()

        prep = await self.upload_prepare(
            bot_config=bot_config,
            token_manager=token_manager,
            target_id=target_id,
            is_c2c=is_c2c,
            file_type=file_type,
            file_name=filename,
            file_size=len(data_bytes),
            md5_hex=md5_hex,
            sha1_hex=sha1_hex,
            md5_10m_hex=md5_10m_hex,
        )
        block = max(prep.block_size, 1)
        concurrency = (
            max(min(prep.upload_config.concurrency, 16), 1)
            if prep.upload_config
            else self._config.qq_bdh_concurrency
        )
        sem = anyio.Semaphore(concurrency)

        async def _send_part(seq_idx: int, part_index: int, url: str) -> None:
            chunk = data_bytes[seq_idx * block : (seq_idx + 1) * block]
            async with sem:
                part_md5 = await self.put_upload_part(presigned_url=url, chunk=chunk)
                for attempt in range(3):
                    try:
                        await self.upload_part_finish(
                            bot_config=bot_config,
                            token_manager=token_manager,
                            target_id=target_id,
                            is_c2c=is_c2c,
                            upload_id=prep.upload_id,
                            part_index=part_index,
                            block_size=len(chunk),
                            md5_hex=part_md5,
                        )
                        return
                    except QQActionFailed as exc:
                        if exc.code != _BDH_TRANSIENT_CODE or attempt == 2:
                            raise
                        await anyio.sleep(0.2)

        async with anyio.create_task_group() as tg:
            for seq_idx, part in enumerate(prep.parts):
                tg.start_soon(_send_part, seq_idx, part.index, part.presigned_url)

        return await self.post_files(
            bot_config=bot_config,
            token_manager=token_manager,
            target_id=target_id,
            is_c2c=is_c2c,
            upload_id=prep.upload_id,
            srv_send_msg=False,
        )

    async def download_attachment(
        self,
        *,
        url: str,
        max_bytes: int | None = None,
    ) -> bytes:
        """Download an inbound QQ attachment with SSRF host allowlist and size cap."""
        safe_url = validate_media_url(url)
        limit = (
            max_bytes
            if max_bytes is not None
            else self._config.qq_max_media_download_bytes
        )
        resp = await self._adapter.request(
            Request("GET", safe_url, timeout=self._config.qq_timeout)
        )
        if not (200 <= resp.status_code < 300):
            raise MediaError(f"Attachment download returned HTTP {resp.status_code}")
        raw = (
            bytes(resp.content)
            if isinstance(resp.content, (bytes, bytearray))
            else str(resp.content or "").encode("utf-8")
        )
        if len(raw) > limit:
            raise MediaLimitExceeded(
                f"Attachment exceeds limit ({len(raw)} > {limit} bytes).",
                limit_bytes=limit,
                actual_bytes=len(raw),
            )
        return raw


__all__ = ["MediaService"]
