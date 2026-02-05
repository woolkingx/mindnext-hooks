"""shlex 解析器 - 簡單分詞，保留引號內容"""

import shlex
import re
from typing import Dict, Any, List


def parse(text: str) -> Dict[str, Any]:
    """解析命令

    Args:
        text: '/tags todo add "任務" #high #hooks'

    Returns:
        {
            'type': 'command' | 'text',
            'cmd': 'tags',
            'args': ['todo', 'add', '任務'],
            'tags': ['#high', '#hooks'],
            'flags': {'-f': True, '--name': 'value'},
            'raw': ['/tags', 'todo', 'add', '任務', '#high', '#hooks']
        }
    """
    text = text.strip()
    if not text:
        return {'type': 'empty', 'raw': []}

    try:
        tokens = shlex.split(text)
    except ValueError:
        # 引號不匹配等錯誤，fallback 到 split
        tokens = text.split()

    if not tokens:
        return {'type': 'empty', 'raw': []}

    # 分類 tokens
    args = []
    tags = []
    flags = {}

    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.startswith('#'):
            tags.append(t)
        elif t.startswith('--'):
            key = t[2:]
            if '=' in key:
                k, v = key.split('=', 1)
                flags[k] = v
            elif i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                flags[key] = tokens[i + 1]
                i += 1
            else:
                flags[key] = True
        elif t.startswith('-') and len(t) > 1 and not t[1].isdigit():
            # -f, -rf (不是 -1 這種數字)
            # 對於短選項，檢查是否有值
            for idx, c in enumerate(t[1:]):
                # 如果是最後一個字符，檢查下一個 token 是否為值
                if idx == len(t[1:]) - 1 and i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                    flags[c] = tokens[i + 1]
                    i += 1
                else:
                    flags[c] = True
        else:
            args.append(t)
        i += 1

    # 判斷類型
    if args and args[0].startswith('/'):
        cmd = args[0][1:]  # 去掉 /
        return {
            'type': 'command',
            'cmd': cmd,
            'sub': args[1] if len(args) > 1 else None,
            'action': args[2] if len(args) > 2 else None,
            'args': args[3:] if len(args) > 3 else [],
            'tags': tags,
            'flags': flags,
            'raw': tokens,
        }
    else:
        return {
            'type': 'text',
            'args': args,
            'tags': tags,
            'flags': flags,
            'raw': tokens,
        }


def tokenize(text: str) -> List[str]:
    """僅分詞"""
    try:
        return shlex.split(text)
    except ValueError:
        return text.split()
