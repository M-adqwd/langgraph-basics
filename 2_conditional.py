"""条件边：START -> classify -> 三条分支之一 -> END。

classify 把路由名写进状态。route_ticket 不是节点，它是挂在 classify
后面的路径函数，每一轮只返回一个分支名。没被选中的节点不会执行。

说明见 2_conditional.md。

运行：
        python 2_conditional.py
"""

from __future__ import annotations

import operator
import warnings
from typing import Annotated, Literal

# langchain 导入时会把这条弃用提示重新打开。它来自检查点序列化的默认参数，
# 与这张图无关，所以先导入，再关掉，然后再导入 LangGraph。
import langchain

warnings.filterwarnings(
    "ignore",
    message=r"The default value of `allowed_objects` will change",
)

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

Route = Literal["refund", "order", "general"]


class TicketState(TypedDict):
    text: str
    route: str
    reply: str
    trace: Annotated[list[str], operator.add]


def classify(state: TicketState) -> dict:
    text = state["text"]
    if any(word in text for word in ("退款", "退货")):
        route: Route = "refund"
    elif any(word in text for word in ("订单", "物流", "发货")):
        route = "order"
    else:
        route = "general"
    print(f"[classify] 「{text}」 -> {route}")
    return {"route": route, "trace": [f"classify:{route}"]}


def refund(state: TicketState) -> dict:
    print("[refund] 处理退款")
    reply = f"已受理退款：「{state['text']}」。请提供订单号。"
    return {"reply": reply, "trace": ["refund"]}


def order(state: TicketState) -> dict:
    print("[order] 查询订单")
    reply = f"订单问题已记录：「{state['text']}」。正在查询物流。"
    return {"reply": reply, "trace": ["order"]}


def general(state: TicketState) -> dict:
    print("[general] 普通咨询")
    reply = f"已收到：「{state['text']}」。人工稍后回复。"
    return {"reply": reply, "trace": ["general"]}


def route_ticket(state: TicketState) -> Route:
    """路径函数：返回值必须是 path_map 里的键。"""
    return state["route"]  # type: ignore[return-value]


def build_graph():
    graph = StateGraph(TicketState)
    graph.add_node("classify", classify)
    graph.add_node("refund", refund)
    graph.add_node("order", order)
    graph.add_node("general", general)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_ticket,
        {"refund": "refund", "order": "order", "general": "general"},
    )
    graph.add_edge("refund", END)
    graph.add_edge("order", END)
    graph.add_edge("general", END)
    return graph.compile()


SAMPLES = (
    "我要退款，衣服不合适",
    "订单什么时候发货",
    "会员积分怎么用",
)


def main() -> None:
    app = build_graph()
    print(app.get_graph().draw_mermaid())
    for text in SAMPLES:
        print(f"—— 输入：{text} ——")
        result = app.invoke({"text": text, "route": "", "reply": "", "trace": []})
        print(result["reply"])
        print("经过节点:", " -> ".join(result["trace"]))
        print()


if __name__ == "__main__":
    main()
