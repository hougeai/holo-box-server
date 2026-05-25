import os
import sys
import re
import json
import asyncio
import aiohttp
import websockets
from .log import mcp_logger as logger


def build_server_command(protocol, cfg):
    """Build [cmd,...] for the server process for a given target."""
    if protocol == 'stdio':
        command = cfg.get('command')
        # 确保使用当前虚拟环境的 python，避免 PATH 里 python 无依赖
        if command in ('python', 'python3'):
            command = sys.executable
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
        raise Exception('Unknown MCP protocol: %s' % protocol)
    return cmd


async def connect_with_retry(uri, mcp):
    """Connect to WebSocket server with retry mechanism for a given server target."""
    reconnect_attempt = 0
    backoff = 1
    mcp_id = mcp['endpoint_id']
    max_retries = 7
    while reconnect_attempt <= max_retries:
        try:
            if reconnect_attempt > 0:
                logger.info(f'[{mcp_id}] Waiting {backoff}s before reconnection attempt {reconnect_attempt}...')
                await asyncio.sleep(backoff)
            # Attempt to connect
            await connect_to_server(uri, mcp)
        except asyncio.CancelledError as e:
            logger.info(f'[{mcp_id}] connect_with_retry task cancelled.')
            raise e  # 必须重新抛出，否则 task 无法被取消
        except websockets.exceptions.ConnectionClosed as e:
            reconnect_attempt += 1
            logger.warning(f'[{mcp_id}] WebSocket connection closed (attempt {reconnect_attempt}): {e}')
            backoff = min(backoff * 2, 120)
        except Exception as e:
            reconnect_attempt += 1
            logger.error(f'[{mcp_id}] Process error (attempt {reconnect_attempt}): {e}')
            backoff = min(backoff * 2, 120)
    # 重试耗尽，抛出异常让 task 标记为失败
    raise Exception(f'[{mcp_id}] Failed to connect after {max_retries} attempts')


async def connect_to_server(uri, mcp):
    """Connect to WebSocket server and pipe stdio for the given server target."""
    mcp_id = mcp['endpoint_id']
    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f'{mcp_id} successfully connected to WebSocket server {uri}')
            # Acquire shared process for this mcp (one process per mcp_id)
            process = await process_manager.acquire(mcp)
            logger.info(f'{mcp_id} acquired MCP process')
            # 检查子进程是否存活（404、认证失败等会导致子进程立即退出）
            try:
                await asyncio.wait_for(process.wait(), timeout=3.0)
                raise RuntimeError(f'MCP process exited with code {process.returncode} shortly after startup')
            except asyncio.TimeoutError:
                pass  # 进程 3s 内没死，存活
            # Register this websocket with the shared process manager so stdout reader can route messages
            await process_manager.register_ws(mcp_id, websocket)
            logger.info(f'{mcp_id} registered websocket')
            # 通知 connect() 连接已真正建立
            event = mcp.get('_connected_event')
            if event:
                event.set()
            # Only create the websocket->process writer task here. The process->websocket routing is handled by the shared stdout reader in ProcessManager.
            await pipe_websocket_to_process(websocket, process, mcp_id)
            # When pipe_websocket_to_process returns, connection closed or task ended.
            logger.info(f'{mcp_id} websocket->process pipe ended')
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f'{mcp_id} Connection error: {e}')
        raise e  # Re-throw exception to trigger reconnection
    except Exception as e:
        logger.error(f'{mcp_id} Connection error: {e}')
        raise e  # Re-throw exception
    finally:
        # Always unregister websocket so shared stdout reader won't try to send to a closed socket
        try:
            await process_manager.terminate(mcp_id)
            logger.info(f'{mcp_id} terminate websocket')
        except Exception as e:
            logger.exception(f'{mcp_id} Error during terminate websocket: {e}')


