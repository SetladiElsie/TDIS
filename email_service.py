"""
Email service for sending notifications
Supports multiple SMTP providers (Gmail, SendGrid, Mailgun, etc.)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """Handle email sending with HTML templates"""
    
    def __init__(self, app_config):
        self.config = app_config
        self.enabled = bool(
            app_config.get('MAIL_SERVER') and 
            app_config.get('MAIL_USERNAME') and 
            app_config.get('MAIL_PASSWORD')
        )
        
        if not self.enabled:
            logger.warning("Email service is DISABLED - MAIL_SERVER, MAIL_USERNAME, or MAIL_PASSWORD not configured")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML version of email body
            text_body: Plain text version (optional, auto-generated if not provided)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning(f"Email service disabled - would have sent email to {to_email}")
            logger.debug(f"Subject: {subject}")
            logger.debug(f"Body: {html_body}")
            return False
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.config.get('MAIL_FROM', 'noreply@tia-solutions.co.za')
            message['To'] = to_email
            
            # Auto-generate plain text from HTML if not provided
            if not text_body:
                # Simple HTML to text conversion
                import re
                text_body = re.sub('<[^<]+?>', '', html_body)
                text_body = text_body.replace('&nbsp;', ' ')
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            message.attach(part1)
            message.attach(part2)
            
            # Send via SMTP
            with smtplib.SMTP(self.config.get('MAIL_SERVER'), self.config.get('MAIL_PORT', 587)) as server:
                server.starttls()
                server.login(self.config.get('MAIL_USERNAME'), self.config.get('MAIL_PASSWORD'))
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_temporary_password_email(
        self,
        user_name: str,
        user_email: str,
        temporary_password: str,
        admin_name: Optional[str] = None
    ) -> bool:
        """
        Send temporary password to new user
        
        Args:
            user_name: Name of the user receiving the password
            user_email: Email address of the user
            temporary_password: The generated temporary password
            admin_name: Name of admin who created the account (optional)
        
        Returns:
            True if sent successfully
        """
        subject = "Welcome to TIA Solutions - Tender Extraction Portal"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-top: none;
            border-radius: 0 0 10px 10px;
        }}
        .credential-box {{
            background: white;
            border: 2px solid #764ba2;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .credential-label {{
            font-weight: bold;
            color: #764ba2;
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .credential-value {{
            font-family: 'Courier New', monospace;
            font-size: 18px;
            color: #333;
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            word-break: break-all;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .button {{
            display: inline-block;
            background: #764ba2;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .tagline {{
            font-size: 14px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">TIA Solutions</div>
        <div class="tagline">Technology Infrastructure Architects</div>
    </div>
    
    <div class="content">
        <h2>Welcome, {user_name}!</h2>
        
        <p>Your account has been created{"" if not admin_name else f" by {admin_name}"} for the Tender Extraction Portal.</p>
        
        <div class="credential-box">
            <div class="credential-label">Email / Username</div>
            <div class="credential-value">{user_email}</div>
        </div>
        
        <div class="credential-box">
            <div class="credential-label">Temporary Password</div>
            <div class="credential-value">{temporary_password}</div>
        </div>
        
        <div class="warning">
            <strong>⚠️ Security Notice:</strong><br>
            This is a temporary password. You will be required to change it on your first login for security purposes.
        </div>
        
        <a href="http://localhost:3000" class="button">Login to Portal</a>
        
        <h3>Next Steps:</h3>
        <ol>
            <li>Visit the Tender Extraction Portal</li>
            <li>Log in using your email and temporary password above</li>
            <li>You will be prompted to create a new secure password</li>
            <li>Start uploading and extracting tender documents</li>
        </ol>
        
        <p>If you have any questions or issues, please contact your administrator.</p>
    </div>
    
    <div class="footer">
        <p>
            <strong>TIA Solutions</strong><br>
            Technology Infrastructure Architects<br>
            This is an automated message. Please do not reply to this email.
        </p>
    </div>
</body>
</html>
        """
        
        return self.send_email(user_email, subject, html_body)
    
    def send_password_reset_email(
        self,
        user_name: str,
        user_email: str,
        new_temporary_password: str,
        admin_name: Optional[str] = None
    ) -> bool:
        """
        Send password reset notification
        
        Args:
            user_name: Name of the user
            user_email: Email address of the user
            new_temporary_password: The new generated temporary password
            admin_name: Name of admin who reset the password (optional)
        
        Returns:
            True if sent successfully
        """
        subject = "Your Password Has Been Reset - TIA Solutions"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-top: none;
            border-radius: 0 0 10px 10px;
        }}
        .credential-box {{
            background: white;
            border: 2px solid #764ba2;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .credential-label {{
            font-weight: bold;
            color: #764ba2;
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .credential-value {{
            font-family: 'Courier New', monospace;
            font-size: 18px;
            color: #333;
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            word-break: break-all;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .button {{
            display: inline-block;
            background: #764ba2;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .tagline {{
            font-size: 14px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">TIA Solutions</div>
        <div class="tagline">Technology Infrastructure Architects</div>
    </div>
    
    <div class="content">
        <h2>Password Reset Notification</h2>
        
        <p>Hello {user_name},</p>
        
        <p>Your password has been reset{"" if not admin_name else f" by {admin_name}"}. Below is your new temporary password:</p>
        
        <div class="credential-box">
            <div class="credential-label">New Temporary Password</div>
            <div class="credential-value">{new_temporary_password}</div>
        </div>
        
        <div class="warning">
            <strong>⚠️ Security Notice:</strong><br>
            For security purposes, you will be required to change this temporary password on your next login.
        </div>
        
        <a href="http://localhost:3000" class="button">Login to Portal</a>
        
        <p>If you did not request this password reset, please contact your administrator immediately.</p>
    </div>
    
    <div class="footer">
        <p>
            <strong>TIA Solutions</strong><br>
            Technology Infrastructure Architects<br>
            This is an automated message. Please do not reply to this email.
        </p>
    </div>
</body>
</html>
        """
        
        return self.send_email(user_email, subject, html_body)


# Global email service instance
_email_service: Optional[EmailService] = None


def init_email_service(app_config) -> EmailService:
    """Initialize the global email service"""
    global _email_service
    _email_service = EmailService(app_config)
    return _email_service


def get_email_service() -> Optional[EmailService]:
    """Get the global email service instance"""
    return _email_service
