import json
import urllib.request
import base64
import os

GITHUB_TOKEN = os.environ.get('GH_TOKEN', '')
REPO_MAP = {
    'goldenjackets.by': 'goldenjackets-community/golden-jackets-by',
    'www.goldenjackets.by': 'goldenjackets-community/golden-jackets-by',
    'goldenjackets.co.il': 'goldenjackets-community/golden-jackets-israel',
    'www.goldenjackets.co.il': 'goldenjackets-community/golden-jackets-israel',
    'goldenjackets.us': 'goldenjackets-community/golden-jackets-usa',
    'www.goldenjackets.us': 'goldenjackets-community/golden-jackets-usa',
    'goldenjackets.fr': 'goldenjackets-community/golden-jackets-france',
    'www.goldenjackets.fr': 'goldenjackets-community/golden-jackets-france',
    'goldenjackets.it': 'goldenjackets-community/golden-jackets-italy',
    'www.goldenjackets.it': 'goldenjackets-community/golden-jackets-italy',
    'goldenjackets.pe': 'goldenjackets-community/golden-jackets-peru',
    'www.goldenjackets.pe': 'goldenjackets-community/golden-jackets-peru',
    'goldenjackets.in': 'goldenjackets-community/golden-jackets-india',
    'www.goldenjackets.in': 'goldenjackets-community/golden-jackets-india',
    'goldenjacketsbrazil.com': 'goldenjackets-community/golden-jackets-brazil',
    'www.goldenjacketsbrazil.com': 'goldenjackets-community/golden-jackets-brazil',
    'goldenjackets.pl': 'goldenjackets-community/golden-jackets-poland',
    'www.goldenjackets.pl': 'goldenjackets-community/golden-jackets-poland',
    'goldenjackets.co.uk': 'goldenjackets-community/golden-jackets-uk',
    'www.goldenjackets.co.uk': 'goldenjackets-community/golden-jackets-uk',
    'goldenjackets.cl': 'goldenjackets-community/golden-jackets-chile',
    'www.goldenjackets.cl': 'goldenjackets-community/golden-jackets-chile',
    'goldenjackets.co': 'goldenjackets-community/golden-jackets-colombia',
    'www.goldenjackets.co': 'goldenjackets-community/golden-jackets-colombia',
}

