"""
闹钟提醒 MCP Server

职责：仅做语义解析 + 调用后端 REST API
所有调度逻辑、数据持久化、消息推送均由后端完成
"""

import json
import os

import aiohttp
from fastmcp import FastMCP

server = FastMCP('Alarm Server')

PORT = os.getenv('BACK_END_PORT', '3000')
BACKEND_API_BASE = f'http://localhost:{PORT}/api/v1'


async def _call_backend(method: str, path: str, body: dict = None) -> dict:
    """异步调用后端 REST API"""
    url = f'{BACKEND_API_BASE}{path}'
    headers = {'Content-Type': 'application/json', 'token': 'dev'}
    kwargs = {'headers': headers}
    if body:
        kwargs['json'] = body
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as resp:
                return await resp.json()
    except aiohttp.ClientError as e:
        return {'code': 500, 'msg': f'请求失败: {str(e)}'}
    except Exception as e:
        return {'code': 500, 'msg': f'请求失败: {str(e)}'}


@server.tool()
async def alarm_set(
    name: str,
    delay_seconds: int = 0,
    cron_expr: str = '',
    serial_number: str = '',
) -> dict:
    """为用户添加各种闹钟提醒功能

    示例：
    - 一次性提醒（5分钟后）→ delay_seconds=300, name="出发"
    - 每天下午2点提醒刷牙 → cron_expr="0 14 * * *", name="刷牙"
    - 每小时提醒喝水      → cron_expr="0 * * * *", name="喝水"
    - 工作日早上9点开会    → cron_expr="0 9 * * 1-5", name="开会"

    Args:
        name: 提醒内容（必填），从用户语义中提取
        delay_seconds: 一次性提醒，多少秒后触发（二选一）
        cron_expr: 周期性提醒，cron 表达式（二选一）
            - 标准 5 段式: "分 时 日 月 周"，如 "0 14 * * *","0 9 * * 1-5"
        serial_number: 设备序列号（由平台自动注入，MCP 调用方无需传入）
    """
    # 参数校验
    name = name.strip()
    if not name:
        return {'success': False, 'message': '提醒名称不能为空'}
    if delay_seconds > 0 and cron_expr:
        return {'success': False, 'message': 'delay_seconds 和 cron_expr 不能同时设置'}
    if delay_seconds <= 0 and not cron_expr:
        return {'success': False, 'message': '请设置 delay_seconds（一次性）或 cron_expr（周期性）'}

    alarm_type = 'once' if delay_seconds > 0 else 'recurring'

    # 调用后端 API 创建闹钟
    res = await _call_backend('POST', '/agent/alarm/create', {
        'serial_number': serial_number,
        'name': name,
        'alarm_type': alarm_type,
        'delay_seconds': delay_seconds,
        'cron_expr': cron_expr,
    })

    if res.get('code') == 200:
        alarm_data = res.get('data', {})
        next_trigger = alarm_data.get('next_trigger_time', '')
        message = f'已设置提醒: {name}\n下次触发: {next_trigger}'
        return {'success': True, 'message': message, 'alarm_id': alarm_data.get('id')}
    return {'success': False, 'message': f'设置闹钟失败: {res.get("msg", "未知错误")}'}


@server.tool()
async def alarm_del(id: int) -> dict:
    """根据 id 删除一个闹钟提醒

    首先用 alarm_queryall 查询所有闹钟，然后基于用户意图给出闹钟列表中的一个 id，删除前需要和用户确认

    Args:
        id: 闹钟 ID
    """
    res = await _call_backend('DELETE', f'/agent/alarm/delete?id={id}')
    if res.get('code') == 200:
        return {'success': True, 'message': '已删除闹钟'}
    return {'success': False, 'message': f'删除闹钟失败: {res.get("msg", "未知错误")}'}


@server.tool()
async def alarm_queryall(serial_number: str = '') -> dict:
    """查询本设备所有的提醒和闹钟

    Args:
        serial_number: 设备序列号（由平台自动注入）
    """
    res = await _call_backend('GET', f'/agent/alarm/list?serial_number={serial_number}')
    if res.get('code') == 200:
        alarms = res.get('data', [])
        return {'success': True, 'alarms': alarms, 'total': len(alarms)}
    return {'success': False, 'message': f'查询闹钟失败: {res.get("msg", "未知错误")}'}


@server.tool()
async def alarm_toggle(id: int, enabled: bool) -> dict:
    """启用或禁用闹钟

    Args:
        id: 闹钟 ID
        enabled: True 启用，False 禁用
    """
    res = await _call_backend('POST', '/agent/alarm/update', {'id': id, 'enabled': enabled})
    if res.get('code') == 200:
        action = '启用' if enabled else '禁用'
        return {'success': True, 'message': f'已{action}闹钟'}
    return {'success': False, 'message': f'操作失败: {res.get("msg", "未知错误")}'}


if __name__ == '__main__':
    server.run()
