#!/usr/bin/env python3

"""MailChimp proxy server."""

from mailchimp3 import MailChimp
from sanic import Sanic, response
from sanic.exceptions import abort
from sanic_cors import CORS
from sanic_gzip import Compress
import argparse


_DEFAULT_PORT = 80
_API_KEY = None
_LIST_ID = None

# Create the sanic app
app = Sanic('mailchimp-proxy')
CORS(app)
compress = Compress()


# Serve the list
@app.post('/newsletter/subscribe')
@compress.compress()
async def subscribe(request):
    """Get the add-on list which matches a set of filters."""
    if 'email' not in request.json or 'subscribe' not in request.json:
        abort(400)

    address = request.json['email']
    status = 'subscribed' if request.json['subscribe'] else 'unsubscribed'

    try:
        client = MailChimp(mc_api=_API_KEY)
        result = client.search_members.get(
            query=address,
            list_id=_LIST_ID,
            fields=','.join([
                'exact_matches.members.id',
                'exact_matches.members.status',
            ])
        )

        if 'exact_matches' in result and \
                'members' in result['exact_matches'] and \
                len(result['exact_matches']['members']) > 0:
            if result['exact_matches']['members'][0]['status'] != status:
                client.lists.members.update(
                    list_id=_LIST_ID,
                    subscriber_hash=result['exact_matches']['members'][0]['id'],  # noqa
                    data={
                        'status': status,
                    }
                )
        else:
            client.lists.members.create(
                list_id=_LIST_ID,
                data={
                    'email_address': address,
                    'status': status,
                    'merge_fields': {},
                }
            )
    except Exception as e:
        print(e)
        abort(500)

    return response.empty()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='MailChimp proxy server for WebThings Gateway'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=_DEFAULT_PORT,
        help='port for server',
    )
    parser.add_argument(
        '--api-key',
        type=str,
        required=True,
        help='MailChimp API key',
    )
    parser.add_argument(
        '--list-id',
        type=str,
        required=True,
        help='MailChimp list ID',
    )
    args = parser.parse_args()

    _API_KEY = args.api_key
    _LIST_ID = args.list_id

    app.run(host='0.0.0.0', port=args.port)
