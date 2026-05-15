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

    # Route 53
    try:
        zones = route53.list_hosted_zones()['HostedZones']
        gj_zones = [z for z in zones if 'goldenjacket' in z['Name'].lower()]
        nodes.append({'id': 'route53', 'x': 300, 'y': 300, 'icon': '🌐', 'name': 'Route 53', 'detail': f'DNS\n{len(gj_zones)} Hosted Zones', 'type': 'route53', 'tooltip': '\n'.join([z['Name'] for z in gj_zones])})
        edges.append({'from': 'user', 'to': 'route53', 'color': '#FFD700'})
    except:
        pass

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

    # S3 buckets
    try:
        buckets = s3.list_buckets()['Buckets']
        gj_buckets = [b for b in buckets if 'goldenjacket' in b['Name'].lower()]
        y_pos = 180
        for b in gj_buckets[:6]:
            node_id = f"s3-{b['Name'].replace('.','_')[:20]}"
            nodes.append({'id': node_id, 'x': 740, 'y': y_pos, 'icon': '📦', 'name': 'S3', 'detail': b['Name'], 'type': 's3', 'tooltip': f"Bucket: {b['Name']}\nCreated: {b['CreationDate'].strftime('%Y-%m-%d')}"})
            y_pos += 100
    except:
        pass

    # Lambda functions
    try:
        funcs = lambda_client.list_functions()['Functions']
        gj_funcs = [f for f in funcs if 'gj' in f['FunctionName'].lower() or 'golden' in f['FunctionName'].lower()]
        y_pos = 450
        for f in gj_funcs:
            node_id = f"lambda-{f['FunctionName'].replace('-','_')}"
            runtime = f.get('Runtime', 'N/A')
            nodes.append({'id': node_id, 'x': 520, 'y': y_pos, 'icon': '⚙️', 'name': 'Lambda', 'detail': f"{f['FunctionName']}\n{runtime}", 'type': 'lambda', 'tooltip': f"Function: {f['FunctionName']}\nRuntime: {runtime}\nMemory: {f.get('MemorySize', 'N/A')}MB\nTimeout: {f.get('Timeout', 'N/A')}s"})
            y_pos += 90
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

    # Auto-generate edges
    node_ids = [n['id'] for n in nodes]
    lambda_ids = [n['id'] for n in nodes if n['type'] == 'lambda']
    s3_ids = [n['id'] for n in nodes if n['type'] == 's3']
    cf_ids = [n['id'] for n in nodes if n['type'] == 'cloudfront']

    # Route53 → CloudFront
    for cf in cf_ids:
        edges.append({'from': 'route53', 'to': cf, 'color': '#8b5cf6'})

    # CloudFront → S3 (pair them)
    for i, cf in enumerate(cf_ids):
        if i < len(s3_ids):
            edges.append({'from': cf, 'to': s3_ids[i], 'color': '#3ecf8e'})

    # GitHub → S3
    if 'github' in node_ids:
        for sid in s3_ids[:2]:
            edges.append({'from': 'github', 'to': sid, 'color': '#e0e0e0'})

    # User → Cognito
    if 'cognito' in node_ids:
        edges.append({'from': 'user', 'to': 'cognito', 'color': '#ef4444'})
        for lid in lambda_ids:
            if 'admin' in lid:
                edges.append({'from': 'cognito', 'to': lid, 'color': '#f90'})

    # Lambdas → GitHub, SNS
    for lid in lambda_ids:
        if 'apply' in lid or 'admin' in lid:
            if 'github' in node_ids:
                edges.append({'from': lid, 'to': 'github', 'color': '#e0e0e0'})
            if 'sns' in node_ids:
                edges.append({'from': lid, 'to': 'sns', 'color': '#ec4899'})
        if 'counter' in lid and 'dynamodb' in node_ids:
            edges.append({'from': lid, 'to': 'dynamodb', 'color': '#3b82f6'})

    # User → Lambda apply/counter
    for lid in lambda_ids:
        if 'apply' in lid or 'counter' in lid:
            edges.append({'from': 'user', 'to': lid, 'color': '#f90'})

    # S3 → Backup
    if 'backup' in node_ids:
        for sid in s3_ids[:2]:
            edges.append({'from': sid, 'to': 'backup', 'color': '#14b8a6'})

    # Save to S3
    data = {'nodes': nodes, 'edges': edges, 'updated': context.function_name if context else 'local'}
    s3.put_object(
        Bucket=BUCKET,
        Key=OUTPUT_KEY,
        Body=json.dumps(data),
        ContentType='application/json',
        CacheControl='max-age=60'
    )

    return {'statusCode': 200, 'body': json.dumps({'nodes': len(nodes), 'edges': len(edges)})}
