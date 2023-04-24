import asyncio
import json
import logging
import os
import re
import socket
import subprocess
from pprint import pprint
import requests
from aiohttp import ClientSession
from dotenv import load_dotenv

load_dotenv('issuer.env')

def flatten(args):
    """Flatten a nested list."""
    for arg in args:
        if isinstance(arg, (list, tuple)):
            yield from flatten(arg)
        else:
            yield arg


def divider(func):
    def wrapper(*args, **kwargs):
        char = "="
        print(char * 32)
        result = func(*args, **kwargs)
        return result

    return wrapper


def is_port_in_use(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        result = s.connect_ex((host, port))
        return result == 0


class Controller:
    def __init__(self):
        self.acapy_inbound_port = 8000
        self.acapy_admin_port = 10000
        self.acapy_endpoint_port = 7000
        self.acapy_profile_endpoint_port = 7050
        self.internal = os.getenv("INTERNAL")
        self.admin_endpoint = f"http://{self.internal}:{str(self.acapy_admin_port)}"
        self.acapy_wallet_type = os.getenv("ACAPY_WALLET_TYPE")
        self.acapy_outbound_transport = os.getenv('ACAPY_OUTBOUND_TRANSPORT')
        self.acapy_wallet_name = os.getenv('ACAPY_WALLET_NAME')
        self.acapy_wallet_key = os.getenv('ACAPY_WALLET_KEY')
        self.acapy_wallet_seed = os.getenv('ACAPY_WALLET_SEED')
        self.acapy_label = os.getenv('ACAPY_LABEL')
        self.acapy_wallet_storage_type = os.getenv('ACAPY_WALLET_STORAGE_TYPE')
        self.acapy_trace_target = os.getenv('ACAPY_TRACE_TARGET')
        self.acapy_trace_tag = os.getenv('ACAPY_TRACE_TAG')
        self.acapy_trace_label = os.getenv('ACAPY_TRACE_LABEL')
        self.genesis_base = os.getenv("ACAPY_GENESIS_BASE")
        self.genesis_url = os.getenv("ACAPY_GENESIS_URL")
        self.did = None
        self.headers = {
            # 'X-API-Key': os.getenv('ACAPY_ADMIN_API_KEY'),
            'Content-Type': 'application/json',
            'accept': 'application/json',
        }
        SEED = os.getenv('ACAPY_WALLET_SEED')
        LABEL = os.getenv('ACAPY_LABEL')
        pass
    @divider
    async def register_did(self, alias, seed, local_scope: bool = True, did=None):
        """Register a DID."""
        json_response = None
        role = "TRUST_ANCHOR"
        session = ClientSession()
        if local_scope:
            # for a local did to be added to a wallet
            endpoint = f"{self.admin_endpoint}/wallet/did/create"
            payload = {
                "method": "key",
                "options": {"key_type": "ed25519"}
            }
        else:
            # for an issuer agent to register did to a ledger
            endpoint = f"{os.getenv('ACAPY_GENESIS_BASE')}/register"
            payload = {
                "seed": seed,
                "role": role,
                "alias": alias
            }
            if did:
                payload["did"] = did
        try:
            response = await session.post(url=endpoint, json=payload, headers=self.headers)
            json_response = await response.json()
        except Exception as e:
            logging.warning("Error:", exc_info=True)
        await session.close()
        if json_response:
            print("DID registered to Ledger", json_response)
            return (json_response["result"]["did"], json_response["result"]["verkey"]) if local_scope else (
                json_response["did"], json_response["verkey"])
        else:
            return "None", "None"

    async def get_genesis_transactions(self):
        """Get the genesis transactions."""
        try:
            response = requests.get(self.genesis_url, headers=self.headers)
            response.raise_for_status()
        except Exception as e:
            print(e, f"Error loading genesis transactions. {self.genesis_url}")
            transactions = "None"
        else:
            print("Successfully retrieved genesis transactions.")
            transactions = response.text
            return transactions

    async def agent_status(self):
        is_running = is_port_in_use(host=self.internal, port=self.acapy_admin_port)
        status = "Running" if is_running else "Off"
        print(f"Agent Status: {status} at port {self.acapy_admin_port}.")
        return status

    async def get_agent_args(self, provision=False, debug=False):
        """Get the agent arguments."""
        print("Getting agent arguments")
        try:
            self.inbound_transport = self.acapy_outbound_transport.split(), self.internal, str(self.acapy_inbound_port)


            agent_args = [
                ("--endpoint", f"http://{self.internal}:{self.acapy_endpoint_port}"),
                ("--wallet-type", self.acapy_wallet_type),
                ("--wallet-name", self.acapy_wallet_name),
                ("--wallet-key", self.acapy_wallet_key),
                ("--seed", self.acapy_wallet_seed),
                ("--genesis-url", self.genesis_url),
                ("--genesis-transactions", await self.get_genesis_transactions()),
                ("--profile-endpoint", f"http://{self.internal}:{self.acapy_profile_endpoint_port}"),
                "--public-invites",
                "--recreate-wallet",
            ]

            if not provision:
                # add additional start options
                # ("--admin-api-key", os.getenv('ACAPY_ADMIN_API_KEY')),
                command = "start"
                agent_args.extend([
                    ("--label", self.acapy_label),
                    ("--inbound-transport", self.inbound_transport),
                    ("--outbound-transport", self.acapy_outbound_transport.split()),
                    ("--admin", self.internal, str(self.acapy_admin_port)),
                    "--admin-insecure-mode",
                    # ("--admin-api-key", os.getenv('ACAPY_ADMIN_API_KEY')),
                    ("--wallet-storage-type", self.acapy_wallet_storage_type),
                    # "--auto-ping-connection"
                ])
            else:
                command = "provision"
            if debug:
                agent_args.extend([
                    "--trace",
                    ("--trace-target", self.acapy_trace_target),
                    ("--trace-tag", self.acapy_trace_tag),
                    ("--trace-label", self.acapy_trace_label),
                ])
        except Exception as e:
            logging.critical("Error getting arg params", exc_info=True)
        else:
            flattened_args = ["aca-py", command] + list(flatten(agent_args))
            print(flattened_args)
            return flattened_args

    @divider
    async def start_agent(self, debug=False):
        """Start the agent."""
        print("Starting up...")
        agent_args = await self.get_agent_args(provision=False, debug=debug)
        try:
            process = subprocess.Popen(agent_args, shell=False)
        except Exception as e:
            print(e)

    @divider
    async def terminate_agent(self, old_instances=True):
        """Terminate the agent."""
        print("Terminating the agent...")
        suffix = "shutdown"
        async with ClientSession() as session:
                endpoint = f"http://{self.internal}:{str(self.acapy_endpoint_port)}/{suffix}"
                print(endpoint)
                try:
                    response = await session.get(url=endpoint, headers=self.headers)
                except Exception as e:
                    print(e)
                    return "Agent may already be closed."
                else:
                    print(f"Agent has been closed successfully: {response}")

    @divider
    async def provision_agent(self, debug=False):
        """Provision the agent."""
        print("Provisioning Agent...")
        agent_args = await self.get_agent_args(provision=True, debug=debug)
        try:
            process = subprocess.Popen(agent_args, shell=False)
        except Exception as e:
            print(e)
        else:
            print("Agent has been provisioned successfully...")

    @divider
    async def create_agent_base_wallet(self):
        """Create a base wallet for the agent."""
        print("Creating Wallet...")
        try:
            await self.provision_agent(debug=False)
            did, ver_key = await self.register_did(alias=self.acapy_label, seed=self.acapy_wallet_seed, local_scope=False)
        except Exception as e:
            print("Error:", e)
        else:
            pass
        finally:
            info = {
                "seed": self.acapy_wallet_seed,
                "wallet_name": self.acapy_wallet_name,
                "wallet_type": self.acapy_wallet_type,
                "wallet_key": self.acapy_wallet_key,
                "wallet_verkey": ver_key,
                "wallet_did": did
            }
            if did is None and ver_key is None:
                logging.error("Error: Could not register wallet.")
                return None
        # compiles new wallet info

        pprint(info)
        return info
    @divider
    async def create_invitation(self):
        "out of band"
        print("Creating invitation...")
        endpoint = self.admin_endpoint
        suffix = "/out-of-band/create-invitation"
        alias = "sb_iss_connect"
        handshake_protocols = ["did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"]
        accept = [
            "didcomm/aip1",
            "didcomm/aip2;env=rfc19"
        ]
        params = json.dumps({
            "auto_accept": False,
            "multi_use": True,
        })
        data = json.dumps({
            "accept": accept,
            "alias": alias,
            "attachments": [],
            "handshake_protocols": handshake_protocols,
            "metadata": {},
            "my_label": "Invitation to Connect",
            "protocol_version": "1.1",
            "use_public_did": False,
        })
        print(suffix)
        async with ClientSession() as session:
            try:
                async with session.post(url=endpoint + suffix, data=data, headers=self.headers,
                                        params=params) as response:
                    json_response = await response.json()
                    invitation = json.dumps(json_response["invitation"])
            except Exception as e:
                print(e, "Error generating invite.")
                return "Error"
            else:
                if response.status == 200:
                    print("Invitation generated.")
                    print("ACCEPT RESPONSE:\n", invitation)
                return invitation


    async def receive_invite(self, auto_accept: bool = True):
        input_data = input('Enter Invitation :\n')
        data = json.loads(input_data)
        async with ClientSession() as session:
            params = {"auto_accept": auto_accept}
            if "/out-of-band/" in data:
                print("yes, out of ban is present")
                # reuse connections if possible
                params["use_existing_connection"] = "true"
                suffix = "/out-of-band/receive-invitation"
            else:
                suffix = "/connections/receive-invitation"

            try:
                async with session.post(url=self.admin_endpoint + suffix, data=json.dumps(data), headers=self.headers,
                                        params=params) as response:
                    json_response = await response.json()
            except Exception as e:
                print(e, "Error Receiving invite.")
                return "Error"
            else:

                if response.status == 200:
                    print("Invitation received.")
                    print("ACCEPT RESPONSE:\n", json_response)
                return json_response


async def main():
    c = Controller()
    await c.agent_status()
    choices = {
        1: {
            "text": "Start Agent",
            "action": c.start_agent,
        },
        2: {
            "text": "Provision Base Wallet",
            "action": c.create_agent_base_wallet,
        },
        3: {
            "text": "Stop Agent",
            "action": c.terminate_agent,
        },
        4: {
            "text": "Get Status",
            "action": c.agent_status,
        },
        5: {
            "text": "Create Invite",
            "action": c.create_invitation,
        },
        6: {
            "text": "Accept Invite",
            "action": c.receive_invite,
        },
    }
    cycle = 0
    while True:
        print("ISSUER AGENT")
        await asyncio.sleep(3.0)
        for num, option in choices.items():
            print(f"{num}. {option['text']}")
        try:
            input_choice = int(input("Enter option number: "))
        except ValueError:
            print("Invalid input. Please enter a number.\n")
            continue
        if input_choice in choices:
            cycle += 1
            user_choice = choices[input_choice]
            print("Performing Action: ", user_choice["text"])
            try:
                await user_choice["action"]()
            except Exception as e:
                print(e)


asyncio.run(main())
