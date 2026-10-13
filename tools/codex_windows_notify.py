#!/usr/bin/env python3
"""Send Codex CLI notification payloads to Windows Toast from WSL."""

import base64
import json
import os
import subprocess
import sys
from pathlib import Path


POWERSHELL = '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
LOG_PATH = Path('/tmp/codex-windows-notify.log')

POWERSHELL_SCRIPT = r'''
$title = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($args[0]))
$message = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($args[1]))
$escapedTitle = [System.Security.SecurityElement]::Escape($title)
$escapedMessage = [System.Security.SecurityElement]::Escape($message)

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
$xml = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]::new()
$xml.LoadXml("<toast><visual><binding template='ToastGeneric'><text>$escapedTitle</text><text>$escapedMessage</text></binding></visual></toast>")
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Windows PowerShell').Show($toast)
'''


def read_payload():
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {'last-assistant-message': raw}


def get_text(payload, *keys, default=''):
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def main():
    payload = read_payload()
    event_type = get_text(payload, 'type', 'event', default='notification')
    message = get_text(
        payload,
        'last-assistant-message',
        'message',
        'reason',
        default='Codex 작업 상태가 변경되었습니다.',
    )
    cwd = get_text(payload, 'cwd', default='')
    if cwd and cwd not in message:
        message = f'{message}\n{cwd}'

    title_map = {
        'agent-turn-complete': 'Codex 작업 완료',
        'approval-requested': 'Codex 승인 필요',
        'user-input-requested': 'Codex 입력 필요',
    }
    title = title_map.get(event_type, 'Codex 알림')
    title_encoded = base64.b64encode(title.encode('utf-8')).decode('ascii')
    message_encoded = base64.b64encode(message[:500].encode('utf-8')).decode('ascii')

    try:
        result = subprocess.run(
            [
                POWERSHELL,
                '-NoProfile',
                '-NonInteractive',
                '-ExecutionPolicy',
                'Bypass',
                '-Command',
                POWERSHELL_SCRIPT,
                title_encoded,
                message_encoded,
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
        if result.returncode != 0:
            write_terminal_fallback(title, message)
            LOG_PATH.write_text(
                f'PowerShell notifier returned {result.returncode}\n',
                encoding='utf-8',
            )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        write_terminal_fallback(title, message)
        LOG_PATH.write_text(f'{type(exc).__name__}: {exc}\n', encoding='utf-8')


def write_terminal_fallback(title, message):
    """Use terminal-native notifications when WSL interop is unavailable."""
    text = f'{title}: {message[:300]}'
    sequence = f'\033]9;{text.replace(chr(7), " ")}\007\a'
    try:
        fd = os.open('/dev/tty', os.O_WRONLY)
        os.write(fd, sequence.encode('utf-8', errors='replace'))
        os.close(fd)
    except OSError:
        return


if __name__ == '__main__':
    main()
