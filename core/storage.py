"""
Custom Django storage backend using Supabase Storage REST API.
Uploads files to Supabase Storage bucket and returns public URLs.
"""
import os
import requests
from django.core.files.storage import Storage
from django.conf import settings
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    def __init__(self):
        self.supabase_url = getattr(settings, 'SUPABASE_URL', '')
        self.secret_key = getattr(settings, 'SUPABASE_SECRET_KEY', '')
        self.bucket = getattr(settings, 'SUPABASE_BUCKET', 'media')

    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'apikey': self.secret_key,
        }

    def _upload_url(self, name):
        return f'{self.supabase_url}/storage/v1/object/{self.bucket}/{name}'

    def _public_url(self, name):
        return f'{self.supabase_url}/storage/v1/object/public/{self.bucket}/{name}'

    def _save(self, name, content):
        # Sanitize name
        name = name.replace('\\', '/')
        content.seek(0)
        file_data = content.read()

        # Detect content type
        ext = os.path.splitext(name)[1].lower()
        content_types = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif',
            '.webp': 'image/webp', '.pdf': 'application/pdf',
        }
        content_type = content_types.get(ext, 'application/octet-stream')

        headers = self._get_headers()
        headers['Content-Type'] = content_type

        # Try upload, if exists use upsert
        url = self._upload_url(name)
        response = requests.post(url, data=file_data, headers=headers)

        if response.status_code == 409:
            # File exists — upsert
            headers['x-upsert'] = 'true'
            response = requests.post(url, data=file_data, headers=headers)

        if response.status_code not in (200, 201):
            raise Exception(f'Supabase upload failed: {response.status_code} {response.text}')

        return name

    def url(self, name):
        return self._public_url(name)

    def exists(self, name):
        # Check if file exists by trying to get its info
        url = f'{self.supabase_url}/storage/v1/object/info/public/{self.bucket}/{name}'
        response = requests.get(url, headers=self._get_headers())
        return response.status_code == 200

    def delete(self, name):
        url = f'{self.supabase_url}/storage/v1/object/{self.bucket}'
        requests.delete(url, json={'prefixes': [name]}, headers=self._get_headers())

    def size(self, name):
        return 0

    def get_available_name(self, name, max_length=None):
        # Add timestamp to avoid conflicts
        import time
        base, ext = os.path.splitext(name)
        return f'{base}_{int(time.time())}{ext}'
