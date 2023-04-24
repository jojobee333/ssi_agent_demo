# ssi_agent_demo
This code defines a Python class, Controller, with various methods for managing a self-sovereign identity (SSI) agent. The Controller class has methods for registering a DID, getting the agent status, starting and stopping the agent, creating an invitation, and accepting an invitation.

The code makes use of the following libraries:
* asyncio: a library for writing asynchronous code in Python
* json: a library for encoding and decoding JSON data
* logging: a library for logging messages
* os: a library for interacting with the operating system
* re: a library for working with regular expressions
* socket: a library for working with sockets
* subprocess: a library for running subprocesses
* pprint: a library for pretty-printing data structures
* requests: a library for making HTTP requests
* aiohttp: an asynchronous HTTP client/server library for asyncio
* dotenv: a library for working with environment variables

The script defines the following functions:

* flatten(args): A function that takes a nested list as an argument and yields a flattened version of that list.
* divider(func): A decorator function that takes another function as an argument and returns a new function that prints a divider before and after calling the original function.
* is_port_in_use(host, port): A function that takes a host and port as arguments and returns True if the port is in use, False otherwise.

The Controller class defines the following methods:


 * register_did(self, alias, seed, local_scope: bool = True, did=None): A method that registers a DID to a specified ledger url(Decentralized Identifier).
 * get_genesis_transactions(self): A method that retrieves the genesis transactions for the agent.
 * agent_status(self): A method that checks the status of the agent.
 * get_agent_args(self, provision=False, debug=False): A method that gets the arguments for starting the agent.
 * start_agent(self, debug=False): A method that starts the agent.
 * terminate_agent(self, old_instances=True): A method that terminates the agent.
 * provision_agent(self, debug=False): A method that provisions the agent.
 * create_agent_base_wallet(self): A method that creates a base wallet for the agent.
 * create_invitation(self): A method that creates an invitation to connect with another agent.
 * receive_invite(self, auto_accept: bool = True): A method that receives an invitation from another agent.
