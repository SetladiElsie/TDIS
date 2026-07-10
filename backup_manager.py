"""Database backup management"""

import os
import subprocess
import shutil
import json
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)


class BackupManager:
    """Manage database backups"""
    
    def __init__(self, backup_dir='backups'):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, db_type='sqlite'):
        """Create database backup"""
        try:
            if db_type == 'sqlite':
                return self._backup_sqlite()
            elif db_type == 'postgresql':
                return self._backup_postgresql()
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def _backup_sqlite(self):
        """Backup SQLite database"""
        try:
            db_path = os.getenv('DATABASE_URL', 'sqlite:///tender.db').replace('sqlite:///', '')
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'backup_sqlite_{timestamp}.db')
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                logger.info(f"SQLite backup created: {backup_path}")
                
                return {
                    'status': 'success',
                    'backup_path': backup_path,
                    'timestamp': timestamp,
                    'type': 'sqlite'
                }
            else:
                raise FileNotFoundError(f"Database not found: {db_path}")
        
        except Exception as e:
            logger.error(f"SQLite backup failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _backup_postgresql(self):
        """Backup PostgreSQL database"""
        try:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL not configured")
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'backup_postgres_{timestamp}.sql')
            
            # Parse connection string
            # postgresql://user:password@host:port/database
            import re
            match = re.match(
                r'postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<db>\w+)',
                db_url
            )
            
            if not match:
                raise ValueError("Invalid PostgreSQL connection string")
            
            env = os.environ.copy()
            env['PGPASSWORD'] = match.group('password')
            
            cmd = [
                'pg_dump',
                '-U', match.group('user'),
                '-h', match.group('host'),
                '-p', match.group('port'),
                '-d', match.group('db'),
                '-f', backup_path
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True)
            
            if result.returncode == 0:
                logger.info(f"PostgreSQL backup created: {backup_path}")
                return {
                    'status': 'success',
                    'backup_path': backup_path,
                    'timestamp': timestamp,
                    'type': 'postgresql'
                }
            else:
                raise RuntimeError(f"pg_dump failed: {result.stderr.decode()}")
        
        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def list_backups(self):
        """List all backups"""
        try:
            backups = []
            for filename in sorted(os.listdir(self.backup_dir)):
                filepath = os.path.join(self.backup_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    backups.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            return backups
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    def restore_backup(self, backup_filename, db_type='sqlite'):
        """Restore from backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup not found: {backup_path}")
            
            if db_type == 'sqlite':
                return self._restore_sqlite(backup_path)
            elif db_type == 'postgresql':
                return self._restore_postgresql(backup_path)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
        
        except Exception as e:
            logger.error(f"Backup restore failed: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def _restore_sqlite(self, backup_path):
        """Restore SQLite database"""
        try:
            db_path = os.getenv('DATABASE_URL', 'sqlite:///tender.db').replace('sqlite:///', '')
            
            # Create backup of current database
            current_backup = os.path.join(self.backup_dir, f'pre_restore_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.db')
            if os.path.exists(db_path):
                shutil.copy2(db_path, current_backup)
            
            # Restore backup
            shutil.copy2(backup_path, db_path)
            logger.info(f"SQLite restored from: {backup_path}")
            
            return {
                'status': 'success',
                'message': f'Restored from {backup_path}',
                'previous_backup': current_backup
            }
        
        except Exception as e:
            logger.error(f"SQLite restore failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _restore_postgresql(self, backup_path):
        """Restore PostgreSQL database"""
        try:
            db_url = os.getenv('DATABASE_URL')
            
            import re
            match = re.match(
                r'postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<db>\w+)',
                db_url
            )
            
            if not match:
                raise ValueError("Invalid PostgreSQL connection string")
            
            env = os.environ.copy()
            env['PGPASSWORD'] = match.group('password')
            
            cmd = [
                'psql',
                '-U', match.group('user'),
                '-h', match.group('host'),
                '-p', match.group('port'),
                '-d', match.group('db'),
                '-f', backup_path
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True)
            
            if result.returncode == 0:
                logger.info(f"PostgreSQL restored from: {backup_path}")
                return {
                    'status': 'success',
                    'message': f'Restored from {backup_path}'
                }
            else:
                raise RuntimeError(f"psql restore failed: {result.stderr.decode()}")
        
        except Exception as e:
            logger.error(f"PostgreSQL restore failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def delete_backup(self, backup_filename):
        """Delete a backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup not found: {backup_path}")
            
            os.remove(backup_path)
            logger.info(f"Backup deleted: {backup_path}")
            
            return {'status': 'success', 'message': f'Backup deleted: {backup_filename}'}
        
        except Exception as e:
            logger.error(f"Backup deletion failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def get_backup_stats(self):
        """Get backup statistics"""
        try:
            backups = self.list_backups()
            total_size = sum(b['size'] for b in backups)
            
            return {
                'total_backups': len(backups),
                'total_size': total_size,
                'backups': backups
            }
        except Exception as e:
            logger.error(f"Failed to get backup stats: {str(e)}")
            return {'error': str(e)}
