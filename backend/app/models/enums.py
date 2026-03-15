from enum import Enum


# 需要获取所有可用选项时（如下拉菜单）；进行数据验证时（检查值是否在允许范围内）；生成API文档时（展示所有可用选项）
class EnumBase(Enum):
    @classmethod
    # 获取所有枚举值
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    # 获取所有枚举名称
    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class MethodType(str, Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'


class MenuType(str, Enum):
    CATALOG = 'catalog'  # 目录
    MENU = 'menu'  # 菜单


class McpProtocol(str, Enum):
    STDIO = 'stdio'
    SSE = 'sse'
    HTTP = 'http'


class SubjectType(str, Enum):
    HUMAN = 'human'
    ANIMAL = 'animal'


class GiftType(str, Enum):
    REGISTER = 'register'  # 注册赠送
    ACTIVITY = 'activity'  # 活动赠送
    COMPENSATION = 'compensation'  # 补偿赠送


class PointsFlowType(str, Enum):
    RECHARGE = 'recharge'  # 充值
    GIFT = 'gift'  # 赠送
    ORDER = 'order'  # 订单消费
    EXPIRE = 'expire'  # 过期扣减
