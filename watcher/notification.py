from datetime import datetime
import logging
from firebase_admin import messaging
import asyncio
from typing import Optional, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_push_notification(
    title: str,
    body: str,
    target_device_token: str,
    data: Optional[Dict[str, str]] = None
):  
    """
    Sends a push notification to a target device using Firebase Cloud Messaging (FCM).

    Args:
        title (str): The title of the notification.
        body (str): The body text of the notification.
        target_device_token (str): The FCM device token of the target device.
        data (Optional[Dict[str, str]]): Optional dictionary of custom data to send with the notification.
            A 'click_action' field will automatically be added to support Flutter notification handling.

    Returns:
        dict: A dictionary containing either a success message and the FCM response,
              or an error message in case of failure.
    """
    try:
        if data is None:
            data = {}

        data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data,
            token=target_device_token,
        )

        response = messaging.send(message)
        return {"message": "Notification sent successfully", "response": response}

    except Exception as e:
        logger.error(f"Error sending notification Watcher: {str(e)}")
        return {"error": str(e)}


