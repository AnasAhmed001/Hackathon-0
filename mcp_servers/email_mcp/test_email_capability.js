// Test script to demonstrate how Claude Code would use the Email MCP server
require('dotenv').config({ path: require('path').join(__dirname, '.env') });

console.log('📧 Email MCP Server - Capability Test');
console.log('====================================');
console.log('');
console.log('Once you have configured your SMTP app password in .env,');
console.log('the Email MCP server will provide these capabilities to Claude Code:');
console.log('');

console.log('1. 📨 SEND EMAIL CAPABILITY');
console.log('   Name: send-email');
console.log('   Description: Send an email via Gmail');
console.log('   Parameters:');
console.log('   - to: Recipient email address');
console.log('   - subject: Email subject');
console.log('   - text: Plain text content');
console.log('   - html: HTML content (optional)');
console.log('');
console.log('   Example usage in Claude Code:');
console.log('   {');
console.log('     "type": "mcp",');
console.log('     "server": "email",');
console.log('     "tool": "send-email",');
console.log('     "params": {');
console.log('       "to": "recipient@example.com",');
console.log('       "subject": "Test from AI Employee",');
console.log('       "text": "This is a test email sent by the AI Employee."');
console.log('     }');
console.log('   }');
console.log('');

console.log('📋 SETUP CHECKLIST:');
console.log('□ 1. Set GMAIL_EMAIL in .env');
console.log('□ 2. Generate Gmail App Password and set GMAIL_APP_PASSWORD in .env');
console.log('□ 3. Optional: set DRY_RUN=true for safe testing');
console.log('□ 4. Start server: npm start');
console.log('□ 5. Configure Claude Code to use the server');
console.log('');

console.log('💡 TIP: This server uses stdio transport.');
console.log('    No port binding is required for local Claude integration.');