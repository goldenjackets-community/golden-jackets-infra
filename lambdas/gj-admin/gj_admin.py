import traceback
import json
import boto3
import urllib.request
import os
import time

def trunc_subject(s): return s[:100]

cognito = boto3.client('cognito-idp', region_name='us-east-1')
backup = boto3.client('backup', region_name='us-east-1')
POOL_ID = 'us-east-1_Z0VzzrmIX'

# Global admins can see all chapters
GLOBAL_ADMINS = ['ricardo.gulias@goldenjacketsbrazil.com', 'erickmancz@gmail.com', 'wagnermazevedo@hotmail.com']

def get_caller_email(event):
    claims = event.get('requestContext', {}).get('authorizer', {}).get('jwt', {}).get('claims', {})
    return claims.get('email', '')

def get_user_groups(email):
    try:
        resp = cognito.admin_list_groups_for_user(UserPoolId=POOL_ID, Username=email)
        return [g['GroupName'] for g in resp['Groups']]
    except:
        return []

def get_users_in_group(group):
    users = []
    try:
        params = {'UserPoolId': POOL_ID, 'GroupName': group, 'Limit': 60}
        while True:
            resp = cognito.list_users_in_group(**params)
            for u in resp['Users']:
                email = next((a['Value'] for a in u['Attributes'] if a['Name'] == 'email'), '')
                users.append({
                    'email': email,
                    'status': u['UserStatus'],
                    'created': u['UserCreateDate'].isoformat()
                })
            if 'NextToken' not in resp:
                break
            params['NextToken'] = resp['NextToken']
    except:
        pass
    return users


# --- PR Management ---

def github_api(method, path, body=None):
    token = os.environ.get('GITHUB_TOKEN', '')
    url = f'https://api.github.com{path}'
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'gj-admin'}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def list_prs(chapter):
    repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
    repo = repo_map.get(chapter, '')
    if not repo:
        return []
    result = github_api('GET', f'/repos/goldenjackets-community/{repo}/pulls?state=open')
    if isinstance(result, list):
        prs = []
        for pr in result:
            item = {'number': pr['number'], 'title': pr['title'], 'author': pr['user']['login'], 'created_at': pr['created_at'], 'body': pr.get('body', ''), 'type': 'member' if 'New Member' in pr['title'] or 'Add member' in pr['title'] else 'article'}
            prs.append(item)
        return prs
    return []

def merge_pr(chapter, pr_number):
    # Duplicate removed - see definition at line ~656
    pass


def close_pr(chapter, pr_number):
    repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
    repo = repo_map.get(chapter, '')
    if not repo:
        return {'error': 'Invalid chapter'}
    return github_api('PATCH', f'/repos/goldenjackets-community/{repo}/pulls/{pr_number}', {'state': 'closed'})


