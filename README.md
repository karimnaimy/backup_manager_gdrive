# Backup Manager GDrive

A Python-based backup tool that uploads server files and databases to Google Drive. Built with modern Python practices using uv package manager and clean modular architecture.

## Features

- 📁 **File & Directory Backup**: JSON-configurable file/directory backups with individual policies
- 🗄️ **MySQL Database Support**: Automated database dumps with compression
- ☁️ **Google Drive Integration**: Secure headless authentication with organized folder structure
- ⚙️ **Flexible Configuration**: Environment variables and JSON configuration files
- 🔄 **Individual Cleanup Policies**: Separate backup retention for databases vs files
- 🚀 **Selective Backups**: Command-line flags for MySQL-only or files-only backups
- 📁 **Organized Storage**: Automatic `database/` and `files/` folder creation in Google Drive
- 🕐 **Cron Ready**: Easy automation with provided instructions

## Project Structure

```
backup-manager-gdrive/
├── backup.py              # Main executable script
├── files_config.json      # File backup configuration
├── .env                   # Environment configuration
├── credentials/
│   └── gdrive.json        # Google OAuth2 credentials
└── src/backup/
    ├── config.py          # Pydantic settings
    ├── drive_manager.py   # Google Drive operations
    ├── mysql_backup.py    # MySQL backup logic
    ├── files_backup.py    # Files backup logic
    └── service.py         # Main orchestrator
```

## Setup

### 1. Install Dependencies

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 2. Google Drive Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable the Google Drive API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Desktop application"
6. Download the JSON file and save as `credentials/gdrive.json`

### 3. MySQL User Setup (Recommended)

For security, create a dedicated MySQL user with minimal permissions:

```sql
-- Connect as root or admin user
mysql -u root -p

-- Create backup user
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'secure_backup_password';

-- Grant minimal required permissions
GRANT SELECT, LOCK TABLES, SHOW VIEW ON *.* TO 'backup_user'@'localhost';
GRANT RELOAD, PROCESS ON *.* TO 'backup_user'@'localhost';

-- For specific databases only (optional - more secure):
-- GRANT SELECT, LOCK TABLES, SHOW VIEW ON database_name.* TO 'backup_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Test the user
EXIT;
mysql -u backup_user -p
SHOW DATABASES;
EXIT;
```

**Permission Breakdown:**
- `SELECT`: Read data from tables
- `LOCK TABLES`: Lock tables during backup for consistency
- `SHOW VIEW`: Access view definitions
- `RELOAD`: Required for `mysqldump --single-transaction`
- `PROCESS`: View running processes (needed for consistent backups)

**Security Notes:**
- Use a strong password for the backup user
- Consider restricting to specific databases if you don't need full server backup
- The user cannot INSERT, UPDATE, DELETE, or DROP - only read data

### 4. Configuration

#### Environment Variables (`.env` file)

```bash
# Backup settings
BACKUP_BACKUP_NAME_PREFIX=myserver-backup
BACKUP_COMPRESSION_LEVEL=6
BACKUP_MAX_DATABASE_BACKUPS=50
BACKUP_MAX_FILES_BACKUPS=1

# Google Drive
BACKUP_GOOGLE_DRIVE__CREDENTIALS_FILE=credentials/gdrive.json
BACKUP_GOOGLE_DRIVE__TOKEN_FILE=token.json
BACKUP_GOOGLE_DRIVE__FOLDER_NAME=Server Backups

# MySQL settings
BACKUP_MYSQL_HOST=localhost
BACKUP_MYSQL_USER=your_user
BACKUP_MYSQL_PASSWORD=your_password
BACKUP_MYSQL_DATABASES=                    # Empty = all databases
```

#### Files Configuration (`files_config.json`)

```json
{
  "directories": [
    {
      "source": "/var/www",
      "max": 2,
      "name": "website_files",
      "exclude": ["*.log", "cache/*", "tmp/*"]
    },
    {
      "source": "/etc/apache2/sites-available",
      "max": 5,
      "name": "apache_config"
    }
  ],
  "files": [
    {
      "source": "/etc/hosts",
      "name": "hosts_file",
      "max": 10
    }
  ]
}
```

**Configuration Options:**
- `source`: Path to file/directory (required)
- `name`: Backup name (optional, defaults to file/folder name)
- `max`: Max backups to keep (optional, defaults to 1)
- `exclude`: Patterns to exclude for directories (optional)

