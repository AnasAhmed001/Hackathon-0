// Simple test to verify the Email MCP server structure
require('dotenv').config({ path: require('path').join(__dirname, '.env') });
console.log('Testing Email MCP Server Setup');

try {
  require('@modelcontextprotocol/sdk/server/mcp.js');
  require('@modelcontextprotocol/sdk/server/stdio.js');
  console.log('✅ MCP SDK server imports are valid');
} catch (error) {
  console.log('❌ MCP SDK imports failed');
  console.log(`   ${error.message}`);
}

// Check if required environment variables are available
const requiredEnvVars = [
  'GMAIL_EMAIL',
  'GMAIL_APP_PASSWORD'
];

let allEnvVarsPresent = true;
for (const varName of requiredEnvVars) {
  if (!process.env[varName]) {
    console.log(`⚠️  Missing environment variable: ${varName}`);
    allEnvVarsPresent = false;
  } else {
    // Don't log the actual values for security
    console.log(`✅ Environment variable ${varName} is set`);
  }
}

if (allEnvVarsPresent) {
  console.log('\n🎉 All required environment variables are set!');
  console.log('You can now start the Email MCP server with:');
  console.log('  npm start');
  console.log('This server runs over stdio (no HTTP port required).');
  console.log('\nThe server provides these capabilities:');
  console.log('- send-email: Send an email via Gmail');
} else {
  console.log('\n❌ Some required environment variables are missing.');
  console.log('Please update the .env file with GMAIL_EMAIL and GMAIL_APP_PASSWORD.');
  console.log('Use a Gmail App Password, not your regular Gmail password.');
}