async def pipe_websocket_to_process(websocket, process, mcp_id):
    """Read data from WebSocket and write to shared process stdin"""
    try:
        while True:
            # Read message from WebSocket
            message = await websocket.recv()
            logger.info(f'[ws-{mcp_id}] 收到websocket信息：{type(message)} {message}')
            # parse text message to dict
            try:
                text = message.encode('utf-8')
                msg_dict = json.loads(text)
            except Exception as e:
                logger.error(f'[ws-{mcp_id}] Received non-JSON or parse error: {e} - ignoring')
                continue
            # Prefix id with device_id to allow shared process to echo id back for routing
            # if 'id' in msg_dict:
            #     orig_id = msg_dict['id']
            #     msg_dict['id'] = f'{orig_id}'
            # 把小智平台带的 serialNumber 注入到 tools/call 的 arguments 里，
            # 让 MCP server 的 tool 函数能拿到设备标识
            if msg_dict.get('method') == 'tools/call':
                serial = msg_dict.get('params', {}).get('serialNumber', '')
                if serial:
                    msg_dict['params'].setdefault('arguments', {})['serial_number'] = serial
            # write into shared process stdin (one writer per websocket task, but it's OK to write to same pipe)
            try:
                line = (json.dumps(msg_dict, ensure_ascii=False) + '\n').encode('utf-8')
                process.stdin.write(line)
                await process.stdin.drain()
            except Exception as e:
                logger.error(f'[ws-{mcp_id}] Error writing to process stdin: {e}')
                raise
    except asyncio.CancelledError:
        logger.error(f'[ws-{mcp_id}] pipe_websocket_to_process cancelled')
        raise
    except websockets.exceptions.ConnectionClosed:
        logger.error(f'[ws-{mcp_id}] websocket closed')
    except Exception as e:
        logger.error(f'[ws-{mcp_id}] Error in WebSocket to process pipe: {e}')
        raise


class ProcessManager:
    def __init__(self):
        self.processes = {}  # mcp_id -> subprocess.Process
        self.ws_map = {}  # mcp_id -> websocket
        self.stdout_tasks = {}  # mcp_id -> asyncio.Task reading stdout
        self.stderr_tasks = {}  # mcp_id -> asyncio.Task reading stderr
        self.lock = asyncio.Lock()

    async def acquire(self, mcp):
        """Get or start process for this mcp."""
        mcp_id = mcp['endpoint_id']
        async with self.lock:
            if mcp_id in self.processes:
                logger.info(f'[Process-{mcp_id}] Reusing MCP process')
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
            logger.info(f'[Process-{mcp_id}] Started MCP process: {cmd}')
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
            logger.error(f'[Process:{mcp_id}] Error terminating process: {e}')
        logger.info(f'[Process:{mcp_id}] MCP process terminated')

    async def _stdout_reader(self, process, mcp_id):
        """Single stdout reader per shared process; route messages to registered websockets.

        Expected: process writes JSON lines. The JSON must have an 'id' like "<device_id>-<orig_id>".
        """
        name = f'stdout-{mcp_id}'
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
                ws = self.ws_map.get(mcp_id)
                if ws:
                    asyncio.create_task(self._safe_send(ws, data_dict, mcp_id))
                else:
                    logger.warning(f'[{name}] no websocket registered (message {data_dict})')

        except asyncio.CancelledError:
            logger.info(f'[{name}] stdout reader cancelled')
            raise
        except Exception:
            logger.exception(f'[{name}] Error in stdout reader')
            raise
        finally:
            logger.info(f'[{name}] stdout reader exiting')

    async def _stderr_reader(self, process, mcp_id):
        name = f'stderr-{mcp_id}'
        try:
            while True:
                raw = await process.stderr.readline()
                if not raw:
                    logger.info(f'[{name}] stderr closed')
                    break
                logger.info(f'[{name}]: {raw.decode("utf-8").strip()}')
        except asyncio.CancelledError:
            logger.error(f'[{name}] stderr reader cancelled')
            raise
        except Exception:
            logger.exception(f'[{name}] Error in stderr reader')
            raise
        finally:
            logger.info(f'[{name}] stderr reader exiting')

    def _decode_unicode_escapes(self, raw_text):
        """Decode literal \\uXXXX escape sequences in string to actual Unicode chars (for log readability only)."""
        return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), raw_text)

    async def _safe_send(self, websocket, data_dict, mcp_id):
        """Send data to websocket and catch exceptions to avoid crashing the reader."""
        try:
            text = json.dumps(data_dict, ensure_ascii=False)
            await websocket.send(text)
            # Decode inner \uXXXX escapes for human-readable logging
            logger.info(f'[Process-{mcp_id}] sent: {self._decode_unicode_escapes(text)}')
        except Exception as e:
            logger.warning(f'[Process-{mcp_id}] Failed sent: {e}')


process_manager = ProcessManager()


