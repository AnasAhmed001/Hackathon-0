# PM2 Setup For AI Employee (Windows)

This project supports two operation modes with PM2.

## Mode A: Daemon Watchers (recommended)

Runs long-lived watchers directly:

- filesystem-watcher
- gmail-watcher
- approval-handler

Use config: `pm2/ecosystem.watchers.config.cjs`

## Mode B: Scheduler Mode

Runs the Python scheduler loop:

- task-scheduler

Use config: `pm2/ecosystem.scheduler.config.cjs`

Important: avoid running Mode A and Mode B together, because scheduler mode also triggers watcher scripts and can create duplicate processing behavior.

## Install PM2

```powershell
npm install -g pm2
```

## Start Mode A

```powershell
Set-Location "D:\My Work\Hackathon-0"
New-Item -ItemType Directory -Force -Path "scripts\\logs" | Out-Null
pm2 start pm2\\ecosystem.watchers.config.cjs
pm2 save
```

## Start Mode B

```powershell
Set-Location "D:\My Work\Hackathon-0"
New-Item -ItemType Directory -Force -Path "scripts\\logs" | Out-Null
pm2 start pm2\\ecosystem.scheduler.config.cjs
pm2 save
```

## Common PM2 Commands

```powershell
pm2 list
pm2 logs
pm2 logs gmail-watcher
pm2 restart gmail-watcher
pm2 stop all
pm2 delete all
```

## Startup On Reboot (Windows)

```powershell
pm2 startup
pm2 save
```

If Gmail watcher fails at startup, verify that credentials exist at `D:\My Work\Hackathon-0\credentials.json` or update the path in the PM2 ecosystem file.
