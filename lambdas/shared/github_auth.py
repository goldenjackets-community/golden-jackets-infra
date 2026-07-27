"""
GitHub App Authentication for Golden Jackets Lambdas.
Generates installation tokens dynamically — no static PAT needed.

Usage:
    from github_auth import get_installation_token
    token = get_installation_token()
    # Use token in Authorization header: f'token {token}'
"""

import json
import os
import time
import urllib.request
import hmac
import hashlib
import base64
import struct

# Config from environment
APP_ID = os.environ.get('GH_APP_ID', '4409622')
PRIVATE_KEY = os.environ.get('GH_APP_PRIVATE_KEY', '')
INSTALLATION_ID = os.environ.get('GH_APP_INSTALLATION_ID', '')

# Token cache (Lambda container reuse)
_cached_token = None
_cached_expiry = 0


def _base64url_encode(data):
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=')


def _create_jwt():
    """Create a JWT signed with the GitHub App private key (RS256)."""
    now = int(time.time())
    payload = {
        'iat': now - 60,  # Issued at (60s in past for clock drift)
        'exp': now + (10 * 60),  # Expires in 10 minutes
        'iss': APP_ID
    }

    # Header
    header = json.dumps({'alg': 'RS256', 'typ': 'JWT'}).encode()

    # We need to sign with RSA — use the subprocess approach since
    # Lambda doesn't have PyJWT by default but has openssl
    import subprocess
    import tempfile

    # Write key to temp file
    key_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
    key_file.write(PRIVATE_KEY.replace('\\n', '\n'))
    key_file.close()

    # Create JWT parts
    header_b64 = _base64url_encode(json.dumps({'alg': 'RS256', 'typ': 'JWT'}).encode()).decode()
    payload_b64 = _base64url_encode(json.dumps(payload).encode()).decode()
    message = f'{header_b64}.{payload_b64}'

    # Sign with openssl
    try:
        result = subprocess.run(
            ['openssl', 'dgst', '-sha256', '-sign', key_file.name],
            input=message.encode(),
            capture_output=True
        )
        signature = _base64url_encode(result.stdout).decode()
    finally:
        os.unlink(key_file.name)

    return f'{message}.{signature}'


def _get_installation_id():
    """Get the installation ID for the org (cached in env var or fetched once)."""
    if INSTALLATION_ID:
        return INSTALLATION_ID

    jwt = _create_jwt()
    req = urllib.request.Request(
        'https://api.github.com/app/installations',
        headers={
            'Authorization': f'Bearer {jwt}',
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'gj-automation'
        }
    )
    resp = urllib.request.urlopen(req)
    installations = json.loads(resp.read().decode())

    # Find goldenjackets-community installation
    for inst in installations:
        if inst.get('account', {}).get('login') == 'goldenjackets-community':
            return str(inst['id'])

    # Fallback: first installation
    if installations:
        return str(installations[0]['id'])

    raise Exception('No GitHub App installation found for goldenjackets-community')


def get_installation_token():
    """
    Get a valid installation token. Caches for reuse within Lambda container.
    Returns a token string ready to use in: Authorization: token <TOKEN>
    """
    global _cached_token, _cached_expiry

    # Return cached token if still valid (with 5 min buffer)
    if _cached_token and time.time() < (_cached_expiry - 300):
        return _cached_token

    installation_id = _get_installation_id()
    jwt = _create_jwt()

    req = urllib.request.Request(
        f'https://api.github.com/app/installations/{installation_id}/access_tokens',
        method='POST',
        headers={
            'Authorization': f'Bearer {jwt}',
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'gj-automation'
        }
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())

    _cached_token = data['token']
    # Token expires in 1 hour by default
    _cached_expiry = time.time() + 3600

    return _cached_token
