require('dotenv').config({ path: require('path').join(__dirname, '.env') });
const { McpServer } = require('@modelcontextprotocol/sdk/server/mcp.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const nodemailer = require('nodemailer');
const z = require('zod/v4');

function getMissingSmtpEnv() {
  const required = ['GMAIL_EMAIL', 'GMAIL_APP_PASSWORD'];
  return required.filter((key) => !process.env[key]);
}

function isDryRun() {
  return String(process.env.DRY_RUN || '').toLowerCase() === 'true';
}

function createTransporter() {
  return nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.GMAIL_EMAIL,
      pass: process.env.GMAIL_APP_PASSWORD,
    },
  });
}

async function sendEmail(to, subject, text, html = null) {
  const missing = getMissingSmtpEnv();
  if (missing.length > 0) {
    return { success: false, error: `Missing required environment variables: ${missing.join(', ')}` };
  }

  if (isDryRun()) {
    return {
      success: true,
      dryRun: true,
      message: 'DRY_RUN enabled. Email was not sent.',
      preview: {
        from: process.env.GMAIL_EMAIL,
        to,
        subject,
        text,
        hasHtml: Boolean(html),
      },
    };
  }

  try {
    const transporter = createTransporter();
    const mailOptions = {
      from: process.env.GMAIL_EMAIL,
      to,
      subject,
      text,
      ...(html ? { html } : {}),
    };

    const result = await transporter.sendMail(mailOptions);
    return { success: true, messageId: result.messageId, accepted: result.accepted };
  } catch (error) {
    console.error('Error sending email:', error);
    return { success: false, error: error.message };
  }
}

function okResponse(payload) {
  return {
    content: [{ type: 'text', text: JSON.stringify(payload, null, 2) }],
    structuredContent: payload,
  };
}

function errorResponse(message) {
  return {
    content: [{ type: 'text', text: message }],
    isError: true,
  };
}

// Define the MCP server
const server = new McpServer({
  name: 'email-mcp',
  version: '1.0.0',
});

server.registerTool('send-email', {
  description: 'Send an email via Gmail using SMTP app password',
  inputSchema: {
    to: z.string().email().describe('Recipient email address'),
    subject: z.string().min(1).describe('Email subject'),
    text: z.string().min(1).describe('Plain text content'),
    html: z.string().optional().describe('Optional HTML content'),
  },
}, async ({ to, subject, text, html }) => {
  try {
    const result = await sendEmail(to, subject, text, html);
    return okResponse(result);
  } catch (error) {
    return errorResponse(`send-email failed: ${error.message}`);
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('email-mcp stdio server started');
}

main().catch((error) => {
  console.error('email-mcp startup failed:', error);
  process.exit(1);
});