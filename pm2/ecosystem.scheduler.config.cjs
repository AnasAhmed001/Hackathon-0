module.exports = {
  apps: [
    {
      name: 'task-scheduler',
      script: 'py',
      args: [
        'scripts\\schedule_tasks.py',
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
      out_file: 'scripts\\logs\\task-scheduler.out.log',
      error_file: 'scripts\\logs\\task-scheduler.err.log'
    }
  ]
};
