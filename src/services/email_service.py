"""邮件发送服务 — 通过 QQ SMTP 发送验证码"""

from __future__ import annotations

import smtplib
import random
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional

from config.settings import settings
from src.utils.logger import logger


# 内存存储验证码（简单方案，重启后失效）
_pending_codes: dict[str, tuple[str, float]] = {}  # email -> (code, expiry_timestamp)


import time

def generate_code(email: str) -> str:
    """生成 6 位数字验证码并存储（10分钟有效）"""
    code = str(random.randint(100000, 999999))
    _pending_codes[email] = (code, time.time() + 600)  # 10 min expiry
    return code


def verify_code(email: str, code: str) -> bool:
    """验证用户输入的验证码是否正确（检查过期）"""
    entry = _pending_codes.get(email)
    if entry is None:
        return False
    stored_code, expiry = entry
    if time.time() > expiry:
        del _pending_codes[email]
        return False
    if stored_code == code:
        del _pending_codes[email]
        return True
    return False


def send_verification_email(to_email: str, code: str) -> bool:
    """发送验证码邮件"""
    if not settings.smtp_user or not settings.smtp_pass:
        logger.error("SMTP not configured")
        return False

    try:
        msg = MIMEText(f"""您好！

欢迎注册「生活预演家」AI 决策模拟助手。

您的注册验证码是：{code}

验证码 10 分钟内有效，请勿泄露给他人。

---
生活预演家 · 提前看到每个选择的结果
""", "plain", "utf-8")
        msg["From"] = formataddr(("生活预演家", settings.smtp_from or settings.smtp_user))
        msg["To"] = to_email
        msg["Subject"] = "注册验证码 - 生活预演家"

        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())

        logger.info(f"Verification email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
