import asyncio


async def _read_response(reader: asyncio.StreamReader) -> tuple[int, str]:
    """Read an SMTP response, handling multi-line replies.

    No per-read timeout here — the caller wraps the entire SMTP session
    in a single ``asyncio.wait_for`` so the overall budget is enforced.
    """
    lines: list[str] = []
    while True:
        raw = await reader.readline()
        line = raw.decode("utf-8", errors="replace").strip()
        lines.append(line)
        # Multi-line responses use "250-" prefix; final line uses "250 "
        if len(line) >= 4 and line[3] == " ":
            break
        if len(line) < 4:
            break
    full = "\n".join(lines)
    try:
        code = int(full[:3])
    except (ValueError, IndexError):
        code = 0
    return code, full


async def _run_smtp_session(
    email: str,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> tuple[bool | None, bool | None, str | None]:
    """Execute SMTP verification conversation on an established connection."""
    # Read banner
    code, _ = await _read_response(reader)
    if code != 220:
        return None, None, f"Unexpected banner code: {code}"

    # EHLO
    writer.write(b"EHLO verify.local\r\n")
    await writer.drain()
    code, _ = await _read_response(reader)
    if code != 250:
        return None, None, f"EHLO rejected with code: {code}"

    # MAIL FROM
    writer.write(b"MAIL FROM:<>\r\n")
    await writer.drain()
    code, _ = await _read_response(reader)
    if code != 250:
        return None, None, f"MAIL FROM rejected with code: {code}"

    # RCPT TO — test the actual address
    writer.write(f"RCPT TO:<{email}>\r\n".encode())
    await writer.drain()
    code, _ = await _read_response(reader)

    if code == 550 or code == 551 or code == 552 or code == 553:
        writer.write(b"QUIT\r\n")
        await writer.drain()
        return False, False, f"Mailbox rejected with code: {code}"

    if code != 250:
        # Greylisting (450/451) or other temporary error
        writer.write(b"QUIT\r\n")
        await writer.drain()
        return None, None, f"Inconclusive response code: {code}"

    # Catch-all detection: try a random address that shouldn't exist
    domain = email.split("@")[1]
    local = email.split("@")[0]
    probe = f"xyznonexistent42_{local}@{domain}"
    writer.write(f"RCPT TO:<{probe}>\r\n".encode())
    await writer.drain()
    catchall_code, _ = await _read_response(reader)
    is_catch_all = catchall_code == 250

    writer.write(b"QUIT\r\n")
    await writer.drain()

    if is_catch_all:
        return None, True, "Server accepts all addresses (catch-all)"

    return True, False, "Mailbox verified"


async def verify_smtp(
    email: str,
    mx_host: str,
    timeout: float = 10.0,
) -> tuple[bool | None, bool | None, str | None]:
    """
    Verify a mailbox exists via SMTP RCPT TO.

    Returns (verified, is_catch_all, reason):
        - verified: True = accepted, False = rejected, None = inconclusive
        - is_catch_all: True if server accepts everything
        - reason: human-readable explanation
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(mx_host, 25),
            timeout=timeout,
        )
    except TimeoutError:
        return None, None, "SMTP connection timed out"
    except OSError as e:
        return None, None, f"SMTP connection failed: {e}"

    try:
        return await asyncio.wait_for(
            _run_smtp_session(email, reader, writer),
            timeout=timeout,
        )
    except TimeoutError:
        return None, None, "SMTP session timed out"
    except OSError as e:
        return None, None, f"SMTP connection failed: {e}"
    finally:
        writer.close()
