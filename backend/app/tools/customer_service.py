"""
客服工具函数
提供订单查询、物流查询、退换货政策查询等功能
"""

from langchain_core.tools import tool


@tool
def query_order_status(order_id: str = "") -> str:
    """
    查询订单状态

    Args:
        order_id: 订单号（可选）

    Returns:
        订单状态信息
    """
    if not order_id:
        return "请提供订单号，例如：ORD-2024-001"
    return (
        f"订单 {order_id} 的状态：\n"
        f"- 状态：已发货\n"
        f"- 预计送达：2026-06-05\n"
        f"- 配送方式：标准快递"
    )


@tool
def query_logistics(order_id: str = "") -> str:
    """
    查询物流信息

    Args:
        order_id: 订单号（可选）

    Returns:
        物流信息
    """
    if not order_id:
        return "请提供订单号，例如：ORD-2024-001"
    return (
        f"订单 {order_id} 的物流信息：\n"
        f"- 快递公司：顺丰速运\n"
        f"- 运单号：SF1234567890\n"
        f"- 当前位置：北京转运中心\n"
        f"- 预计送达：2026-06-05"
    )


@tool
def query_return_policy() -> str:
    """
    查询退换货政策

    Returns:
        退换货政策信息
    """
    return (
        "退换货政策：\n"
        "1. 自签收之日起 7 天内可申请退货\n"
        "2. 商品需保持原包装、吊牌完好\n"
        "3. 退款将在 3-5 个工作日内原路返回\n"
        "4. 如有疑问请联系客服热线：400-123-4567"
    )


@tool
def query_payment_methods() -> str:
    """
    查询支付方式

    Returns:
        支持的支付方式
    """
    return (
        "支持的支付方式：\n"
        "1. 微信支付\n"
        "2. 支付宝\n"
        "3. 银行卡\n"
        "4. 货到付款"
    )


@tool
def query_shipping_fee(province: str = "") -> str:
    """
    查询运费

    Args:
        province: 省份名称（可选）

    Returns:
        运费信息
    """
    if not province:
        return "请提供省份名称，例如：北京、上海"
    return (
        f"{province} 地区的运费标准：\n"
        f"- 订单满 99 元：免运费\n"
        f"- 订单不满 99 元：运费 10 元\n"
        f"- 偏远地区：运费 20 元"
    )