## Usage

### First Run (Authentication)

```bash
# Run any backup command
uv run python backup.py --mysql

# Follow the prompts:
# 1. Open the provided URL in any browser
# 2. Authorize the application
# 3. Copy the authorization code
# 4. Paste it back in the terminal
```

### Regular Usage

```bash
# Backup both MySQL and files
uv run python backup.py

# MySQL databases only
uv run python backup.py --mysql

# Files only
uv run python backup.py --files
```

## Automated Backups (Cron Setup)

### Quick Setup

1. **Find your uv path and test commands:**
   ```bash
   which uv
   cd /path/to/backup-manager-gdrive
   uv run python backup.py --mysql  # Test first
   ```

2. **Create log directory:**
   ```bash
   sudo mkdir -p /var/log && sudo chown $USER:$USER /var/log
   ```

3. **Add to crontab:**
   ```bash
   crontab -e
   ```

4. **Add these lines (update paths for your system):**
   ```bash
   # MySQL backup every hour
   0 * * * * cd /path/to/backup-manager-gdrive && /home/user/.local/bin/uv run python backup.py --mysql >> /var/log/backup.log 2>&1
   
   # Files backup twice daily (2 AM and 2 PM)
   0 2,14 * * * cd /path/to/backup-manager-gdrive && /home/user/.local/bin/uv run python backup.py --files >> /var/log/backup.log 2>&1
   ```

### Monitor Backups

```bash
# View current crontab
crontab -l

# Monitor logs in real-time
tail -f /var/log/backup.log

# View recent backup activity
tail -n 100 /var/log/backup.log

# Check cron service
sudo systemctl status cron
```

### Alternative Schedules

```bash
# Files backup every 12 hours
0 */12 * * * cd /path/to/backup-manager-gdrive && uv run python backup.py --files >> /var/log/backup.log 2>&1

# Full backup once daily at 3 AM
0 3 * * * cd /path/to/backup-manager-gdrive && uv run python backup.py >> /var/log/backup.log 2>&1
```

## Google Drive Organization

The tool automatically creates this folder structure in Google Drive:

```
Server Backups/
├── database/
│   ├── myserver-backup_mysql_20250822_101722.sql.gz
│   └── myserver-backup_mysql_20250822_111534.sql.gz
└── files/
    ├── myserver-backup_files_website_files_20250822_103731.tar.gz
    └── myserver-backup_files_apache_config_20250822_103745.tar.gz
```

## Backup Policies

- **Database backups**: Keep 50 recent backups (configurable)
- **File backups**: Individual max setting per file/directory in JSON config
- **Automatic cleanup**: Removes old backups when limits are exceeded
- **Selective backups**: Use `--mysql` or `--files` flags for specific backup types

## Security Notes

- OAuth2 credentials are stored locally (`credentials/` and `token.json`)
- Database passwords are in `.env` file - keep secure
- Consider using dedicated backup database user with minimal permissions
- Google Drive files are encrypted in transit and at rest

## Troubleshooting

### Cron Issues
```bash
# Test the exact command cron will run
cd /path/to/backup-manager-gdrive && /home/user/.local/bin/uv run python backup.py --mysql

# Check cron service
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog
```

### Authentication Issues
- Ensure `credentials/gdrive.json` is valid OAuth2 desktop application credentials
- Check Google Drive API is enabled in Google Cloud Console

### Database Issues  
- Ensure `mysqldump` is installed: `which mysqldump`
- Check database user permissions
- Test connection: `mysql -h localhost -u username -p`

### Permission Issues
- Ensure read access to all backup paths in `files_config.json`
- Check `/tmp/backup` directory is writable
- Verify log directory permissions: `ls -la /var/log/backup.log`

## Development

```bash
# Install in development mode
uv sync --dev

# Run with custom config
BACKUP_FILES_CONFIG_PATH=custom-config.json uv run python backup.py
```

## Architecture

The project uses clean separation of concerns:

- **`drive_manager.py`**: Handles all Google Drive operations (upload, folder creation, cleanup)
- **`mysql_backup.py`**: MySQL database dump logic with individual policies
- **`files_backup.py`**: File/directory backup with JSON configuration parsing
- **`service.py`**: Main orchestrator that coordinates all backup modules
- **`config.py`**: Pydantic v2 settings with environment variable support