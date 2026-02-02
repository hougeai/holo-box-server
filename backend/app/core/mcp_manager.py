import os
import sys
import json
import asyncio
import aiohttp
import websockets
from .log import mcp_logger as logger


def build_server_command(protocol, cfg):
    """Build [cmd,...] for the server process for a given target."""
    if protocol == 'stdio':
        command = cfg.get('command')
        args = cfg.get('args') or []
        cmd = [command] + args
    elif protocol in ('sse', 'http'):
        url = cfg.get('url')
        # Unified approach: always use current Python to run mcp-proxy module
        cmd = [sys.executable, '-m', 'mcp_proxy']
        if protocol == 'http':
            cmd += ['--transport', 'streamablehttp']
        # optional headers: {"Authorization": "Bearer xxx"}
        headers = cfg.get('headers') or {}
        for k, v in headers.items():
            cmd += ['-H', k, str(v)]
        cmd.append(url)
    else:
        raise Exception('Unknown MCP protocole: %s' % protocol)
    return cmd


async def connect_with_retry(uri, mcp):
    """Connect to WebSocket server with retry mechanism for a given server target."""
    reconnect_attempt = 0
    backoff = 1
    mcp_id = mcp['id']
    max_retries = 7
    while reconnect_attempt <= max_retries:
        try:
            if reconnect_attempt > 0:
                logger.info(f'[{mcp_id}] Waiting {backoff}s before reconnection attempt {reconnect_attempt}...')
                await asyncio.sleep(backoff)
            # Attempt to connect
            await connect_to_server(uri, mcp)
        except asyncio.CancelledError:
            logger.info(f'[{mcp_id}] connect_with_retry task cancelled.')
            raise  # 必须重新抛出，否则 task 无法被取消
        except websockets.exceptions.ConnectionClosed as e:
            reconnect_attempt += 1
            logger.warning(f'[{mcp_id}] WebSocket connection closed (attempt {reconnect_attempt}): {e}')
            backoff = min(backoff * 2, 120)
        except Exception as e:
            reconnect_attempt += 1
            logger.error(f'[{mcp_id}] Process error (attempt {reconnect_attempt}): {e}')
            backoff = min(backoff * 2, 120)
    # 最后也要清理process
    logger.error(f'[{mcp_id}] Failed to connect after {max_retries} attempts')


async def connect_to_server(uri, mcp):
    """Connect to WebSocket server and pipe stdio for the given server target."""
    mcp_id = mcp['id']
    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f'{mcp_id} successfully connected to WebSocket server {uri}')
            # Acquire shared process for this mcp (one process per mcp_id)
            process = await process_manager.acquire(mcp)
            logger.info(f'{mcp_id} acquired shared MCP process')
            # Register this websocket with the shared process manager so stdout reader can route messages
            await process_manager.register_ws(mcp_id, websocket)
            logger.info(f'{mcp_id} registered websocket')
            # Only create the websocket->process writer task here. The process->websocket routing is handled by the shared stdout reader in ProcessManager.
            await pipe_websocket_to_process(websocket, process, mcp_id)
            # When pipe_websocket_to_process returns, connection closed or task ended.
            logger.info(f'{mcp_id} websocket->process pipe ended')
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f'{mcp_id} Connection error: {e}')
        raise  # Re-throw exception to trigger reconnection
    except Exception as e:
        logger.error(f'{mcp_id} Connection error: {e}')
        raise  # Re-throw exception
    finally:
        # Always unregister websocket so shared stdout reader won't try to send to a closed socket
        try:
            await process_manager.unregister_ws(mcp_id)
            logger.info(f'{mcp_id} Unregistered websocket')
        except Exception as e:
            logger.exception(f'{mcp_id} Error during unregister_ws: {e}')


