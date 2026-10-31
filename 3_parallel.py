"""并行图：prepare 之后三路同时检查，全部完成后才进入 merge。

一个节点有多条出边时，这些下游处于同一步。汇合边的起点写成列表，
merge 会等三个检查节点都返回。三个节点写不同的字段，trace 用
operator.add 合并，这样并行更新不会互相覆盖。

说明见 3_parallel.md。

运行：
        python 3_parallel.py
"""

from __future__ import annotations

import operator
import threading
import time
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

# 每个分支停 0.3 秒。耗时太短时，线程池可能复用同一个线程。
_PAUSE = 0.3
_T0 = 0.0


class ReviewState(TypedDict):
    text: str
    length_note: str
    keyword_note: str
    punct_note: str
    summary: str
    trace: Annotated[list[str], operator.add]


def _mark(name: str) -> str:
    time.sleep(_PAUSE)
    elapsed = time.perf_counter() - _T0
    thread = threading.current_thread().name
    line = f"{name} 线程={thread} 距 prepare 结束 {elapsed:.3f}s"
    print(f"[{name}] {line}")
    return line


def prepare(state: ReviewState) -> dict:
    global _T0
    _T0 = time.perf_counter()
    print(f"[prepare] 原文：{state['text']}")
    return {"trace": ["prepare"]}


def length_check(state: ReviewState) -> dict:
    note = _mark("length_check")
    count = len(state["text"])
    return {
        "length_note": f"{note}；共 {count} 个字符",
        "trace": ["length_check"],
    }


def keyword_check(state: ReviewState) -> dict:
    note = _mark("keyword_check")
    hit = "LangGraph" in state["text"]
    flag = "包含 LangGraph" if hit else "没有 LangGraph"
    return {"keyword_note": f"{note}；{flag}", "trace": ["keyword_check"]}


def punct_check(state: ReviewState) -> dict:
    note = _mark("punct_check")
    flag = "有句号" if "。" in state["text"] else "没有句号"
    return {"punct_note": f"{note}；{flag}", "trace": ["punct_check"]}


def merge(state: ReviewState) -> dict:
    print("[merge] 三路结果都到了，开始汇总")
    summary = "\n".join(
        (
            state["length_note"],
            state["keyword_note"],
            state["punct_note"],
        )
    )
    return {"summary": summary, "trace": ["merge"]}


def build_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("prepare", prepare)
    graph.add_node("length_check", length_check)
    graph.add_node("keyword_check", keyword_check)
    graph.add_node("punct_check", punct_check)
    graph.add_node("merge", merge)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "length_check")
    graph.add_edge("prepare", "keyword_check")
    graph.add_edge("prepare", "punct_check")
    graph.add_edge(
        ["length_check", "keyword_check", "punct_check"],
        "merge",
    )
    graph.add_edge("merge", END)
    return graph.compile()


def main() -> None:
    app = build_graph()
    print(app.get_graph().draw_mermaid())
    result = app.invoke(
        {
            "text": "LangGraph 用状态图描述步骤。",
            "length_note": "",
            "keyword_note": "",
            "punct_note": "",
            "summary": "",
            "trace": [],
        }
    )
    print("—— 汇总 ——")
    print(result["summary"])
    print("trace:", result["trace"])


if __name__ == "__main__":
    main()
