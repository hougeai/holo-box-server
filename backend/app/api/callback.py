from fastapi import APIRouter, Request, HTTPException, Response
import json
from models.finance import Recharge
from controllers.finance import recharge_controller
from core.log import logger
from core.pay import payment_service


router = APIRouter(tags=['回调模块'])


@router.post('/alipay/notify', summary='支付宝异步通知回调')
async def alipay_notify(request: Request):
    # 获取请求体内容
    form_data = await request.form()
    # 将表单数据转换为字典
    data = dict(form_data)
    logger.info(f'收到支付宝异步通知: {data}')

    # 验证签名
    if not payment_service.alipay_api.verify_notification(data):
        logger.error('支付宝异步通知签名验证失败')
        raise HTTPException(status_code=400, detail='Invalid signature')

    # 获取订单号和交易状态
    out_trade_no = data.get('out_trade_no', '')
    trade_status = data.get('trade_status', '')

    if not out_trade_no:
        logger.error('支付宝异步通知缺少订单号')
        raise HTTPException(status_code=400, detail='Missing order number')

    # 处理不同的交易状态
    if trade_status == 'TRADE_SUCCESS' or trade_status == 'TRADE_FINISHED':
        # 支付成功，更新订单状态
        try:
            obj = await Recharge.filter(trade_id=out_trade_no).first()
            if not obj:
                raise HTTPException(status_code=404, detail='Order not found')
            if not obj.is_paid:
                await recharge_controller.confirm_payment(id=obj.id)
            else:
                logger.info(f'订单 {out_trade_no} 已经处理过，无需重复处理')
        except Exception as e:
            logger.error(f'处理订单 {out_trade_no} 时出错: {str(e)}')
            raise HTTPException(status_code=500, detail='Internal server error')
    elif trade_status == 'TRADE_CLOSED':
        logger.info(f'订单 {out_trade_no} 已关闭')
    else:
        logger.warning(f'未知的交易状态: {trade_status}')
    # 返回成功响应给支付宝，必须是纯文本格式的"success"
    return Response(content='success', media_type='text/plain')


@router.post('/wechat/notify', summary='微信支付异步通知回调')
async def wechat_notify(request: Request):
    # 获取请求头和请求体
    body = await request.body()
    body_str = body.decode('utf-8')
    logger.info(f'收到微信支付异步通知: {body_str}')

    # 验证签名 - 使用 request.headers 直接获取（保持原始大小写）
    is_valid = payment_service.verify_wxpay_notification(request.headers, body_str)
    if not is_valid:
        logger.error('微信支付异步通知签名验证失败')
        raise HTTPException(status_code=400, detail='Invalid signature')

    # 解析通知内容
    notify_data = payment_service.parse_wxpay_notification(body_str)
    if not notify_data:
        logger.error('微信支付通知内容解析失败')
        raise HTTPException(status_code=400, detail='Parse failed')
    logger.info(f'解析通知内容: {notify_data}')
    # 从原始请求中获取事件类型
    body_json = json.loads(body_str)
    event_type = body_json.get('event_type', '')

    # 获取订单号
    out_trade_no = notify_data.get('out_trade_no', '')
    if not out_trade_no:
        logger.error('微信支付通知缺少订单号')
        raise HTTPException(status_code=400, detail='Missing order number')

    # 处理支付成功回调
    if event_type == 'TRANSACTION.SUCCESS':
        trade_state = notify_data.get('trade_state', '')
        if trade_state == 'SUCCESS':
            try:
                obj = await Recharge.filter(trade_id=out_trade_no).first()
                if not obj:
                    logger.warning(f'订单 {out_trade_no} 不存在')
                    raise HTTPException(status_code=404, detail='Order not found')
                if not obj.is_paid:
                    await recharge_controller.confirm_payment(id=obj.id)
                    logger.info(f'微信支付订单 {out_trade_no} 已确认充值')
                else:
                    logger.info(f'订单 {out_trade_no} 已经处理过，无需重复处理')
            except Exception as e:
                logger.error(f'处理订单 {out_trade_no} 时出错: {str(e)}')
                raise HTTPException(status_code=500, detail='Internal server error')
        else:
            logger.warning(f'微信支付状态: {trade_state}')

    # 处理退款成功回调
    elif event_type == 'REFUND.SUCCESS':
        refund_status = notify_data.get('refund_status', '')
        if refund_status == 'SUCCESS':
            try:
                obj = await Recharge.filter(trade_id=out_trade_no).first()
                if not obj:
                    logger.warning(f'订单 {out_trade_no} 不存在')
                    raise HTTPException(status_code=404, detail='Order not found')
                if not obj.is_refunded:
                    await recharge_controller.confirm_refund(id=obj.id)
                    logger.info(f'微信退款订单 {out_trade_no} 已确认退款，退款金额: {obj.refund_amount}')
                else:
                    logger.info(f'订单 {out_trade_no} 退款已处理过，无需重复处理')
            except Exception as e:
                logger.error(f'处理退款订单 {out_trade_no} 时出错: {str(e)}')
                raise HTTPException(status_code=500, detail='Internal server error')
        else:
            logger.warning(f'微信退款状态: {refund_status}')
    else:
        logger.warning(f'未处理的微信支付事件类型: {event_type}')

    # 返回成功响应给微信
    return Response(content='{"code":"SUCCESS","message":"成功"}', media_type='application/json')
