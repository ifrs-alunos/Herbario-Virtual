import requests

from alerts.constants import WHATSAPP_API_URL


def send_message(phone_number: str, message: str) -> dict:
    """
    Sends a request to the whatsapp-web.js API to send a message to a phone number.
    http://localhost:3000/api-docs/#/default/post_sendMessage
    Args:
        phone_number: Whatsapp phone number, with both the country and region codes, without the 9 at the beginning.
        message: Message to be sent, must be a string.

    Returns:
        A dictionary with the response from the API.
    """
    body = {
        "phoneNumber": phone_number,
        "messageText": message
    }

    response = requests.post(WHATSAPP_API_URL + "/sendMessage", json=body)

    return response.json()


def convert_phone_number(phone_number: str) -> str:
    """
    Converts a phone number to the format required by the whatsapp-web.js API.
    Args:
        phone_number: Whatsapp phone number

    Returns:
        The phone number in the format required by the API.
    """

    return f"55{phone_number[0:2]}{phone_number[3:]}"
