import json
import boto3
import string
import random

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('url-shortener')

def generate_short_code():
    # 6 chars is enough to avoid collisions at small scale
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=6))

def lambda_handler(event, context):
    method = event['httpMethod']

    if method == 'POST':
        body = json.loads(event['body'])
        long_url = body['long_url']
        short_code = generate_short_code()

        # store the mapping in dynamo
        table.put_item(Item={
            'short_code': short_code,
            'long_url': long_url
        })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'short_code': short_code,
                'short_url': f"https://your-api-url/{short_code}"
            })
        }

    elif method == 'GET':
        short_code = event['pathParameters']['short_code']
        response = table.get_item(Key={'short_code': short_code})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'URL not found'})
            }

        return {
            'statusCode': 301,
            'headers': {'Location': response['Item']['long_url']},
            'body': ''
        }