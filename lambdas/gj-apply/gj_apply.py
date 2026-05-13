import json
import urllib.request
import base64
import os

GITHUB_TOKEN = os.environ.get('GH_TOKEN', '')
REPO_MAP = {
    'goldenjacketsbrazil.com': 'goldenjackets-community/golden-jackets-brazil',
    'www.goldenjacketsbrazil.com': 'goldenjackets-community/golden-jackets-brazil',
    'goldenjackets.pl': 'goldenjackets-community/golden-jackets-poland',
    'www.goldenjackets.pl': 'goldenjackets-community/golden-jackets-poland',
}
DEFAULT_REPO = os.environ.get('GITHUB_REPO', 'goldenjackets-community/golden-jackets-brazil')

def gh_api(method, path, data=None, repo=None):
    r = repo or DEFAULT_REPO
    url = f'https://api.github.com/repos/{r}/{path}'
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
        headers={'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'})
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        if e.code == 422 and 'already exists' in err_body:
            return {'exists': True}
        raise Exception(f'HTTP Error {e.code}: {err_body[:200]}')

def get_file(path, branch, repo=None):
    try:
        data = gh_api('GET', f'contents/{path}?ref={branch}', repo=repo)
        content = base64.b64decode(data['content']).decode()
        return content, data['sha']
    except:
        return None, None

def put_file(path, content, message, branch, sha=None, repo=None):
    payload = {'message': message, 'content': base64.b64encode(content.encode()).decode(), 'branch': branch}
    if sha:
        payload['sha'] = sha
    return gh_api('PUT', f'contents/{path}', payload, repo=repo)

def build_card(name, city, state, date, linkedin, member_type, photo_path):
    if member_type == 'golden':
        return f"""      <div class="member-card" data-state="{state}">
        <img src="{photo_path}" alt="{name}" class="photo">
        <h3>{name}</h3>
        <div class="location">{city}</div>
        <div class="tags">
          <span class="tag">Golden Jacket</span>
          <span class="tag">Member</span>
        </div>
        <div class="certified">Certified on {date}</div>
        <div class="socials">
          <a href="{linkedin}" target="_blank">in</a>
        </div>
      </div>"""
    else:
        certs = '11' if '11' in member_type else '10'
        away = '1' if certs == '11' else '2'
        return f"""      <div class="member-card challenger" data-state="{state}">
        <img src="{photo_path}" alt="{name}" class="photo">
        <h3>{name}</h3>
        <div class="location">{city}</div>
        <div class="tags">
          <span class="tag">{certs}/12 Certifications</span>
          <span class="tag">Challenger</span>
        </div>
        <div class="certified" style="color:#fff;font-weight:700;">{away} away from Golden Jacket \U0001f525</div>
        <div class="socials">
          <a href="{linkedin}" target="_blank">in</a>
        </div>
      </div>"""

def lambda_handler(event, context):
    cors = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }

    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {'statusCode': 200, 'headers': cors, 'body': ''}

    try:
        # Detect which chapter based on origin header
        origin = event.get('headers', {}).get('origin', '')
        origin_host = origin.replace('https://', '').replace('http://', '').rstrip('/')
        REPO = REPO_MAP.get(origin_host, DEFAULT_REPO)

        body = json.loads(event.get('body', '{}'))
        name = body['name']
        city = body['city']
        state = body['state']
        date = body.get('date', '')
        linkedin = body['linkedin']
        email = body.get('email', '')
        member_type = body.get('memberType', 'golden')
        photo_b64 = body.get('photo', '')
        photo_name = body.get('photoName', '')
        consent = body.get('consentAccepted', False)
        consent_date = body.get('consentDate', '')

        safe_name = name.lower().replace(' ', '-').replace('.', '').replace("'", '')
        photo_ext = photo_name.split('.')[-1] if photo_name else 'jpg'
        photo_path = f'assets/members/{safe_name}.{photo_ext}'
        branch = f'add-member-{safe_name}'

        # Get main branch SHA
        ref_data = gh_api('GET', 'git/ref/heads/main')
        sha = ref_data['object']['sha']

        # Create branch
        gh_api('POST', 'git/refs', {'ref': f'refs/heads/{branch}', 'sha': sha}, repo=REPO)

        # Upload photo
        if photo_b64:
            put_file(photo_path, '', f'Add photo for {name}', branch, repo=REPO)
            # Use raw API for binary
            payload = {'message': f'Add photo for {name}', 'content': photo_b64, 'branch': branch}
            gh_api('PUT', f'contents/{photo_path}', payload, repo=REPO)

        # Get index.html and add card
        index_content, index_sha = get_file('index.html', branch, repo=REPO)
        if index_content:
            card = build_card(name, city, state, date, linkedin, member_type, photo_path)
            if member_type == 'golden' or member_type == '':
                marker = '<!-- END_GOLDEN -->'
                if marker not in index_content:
                    marker = '\U0001f396\ufe0f Alumni'
            else:
                marker = '<!-- END_CHALLENGERS -->'
            
            if marker in index_content:
                index_content = index_content.replace(marker, card + '\n' + marker)
                put_file('index.html', index_content, f'Add member card: {name}', branch, index_sha, repo=REPO)

        # Create PR
        pr_body = f"""## New Member Application

**Name:** {name}
**City:** {city}
**State:** {state}
**Certified Date:** {date}
**LinkedIn:** {linkedin}
**Email:** {email}
**Type:** {member_type}
**Photo:** {photo_path}
**Consent:** {consent} ({consent_date})

---
_Auto-generated by the Golden Jackets apply form._
"""
        pr_data = gh_api('POST', 'pulls', {
            'title': f'New Member: {name}',
            'body': pr_body,
            'head': branch,
            'base': 'main'
        }, repo=REPO)

        return {
            'statusCode': 200,
            'headers': cors,
            'body': json.dumps({'message': f"Application submitted! PR #{pr_data.get('number','')} created.", 'pr': pr_data.get('html_url','')})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': cors,
            'body': json.dumps({'error': str(e)})
        }
