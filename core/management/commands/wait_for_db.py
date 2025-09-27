"""
Django command to wait for database availability
"""

from django.core.management.base import BaseCommand
from django.db import connections, connection
from django.db.utils import OperationalError
import time
import sys


class Command(BaseCommand):
    """Django command to wait for database"""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write('Waiting for Database...')
        
        max_retries = 30  # Maximum 60 seconds (30 * 2 seconds)
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Close any existing connections first
                connection.close()
                
                # Get fresh connection
                db_conn = connections['default']
                
                # Test the connection with a simple query
                with db_conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    result = cursor.fetchone()
                    if result[0] == 1:
                        self.stdout.write(self.style.SUCCESS('Database available!'))
                        
                        # Additional stability check - wait a bit more and test again
                        time.sleep(2)
                        with db_conn.cursor() as cursor:
                            cursor.execute('SELECT version()')
                            cursor.fetchone()
                        
                        self.stdout.write(self.style.SUCCESS('Database connection stable!'))
                        return
                
            except OperationalError as e:
                retry_count += 1
                self.stdout.write(f'Database unavailable (attempt {retry_count}/{max_retries}): {e}')
                time.sleep(2)
                
            except Exception as e:
                retry_count += 1
                self.stdout.write(f'Database error (attempt {retry_count}/{max_retries}): {e}')
                time.sleep(2)
        
        self.stdout.write(self.style.ERROR('Database failed to become available!'))
        sys.exit(1)