def rebuild_remaining_prs(chapter, merged_pr_number):
    """After merging a PR, rebuild other open article PRs to avoid conflicts."""
    import base64 as b64, re
    repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
    repo = repo_map.get(chapter, '')
    if not repo:
        return
    org = 'goldenjackets-community'
    open_prs = github_api('GET', f'/repos/{org}/{repo}/pulls?state=open')
    if not isinstance(open_prs, list):
        return
    article_prs = [pr for pr in open_prs if pr['number'] != merged_pr_number and '📝' in pr.get('title', '')]
    if not article_prs:
        return
    for pr in article_prs:
        try:
            pr_body = pr.get('body', '')
            pr_title = pr.get('title', '')
            old_branch = pr['head']['ref']
            url_match = re.search(r'\*\*URL:\*\*\s*(https?://[^\s\n]+)', pr_body)
            summary_match = re.search(r'\*\*Summary:\*\*\s*([^\n]+)', pr_body)
            author_match = re.search(r'\*\*Author:\*\*\s*([^\n]+)', pr_body)
            if not url_match:
                continue
            url = url_match.group(1)
            summary = summary_match.group(1) if summary_match else ''
            author = author_match.group(1) if author_match else 'Unknown'
            title = pr_title.replace('📝 New article: ', '')
            # Close old PR and delete branch
            github_api('PATCH', f'/repos/{org}/{repo}/pulls/{pr["number"]}', {'state': 'closed'})
            github_api('DELETE', f'/repos/{org}/{repo}/git/refs/heads/{old_branch}')
            # Get fresh default branch
            default_branch = 'main'
            ref_data = github_api('GET', f'/repos/{org}/{repo}/git/ref/heads/main')
            if 'object' not in ref_data:
                ref_data = github_api('GET', f'/repos/{org}/{repo}/git/ref/heads/master')
                default_branch = 'master'
            master_sha = ref_data['object']['sha']
            # Create new branch
            new_branch = old_branch.split('-rebuild')[0] + '-r' + str(merged_pr_number)
            github_api('POST', f'/repos/{org}/{repo}/git/refs', {'ref': f'refs/heads/{new_branch}', 'sha': master_sha})
            # Get current index.html
            index_data = github_api('GET', f'/repos/{org}/{repo}/contents/index.html?ref={new_branch}')
            content = b64.b64decode(index_data['content']).decode()
            file_sha = index_data['sha']
            # Build article card
            from datetime import datetime
            date_str = datetime.utcnow().strftime('%b %d, %Y')
            article_card = f'<div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:12px;transition:all 0.3s;" onmouseover="this.style.borderColor=\'rgba(255,215,0,0.4)\'" onmouseout="this.style.borderColor=\'var(--border)\'">\n        <p style="color:var(--text-muted);font-size:0.7em;margin-bottom:4px;"><span style="background:rgba(255,215,0,0.15);color:var(--gold);padding:2px 8px;border-radius:4px;font-size:0.9em;font-weight:600;margin-right:6px;">📝 Article</span> {date_str} · <span style="color:var(--gold);font-style:italic;">{author}</span></p>\n        <a href="{url}" target="_blank" rel="noopener noreferrer" style="color:var(--gold);font-weight:700;font-size:1em;text-decoration:none;">{title}</a>\n        <p style="color:var(--text-muted);font-size:0.85em;margin-top:6px;">{summary}</p>\n      </div>\n'
            marker = '<!-- END_ARTICLES -->'
            if marker in content:
                content = content.replace(marker, article_card + '        ' + marker)
            new_b64 = b64.b64encode(content.encode()).decode()
            github_api('PUT', f'/repos/{org}/{repo}/contents/index.html', {'message': f'Add article: {title}', 'content': new_b64, 'branch': new_branch, 'sha': file_sha})
            # Create new PR
            github_api('POST', f'/repos/{org}/{repo}/pulls', {'title': pr_title, 'head': new_branch, 'base': default_branch, 'body': pr_body})
        except:
            continue

