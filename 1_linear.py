"""线性图：START -> outline -> draft -> END。

这是最小的 StateGraph。节点只做一件事：读当前状态，返回要合并进去的字段。
边是固定的，所以每次运行都是同一条路径。

说明见 1_linear.md。

运行：
        python 1_linear.py
"""

from __future__ import annotations

import operator
import warnings
from typing import Annotated

# langchain 导入时会把这条弃用提示重新打开。它来自检查点序列化的默认参数，
# 与这张图无关，所以先导入，再关掉，然后再导入 LangGraph。
import langchain

warnings.filterwarnings(
    "ignore",
    message=r"The default value of `allowed_objects` will change",
)

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


class DocState(TypedDict):
    topic: str
    outline: str
    draft: str
    # operator.add 把每个节点返回的列表接到已有 trace 后面。
    trace: Annotated[list[str], operator.add]


def write_outline(state: DocState) -> dict:
    topic = state["topic"].strip()
    outline = f"1. {topic} 是什么\n2. 它由哪些部分组成\n3. 一个最小例子"
    print(f"[outline] 写出提纲，主题是「{topic}」")
    return {"outline": outline, "trace": ["outline"]}


def write_draft(state: DocState) -> dict:
    draft = (
        f"主题：{state['topic']}。\n"
        f"提纲如下：\n{state['outline']}\n"
        "这是一条只沿固定边往前走的流水线。"
    )
    print("[draft] 根据提纲写成短文")
    return {"draft": draft, "trace": ["draft"]}


def build_graph():
    graph = StateGraph(DocState)
    graph.add_node("outline", write_outline)
    graph.add_node("draft", write_draft)
    graph.add_edge(START, "outline")
    graph.add_edge("outline", "draft")
    graph.add_edge("draft", END)
    return graph.compile()


def main() -> None:
    app = build_graph()
    print(app.get_graph().draw_mermaid())
    result = app.invoke(
        {"topic": "LangGraph 的状态图", "outline": "", "draft": "", "trace": []}
    )
    print("—— 最终状态 ——")
    print(result["draft"])
    print("经过节点:", " -> ".join(result["trace"]))


if __name__ == "__main__":
    main()
