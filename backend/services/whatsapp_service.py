"""
WhatsApp Service for Vehicle Detection System
Handles sending notifications via Evolution API
"""

import json
import logging
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self, api_url: str, api_key: str, instance_name: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.instance_name = instance_name
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    async def send_message(self, 
                          phone_number: str, 
                          message: str,
                          message_type: str = "text") -> Dict[str, Any]:
        """
        Send a WhatsApp message
        
        Args:
            phone_number: Recipient phone number (with country code, no spaces or special chars)
            message: Message content
            message_type: Type of message (text, image, video, document, etc.)
            
        Returns:
            API response as dictionary
        """
        # Clean phone number (remove spaces, dashes, parentheses)
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Ensure number has country code
        if not clean_number.startswith('1') and len(clean_number) == 10:
            # Assume US number if 10 digits and doesn't start with 1
            clean_number = '1' + clean_number
        
        # Evolution API v2 endpoint for sending a text message
        url = f"{self.api_url}/message/sendText/{self.instance_name}"

        payload = {
            "number": clean_number,
            "text": message
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"WhatsApp message sent to {clean_number}: {message[:50]}...")
                return {
                    "success": True,
                    "message_id": result.get("key", {}).get("id"),
                    "response": result
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending WhatsApp message: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "response": e.response.json() if e.response.headers.get("content-type") == "application/json" else None
            }
        except httpx.RequestError as e:
            logger.error(f"Request error sending WhatsApp message: {str(e)}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def send_parking_alert(self, 
                                phone_number: str, 
                                vehicle_info: Dict[str, Any],
                                camera_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a parking alert notification
        
        Args:
            phone_number: Recipient phone number
            vehicle_info: Dictionary with vehicle details
            camera_info: Dictionary with camera details
            
        Returns:
            API response as dictionary
        """
        # Format the alert message
        license_plate = vehicle_info.get('license_plate', 'DESCONOCIDA')
        vehicle_type = vehicle_info.get('vehicle_type', 'VEHÍCULO')
        confidence = vehicle_info.get('confidence', 0)
        camera_name = camera_info.get('name', 'CÁMARA DESCONOCIDA')
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        message = (
            f"🚨 *ALERTA DE ESTACIONAMIENTO* 🚨\n\n"
            f"Se ha detectado un {vehicle_type} estacionado por tiempo excesivo.\n\n"
            f"📋 *Detalles:*\n"
            f"• Placa: {license_plate}\n"
            f"• Tipo: {vehicle_type}\n"
            f"• Confianza: {confidence:.0%}\n"
            f"• Cámara: {camera_name}\n"
            f"• Hora: {timestamp}\n\n"
            f"Por favor, verifique la situación."
        )
        
        return await self.send_message(phone_number, message)
    
    async def send_camera_offline_alert(self, 
                                       phone_number: str, 
                                       camera_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a camera offline notification
        
        Args:
            phone_number: Recipient phone number
            camera_info: Dictionary with camera details
            
        Returns:
            API response as dictionary
        """
        camera_name = camera_info.get('name', 'CÁMARA DESCONOCIDA')
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        message = (
            f"📵 *CÁMARA DESCONECTADA* 📵\n\n"
            f"La cámara ha dejado de responder.\n\n"
            f"📋 *Detalles:*\n"
            f"• Cámara: {camera_name}\n"
            f"• Hora: {timestamp}\n\n"
            f"Por favor, verifique la conexión de la cámara."
        )
        
        return await self.send_message(phone_number, message)
    
    async def send_system_alert(self, 
                               phone_number: str, 
                               alert_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a system alert notification
        
        Args:
            phone_number: Recipient phone number
            alert_info: Dictionary with alert details
            
        Returns:
            API response as dictionary
        """
        alert_type = alert_info.get('type', 'SISTEMA')
        description = alert_info.get('description', 'ALERTA DEL SISTEMA')
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        message = (
            f"⚠️ *ALERTA DEL SISTEMA* ⚠️\n\n"
            f"Se ha detectado una condición que requiere atención.\n\n"
            f"📋 *Detalles:*\n"
            f"• Tipo: {alert_type}\n"
            f"• Descripción: {description}\n"
            f"• Hora: {timestamp}\n\n"
            f"Por favor, revise el sistema lo antes posible."
        )
        
        return await self.send_message(phone_number, message)
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the Evolution API
        
        Returns:
            API response as dictionary
        """
        # Evolution API v2 endpoint: connection state of the configured instance
        # (validates that the API is reachable, the API key is accepted and the
        # instance exists / is linked to a WhatsApp number)
        url = f"{self.api_url}/instance/connectionState/{self.instance_name}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info("WhatsApp API connection test successful")
                return {
                    "success": True,
                    "response": result
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error testing WhatsApp API: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "response": e.response.json() if e.response.headers.get("content-type") == "application/json" else None
            }
        except httpx.RequestError as e:
            logger.error(f"Request error testing WhatsApp API: {str(e)}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error testing WhatsApp API: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    async def get_connection_state(self) -> Dict[str, Any]:
        """
        Get the current connection state of the WhatsApp instance
        from the Evolution API (open / close / connecting / ...).

        Returns:
            Dictionary with keys: success, connected, state, response
        """
        # Evolution API v2 endpoint: connection state of the configured instance
        url = f"{self.api_url}/instance/connectionState/{self.instance_name}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()

                instance = result.get("instance", {})
                state = instance.get("state")

                return {
                    "success": True,
                    "connected": state == "open",
                    "state": state,
                    "response": result
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting WhatsApp connection state: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "connected": False,
                "state": None,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "response": e.response.json() if e.response.headers.get("content-type") == "application/json" else None
            }
        except httpx.RequestError as e:
            logger.error(f"Request error getting WhatsApp connection state: {str(e)}")
            return {
                "success": False,
                "connected": False,
                "state": None,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error getting WhatsApp connection state: {str(e)}")
            return {
                "success": False,
                "connected": False,
                "state": None,
                "error": f"Unexpected error: {str(e)}"
            }

# Singleton instance (will be initialized with actual values from environment)
whatsapp_service = None

def initialize_whatsapp_service(api_url: str, api_key: str, instance_name: str):
    """Initialize the WhatsApp service singleton"""
    global whatsapp_service
    whatsapp_service = WhatsAppService(api_url, api_key, instance_name)
    return whatsapp_service