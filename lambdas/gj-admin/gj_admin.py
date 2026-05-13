import traceback
import json
import boto3

cognito = boto3.client('cognito-idp', region_name='us-east-1')
backup = boto3.client('backup', region_name='us-east-1')
POOL_ID = 'us-east-1_Z0VzzrmIX'

# Global admins can see all chapters
GLOBAL_ADMINS = ['ricardo.gulias@darede.com.br']

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

        # If no chapter specified, use caller's first group
        if not chapter and caller_groups:
            chapter = caller_groups[0]

        # Verify caller has access to requested chapter
        if not is_global_admin and chapter not in caller_groups:
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
            vault = 'gj-poland-backups' if chapter == 'poland' else 'gj-site-backups'
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
            vault = 'gj-poland-backups' if chapter == 'poland' else 'gj-site-backups'
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

        else:
            return {'statusCode': 400, 'headers': cors, 'body': json.dumps({'error': 'unknown action'})}

    except Exception as e:
        return {'statusCode': 500, 'headers': cors, 'body': json.dumps({'error': str(e)})}