def lambda_handler(event, context):
    cors = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }

    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {'statusCode': 200, 'headers': cors, 'body': ''}

    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action', '')
        chapter = body.get('chapter', '')

        # Get caller identity
        caller_email = get_caller_email(event)
        caller_groups = get_user_groups(caller_email)
        is_global_admin = caller_email in GLOBAL_ADMINS

        # If no chapter specified, detect from origin header or use caller's first group
        if not chapter:
            origin = event.get('headers', {}).get('origin', '')
            origin_host = origin.replace('https://', '').replace('http://', '').rstrip('/')
            origin_chapter_map = {'goldenjacketsbrazil.com': 'brazil', 'www.goldenjacketsbrazil.com': 'brazil', 'goldenjackets.pl': 'poland', 'www.goldenjackets.pl': 'poland', 'goldenjackets.co.uk': 'uk', 'www.goldenjackets.co.uk': 'uk'}
            chapter = origin_chapter_map.get(origin_host, '')
        if not chapter and caller_groups:
            chapter = caller_groups[0]

        # Verify caller has access to requested chapter
        # Skip chapter check for actions that don't need it
        skip_chapter_actions = ['post-job', 'list-jobs', 'delete-job', 'apply-job', 'submit-article', 'suggest-topic']
        if not is_global_admin and chapter not in caller_groups and action not in skip_chapter_actions:
            return {'statusCode': 403, 'headers': cors, 'body': json.dumps({'error': 'Access denied to this chapter'})}

        if action == 'list-users':
            if is_global_admin and not chapter:
                # Global admin without chapter filter: show all
                users = []
                resp = cognito.list_users(UserPoolId=POOL_ID)
                for u in resp['Users']:
                    email = next((a['Value'] for a in u['Attributes'] if a['Name'] == 'email'), '')
                    users.append({
                        'email': email,
                        'status': u['UserStatus'],
                        'created': u['UserCreateDate'].isoformat()
                    })
            else:
                users = get_users_in_group(chapter)
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'users': users, 'chapter': chapter})}

        elif action == 'create-user':
            email = body.get('email', '')
            if not email:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'email required'})}
            cognito.admin_create_user(
                UserPoolId=POOL_ID,
                Username=email,
                UserAttributes=[{'Name': 'email', 'Value': email}, {'Name': 'email_verified', 'Value': 'true'}],
                DesiredDeliveryMediums=['EMAIL']
            )
            # Add user to the chapter group
            if chapter:
                cognito.admin_add_user_to_group(UserPoolId=POOL_ID, Username=email, GroupName=chapter)
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': f'User {email} created in {chapter}'})}

        elif action == 'delete-user':
            email = body.get('email', '')
            if not email:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'email required'})}
            # Verify user belongs to caller's chapter
            target_groups = get_user_groups(email)
            if not is_global_admin and chapter not in target_groups:
                return {'statusCode': 403, 'headers': cors, 'body': json.dumps({'error': 'Cannot delete user from another chapter'})}
            cognito.admin_delete_user(UserPoolId=POOL_ID, Username=email)
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': f'User {email} deleted'})}

        elif action == 'resend-pending':
            users = get_users_in_group(chapter) if chapter else []
            resent = []
            for u in users:
                if u['status'] == 'FORCE_CHANGE_PASSWORD':
                    try:
                        cognito.admin_create_user(
                            UserPoolId=POOL_ID,
                            Username=u['email'],
                            MessageAction='RESEND',
                            DesiredDeliveryMediums=['EMAIL']
                        )
                        resent.append(u['email'])
                    except:
                        pass
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'resent': resent, 'count': len(resent)})}

        elif action == 'backup-status':
            vault = {'poland': 'gj-poland-backups', 'uk': 'gj-uk-backups'}.get(chapter, 'gj-site-backups')
            jobs = backup.list_backup_jobs(MaxResults=10, ByBackupVaultName=vault)
            result = []
            for j in jobs.get('BackupJobs', []):
                result.append({
                    'status': j['State'],
                    'resource': j.get('ResourceArn', 'N/A').split(':')[-1],
                    'date': j.get('CreationDate', '').isoformat() if hasattr(j.get('CreationDate', ''), 'isoformat') else str(j.get('CreationDate', ''))
                })
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'jobs': result})}

        elif action == 'restore-backup':
            if not is_global_admin:
                return {'statusCode': 403, 'headers': cors, 'body': json.dumps({'error': 'Only global admins can restore backups'})}
            vault = {'poland': 'gj-poland-backups', 'uk': 'gj-uk-backups'}.get(chapter, 'gj-site-backups')
            bucket = 'goldenjackets.pl' if chapter == 'poland' else 'www.goldenjacketsbrazil.com'
            jobs = backup.list_backup_jobs(MaxResults=1, ByBackupVaultName=vault, ByState='COMPLETED')
            if not jobs.get('BackupJobs'):
                return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': 'No completed backups found yet'})}
            rp = jobs['BackupJobs'][0].get('RecoveryPointArn', '')
            backup.start_restore_job(
                RecoveryPointArn=rp,
                IamRoleArn='arn:aws:iam::800712212925:role/gj-backup-role',
                Metadata={'NewBucketName': bucket, 'Encrypted': 'false'}
            )
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': 'Restore started from latest backup'})}

        elif action == 'submit-article':
            import urllib.request
            import base64
            import os
            title = body.get('title', '')
            url = body.get('url', '')
            summary = body.get('summary', '')
            author = body.get('author', 'unknown')
            GH_TOKEN = os.environ.get('GITHUB_TOKEN', '')
            article_repo_map = {'brazil': 'goldenjackets-community/golden-jackets-brazil', 'poland': 'goldenjackets-community/golden-jackets-poland', 'uk': 'goldenjackets-community/golden-jackets-uk'}
            REPO = article_repo_map.get(chapter, 'goldenjackets-community/golden-jackets-brazil')

            def gh_api(method, path, data=None):
                api_url = f'https://api.github.com/repos/{REPO}/{path}'
                req_body = json.dumps(data).encode() if data else None
                req = urllib.request.Request(api_url, data=req_body, method=method, headers={'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'})
                try:
                    resp = urllib.request.urlopen(req)
                    return json.loads(resp.read())
                except urllib.error.HTTPError as e:
                    err_body = e.read().decode()
                    if e.code == 422 and 'already exists' in err_body:
                        return {'exists': True}
                    raise Exception(f'GitHub API Error {e.code}: {err_body[:200]}')

            safe_title = title.lower().replace(' ', '-').replace(':', '').replace('/', '-')[:50]
            branch = f'article-{safe_title}'

            # Get default branch SHA
            try:
                ref_data = gh_api('GET', 'git/ref/heads/main')
                default_branch = 'main'
            except:
                ref_data = gh_api('GET', 'git/ref/heads/master')
                default_branch = 'master'
            sha = ref_data['object']['sha']

            # Create branch
            gh_api('POST', 'git/refs', {'ref': f'refs/heads/{branch}', 'sha': sha})

            # Get index.html and add article
            get_url = f'https://api.github.com/repos/{REPO}/contents/index.html?ref={branch}'
            req = urllib.request.Request(get_url, headers={'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github.v3+json'})
            resp = urllib.request.urlopen(req)
            file_data = json.loads(resp.read())
            content = base64.b64decode(file_data['content']).decode()
            file_sha = file_data['sha']

            from datetime import datetime
            date_str = datetime.utcnow().strftime('%b %d, %Y')

            # Map email to display name
            author_name = author.split('@')[0].replace('.', ' ').title()
            try:
                user_resp = cognito.admin_get_user(UserPoolId=POOL_ID, Username=author)
                for attr in user_resp.get('UserAttributes', []):
                    if attr['Name'] == 'name':
                        author_name = attr['Value']
                        break
            except:
                pass

            article_card = f'''<div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:12px;transition:all 0.3s;" onmouseover="this.style.borderColor='rgba(255,215,0,0.4)'" onmouseout="this.style.borderColor='var(--border)'">
        <p style="color:var(--text-muted);font-size:0.7em;margin-bottom:4px;"><span style="background:rgba(255,215,0,0.15);color:var(--gold);padding:2px 8px;border-radius:4px;font-size:0.9em;font-weight:600;margin-right:6px;">📝 Article</span> {date_str} · <span style="color:var(--gold);font-style:italic;">{author_name}</span></p>
        <a href="{url}" target="_blank" rel="noopener noreferrer" style="color:var(--gold);font-weight:700;font-size:1em;text-decoration:none;">{title}</a>
        <p style="color:var(--text-muted);font-size:0.85em;margin-top:6px;">{summary}</p>
      </div>\n'''

            marker = '<!-- END_ARTICLES -->'
            if marker in content:
                content = content.replace(marker, article_card + '        ' + marker)
                put_payload = {
                    'message': f'Add article: {title}',
                    'content': base64.b64encode(content.encode()).decode(),
                    'branch': branch,
                    'sha': file_sha
                }
                gh_api('PUT', 'contents/index.html', put_payload)

            # Create PR
            pr_body = f'**Title:** {title}\n**URL:** {url}\n**Summary:** {summary}\n**Author:** {author}\n\n_Auto-generated by article submission form._'
            gh_api('POST', 'pulls', {'title': f'📝 New article: {title}', 'head': branch, 'base': default_branch, 'body': pr_body})

            # Send SNS notification
            sns = boto3.client('sns', region_name='us-east-1')
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:800712212925:goldenjackets-alerts',
                Subject=trunc_subject(f'📝 New Article: {title}'),
                Message=f'Author: {author}\nTitle: {title}\nURL: {url}\nSummary: {summary}\n\nPR created on GitHub.'
            )

            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': 'Article submitted! PR created for review.'})}

        elif action == 'post-job':
            import uuid
            from datetime import datetime
            ddb = boto3.resource('dynamodb', region_name='us-east-1').Table('gj-jobs')
            item = {
                'id': str(uuid.uuid4())[:8],
                'company': body.get('company', ''),
                'role': body.get('role', ''),
                'location': body.get('location', ''),
                'link': body.get('link', ''),
                'contact': body.get('contact', ''),
                'posted_by': get_caller_email(event) or body.get('posted_by', ''),
                'created': datetime.utcnow().isoformat(),
                'active': True
            }
            ddb.put_item(Item=item)
            # Notify founder
            sns = boto3.client('sns', region_name='us-east-1')
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:800712212925:goldenjackets-alerts',
                Subject=trunc_subject(f"💼 New Job Posted: {item['role']} @ {item['company']}"),
                Message=f"Role: {item['role']}\nCompany: {item['company']}\nLocation: {item['location']}\nLink: {item['link']}\nContact: {item['contact']}\nPosted by: {item['posted_by']}"
            )
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': 'Job posted!', 'id': item['id']})}

        elif action == 'list-jobs':
            ddb = boto3.resource('dynamodb', region_name='us-east-1').Table('gj-jobs')
            from boto3.dynamodb.conditions import Attr
            resp = ddb.scan(FilterExpression=Attr('active').eq(True))
            jobs = sorted(resp.get('Items', []), key=lambda x: x.get('created',''), reverse=True)
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'jobs': jobs}, default=str)}

        elif action == 'delete-job':
            ddb = boto3.resource('dynamodb', region_name='us-east-1').Table('gj-jobs')
            ddb.update_item(Key={'id': body.get('id','')}, UpdateExpression='SET active = :f', ExpressionAttributeValues={':f': False})
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': 'Job removed'})}

        elif action == 'apply-job':
            job_id = body.get('id', '')
            applicant_email = get_caller_email(event) or body.get('applicant', '')
            ddb = boto3.resource('dynamodb', region_name='us-east-1').Table('gj-jobs')
            resp = ddb.get_item(Key={'id': job_id})
            job = resp.get('Item', {})
            if not job:
                return {'statusCode': 404, 'headers': cors, 'body': json.dumps({'error': 'Job not found'})}
            poster_email = job.get('posted_by', '')
            role = job.get('role', '')
            company = job.get('company', '')
            sns = boto3.client('sns', region_name='us-east-1')
            # Notify poster
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:800712212925:goldenjackets-alerts',
                Subject=trunc_subject(f"🤝 Someone is interested in your job: {role} @ {company}"),
                Message=f"Hi {poster_email}!\n\n{applicant_email} is interested in your job posting:\n\nRole: {role}\nCompany: {company}\n\nPlease connect with them directly.\n\n— Golden Jackets Job Board"
            )
            # Notify applicant
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:800712212925:goldenjackets-alerts',
                Subject=trunc_subject(f"✅ You applied: {role} @ {company}"),
                Message=f"Hi {applicant_email}!\n\nYou expressed interest in:\n\nRole: {role}\nCompany: {company}\nPosted by: {poster_email}\n\nThe poster has been notified. You can also reach them directly.\n\n— Golden Jackets Job Board"
            )
            # Notify founder
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:800712212925:goldenjackets-alerts',
                Subject=trunc_subject(f"💼 Job Match: {applicant_email} → {role} @ {company}"),
                Message=f"Applicant: {applicant_email}\nJob: {role} @ {company}\nPoster: {poster_email}"
            )
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': 'Interest sent! The poster has been notified.'})}


        elif action == 'list-prs':
            prs = list_prs(chapter)
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'prs': prs})}

        elif action == 'merge-pr':
            pr_number = body.get('pr_number')
            if not pr_number:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'pr_number required'})}
            result = merge_pr(chapter, pr_number)
            if 'error' in result:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps(result)}
            # Rebuild remaining article PRs to avoid merge conflicts
            rebuild_remaining_prs(chapter, pr_number)
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': f'PR #{pr_number} merged successfully'})}

        elif action == 'close-pr':
            pr_number = body.get('pr_number')
            reason = body.get('reason', 'No reason provided')
            if not pr_number:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'pr_number required'})}
            repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
            repo = repo_map.get(chapter, '')
            pr_info = github_api('GET', f'/repos/goldenjackets-community/{repo}/pulls/{pr_number}')
            pr_title = pr_info.get('title', f'PR #{pr_number}')
            result = close_pr(chapter, pr_number)
            if 'error' in result:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps(result)}
            sns = boto3.client('sns', region_name='us-east-1')
            sns.publish(TopicArn='arn:aws:sns:us-east-1:800712212925:goldenjackets-alerts', Subject=trunc_subject(f'❌ Article Rejected: {pr_title}'), Message=f'Article: {pr_title}\nRejected by: {caller_email}\nReason: {reason}\n\nPlease modify and resubmit if appropriate.')
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': f'PR #{pr_number} rejected. Reason sent to author.'})}

        elif action == 'list-members':
            import base64 as b64, re
            repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
            repo = repo_map.get(chapter, '')
            if not repo:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'Invalid chapter'})}
            index_data = github_api('GET', f'/repos/goldenjackets-community/{repo}/contents/index.html')
            content = b64.b64decode(index_data.get('content', '')).decode()
            names = re.findall(r'<h3>([^<]+)</h3>', content)
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'members': names})}

        elif action == 'update-photo':
            name = body.get('name', '')
            photo_b64 = body.get('photo', '')
            filename = body.get('filename', 'photo.jpg')
            if not name or not photo_b64:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'name and photo required'})}
            repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
            repo = repo_map.get(chapter, '')
            if not repo:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'Invalid chapter'})}
            org = 'goldenjackets-community'
            # Find actual photo path from index.html
            import base64 as b64, re
            index_data = github_api('GET', f'/repos/{org}/{repo}/contents/index.html')
            index_content = b64.b64decode(index_data.get('content', '')).decode()
            # Search for img src near the member name
            pattern = r'<img\s+src="(assets/members/[^"]+)"[^>]*alt="[^"]*' + re.escape(name.split()[0])
            match = re.search(pattern, index_content, re.IGNORECASE)
            if not match:
                # Try simpler: find any img src near the name
                idx = index_content.lower().find(name.lower())
                if idx == -1:
                    idx = index_content.lower().find(name.split()[0].lower())
                if idx > -1:
                    chunk = index_content[max(0,idx-500):idx+100]
                    m2 = re.search(r'src="(assets/members/[^"]+)"', chunk)
                    if m2:
                        match = m2
                if not match:
                    return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': f'Member "{name}" not found on site'})}
            photo_path = match.group(1)
            # Get existing file sha
            existing = github_api('GET', f'/repos/{org}/{repo}/contents/{photo_path}')
            sha = existing.get('sha')
            payload = {'message': f'Update photo: {name}', 'content': photo_b64}
            if sha:
                payload['sha'] = sha
            github_api('PUT', f'/repos/{org}/{repo}/contents/{photo_path}', payload)
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps({'message': f'Photo updated for {name}. Site will update in ~1 minute.'})}

        elif action == 'move-member':
            member_name = body.get('name', '')
            target = body.get('target', '')
            if not member_name or not target:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'name and target required'})}
            if target not in ('golden', 'alumni', 'challenger'):
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'target must be golden, alumni or challenger'})}
            result = move_member_card(chapter, member_name, target)
            if 'error' in result:
                return {'statusCode': 400, 'headers': cors, 'body': json.dumps(result)}
            return {'statusCode': 200, 'headers': cors, 'body': json.dumps(result)}


        elif action == "suggest-topic":
            topic = body.get("topic", "")
            name = body.get("name", "")
            stype = body.get("type", "podcast")
            email = body.get("email", "unknown")
            sns_client = boto3.client("sns", region_name="us-east-1")
            sns_client.publish(
                TopicArn="arn:aws:sns:us-east-1:800712212925:gj-brazil-alerts",
                Subject=trunc_subject("Topic Suggestion: " + topic),
                Message="New topic suggestion!\n\nFrom: " + name + " (" + email + ")\nType: " + stype + "\nTopic: " + topic
            )
            return {"statusCode": 200, "headers": cors, "body": json.dumps({"message": "Suggestion received!"})}
        else:
            return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'unknown action'})}


    except Exception as e:
        return {'statusCode': 500, 'headers': cors, 'body': json.dumps({'error': str(e)})}

