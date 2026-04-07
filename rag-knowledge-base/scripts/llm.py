#!/usr/bin/env python3
"""
LLM 统一接口

提供 LLM 调用能力，支持：
  - OpenAI 兼容格式的 API（NVIDIA NIM、OpenAI 等）
  - 并发批量调用
  - 重试机制
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable


# ─── 配置 ─────────────────────────────────────────
LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL: str = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_TIMEOUT: int = 60


# ─── 基础调用 ─────────────────────────────────────
def generate_text(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 1.0,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    """调用 LLM 生成文本

    Args:
        prompt: 提示词
        max_tokens: 最大 token 数
        temperature: 温度参数
        api_key: API Key（默认使用环境变量）
        model: 模型名称（默认使用 LLM_MODEL）
        base_url: API 端点（默认使用 LLM_BASE_URL）

    Returns:
        生成的文本
    """
    import requests

    key = api_key or LLM_API_KEY
    if not key:
        raise ValueError(
            "未设置 LLM API Key。\n"
            "请设置环境变量 LLM_API_KEY 或传入 api_key 参数"
        )

    url = (base_url or LLM_BASE_URL).rstrip("/") + "/chat/completions"

    resp = requests.post(
        url,
        json={
            "model": model or LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        timeout=LLM_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content", "").strip()


# ─── 批量调用 ─────────────────────────────────────
class LLMThreadPool:
    """线程池批量 LLM 调用器

    支持：
      - 并发批量调用
      - 结果按原始顺序返回
      - 失败自动重试

    用法：
        pool = LLMThreadPool(max_workers=8)
        results = pool.generate_batch([prompt1, prompt2, prompt3], max_tokens=256)
    """

    def __init__(
        self,
        max_workers: int = 8,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """初始化

        Args:
            max_workers: 最大并发数
            api_key: API Key
            model: 模型名称
            base_url: API 端点
        """
        self.api_key = api_key or LLM_API_KEY
        self.model = model or LLM_MODEL
        self.base_url = base_url or LLM_BASE_URL
        self.max_workers = max_workers

    def _call_once(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """单次 API 调用"""
        import requests

        url = self.base_url.rstrip("/") + "/chat/completions"
        resp = requests.post(
            url,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=LLM_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "").strip()

    def _call_with_retry(
        self, prompt: str, max_tokens: int, temperature: float, retries: int = 2
    ) -> str:
        """带重试的单次调用"""
        for attempt in range(retries + 1):
            try:
                return self._call_once(prompt, max_tokens, temperature)
            except Exception as e:
                if attempt == retries:
                    raise
                time.sleep(1 * (attempt + 1))  # 指数退避

    def generate_batch(
        self,
        prompts: list[str],
        max_tokens: int = 256,
        temperature: float = 1.0,
        show_progress: Optional[Callable[[int, int, str], None]] = None,
        batch_size: int = 0,
        batch_callback: Optional[Callable[[list[tuple[int, str]]], None]] = None,
    ) -> list[str]:
        """批量生成，结果顺序与 prompts 一致

        Args:
            prompts: 提示词列表
            max_tokens: 每个答案的最大 token 数
            temperature: 温度参数
            show_progress: 进度回调 fn(done, total, last_result)
            batch_size: 分批大小（0=不分批）
            batch_callback: fn([(idx, result), ...]) 每 batch_size 个完成时调用

        Returns:
            与 prompts 等长的结果列表，失败索引返回空字符串
        """
        total = len(prompts)
        results: list[str] = ["" for _ in range(total)]
        done = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(self._call_with_retry, p, max_tokens, temperature): i
                for i, p in enumerate(prompts)
            }

            batch_buf: list[tuple[int, str]] = []

            for future in as_completed(future_to_idx):
                i = future_to_idx[future]
                try:
                    results[i] = future.result()
                except Exception as e:
                    results[i] = ""
                done += 1
                batch_buf.append((i, results[i]))

                if show_progress:
                    show_progress(done, total, results[i][:80] if results[i] else str(e))

                if batch_size > 0 and len(batch_buf) >= batch_size:
                    batch_callback(batch_buf)
                    batch_buf.clear()

            if batch_buf:
                batch_callback(batch_buf)

        return results


# ─── 预建全局线程池实例 ────────────────────────────
_llm_pool: Optional[LLMThreadPool] = None


def get_llm_pool(max_workers: int = 8) -> LLMThreadPool:
    """获取全局 LLMThreadPool 实例（懒加载）"""
    global _llm_pool
    if _llm_pool is None:
        _llm_pool = LLMThreadPool(max_workers=max_workers)
    return _llm_pool


# ─── 便捷函数 ─────────────────────────────────────
def generate_abstract(
    text: str, title: str = "", context: str = "", **kwargs
) -> str:
    """为一个节点生成语义摘要（80-200字）

    Args:
        text: 节点内容
        title: 节点标题
        context: 上下文（上级的标题）
        **kwargs: 传递给 generate_text 的参数
    """
    prompt = f"""为以下内容生成一段简洁的语义摘要，概括其核心主题和关键信息。

要求：摘要必须准确反映内容主题，不要添加不存在的信息。控制在80-200字。只输出摘要，不要解释。

{f"[上级主题] {context}" if context else ""}
{f"[节点标题] {title}" if title else ""}
---
[内容]
{text[:3000]}
---
语义摘要："""
    try:
        return generate_text(prompt, max_tokens=256, **kwargs)
    except Exception:
        return f"{title}：{text[:100]}"


def generate_query_expansions(
    query: str, n: int = 3, **kwargs
) -> list[str]:
    """将用户问题扩展为多个检索查询

    Args:
        query: 原始查询
        n: 扩展数量
        **kwargs: 传递给 generate_text 的参数
    """
    prompt = f"""将以下问题扩展为 {n} 个不同的检索查询，覆盖同义词、不同表述角度。每行一个，控制在15-30字，只输出查询内容不要编号。

问题：{query}

扩展查询："""
    try:
        result = generate_text(prompt, max_tokens=128, **kwargs)
        queries = [q.strip() for q in result.split("\n") if q.strip()]
        return queries[:n]
    except:
        return [query]


def generate_query_decomposition(
    query: str, **kwargs
) -> list[str]:
    """将复杂问题分解为多个简单子问题

    Args:
        query: 原始查询
        **kwargs: 传递给 generate_text 的参数
    """
    prompt = f"""将以下复杂问题分解为多个简单的子问题（每个子问题可独立检索）。每行一个，控制在15-40字，只输出子问题不要解释。

问题：{query}

子问题："""
    try:
        result = generate_text(prompt, max_tokens=256, **kwargs)
        return [q.strip() for q in result.split("\n") if q.strip()]
    except:
        return [query]
