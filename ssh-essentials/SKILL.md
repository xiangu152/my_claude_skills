---
name: ssh-essentials
description: Essential SSH commands for secure remote access, key management, tunneling, and file transfers. Use when the user needs help with SSH connections, key generation, port forwarding, file transfers (scp/sftp/rsync), or SSH configuration. NOT for: general networking questions, VPN setup, or when SSH is not involved.
---

# SSH Essentials

Secure Shell (SSH) for remote access and secure file transfers.

## Basic Connection

### Connecting
```bash
# Connect with username
ssh user@hostname

# Connect to specific port
ssh user@hostname -p 2222

# Connect with verbose output
ssh -v user@hostname

# Connect with specific key
ssh -i ~/.ssh/id_rsa user@hostname

# Connect and run command
ssh user@hostname 'ls -la'
ssh user@hostname 'uptime && df -h'
```

### Interactive use
```bash
# Connect with forwarding agent
ssh -A user@hostname

# Connect with X11 forwarding (GUI apps)
ssh -X user@hostname
ssh -Y user@hostname  # Trusted X11

# Escape sequences (during session)
# ~. - Disconnect
# ~^Z - Suspend SSH
# ~# - List forwarded connections
# ~? - Help
```

## SSH Keys

### Generating keys
```bash
# Generate RSA key
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Generate ED25519 key (recommended)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Generate with custom filename
ssh-keygen -t ed25519 -f ~/.ssh/id_myserver

# Generate without passphrase (automation)
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_deploy
```

### Managing keys
```bash
# Copy public key to server
ssh-copy-id user@hostname

# Copy specific key
ssh-copy-id -i ~/.ssh/id_rsa.pub user@hostname

# Manual key copy
cat ~/.ssh/id_rsa.pub | ssh user@hostname 'cat >> ~/.ssh/authorized_keys'
```

# Check key fingerprint
ssh-keygen -lf ~/.ssh/id_rsa.pub

# Change key passphrase
ssh-keygen -p -f ~/.ssh/id_rsa
```

### SSH agent
```bash
# Start ssh-agent
eval $(ssh-agent)

# Add key to agent
ssh-add ~/.ssh/id_rsa

# List keys in agent
ssh-add -l

# Remove key from agent
ssh-add -d ~/.ssh/id_rsa

# Remove all keys
ssh-add -D

# Set key lifetime (seconds)
ssh-add -t 3600 ~/.ssh/id_rsa
```

> Windows 用户：Claude Code 自带 bash，以上命令直接可用。如果用原生 PowerShell，需先启用 ssh-agent 服务：`Get-Service ssh-agent | Set-Service -StartupType Automatic`

## Port Forwarding & Tunneling

### Local port forwarding
```bash
# Forward local port to remote
ssh -L 8080:localhost:80 user@hostname

# Forward to different remote host
ssh -L 8080:database.example.com:5432 user@jumphost

# Multiple forwards
ssh -L 8080:localhost:80 -L 3306:localhost:3306 user@hostname
```

### Remote port forwarding
```bash
# Forward remote port to local
ssh -R 8080:localhost:3000 user@hostname

# Make service accessible from remote
ssh -R 9000:localhost:9000 user@publicserver
```

### Dynamic port forwarding (SOCKS proxy)
```bash
# Create SOCKS proxy
ssh -D 1080 user@hostname
# Configure SOCKS5 proxy: localhost:1080
```

### Background tunnels
```bash
# Run in background
ssh -f -N -L 8080:localhost:80 user@hostname

# Keep alive
ssh -o ServerAliveInterval=60 -L 8080:localhost:80 user@hostname
```

## Configuration

### SSH config file (`~/.ssh/config`)
```
# Simple host alias
Host myserver
    HostName 192.168.1.100
    User admin
    Port 2222

# With key and options
Host production
    HostName prod.example.com
    User deploy
    IdentityFile ~/.ssh/id_prod
    ForwardAgent yes

# Jump host (bastion)
Host internal
    HostName 10.0.0.5
    User admin
    ProxyJump bastion

Host bastion
    HostName bastion.example.com
    User admin

# Wildcard configuration
Host *.example.com
    User admin
    ForwardAgent yes

# Keep connections alive
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### Using config
```bash
# Connect using alias
ssh myserver

# Jump through bastion automatically
ssh internal
```

## File Transfers

### SCP (Secure Copy)
```bash
# Copy file to remote
scp file.txt user@hostname:/path/to/destination/

# Copy file from remote
scp user@hostname:/path/to/file.txt ./local/

# Copy directory recursively
scp -r /local/dir user@hostname:/remote/dir/

# Copy with specific port
scp -P 2222 file.txt user@hostname:/path/
```

### SFTP (Secure FTP)
```bash
# Connect to SFTP server
sftp user@hostname

# Common SFTP commands:
# pwd, lpwd, ls, lls, cd, lcd, get, put, mkdir, rm, exit
```

### Rsync over SSH
```bash
# Sync directory
rsync -avz /local/dir/ user@hostname:/remote/dir/

# Sync with progress
rsync -avz --progress /local/dir/ user@hostname:/remote/dir/

# Sync with delete (mirror)
rsync -avz --delete /local/dir/ user@hostname:/remote/dir/

# Exclude patterns
rsync -avz --exclude '*.log' --exclude 'node_modules/' \
  /local/dir/ user@hostname:/remote/dir/

# Dry run
rsync -avz --dry-run /local/dir/ user@hostname:/remote/dir/
```

## Security Best Practices

### Hardening SSH
```bash
# Disable password authentication (edit /etc/ssh/sshd_config)
PasswordAuthentication no
PubkeyAuthentication yes

# Disable root login
PermitRootLogin no

# Change default port
Port 2222

# Restart SSH service
sudo systemctl restart sshd
```

## Troubleshooting

### Debugging
```bash
# Verbose output
ssh -vvv user@hostname

# Check permissions
ls -la ~/.ssh/
# Should be: 700 for ~/.ssh, 600 for keys, 644 for .pub files
```

### Common issues
```bash
# Fix permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
chmod 644 ~/.ssh/authorized_keys

# Clear known_hosts entry
ssh-keygen -R hostname
```

## Advanced Operations

### Jump hosts (ProxyJump)
```bash
# Connect through bastion
ssh -J bastion.example.com user@internal.local

# Multiple jumps
ssh -J bastion1,bastion2 user@final-destination
```

### Multiplexing
```bash
# Master connection
ssh -M -S ~/.ssh/control-%r@%h:%p user@hostname

# Reuse connection
ssh -S ~/.ssh/control-user@hostname:22 user@hostname
```

### Execute commands
```bash
# Pipe commands
cat local-script.sh | ssh user@hostname 'bash -s'

# With sudo
ssh -t user@hostname 'sudo command'
```