class MCPManager:
    def __init__(self):
        self.connections = {}
        self._lock = asyncio.Lock()

    async def test(self, obj_in):
        name = obj_in.name
        config = obj_in.config
        protocol = obj_in.protocol
        if protocol == 'stdio':
            cmd = build_server_command(protocol, config)
            env_vars = config.get('env', {})
            merged_env = os.environ.copy()
            merged_env.update(env_vars)
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=merged_env,
                )
                try:
                    init_req = (
                        json.dumps(
                            {
                                'jsonrpc': '2.0',
                                'id': 1,
                                'method': 'initialize',
                                'params': {
                                    'protocolVersion': '2024-11-05',
                                    'capabilities': {},
                                    'clientInfo': {'name': 'test', 'version': '1.0'},
                                },
                            }
                        )
                        + '\n'
                    )
                    proc.stdin.write(init_req.encode())
                    await proc.stdin.drain()
                    line = await asyncio.wait_for(proc.stdout.readline(), timeout=10)
                    if not line:
                        return False, 'MCP 进程无响应'
                    resp = json.loads(line.decode())
                    if resp.get('result'):
                        logger.info(f'[{name}] MCP stdio 测试通过')
                        return True, ''
                    return False, f'MCP initialize 失败: {resp.get("error", "未知")}'
                finally:
                    proc.terminate()
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        proc.kill()
                        await proc.wait()
            except asyncio.TimeoutError:
                return False, 'MCP 进程响应超时 (10s)'
            except Exception as e:
                logger.error(f'[{name}] MCP stdio 测试异常: {e}')
                return False, f'MCP 进程测试失败: {e}'
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
        id = mcp['endpoint_id']
        token = mcp['token']
        if not id or not token:
            return False, 'MCP endpoint_id and token is required'
        # 如果已有连接，先清理
        existing_task = self.connections.get(id)
        if existing_task:
            if not existing_task.done():
                existing_task.cancel()
                try:
                    await existing_task
                except asyncio.CancelledError:
                    pass
            self.connections.pop(id, None)
            logger.info(f'[{id}] existing task cancelled')
        # 确保旧的 process 被清理（防止 task 在重试等待时被取消，process 未清理）
        try:
            await process_manager.terminate(id)
        except Exception as e:
            logger.info(f'{id} cleanup process (may not exist): {e}')

        uri = f'wss://api.xiaozhi.me/mcp/?token={token}'
        connected_event = asyncio.Event()
        mcp['_connected_event'] = connected_event
        task = asyncio.create_task(connect_with_retry(uri, mcp))
        self.connections[id] = task
        # 等待 connect_to_server 发送"连接真正建立"的信号（register_ws 之后），
        # 而非靠固定超时猜测。
        try:
            await asyncio.wait_for(connected_event.wait(), timeout=15.0)
            logger.info(f'[{id}] initial connection established')
            return True, 'Connected to MCP'
        except asyncio.TimeoutError:
            self.connections.pop(id, None)
            task.cancel()
            return False, 'MCP connection timed out'
        except asyncio.CancelledError:
            self.connections.pop(id, None)
            return False, 'MCP connection cancelled'
        except Exception as e:
            self.connections.pop(id, None)
            logger.error(f'[{id}] connect failed shortly after start: {e}')
            return False, f'MCP connection failed: {e}'
        finally:
            mcp.pop('_connected_event', None)

    async def disconnect(self, mcp):
        async with self._lock:
            mcp_id = mcp['endpoint_id']
            task = self.connections.get(mcp_id)
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            self.connections.pop(mcp_id, None)
            try:
                await process_manager.terminate(mcp_id)
            except Exception as e:
                logger.exception(f'{mcp_id} terminate error: {e}')
        return True, 'Disconnected'

    def is_connected(self, mcp_id: str) -> bool:
        """检查指定MCP是否在线（task仍在运行）"""
        task = self.connections.get(mcp_id)
        return task is not None and not task.done()

    def get_connection_status(self, mcp_id: str) -> dict:
        """获取MCP连接状态详情"""
        task = self.connections.get(mcp_id)
        if task is None:
            return {'connected': False, 'status': 'uncreated'}
        if task.done():
            if task.cancelled():
                return {'connected': False, 'status': 'cancelled'}
            exc = task.exception()
            if exc:
                return {'connected': False, 'status': 'failed', 'error': str(exc)}
            return {'connected': False, 'status': 'completed'}
        return {'connected': True, 'status': 'running'}


mcp_manager = MCPManager()
