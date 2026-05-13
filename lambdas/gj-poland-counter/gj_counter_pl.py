import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('gj-poland-visitors')

def lambda_handler(event, context):
    cors = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    }
    
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {'statusCode': 200, 'headers': cors, 'body': ''}

    table.update_item(
        Key={'id': 'counter'},
        UpdateExpression='SET total_visits = if_not_exists(total_visits, :zero) + :one, unique_visitors = if_not_exists(unique_visitors, :zero)',
        ExpressionAttributeValues={':one': 1, ':zero': 0}
    )

    ip = event.get('requestContext', {}).get('http', {}).get('sourceIp', 'unknown')
    try:
        table.put_item(
            Item={'id': f'ip#{ip}', 'first_visit': datetime.utcnow().isoformat()},
            ConditionExpression='attribute_not_exists(id)'
        )
        table.update_item(
            Key={'id': 'counter'},
            UpdateExpression='SET unique_visitors = if_not_exists(unique_visitors, :zero) + :one',
            ExpressionAttributeValues={':one': 1, ':zero': 0}
        )
    except:
        pass

    resp = table.get_item(Key={'id': 'counter'})
    item = resp.get('Item', {})

    return {
        'statusCode': 200,
        'headers': cors,
        'body': json.dumps({
            'total_visits': int(item.get('total_visits', 0)),
            'unique_visitors': int(item.get('unique_visitors', 0))
        })
    }
