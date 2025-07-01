#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import os
import re

import tiktoken

from api.utils.file_utils import get_project_base_directory


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        key = str(cls) + str(os.getpid())
        if key not in instances:
            instances[key] = cls(*args, **kw)
        return instances[key]

    return _singleton


def rmSpace(txt):
    txt = re.sub(r"([^a-z0-9.,\)>]) +([^ ])", r"\1\2", txt, flags=re.IGNORECASE)
    return re.sub(r"([^ ]) +([^a-z0-9.,\(<])", r"\1\2", txt, flags=re.IGNORECASE)


def findMaxDt(fnm):
    m = "1970-01-01 00:00:00"
    try:
        with open(fnm, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip("\n")
                if line == 'nan':
                    continue
                if line > m:
                    m = line
    except Exception:
        pass
    return m


def findMaxTm(fnm):
    m = 0
    try:
        with open(fnm, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip("\n")
                if line == 'nan':
                    continue
                if int(line) > m:
                    m = int(line)
    except Exception:
        pass
    return m


tiktoken_cache_dir = get_project_base_directory()
os.environ["TIKTOKEN_CACHE_DIR"] = tiktoken_cache_dir
# encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
# 初始化tiktoken编码器，用于计算token数量
encoder = tiktoken.get_encoding("cl100k_base")


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string.
    使用tiktoken编码器将文本转换为token并计算数量，用于控制LLM输入长度
    处理步骤：
    1. 使用cl100k_base编码器对字符串进行编码
    2. 返回编码后token列表的长度
    3. 异常情况下返回0
    输入：
    - string (str): 需要计算token数量的文本字符串
    输出：
    - int: 字符串对应的token数量，异常时返回0
    """
    try:
        return len(encoder.encode(string))
    except Exception:
        return 0


def truncate(string: str, max_len: int) -> str:
    """Returns truncated text if the length of text exceed max_len."""
    return encoder.decode(encoder.encode(string)[:max_len])

  
def clean_markdown_block(text):
    text = re.sub(r'^\s*```markdown\s*\n?', '', text)
    text = re.sub(r'\n?\s*```\s*$', '', text)
    return text.strip()

  
def get_float(v):
    if v is None:
        return float('-inf')
    try:
        return float(v)
    except Exception:
        return float('-inf')