# --- PR Management (Pending Applications & Articles) ---
import urllib.request
import os

def github_api(method, path, body=None):
    token = os.environ.get('GITHUB_TOKEN', '')
    url = f'https://api.github.com{path}'
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'gj-admin'}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}

def move_member_card(chapter, member_name, target):
    import re, base64
    repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
    repo = repo_map.get(chapter, '')
    if not repo:
        return {'error': 'Invalid chapter'}
    token = os.environ.get('GITHUB_TOKEN', '')
    org = 'goldenjackets-community'
    try:
        branch = 'main'
        url = f'https://api.github.com/repos/{org}/{repo}/contents/index.html?ref={branch}'
        req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'gj-admin'})
        try:
            resp = urllib.request.urlopen(req)
        except:
            branch = 'master'
            url = f'https://api.github.com/repos/{org}/{repo}/contents/index.html?ref={branch}'
            req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'gj-admin'})
            resp = urllib.request.urlopen(req)
        file_data = json.loads(resp.read().decode())
        content = base64.b64decode(file_data['content']).decode()
        sha = file_data['sha']
    except Exception as e:
        return {'error': f'Failed to read index.html: {str(e)}'}
    pattern = r'(<div class="member-card[^"]*"[^>]*>\s*<img[^>]*>\s*<h3>' + re.escape(member_name) + r'</h3>.*?</div>\s*</div>\s*</div>)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        # Try simpler pattern
        lines = content.split('\n')
        start = end = -1
        for i, line in enumerate(lines):
            if f'<h3>{member_name}</h3>' in line:
                # Find the opening div above
                for j in range(i-1, max(i-5, -1), -1):
                    if 'member-card' in lines[j]:
                        start = j
                        break
                # Find closing divs below
                div_count = 0
                for j in range(start, min(start+20, len(lines))):
                    div_count += lines[j].count('<div') - lines[j].count('</div')
                    if div_count <= 0:
                        end = j
                        break
                break
        if start >= 0 and end >= 0:
            card = '\n'.join(lines[start:end+1])
            content = '\n'.join(lines[:start] + lines[end+1:])
        else:
            return {'error': f'Member "{member_name}" not found on the site'}
    else:
        card = match.group(1)
        content = content.replace(card, '')
    if target == 'golden':
        card = re.sub(r'class="member-card[^"]*"', 'class="member-card"', card)
        card = re.sub(r'<span class="tag">Challenger</span>', '<span class="tag">Golden Jacket</span>\n          <span class="tag">Member</span>', card)
        card = re.sub(r'<span class="tag">Alumni</span>', '<span class="tag">Golden Jacket</span>\n          <span class="tag">Member</span>', card)
        card = re.sub(r'<span class="tag">[\d/]+ Certifications</span>\s*', '', card)
        marker = '<!-- END_GOLDEN_JACKETS -->'
    elif target == 'alumni':
        card = re.sub(r'class="member-card[^"]*"', 'class="member-card alumni"', card)
        card = re.sub(r'<span class="tag">Golden Jacket</span>', '<span class="tag">Alumni</span>', card)
        card = re.sub(r'<span class="tag">Challenger</span>', '<span class="tag">Alumni</span>', card)
        card = re.sub(r'<span class="tag">[\d/]+ Certifications</span>\s*', '', card)
        card = re.sub(r'<span class="tag">Member</span>', '', card)
        marker = '<!-- END_ALUMNI -->'
    else:
        card = re.sub(r'class="member-card[^"]*"', 'class="member-card challenger"', card)
        card = re.sub(r'<span class="tag">Golden Jacket</span>', '<span class="tag">Challenger</span>', card)
        card = re.sub(r'<span class="tag">Alumni</span>', '<span class="tag">Challenger</span>', card)
        card = re.sub(r'<span class="tag">Member</span>', '', card)
        marker = '<!-- END_CHALLENGERS -->'
    if marker not in content:
        return {'error': f'Marker {marker} not found in index.html'}
    content = content.replace(marker, card + '\n' + marker)
    labels = {'golden': 'Golden Jacket', 'alumni': 'Alumni', 'challenger': 'Challenger'}
    msg = f'Move {member_name} to {labels[target]}'
    payload = {'message': msg, 'content': base64.b64encode(content.encode()).decode(), 'sha': sha, 'branch': branch}
    url = f'https://api.github.com/repos/{org}/{repo}/contents/index.html'
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'gj-admin'}, method='PUT')
    try:
        urllib.request.urlopen(req)
        return {'message': f'{member_name} moved to {labels[target]}. Site will update in ~1 minute.'}
    except Exception as e:
        return {'error': f'Failed to update: {str(e)}'}

