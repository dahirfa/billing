from odoo import models, fields, api
import requests
import json
import logging
try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
except ImportError:
    service_account = Request = None

_logger = logging.getLogger(__name__)

class Mgs_Res_Users(models.Model):
    _inherit = 'res.users'
    
    fcm_token = fields.Char(string='FCM Token', help='Firebase Cloud Messaging Token')
    
    def _get_fcm_access_token(self):
        """Get OAuth2 access token for FCM HTTP v1 API"""
        try:
            # Get service account key from system parameters
            service_account_info = self.env['ir.config_parameter'].sudo().get_param('fcm.service_account_key')
            if not service_account_info:
                _logger.error("FCM service account key not configured")
                return None
            
            # Parse JSON service account key
            credentials_info = json.loads(service_account_info)
            
            # Create credentials
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/firebase.messaging']
            )
            
            # Get access token
            credentials.refresh(Request())
            return credentials.token
            
        except Exception as e:
            _logger.error(f"Error getting FCM access token: {str(e)}")
            return None
    
    def send_fcm_notification(self, title, body, data=None):
        """Send FCM notification to this user using HTTP v1 API"""
        if not self.fcm_token:
            _logger.warning(f"No FCM token for user {self.name}")
            return False
        
        # Get project ID from system parameters
        project_id = self.env['ir.config_parameter'].sudo().get_param('fcm.project_id')
        if not project_id:
            _logger.error("FCM project ID not configured")
            return False
            
        # Get access token
        access_token = self._get_fcm_access_token()
        if not access_token:
            _logger.error("Could not get FCM access token")
            return False
        
        # New FCM HTTP v1 API URL
        url = f'https://fcm.googleapis.com/v1/projects/{project_id}/messages:send'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        
        # New payload structure for HTTP v1 API
        payload = {
            'message': {
                'token': self.fcm_token,
                'notification': {
                    'title': title,
                    'body': body,
                },
                'data': data or {},
                'android': {
                    'priority': 'high',
                    'notification': {
                        'sound': 'default',
                    }
                },
                'apns': {
                    'payload': {
                        'aps': {
                            'sound': 'default',
                        }
                    }
                }
            }
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                _logger.info(f"FCM notification sent to {self.name}")
                status = f"FCM notification sent to {self.name} Successfully!"
                return status
            else:
                _logger.error(f"FCM notification failed: {response.status_code} - {response.text}")
                status = f"FCM notification failed: {response.status_code} - {response.text}"
                return status
        except Exception as e:
            _logger.error(f"FCM notification error: {str(e)}")
            status = f"FCM notification error: {str(e)}"
            return status   
        
        
        
        
        
        
        
        
        
        
        
        