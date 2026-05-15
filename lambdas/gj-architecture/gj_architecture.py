import json
import boto3

s3 = boto3.client('s3', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
cf_client = boto3.client('cloudfront', region_name='us-east-1')
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
cognito = boto3.client('cognito-idp', region_name='us-east-1')
sns_client = boto3.client('sns', region_name='us-east-1')
backup_client = boto3.client('backup', region_name='us-east-1')
route53 = boto3.client('route53', region_name='us-east-1')

BUCKET = 'www.goldenjacketsbrazil.com'
OUTPUT_KEY = 'architecture-data.json'
CLOUDFRONT_DIST_BR = 'E3N4417EU5IQE6'
CLOUDFRONT_DIST_PL = 'E174XK4PPCRG0L'
COGNITO_POOL_ID = 'us-east-1_Z0VzzrmIX'

def lambda_handler(event, context):
    nodes = []
    edges = []

    # User node (static)
    nodes.append({'id': 'user', 'x': 80, 'y': 300, 'icon': '👤', 'name': 'User / Browser', 'detail': 'goldenjacketsbrazil.com\ngoldenjackets.pl', 'type': 'user', 'tooltip': 'End users accessing the community websites.'})

    # Route 53 (zones are in account 958919067803, adding static)
    nodes.append({'id': 'route53', 'x': 300, 'y': 300, 'icon': '🌐', 'name': 'Route 53', 'detail': '2 Hosted Zones\ngoldenjacketsbrazil.com\ngoldenjackets.pl', 'type': 'route53', 'tooltip': 'goldenjacketsbrazil.com (Z01877031V3TFGYA6MIEA)\ngoldenjackets.pl (Z07410873K29FYP3PO6JN)'})
    edges.append({'from': 'user', 'to': 'route53', 'color': '#FFD700'})

    # CloudFront
    try:
        dists = cf_client.list_distributions()['DistributionList'].get('Items', [])
        gj_dists = [d for d in dists if d['Id'] in [CLOUDFRONT_DIST_BR, CLOUDFRONT_DIST_PL]]
        y_pos = 180
        for d in gj_dists:
            domain = d['Aliases']['Items'][0] if d['Aliases']['Quantity'] > 0 else d['DomainName']
            node_id = f"cf-{d['Id'][-4:]}"
            nodes.append({'id': node_id, 'x': 520, 'y': y_pos, 'icon': '⚡', 'name': f'CloudFront', 'detail': f"{d['Id']}\n{domain}", 'type': 'cloudfront', 'tooltip': f"Distribution: {d['Id']}\nDomain: {domain}\nStatus: {d['Status']}"})
            edges.append({'from': 'route53', 'to': node_id, 'color': '#8b5cf6'})
            y_pos += 200
    except:
        pass

    # S3 buckets (grouped)
    try:
        buckets = s3.list_buckets()['Buckets']
        gj_buckets = [b for b in buckets if 'goldenjacket' in b['Name'].lower()]
        if gj_buckets:
            bucket_names = '\n'.join([b['Name'] for b in gj_buckets])
            nodes.append({'id': 's3', 'x': 740, 'y': 280, 'icon': '📦', 'name': 'S3', 'detail': f"{len(gj_buckets)} buckets\n" + '\n'.join([b['Name'] for b in gj_buckets[:4]]), 'type': 's3', 'tooltip': bucket_names})
    except:
        pass

    # Lambda functions - critical ones as individual boxes
    try:
        funcs = lambda_client.list_functions()['Functions']
        gj_funcs = [f for f in funcs if 'gj' in f['FunctionName'].lower() or 'golden' in f['FunctionName'].lower()]

        # Check alarms
        cw = boto3.client('cloudwatch', region_name='us-east-1')
        alarms_resp = cw.describe_alarms(AlarmNamePrefix='gj-')
        alarm_states = {a['AlarmName']: a['StateValue'] for a in alarms_resp['MetricAlarms']}

        critical = ['gj-admin', 'gj-apply', 'gj-poland-counter']
        others = [f for f in gj_funcs if f['FunctionName'] not in critical]

        # Individual critical lambdas - spaced out
        positions = [{'name': 'gj-admin', 'x': 580, 'y': 500, 'alarm': 'gj-admin-errors'},
                     {'name': 'gj-apply', 'x': 820, 'y': 500, 'alarm': 'gj-apply-errors'},
                     {'name': 'gj-poland-counter', 'x': 1060, 'y': 500, 'alarm': 'gj-counter-errors'}]

        for p in positions:
            func = next((f for f in gj_funcs if f['FunctionName'] == p['name']), None)
            if func:
                state = alarm_states.get(p['alarm'], 'OK')
                status = '🔴 ALARM' if state == 'ALARM' else '🟢 OK'
                nodes.append({
                    'id': f"lambda-{p['name']}",
                    'x': p['x'], 'y': p['y'],
                    'icon': '⚙️',
                    'name': f"Lambda {p['name']}",
                    'detail': f"{func.get('Runtime','N/A')}\n{status}",
                    'type': 'lambda',
                    'tooltip': f"Function: {p['name']}\nRuntime: {func.get('Runtime','N/A')}\nMemory: {func.get('MemorySize',128)}MB\nStatus: {status}",
                    'alarm': state
                })

        # No "others" box - only critical lambdas shown
    except:
        pass

    # DynamoDB
    try:
        tables = dynamodb.list_tables()['TableNames']
        gj_tables = [t for t in tables if 'gj' in t.lower() or 'golden' in t.lower() or 'visitor' in t.lower() or 'counter' in t.lower()]
        if gj_tables:
            nodes.append({'id': 'dynamodb', 'x': 300, 'y': 550, 'icon': '🗄️', 'name': 'DynamoDB', 'detail': f"{len(gj_tables)} tables\n" + '\n'.join(gj_tables[:4]), 'type': 'dynamodb', 'tooltip': '\n'.join(gj_tables)})
    except:
        pass

    # Cognito
    try:
        pool = cognito.describe_user_pool(UserPoolId=COGNITO_POOL_ID)['UserPool']
        users = pool.get('EstimatedNumberOfUsers', 0)
        nodes.append({'id': 'cognito', 'x': 960, 'y': 300, 'icon': '🔐', 'name': 'Cognito', 'detail': f"{COGNITO_POOL_ID}\n~{users} users", 'type': 'cognito', 'tooltip': f"Pool: {pool['Name']}\nUsers: ~{users}\nGroups: brazil, poland"})
        edges.append({'from': 'user', 'to': 'cognito', 'color': '#ef4444'})
    except:
        pass

    # SNS
    try:
        topics = sns_client.list_topics()['Topics']
        gj_topics = [t for t in topics if 'goldenjackets' in t['TopicArn']]
        if gj_topics:
            nodes.append({'id': 'sns', 'x': 1180, 'y': 450, 'icon': '📧', 'name': 'SNS', 'detail': f"{len(gj_topics)} topics\ngoldenjackets-alerts", 'type': 'sns', 'tooltip': '\n'.join([t['TopicArn'].split(':')[-1] for t in gj_topics])})
    except:
        pass

    # Backup vaults
    try:
        vaults = backup_client.list_backup_vaults()['BackupVaultList']
        gj_vaults = [v for v in vaults if 'gj-' in v['BackupVaultName']]
        if gj_vaults:
            nodes.append({'id': 'backup', 'x': 1180, 'y': 250, 'icon': '💾', 'name': 'Backup', 'detail': f"{len(gj_vaults)} vaults\n" + '\n'.join([v['BackupVaultName'] for v in gj_vaults]), 'type': 'backup', 'tooltip': '\n'.join([f"{v['BackupVaultName']} ({v.get('NumberOfRecoveryPoints', 0)} points)" for v in gj_vaults])})
    except:
        pass

    # GitHub (static - can't query without token in this context)
    nodes.append({'id': 'github', 'x': 960, 'y': 100, 'icon': '🐙', 'name': 'GitHub', 'detail': 'goldenjackets-community\n4 repos', 'type': 'github', 'tooltip': 'Org: goldenjackets-community\nRepos: brazil, poland, academy, infra'})

    # API Gateway (static - known IDs)
    nodes.append({'id': 'apigateway', 'x': 520, 'y': 380, 'icon': '🔌', 'name': 'API Gateway', 'detail': '3 APIs\ngj-admin-api\ngj-apply-api\ngj-counter-api', 'type': 'lambda', 'tooltip': 'gj-admin-api (pr8xdjp341)\ngj-apply-api (kqiq2bltjd)\ngj-counter-api (97i05orlfa)'})

    # Auto-generate edges
    node_ids = [n['id'] for n in nodes]
    cf_ids = [n['id'] for n in nodes if n['type'] == 'cloudfront']

    # Route53 → CloudFront
    for cf in cf_ids:
        edges.append({'from': 'route53', 'to': cf, 'color': '#8b5cf6'})

    # CloudFront → S3
    if 's3' in node_ids:
        for cf in cf_ids:
            edges.append({'from': cf, 'to': 's3', 'color': '#3ecf8e'})

    # GitHub → S3
    if 'github' in node_ids and 's3' in node_ids:
        edges.append({'from': 'github', 'to': 's3', 'color': '#e0e0e0'})

    # User → Cognito → Lambda admin
    if 'cognito' in node_ids:
        edges.append({'from': 'user', 'to': 'cognito', 'color': '#ef4444'})
        if 'lambda-gj-admin' in node_ids:
            edges.append({'from': 'cognito', 'to': 'lambda-gj-admin', 'color': '#f90'})

    # API Gateway edges
    if 'apigateway' in node_ids:
        edges.append({'from': 'user', 'to': 'apigateway', 'color': '#f90'})
        if 'lambda-gj-admin' in node_ids:
            edges.append({'from': 'apigateway', 'to': 'lambda-gj-admin', 'color': '#f90'})
        if 'lambda-gj-apply' in node_ids:
            edges.append({'from': 'apigateway', 'to': 'lambda-gj-apply', 'color': '#f90'})
        if 'lambda-gj-poland-counter' in node_ids:
            edges.append({'from': 'apigateway', 'to': 'lambda-gj-poland-counter', 'color': '#f90'})

    # Lambda → GitHub
    if 'lambda-gj-apply' in node_ids and 'github' in node_ids:
        edges.append({'from': 'lambda-gj-apply', 'to': 'github', 'color': '#e0e0e0'})
    if 'lambda-gj-admin' in node_ids and 'github' in node_ids:
        edges.append({'from': 'lambda-gj-admin', 'to': 'github', 'color': '#e0e0e0'})

    # Lambda → SNS
    if 'lambda-gj-apply' in node_ids and 'sns' in node_ids:
        edges.append({'from': 'lambda-gj-apply', 'to': 'sns', 'color': '#ec4899'})
    if 'lambda-gj-admin' in node_ids and 'sns' in node_ids:
        edges.append({'from': 'lambda-gj-admin', 'to': 'sns', 'color': '#ec4899'})

    # Lambda counter → DynamoDB
    if 'lambda-gj-poland-counter' in node_ids and 'dynamodb' in node_ids:
        edges.append({'from': 'lambda-gj-poland-counter', 'to': 'dynamodb', 'color': '#3b82f6'})

    # S3 → Backup
    if 's3' in node_ids and 'backup' in node_ids:
        edges.append({'from': 's3', 'to': 'backup', 'color': '#14b8a6'})

    # AWS Health - check for active events
    health_issues = []
    try:
        health = boto3.client('health', region_name='us-east-1')
        events = health.describe_events(filter={'eventStatusCodes': ['open', 'upcoming']})['events']
        for ev in events:
            health_issues.append({'service': ev.get('service',''), 'description': ev.get('eventTypeCode',''), 'status': ev.get('statusCode','')})
    except:
        pass

    # Save to S3
    data = {'nodes': nodes, 'edges': edges, 'health': health_issues, 'updated': context.function_name if context else 'local'}
    s3.put_object(
        Bucket=BUCKET,
        Key=OUTPUT_KEY,
        Body=json.dumps(data),
        ContentType='application/json',
        CacheControl='max-age=60'
    )

    return {'statusCode': 200, 'body': json.dumps({'nodes': len(nodes), 'edges': len(edges)})}
