module.exports = {
  apps: [
    {
      name: 'filesystem-watcher',
      script: 'py',
      args: [
        'scripts\\filesystem_watcher.py',
        'D:\\My Work\\Hackathon-0\\AI_Employee_Vault'
      ],
      cwd: 'D:\\My Work\\Hackathon-0',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      time: true,
      merge_logs: true,
      out_file: 'scripts\\logs\\filesystem-watcher.out.log',
      error_file: 'scripts\\logs\\filesystem-watcher.err.log'
    },
    {
      name: 'gmail-watcher',
      script: 'py',
      args: [
        'scripts\\gmail_watcher.py',
        'D:\\My Work\\Hackathon-0\\AI_Employee_Vault',
        'D:\\My Work\\Hackathon-0\\credentials.json'
      ],
      cwd: 'D:\\My Work\\Hackathon-0',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      time: true,
      merge_logs: true,
      out_file: 'scripts\\logs\\gmail-watcher.out.log',
      error_file: 'scripts\\logs\\gmail-watcher.err.log'
    },
    {
      name: 'approval-handler',
      script: 'py',
      args: [
        'scripts\\approval_handler.py',
        'D:\\My Work\\Hackathon-0\\AI_Employee_Vault'
      ],
      cwd: 'D:\\My Work\\Hackathon-0',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      time: true,
      merge_logs: true,
      out_file: 'scripts\\logs\\approval-handler.out.log',
      error_file: 'scripts\\logs\\approval-handler.err.log'
    },
    {
      name: 'whatsapp-watcher',
      script: 'py',
      args: [
        'scripts\\whatsapp_watcher.py',
        'D:\\My Work\\Hackathon-0\\AI_Employee_Vault',
        'D:\\My Work\\Hackathon-0\\scripts\\.whatsapp_session',
        '45',
        'false',
        '0',
        'false',
        'false'
      ],
      cwd: 'D:\\My Work\\Hackathon-0',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      time: true,
      merge_logs: true,
      out_file: 'scripts\\logs\\whatsapp-watcher.out.log',
      error_file: 'scripts\\logs\\whatsapp-watcher.err.log'
    },
    {
      name: 'linkedin-poster',
      script: 'py',
      args: [
        'scripts\\linkedin_poster.py',
        'D:\\My Work\\Hackathon-0\\AI_Employee_Vault',
        'D:\\My Work\\Hackathon-0\\scripts\\.linkedin_session',
        'true',
        'false'
      ],
      cwd: 'D:\\My Work\\Hackathon-0',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      time: true,
      merge_logs: true,
      out_file: 'scripts\\logs\\linkedin-poster.out.log',
      error_file: 'scripts\\logs\\linkedin-poster.err.log'
    }
  ]
};