SNS_TOPIC_MAP = {
    'goldenjackets-community/golden-jackets-brazil': 'arn:aws:sns:us-east-1:800712212925:goldenjackets-alerts',
    'goldenjackets-community/golden-jackets-poland': 'arn:aws:sns:us-east-1:800712212925:gj-poland-alerts',
    'goldenjackets-community/golden-jackets-uk': 'arn:aws:sns:us-east-1:800712212925:gj-uk-alerts',
    'goldenjackets-community/golden-jackets-chile': 'arn:aws:sns:us-east-1:800712212925:gj-chile-alerts',
    'goldenjackets-community/golden-jackets-france': 'arn:aws:sns:us-east-1:800712212925:gj-france-alerts',
    'goldenjackets-community/golden-jackets-italy': 'arn:aws:sns:us-east-1:800712212925:gj-italy-alerts',
    'goldenjackets-community/golden-jackets-india': 'arn:aws:sns:us-east-1:800712212925:gj-india-alerts',
    'goldenjackets-community/golden-jackets-usa': 'arn:aws:sns:us-east-1:800712212925:gj-usa-alerts',
    'goldenjackets-community/golden-jackets-peru': 'arn:aws:sns:us-east-1:800712212925:gj-peru-alerts',
    'goldenjackets-community/golden-jackets-colombia': 'arn:aws:sns:us-east-1:800712212925:gj-colombia-alerts',
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

def build_card(name, city, state, date, linkedin, member_type, photo_path, card_number=None):
    import re as _re
    initials = ''.join([w[0].upper() for w in name.split()[:2]])
    photo_html = f'<img src="{photo_path}" alt="{name}" class="photo">' if photo_path else f'<div class="avatar">{initials}</div>'
    number_html = f'<span class="card-number">#{card_number}</span>\n        ' if card_number else ''
    if member_type == 'golden':
        return f"""      <div class="member-card" data-state="{state}">
        {number_html}{photo_html}
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
    elif member_type == 'alumni':
        return f"""      <div class="member-card alumni" data-state="{state}">
        {number_html}{photo_html}
        <h3>{name}</h3>
        <div class="location">{city}</div>
        <div class="tags">
          <span class="tag">Alumni</span>
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
        {number_html}{photo_html}
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

        # Auto-append country to city based on chapter origin
        COUNTRY_APPEND = {
            'goldenjackets-community/golden-jackets-uk': lambda s, c: f"{c}, {'Scotland' if s in ('SC','SCT') else 'Wales' if s in ('WA','WAL') else 'Northern Ireland' if s in ('NI','NIR') else 'England'}, United Kingdom" if 'United Kingdom' not in c else c,
            'goldenjackets-community/golden-jackets-brazil': lambda s, c: f"{c}, Brazil" if 'Brazil' not in c and 'Brasil' not in c else c,
            'goldenjackets-community/golden-jackets-chile': lambda s, c: f"{c}, Chile" if 'Chile' not in c else c,
            'goldenjackets-community/golden-jackets-india': lambda s, c: f"{c}, India" if 'India' not in c else c,
            'goldenjackets-community/golden-jackets-france': lambda s, c: f"{c}, France" if 'France' not in c else c,
            'goldenjackets-community/golden-jackets-italy': lambda s, c: f"{c}, Italy" if 'Italy' not in c and 'Italia' not in c else c,
            'goldenjackets-community/golden-jackets-usa': lambda s, c: f"{c}, USA" if 'USA' not in c and 'United States' not in c else c,
            'goldenjackets-community/golden-jackets-poland': lambda s, c: f"{c}, Poland" if 'Poland' not in c and 'Polska' not in c else c,
            'goldenjackets-community/golden-jackets-peru': lambda s, c: f"{c}, Peru" if 'Peru' not in c else c,
            'goldenjackets-community/golden-jackets-colombia': lambda s, c: f"{c}, Colombia" if 'Colombia' not in c else c,
        }
        if REPO in COUNTRY_APPEND:
            city = COUNTRY_APPEND[REPO](state, city)
        date = body.get('date', '')
        linkedin = body['linkedin']
        email = body.get('email', '')
        member_type = body.get('memberType', 'golden')
        photo_b64 = body.get('photo', '')
        photo_name = body.get('photoName', '')
        consent = body.get('consentAccepted', False)
        consent_date = body.get('consentDate', '')

        import unicodedata
        safe_name = unicodedata.normalize('NFD', name.lower()).encode('ascii', 'ignore').decode('ascii')
        safe_name = safe_name.replace(' ', '-').replace('.', '').replace("'", '')
        photo_ext = photo_name.split('.')[-1] if photo_name else 'jpg'
        photo_path = f'assets/members/{safe_name}.{photo_ext}'
        branch = f'add-member-{safe_name}'

        # Get default branch SHA
        default_branch = 'main'
        try:
            ref_data = gh_api('GET', 'git/ref/heads/main', repo=REPO)
        except:
            ref_data = gh_api('GET', 'git/ref/heads/master', repo=REPO)
            default_branch = 'master'
        sha = ref_data['object']['sha']

        # Create branch (delete if already exists to avoid stale SHA issues)
        result = gh_api('POST', 'git/refs', {'ref': f'refs/heads/{branch}', 'sha': sha}, repo=REPO)
        if result.get('exists'):
            try:
                gh_api('DELETE', f'git/refs/heads/{branch}', repo=REPO)
            except:
                pass
            gh_api('POST', 'git/refs', {'ref': f'refs/heads/{branch}', 'sha': sha}, repo=REPO)

        # Upload photo (include sha if file already exists in branch)
        if photo_b64:
            payload = {'message': f'Add photo for {name}', 'content': photo_b64, 'branch': branch}
            try:
                existing = gh_api('GET', f'contents/{photo_path}?ref={branch}', repo=REPO)
                if existing.get('sha'):
                    payload['sha'] = existing['sha']
            except:
                pass
            gh_api('PUT', f'contents/{photo_path}', payload, repo=REPO)

        # Get index.html and add card
        index_content, index_sha = get_file('index.html', branch, repo=REPO)
        if index_content:
            import re

            # Skip card insertion if member already exists in index.html (prevents duplicates on rebuild)
            if name in index_content:
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


_Rebuilt automatically after PR merge to avoid conflicts._"""
                pr_data = gh_api('POST', 'pulls', {
                    'title': f'New Member: {name}',
                    'body': pr_body,
                    'head': branch,
                    'base': default_branch
                }, repo=REPO)

                return {
                    'statusCode': 200,
                    'headers': cors,
                    'body': json.dumps({'message': f"Member already on site. PR #{pr_data.get('number','')} created (photo only).", 'pr': pr_data.get('html_url','')})
                }

            # Count existing cards to determine card number
            if member_type == 'golden' or member_type == '':
                existing = len(re.findall(r'<div class="member-card[^"]*"[^>]*data-state', index_content.split('id="alumni"')[0] if 'id="alumni"' in index_content else index_content))
            elif member_type == 'alumni':
                alumni_section = index_content.split('id="alumni"')[1].split('</section>')[0] if 'id="alumni"' in index_content else ''
                existing = len(re.findall(r'<div class="member-card', alumni_section))
            else:
                chall_section = index_content.split('id="challengers"')[1].split('</section>')[0] if 'id="challengers"' in index_content else ''
                existing = len(re.findall(r'<div class="member-card', chall_section))
            card_number = existing + 1

            card = build_card(name, city, state, date, linkedin, member_type, photo_path, card_number)

            if member_type == 'golden' or member_type == '':
                # Primary: use END_GOLDEN_JACKETS marker (exists in all chapter sites)
                if '<!-- END_GOLDEN_JACKETS -->' in index_content:
                    index_content = index_content.replace('<!-- END_GOLDEN_JACKETS -->', card + '\n<!-- END_GOLDEN_JACKETS -->', 1)
                else:
                    # Fallback: find closing </div>\n</section> after members-grid
                    m = re.search(r'(    </div>\s*\n  </section>\s*\n(?:<!-- Alumni|<!-- Challengers))', index_content)
                    if m:
                        index_content = index_content.replace(m.group(1), card + '\n' + m.group(1), 1)
            elif member_type == 'alumni':
                # Insert before closing of alumni section grid
                m = re.search(r'(<!-- Alumni cards go here -->|<!-- END_ALUMNI -->)', index_content)
                if m:
                    index_content = index_content.replace(m.group(1), card + '\n      ' + m.group(1), 1)
                else:
                    # Find alumni section's closing </div>\n  </section>
                    parts = index_content.split('id="alumni"')
                    if len(parts) > 1:
                        alumni_part = parts[1]
                        m2 = re.search(r'(    </div>\s*\n  </section>)', alumni_part)
                        if m2:
                            index_content = index_content.replace('id="alumni"' + alumni_part[:m2.start()] + m2.group(1), 'id="alumni"' + alumni_part[:m2.start()] + card + '\n' + m2.group(1), 1)
            else:
                # Challengers
                m = re.search(r'(<!-- Challenger cards go here -->|<!-- END_CHALLENGERS -->)', index_content)
                if m:
                    index_content = index_content.replace(m.group(1), card + '\n      ' + m.group(1), 1)
                else:
                    parts = index_content.split('id="challengers"')
                    if len(parts) > 1:
                        chall_part = parts[1]
                        m2 = re.search(r'(    </div>\s*\n  </section>)', chall_part)
                        if m2:
                            index_content = index_content.replace('id="challengers"' + chall_part[:m2.start()] + m2.group(1), 'id="challengers"' + chall_part[:m2.start()] + card + '\n' + m2.group(1), 1)

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
            'base': default_branch
        }, repo=REPO)

        # Send SNS notification (non-blocking - PR already created)
        try:
            import boto3
            sns = boto3.client('sns', region_name='us-east-1')
            topic_arn = SNS_TOPIC_MAP.get(REPO, 'arn:aws:sns:us-east-1:800712212925:goldenjackets-alerts')
            sns.publish(
                TopicArn=topic_arn,
                Subject=f'🆕 New Member Application: {name}',
                Message=f'Name: {name}\nCity: {city}\nState: {state}\nType: {member_type}\nLinkedIn: {linkedin}\nEmail: {email}\n\nPR created on GitHub.'
            )
        except Exception:
            pass  # PR already created, don't fail the response

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
