import africastalking
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class SMSService:
    """Service for sending SMS via AfricasTalking API"""

    def __init__(self):
        """Initialize the SMS service with AT credentials"""
        self.username = current_app.config.get('AT_USERNAME')
        self.api_key = current_app.config.get('AT_API_KEY')

        # Initialize the SDK
        africastalking.initialize(self.username, self.api_key)
        self.sms = africastalking.SMS

    def send_message(self, recipients, message):
        """
        Send SMS to one or more recipients

        Args:
            recipients (list): List of phone numbers
            message (str): Message content

        Returns:
            dict: Response from AfricasTalking API
        """
        try:
            # Validate recipients format (should include country code)
            formatted_recipients = []
            for recipient in recipients:
                if not recipient.startswith('+'):
                    recipient = '+' + recipient
                formatted_recipients.append(recipient)

            # Send the message
            response = self.sms.send(message, formatted_recipients)
            logger.info(f"SMS sent: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return {"error": str(e)}

    def send_power_alert(self, recipient, device_name, power_usage, threshold):
        """
        Send a power usage alert

        Args:
            recipient (str): Phone number
            device_name (str): Name of the device
            power_usage (float): Current power usage in Watts
            threshold (float): Threshold that was exceeded

        Returns:
            dict: Response from AfricasTalking API
        """
        message = (
            f"ALERT: Your device '{device_name}' "
            f"is consuming {power_usage:.2f}W, which exceeds the "
            f"threshold of {threshold:.2f}W. Please check your system."
        )
        return self.send_message([recipient], message)

    def send_device_status_change(self, recipient, device_name, new_status):
        """
        Send device status change notification

        Args:
            recipient (str): Phone number
            device_name (str): Name of the device
            new_status (str): New status of the device

        Returns:
            dict: Response from AfricasTalking API
        """
        message = f"Your device '{device_name}' is now {new_status}."
        return self.send_message([recipient], message)

    def send_daily_summary(self, recipient, total_usage, cost_estimate, top_devices):
        """
        Send daily power usage summary

        Args:
            recipient (str): Phone number
            total_usage (float): Total power usage in kWh
            cost_estimate (float): Estimated cost
            top_devices (list): List of top power-consuming devices

        Returns:
            dict: Response from AfricasTalking API
        """
        top_devices_str = ", ".join([f"{d['name']}: {d['usage']:.2f}kWh" for d in top_devices[:3]])
        message = (
            f"Daily Power Summary: "
            f"Total usage: {total_usage:.2f}kWh. "
            f"Estimated cost: ${cost_estimate:.2f}. "
            f"Top consumers: {top_devices_str}"
        )
        return self.send_message([recipient], message)

def get_sms_service():
    """Factory function to get SMS service instance"""
    return SMSService()