async def pipe_websocket_to_process(websocket, process, device_id, mcp_id):
    """Read data from WebSocket and write to shared process stdin"""
    try:
        while True:
            # Read message from WebSocket
            message = await websocket.recv()
            logger.info(f'[{mcp_id}:{device_id}] 收到websocket信息：{type(message)} {message}')
            # parse text message to dict
            try:
                text = message.encode('utf-8')
                msg_dict = json.loads(text)
            except Exception as e:
                logger.error(f'[{mcp_id}:{device_id}] Received non-JSON or parse error: {e} - ignoring')
                continue
            # Prefix id with device_id to allow shared process to echo id back for routing
            if 'id' in msg_dict:
                orig_id = msg_dict['id']
                msg_dict['id'] = f'{device_id}-{orig_id}'
            # write into shared process stdin (one writer per websocket task, but it's OK to write to same pipe)
            try:
                line = (json.dumps(msg_dict, ensure_ascii=False) + '\n').encode('utf-8')
                process.stdin.write(line)
                await process.stdin.drain()
            except Exception as e:
                logger.error(f'[{mcp_id}:{device_id}] Error writing to process stdin: {e}')
                raise
    except asyncio.CancelledError:
        logger.info(f'[{mcp_id}:{device_id}] pipe_websocket_to_process cancelled')
        raise
    except websockets.exceptions.ConnectionClosed:
        logger.info(f'[{mcp_id}:{device_id}] websocket closed')
    except Exception as e:
        logger.error(f'[{mcp_id}:{device_id}] Error in WebSocket to process pipe: {e}')
        raise


class ProcessManager:
    def __init__(self):
        self.processes = {}  # mcp_id -> subprocess.Process
        self.ws_map = {}  # mcp_id -> websocket
        self.stdout_tasks = {}  # mcp_id -> asyncio.Task reading stdout
        self.stderr_tasks = {}  # mcp_id -> asyncio.Task reading stderr
        self.lock = asyncio.Lock()

    async def acquire(self, mcp):
        """Get or start shared process for this mcp (keyed by mcp['id'])."""
        mcp_id = mcp['id']
        async with self.lock:
            if mcp_id in self.processes:
                logger.info(f'[mcp-{mcp_id}] Reusing shared MCP process')
                return self.processes[mcp_id]
            protocol = mcp['protocol']
            cfg = mcp.get('config', {})
            cmd = build_server_command(protocol, cfg)
            env = cfg.get('env', {})
            merged_env = os.environ.copy()
            merged_env.update(env)
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=merged_env,
            )
            self.processes[mcp_id] = process
            # start stdout reader and stderr logger tasks
            t_out = asyncio.create_task(self._stdout_reader(process, mcp_id))
            t_err = asyncio.create_task(self._stderr_reader(process, mcp_id))
            self.stdout_tasks[mcp_id] = t_out
            self.stderr_tasks[mcp_id] = t_err
            logger.info(f'[mcp-{mcp_id}] Started shared MCP process: {cmd}')
            return process

    async def register_ws(self, mcp_id, websocket):
        """Register a websocket for a given mcp_id and device_id."""
        async with self.lock:
            # ensure process exists (caller should have called acquire already)
            self.ws_map[mcp_id] = websocket
            logger.info(f'{mcp_id} register_ws: mcp')

    async def terminate(self, mcp_id):
        """Terminate the shared process for given mcp_id"""
        async with self.lock:
            self.ws_map.pop(mcp_id, None)
            proc = self.processes.pop(mcp_id, None)
            # cancel stdout/stderr tasks
            t_out = self.stdout_tasks.pop(mcp_id, None)
            t_err = self.stderr_tasks.pop(mcp_id, None)
        if t_out:
            t_out.cancel()
        if t_err:
            t_err.cancel()
        if not proc:
            return
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
        except Exception as e:
            logger.error(f'[ProcessManager:{mcp_id}] Error terminating process: {e}')
        logger.info(f'[ProcessManager:{mcp_id}] Shared MCP process terminated')

    async def _stdout_reader(self, process, mcp_id):
        """Single stdout reader per shared process; route messages to registered websockets.

        Expected: process writes JSON lines. The JSON must have an 'id' like "<device_id>-<orig_id>".
        """
        name = f'mcp-{mcp_id}'
        try:
            while True:
                raw = await process.stdout.readline()
                if not raw:
                    logger.info(f'[{name}] stdout closed')
                    break
                try:
                    text = raw.decode('utf-8').strip()
                except Exception:
                    logger.error(f'[{name}] stdout decode error')
                    continue
                try:
                    data_dict = json.loads(text)
                except Exception:
                    logger.error(f'[{name}] stdout non-json line: {text!r}')
                    continue
                logger.info(f'[{name}] stdout: {data_dict}')
                # id must include device_id prefix
                id_field = data_dict.get('id')
                if isinstance(id_field, str) and '-' in id_field:
                    device_id, orig_id = id_field.rsplit('-', 1)
                    data_dict['id'] = int(orig_id)
                    ws = None
                    async with self.lock:
                        ws = self.ws_map.get(mcp_id, {}).get(device_id)
                    if ws:
                        # send asynchronously; do not block stdout reader
                        asyncio.create_task(self._safe_send(ws, data_dict, mcp_id))
                    else:
                        logger.warning(f'[{name}] no websocket registered (message {data_dict})')
                else:
                    logger.error(f'[{name}] stdout missing device prefix in id: {data_dict}')
        except asyncio.CancelledError:
            logger.info(f'[{name}] stdout reader cancelled')
            raise
        except Exception:
            logger.exception(f'[{name}] Error in stdout reader')
        finally:
            logger.info(f'[{name}] stdout reader exiting')

    async def _stderr_reader(self, process, mcp_id):
        name = f'mcp-{mcp_id}'
        try:
            while True:
                raw = await process.stderr.readline()
                if not raw:
                    logger.info(f'[{name}] stderr closed')
                    break
                logger.info(f'[{name}] stderr: {raw.decode("utf-8").strip()}')
        except asyncio.CancelledError:
            logger.info(f'[{name}] stderr reader cancelled')
            raise
        except Exception:
            logger.exception(f'[{name}] Error in stderr reader')
        finally:
            logger.info(f'[{name}] stderr reader exiting')

    async def _safe_send(self, websocket, data_dict, mcp_id):
        """Send data to websocket and catch exceptions to avoid crashing the reader."""
        try:
            text = json.dumps(data_dict, ensure_ascii=False)
            await websocket.send(text)
            logger.info(f'[mcp-{mcp_id}] sent: {text}')
        except Exception as e:
            logger.warning(f'[mcp-{mcp_id}] Failed sent: {e}')


