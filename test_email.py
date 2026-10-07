"""
Test script for email configuration
Run this to verify email is working correctly
"""

import sys
from app import create_app
from email_service import get_email_service

def test_email_config():
    """Test if email service is configured and working"""
    print("=" * 60)
    print("TDIS Email Configuration Test")
    print("=" * 60)
    print()
    
    # Create app context
    app = create_app('development')
    
    with app.app_context():
        email_service = get_email_service()
        
        if not email_service:
            print("❌ Email service not initialized")
            print()
            print("Make sure email_service is initialized in app.py")
            return False
        
        if not email_service.enabled:
            print("⚠️  Email service is DISABLED")
            print()
            print("To enable email, add these to your .env file:")
            print()
            print("MAIL_SERVER=smtp.gmail.com")
            print("MAIL_PORT=587")
            print("MAIL_USERNAME=your-email@gmail.com")
            print("MAIL_PASSWORD=your-app-password")
            print("MAIL_FROM=noreply@tia-solutions.co.za")
            print()
            print("See EMAIL_SETUP_GUIDE.md for detailed instructions")
            return False
        
        print("✅ Email service is ENABLED")
        print()
        print("Configuration:")
        print(f"  Server: {app.config.get('MAIL_SERVER')}")
        print(f"  Port: {app.config.get('MAIL_PORT')}")
        print(f"  Username: {app.config.get('MAIL_USERNAME')}")
        print(f"  From: {app.config.get('MAIL_FROM')}")
        print()
        
        # Ask if user wants to send test email
        response = input("Send a test email? (y/n): ").strip().lower()
        
        if response == 'y':
            to_email = input("Enter recipient email address: ").strip()
            
            if not to_email:
                print("❌ No email address provided")
                return False
            
            print()
            print(f"Sending test email to {to_email}...")
            
            success = email_service.send_email(
                to_email=to_email,
                subject='Test Email from TDIS',
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    color: white; padding: 30px; border-radius: 10px; text-align: center;">
                            <h1 style="margin: 0;">TIA Solutions</h1>
                            <p style="margin: 10px 0 0;">Technology Infrastructure Architects</p>
                        </div>
                        <div style="background: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; 
                                    border-top: none; border-radius: 0 0 10px 10px;">
                            <h2>Email Configuration Test</h2>
                            <p>Congratulations! Your email configuration is working correctly.</p>
                            <p><strong>System:</strong> Tender Document Information System (TDIS)</p>
                            <p><strong>Status:</strong> ✅ Email service operational</p>
                            <p><strong>Time:</strong> """ + str(datetime.now()) + """</p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_body="Email configuration test successful! Your TDIS email service is working."
            )
            
            print()
            if success:
                print("✅ Test email sent successfully!")
                print()
                print("Check your inbox (and spam folder) for the test email.")
            else:
                print("❌ Failed to send test email")
                print()
                print("Check the logs for more details:")
                print("  cat logs/app.log | grep -i email")
                print()
                print("Common issues:")
                print("  - Incorrect username/password")
                print("  - Gmail: Need to use App Password (not regular password)")
                print("  - Wrong SMTP server or port")
                print("  - Firewall blocking outbound SMTP connections")
                print()
                print("See EMAIL_SETUP_GUIDE.md for troubleshooting")
            
            return success
        else:
            print("Test cancelled")
            return True

if __name__ == '__main__':
    from datetime import datetime
    test_email_config()
