import asyncio
import json
from dataclasses import dataclass, asdict
from kademlia.network import Server

DEFAULT_PORT = 8468

@dataclass
class Profile:
    username: str
    avatar: str = ''
    about: str = ''
    website: str = ''
    gamertag: str = ''
    work_experience: str = ''
    resume: str = ''
    certifications: str = ''
    wallpaper: str = ''
    font_color: str = ''
    font_size: str = ''
    contact_info: str = ''
    visibility: dict = None

    def to_json(self):
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(data: str):
        info = json.loads(data)
        return Profile(**info)

class Peer:
    def __init__(self, username, port=DEFAULT_PORT):
        self.username = username
        self.port = port
        self.server = Server()
        self.profile = Profile(username=username, visibility={})

    async def start(self, bootstrap_node=None):
        await self.server.listen(self.port)
        if bootstrap_node:
            ip, port = bootstrap_node.split(':')
            await self.server.bootstrap([(ip, int(port))])
        # Store our IP and profile in the DHT
        await self.publish_profile()

    async def publish_profile(self):
        await self.server.set(f'profile:{self.username}', self.profile.to_json())
        await self.server.set(f'address:{self.username}', f'localhost:{self.port}')

    async def lookup_user(self, username):
        data = await self.server.get(f'profile:{username}')
        addr = await self.server.get(f'address:{username}')
        if data and addr:
            return Profile.from_json(data), addr
        return None, None

    async def send_message(self, to_user, message):
        messages = await self.server.get(f'msg:{to_user}')
        queue = json.loads(messages) if messages else []
        queue.append({'from': self.username, 'msg': message})
        await self.server.set(f'msg:{to_user}', json.dumps(queue))

    async def fetch_messages(self):
        messages = await self.server.get(f'msg:{self.username}')
        if messages:
            await self.server.set(f'msg:{self.username}', json.dumps([]))
            return json.loads(messages)
        return []

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Simple P2P social prototype")
    parser.add_argument('--username', required=True, help='Your username')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port to listen on')
    parser.add_argument('--bootstrap', help='bootstrap node address ip:port')
    parser.add_argument('--lookup', help='Lookup user profile')
    parser.add_argument('--message', help='Send message text (requires --lookup)')
    parser.add_argument('--fetch', action='store_true', help='Fetch queued messages')
    args = parser.parse_args()

    peer = Peer(args.username, port=args.port)
    await peer.start(args.bootstrap)

    if args.lookup:
        profile, addr = await peer.lookup_user(args.lookup)
        if profile:
            print(f'Profile for {args.lookup}:')
            print(profile)
            print(f'Address: {addr}')
            if args.message:
                await peer.send_message(args.lookup, args.message)
                print('Message queued.')
        else:
            print('User not found')
    if args.fetch:
        msgs = await peer.fetch_messages()
        if msgs:
            for m in msgs:
                print(f"From {m['from']}: {m['msg']}")
        else:
            print('No messages.')

    # keep running to maintain network connection
    await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