process_manager = ProcessManager()


class MCPManager:
    def __init__(self):
        self.connections = {}

    async def test(self, obj_in):
        name = obj_in.name
        config = obj_in.config
        protocol = obj_in.protocol
        if protocol == 'stdio':
            return False, 'Not support stdio MCP'
        else:
            url = config.get('url', '')
            headers = config.get('headers', {})
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        logger.info(f'[{name}] MCP test response: {response.status}')
                        if 200 <= response.status < 400:
                            return True, ''
                        else:
                            return False, f'HTTP {response.status}: {await response.text()}'
            except Exception as e:
                logger.error(f'[{name}] Error connecting to MCP: {e}')
                return False, f'Error connecting to MCP: {e}'

    async def connect(self, mcp):
        # 为每个MCP创建一个连接
        id = mcp['id']
        token = mcp['token']
        if not token:
            return False, 'MCP token is required'
        uri = f'wss://api.xiaozhi.me/mcp/?token={token}'
        task = asyncio.create_task(connect_with_retry(uri, mcp))
        self.connections[id] = task
        return True, 'Connected to MCP'

    async def disconnect(self, mcp):
        async with self._lock:
            mcp_id = mcp['id']
            task = self.connections.get(mcp_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            try:
                await process_manager.terminate(mcp_id)
            except Exception as e:
                logger.exception(f'{mcp_id} terminate error: {e}')
        return True, 'Disconnected'


mcp_manager = MCPManager()
