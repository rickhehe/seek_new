#!/usr/bin/env python3
import os
import sys
import argparse
import requests
from typing import List, Union
from dotenv import load_dotenv

from src.utils.my_logger import get_logger
logger = get_logger("tg_bot")


def send_telegram(api_key: str, message: str, tg_chat_id: str) -> bool:
    """Send a telegram message to one or more chat IDs."""
    url = f'https://api.telegram.org/bot{api_key}/sendMessage'

    logger.debug(f"Telegram API URL: {url}")
    logger.debug(f"Message to send: '{message}'")

    try:
        response = requests.post(
            url,
            json={
                'chat_id': tg_chat_id,
                'text': message
            },
            timeout=10
        )

        if response.status_code == 200:
            logger.info(f"Message sent to {tg_chat_id}: {message}")
            success_count += 1
        else:
            logger.error(f"Failed to send to {tg_chat_id}: {response.text}")

    except Exception as e:
        logger.error(f"Error sending to {tg_chat_id}: {e}")
