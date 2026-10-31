"""循环：shorten 通过条件边回到自己，直到只剩一个分句。

回边和普通边用的是同一套 add_conditional_edges。路径函数返回
"shorten" 就再执行一次，返回 "done" 就离开循环。steps 用来观察
循环次数，也给递归深度一个明确的停止条件。

说明见 4_cycle.md。

运行：
        python 4_cycle.py
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

Decision = Literal["shorten", "done"]
_MAX_STEPS = 3


class DraftState(TypedDict):
    text: str
    steps: int
    trace: Annotated[list[str], operator.add]


def _clauses(text: str) -> list[str]:
    return [part for part in text.split("，") if part]


def shorten(state: DraftState) -> dict:
    parts = _clauses(state["text"])
    nxt = "，".join(parts[:-1]) if len(parts) > 1 else state["text"]
    steps = state["steps"] + 1
    print(f"[shorten] 第 {steps} 次 -> {nxt}")
    return {"text": nxt, "steps": steps, "trace": [f"shorten#{steps}"]}


def route_after_shorten(state: DraftState) -> Decision:
    """路径函数。返回 shorten 形成回边，返回 done 离开循环。"""
    finished = state["steps"] >= _MAX_STEPS or len(_clauses(state["text"])) <= 1
    return "done" if finished else "shorten"


def finish(state: DraftState) -> dict:
    print(f"[done] 停止，共缩短 {state['steps']} 次，剩余「{state['text']}」")
    return {"trace": ["done"]}


def build_graph():
    graph = StateGraph(DraftState)
    graph.add_node("shorten", shorten)
    graph.add_node("done", finish)
    graph.add_edge(START, "shorten")
    graph.add_conditional_edges(
        "shorten",
        route_after_shorten,
        {"shorten": "shorten", "done": "done"},
    )
    graph.add_edge("done", END)
    return graph.compile()


def main() -> None:
    app = build_graph()
    print(app.get_graph().draw_mermaid())
    result = app.invoke(
        {
            "text": "先读状态，再调用节点，然后按边跳转，最后写出结果",
            "steps": 0,
            "trace": [],
        }
    )
    print("—— 最终状态 ——")
    print("text:", result["text"])
    print("steps:", result["steps"])
    print("经过节点:", " -> ".join(result["trace"]))


if __name__ == "__main__":
    main()