def list_prs(chapter):
    repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
    repo = repo_map.get(chapter, '')
    if not repo:
        return []
    result = github_api('GET', f'/repos/goldenjackets-community/{repo}/pulls?state=open')
    if isinstance(result, list):
        prs = []
        for pr in result:
            prs.append({
                'number': pr['number'],
                'title': pr['title'],
                'author': pr['user']['login'],
                'created_at': pr['created_at'],
                'body': pr.get('body', ''),
                'type': 'member' if 'New Member' in pr['title'] or 'Add member' in pr['title'] else 'article'
            })
        return prs
    return []

def merge_pr(chapter, pr_number):
    repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
    repo = repo_map.get(chapter, '')
    if not repo:
        return {'error': 'Invalid chapter'}
    base = f'/repos/goldenjackets-community/{repo}/pulls/{pr_number}'
    # Get PR head SHA for update-branch
    pr_info = github_api('GET', base)
    head_sha = pr_info.get('head', {}).get('sha', '') if isinstance(pr_info, dict) else ''
    # Update branch with base to resolve simple conflicts
    if head_sha:
        github_api('PUT', f'{base}/update-branch', {'expected_head_sha': head_sha})
        time.sleep(3)
    # Attempt merge
    result = github_api('PUT', f'{base}/merge', {'merge_method': 'squash'})
    if isinstance(result, dict) and 'error' in result and 'conflict' in str(result.get('error', '')).lower():
        return {'error': 'Merge conflict that cannot be auto-resolved. Contact an admin.'}
    return result

def close_pr(chapter, pr_number):
    repo_map = {'brazil': 'golden-jackets-brazil', 'poland': 'golden-jackets-poland', 'uk': 'golden-jackets-uk'}
    repo = repo_map.get(chapter, '')
    if not repo:
        return {'error': 'Invalid chapter'}
    return github_api('PATCH', f'/repos/goldenjackets-community/{repo}/pulls/{pr_number}', {'state': 'closed'})
