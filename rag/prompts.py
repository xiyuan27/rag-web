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
import datetime
import json
import logging
import re
from collections import defaultdict

import json_repair

from api import settings
from api.db import LLMType
from rag.settings import TAG_FLD
from rag.utils import encoder, num_tokens_from_string


def chunks_format(reference):
    """格式化检索结果chunk数据

       处理目的：
       将检索系统返回的chunk数据标准化为统一格式，处理不同来源字段名不一致的问题

       处理步骤：
       1. 定义内部函数get_value()处理字段名映射
       2. 遍历reference中的chunks列表
       3. 为每个chunk提取标准化字段信息
       4. 返回格式化后的chunk列表

       输入：
       - reference (dict): 包含chunks列表和其他检索信息的字典

       输出：
       - list: 标准化格式的chunk字典列表，每个chunk包含：
         - id: chunk唯一标识
         - content: chunk内容
         - document_id: 所属文档ID
         - document_name: 文档名称
         - dataset_id: 数据集ID
         - image_id: 图片ID（如有）
         - positions: 位置信息
         - url: 链接地址
         - similarity: 综合相似度
         - vector_similarity: 向量相似度
         - term_similarity: 词项相似度
         - doc_type: 文档类型
       """
    def get_value(d, k1, k2):
        """获取字典中的值，优先使用k1键，不存在则使用k2键"""
        return d.get(k1, d.get(k2))

    return [
        {
            "id": get_value(chunk, "chunk_id", "id"),
            "content": get_value(chunk, "content", "content_with_weight"),
            "document_id": get_value(chunk, "doc_id", "document_id"),
            "document_name": get_value(chunk, "docnm_kwd", "document_name"),
            "dataset_id": get_value(chunk, "kb_id", "dataset_id"),
            "image_id": get_value(chunk, "image_id", "img_id"),
            "positions": get_value(chunk, "positions", "position_int"),
            "url": chunk.get("url"),
            "similarity": chunk.get("similarity"),
            "vector_similarity": chunk.get("vector_similarity"),
            "term_similarity": chunk.get("term_similarity"),
            "doc_type": chunk.get("doc_type_kwd"),
        }
        for chunk in reference.get("chunks", [])
    ]


def llm_id2llm_type(llm_id):
    """根据LLM ID获取对应的模型类型处理目的：
    通过LLM ID查询系统配置，确定该模型的具体类型（chat、embedding等）

    处理步骤：
    1. 使用TenantLLMService分割模型名称和工厂信息
    2. 遍历系统配置的LLM工厂列表
    3. 在每个工厂的LLM列表中查找匹配的模型
    4. 返回匹配模型的类型信息

    输入：
    - llm_id (str): LLM模型的唯一标识符

    输出：
    - str: 模型类型字符串，如'chat'、'embedding'等
    """
    from api.db.services.llm_service import TenantLLMService
    # 分割模型名称，获取基础ID
    llm_id, *_ = TenantLLMService.split_model_name_and_factory(llm_id)
    # 从系统配置获取LLM工厂信息
    llm_factories = settings.FACTORY_LLM_INFOS
    for llm_factory in llm_factories:
        for llm in llm_factory["llm"]:
            if llm_id == llm["llm_name"]:
                # 返回模型类型的最后一个字符（去除逗号）
                return llm["model_type"].strip(",")[-1]


def message_fit_in(msg, max_length=4000):
    """调整消息列表以适应token长度限制

        处理目的：
        确保对话消息在指定的token长度限制内，超出时进行智能截断

        处理步骤：
        1. 统计所有消息的token数量
        2. 如果总数小于限制，直接返回
        3. 如果超出限制，保留system消息和最后一条消息
        4. 如果仍超出，根据system和user消息比例进行截断
        5. 优先截断占比较大的消息内容

        输入：
        - msg (list): 消息列表，每个消息包含role和content
        - max_length (int): 最大token长度限制，默认4000

        输出：
        - tuple: (实际token数量, 调整后的消息列表)
        """
    def count():
        """计算消息列表的总token数"""
        nonlocal msg
        tks_cnts = []
        for m in msg:
            tks_cnts.append({"role": m["role"], "count": num_tokens_from_string(m["content"])})
        total = 0
        for m in tks_cnts:
            total += m["count"]
        return total

    # 第一步：检查当前token数量
    c = count()
    if c < max_length:
        return c, msg
    # 第二步：保留system消息和最后一条消息
    msg_ = [m for m in msg if m["role"] == "system"]
    if len(msg) > 1:
        msg_.append(msg[-1])
    msg = msg_
    c = count()
    if c < max_length:
        return c, msg

    # 第三步：根据消息长度比例进行截断
    ll = num_tokens_from_string(msg_[0]["content"])
    ll2 = num_tokens_from_string(msg_[-1]["content"])
    # 如果system消息占比超过80%，截断system消息
    if ll / (ll + ll2) > 0.8:
        m = msg_[0]["content"]
        m = encoder.decode(encoder.encode(m)[: max_length - ll2])
        msg[0]["content"] = m
        return max_length, msg
    # 否则截断最后一条消息
    m = msg_[-1]["content"]
    m = encoder.decode(encoder.encode(m)[: max_length - ll2])
    msg[-1]["content"] = m
    return max_length, msg


def kb_prompt(kbinfos, max_tokens):
    """构建知识库检索结果的提示词格式

        处理目的：
        将检索到的知识库chunk信息格式化为结构化的提示词，供LLM使用

        处理步骤：
        1. 提取所有chunk的内容并计算token使用量
        2. 根据max_tokens限制截断内容，避免超出模型限制
        3. 获取相关文档的元数据信息
        4. 按文档分组整理chunk内容
        5. 为每个chunk添加ID和URL信息
        6. 生成最终的结构化知识库提示词

        输入：
        - kbinfos (dict): 包含chunks列表的知识库检索结果
        - max_tokens (int): 最大token数量限制

        输出：
        - list: 格式化的知识库文档列表，每个文档包含：
          - 文档名称和元数据
          - 相关的chunk片段（带ID和URL）
        """
    from api.db.services.document_service import DocumentService
    # 第一步：提取chunk内容并控制token使用量
    knowledges = [ck["content_with_weight"] for ck in kbinfos["chunks"]]
    used_token_count = 0
    chunks_num = 0
    for i, c in enumerate(knowledges):
        used_token_count += num_tokens_from_string(c)
        chunks_num += 1
        # 当达到97%的token限制时停止添加
        if max_tokens * 0.97 < used_token_count:
            knowledges = knowledges[:i]
            logging.warning(f"Not all the retrieval into prompt: {i + 1}/{len(knowledges)}")
            break
    # 第二步：获取文档元数据
    docs = DocumentService.get_by_ids([ck["doc_id"] for ck in kbinfos["chunks"][:chunks_num]])
    docs = {d.id: d.meta_fields for d in docs}
    # 第三步：按文档分组chunk内容
    doc2chunks = defaultdict(lambda: {"chunks": [], "meta": []})
    for i, ck in enumerate(kbinfos["chunks"][:chunks_num]):
        # 构建chunk内容，包含ID和URL信息
        cnt = f"---\nID: {i}\n" + (f"URL: {ck['url']}\n" if "url" in ck else "")
        cnt += re.sub(r"( style=\"[^\"]+\"|</?(html|body|head|title)>|<!DOCTYPE html>)", " ", ck["content_with_weight"], flags=re.DOTALL|re.IGNORECASE)
        doc2chunks[ck["docnm_kwd"]]["chunks"].append(cnt)
        doc2chunks[ck["docnm_kwd"]]["meta"] = docs.get(ck["doc_id"], {})

    # 第四步：生成最终的结构化提示词
    knowledges = []
    for nm, cks_meta in doc2chunks.items():
        txt = f"\nDocument: {nm} \n"
        # 添加文档元数据
        for k, v in cks_meta["meta"].items():
            txt += f"{k}: {v}\n"
        txt += "Relevant fragments as following:\n"
        # 添加相关chunk片段
        for i, chunk in enumerate(cks_meta["chunks"], 1):
            txt += f"{chunk}\n"
        knowledges.append(txt)
    return knowledges


def citation_prompt():
    """生成引用格式规范的提示词

        处理目的：
        为LLM提供标准的引用格式规范和示例，确保生成的回答包含正确的文档引用

        处理步骤：
        1. 定义引用格式规范（[ID:i]格式）
        2. 提供引用规则和限制条件
        3. 给出完整的引用示例
        4. 明确禁止的格式和错误处理

        输入：
        - 无

        输出：
        - str: 包含引用规范和示例的完整提示词
        """
    print("USE PROMPT->citation_prompt", flush=True)
    return """

# Citation requirements:

- Use a uniform citation format such as [ID:i] [ID:j], where "i" and "j" are document IDs enclosed in square brackets. Separate multiple IDs with spaces (e.g., [ID:0] [ID:1]).
- Citation markers must be placed at the end of a sentence, separated by a space from the final punctuation (e.g., period, question mark). A maximum of 4 citations are allowed per sentence.
- DO NOT insert CITATION in the answer if the content is not from retrieved chunks.
- DO NOT use standalone Document IDs (e.g., '#ID#').
- Citations ALWAYS in the "[ID:i]" format.
- STRICTLY prohibit the use of strikethrough symbols (e.g., ~~) or any other non-standard formatting syntax.
- Any failure to adhere to the above rules, including but not limited to incorrect formatting, use of prohibited styles, or unsupported citations, will be considered an error, and no citation will be added for that sentence.

--- Example START ---
<SYSTEM>: Here is the knowledge base:

Document: Elon Musk Breaks Silence on Crypto, Warns Against Dogecoin ...
URL: https://blockworks.co/news/elon-musk-crypto-dogecoin
ID: 0
The Tesla co-founder advised against going all-in on dogecoin, but Elon Musk said it’s still his favorite crypto...

Document: Elon Musk's Dogecoin tweet sparks social media frenzy
ID: 1
Musk said he is 'willing to serve' D.O.G.E. – shorthand for Dogecoin.

Document: Causal effect of Elon Musk tweets on Dogecoin price
ID: 2
If you think of Dogecoin — the cryptocurrency based on a meme — you can’t help but also think of Elon Musk...

Document: Elon Musk's Tweet Ignites Dogecoin's Future In Public Services
ID: 3
The market is heating up after Elon Musk's announcement about Dogecoin. Is this a new era for crypto?...

      The above is the knowledge base.

<USER>: What's the Elon's view on dogecoin?

<ASSISTANT>: Musk has consistently expressed his fondness for Dogecoin, often citing its humor and the inclusion of dogs in its branding. He has referred to it as his favorite cryptocurrency [ID:0] [ID:1].
Recently, Musk has hinted at potential future roles for Dogecoin. His tweets have sparked speculation about Dogecoin's potential integration into public services [ID:3].
Overall, while Musk enjoys Dogecoin and often promotes it, he also warns against over-investing in it, reflecting both his personal amusement and caution regarding its speculative nature.

--- Example END ---

"""


def keyword_extraction(chat_mdl, content, topn=3):
    """从文本内容中提取关键词

       处理目的：
       使用LLM从给定文本中提取最重要的关键词/短语，用于内容分析和索引

       处理步骤：
       1. 构建关键词提取的提示词模板
       2. 设置提取数量和语言要求
       3. 调用LLM进行关键词提取
       4. 清理和验证LLM输出结果
       5. 返回提取的关键词字符串

       输入：
       - chat_mdl: LLM聊天模型实例
       - content (str): 需要提取关键词的文本内容
       - topn (int): 需要提取的关键词数量，默认3个

       输出：
       - str: 逗号分隔的关键词字符串，提取失败时返回空字符串
       """
    prompt = f"""
Role: You are a text analyzer.
Task: Extract the most important keywords/phrases of a given piece of text content.
Requirements:
  - Summarize the text content, and give the top {topn} important keywords/phrases.
  - The keywords MUST be in the same language as the given piece of text content.
  - The keywords are delimited by ENGLISH COMMA.
  - Output keywords ONLY.

### Text Content
{content}

"""
    # 准备消息并适配模型长度限制
    msg = [{"role": "system", "content": prompt}, {"role": "user", "content": "Output: "}]
    _, msg = message_fit_in(msg, chat_mdl.max_length)
    # 调用LLM进行关键词提取
    kwd = chat_mdl.chat(prompt, msg[1:], {"temperature": 0.2})
    if isinstance(kwd, tuple):
        kwd = kwd[0]

    # 清理输出结果
    kwd = re.sub(r"^.*</think>", "", kwd, flags=re.DOTALL)
    if kwd.find("**ERROR**") >= 0:
        return ""
    return kwd


def question_proposal(chat_mdl, content, topn=3):
    """基于文本内容生成相关问题

        处理目的：
        分析文本内容并生成相关的问题，用于问答系统的问题推荐或内容理解验证

        处理步骤：
        1. 构建问题生成的提示词模板
        2. 设置生成数量和质量要求
        3. 调用LLM生成相关问题
        4. 清理和验证LLM输出结果
        5. 返回生成的问题列表

        输入：
        - chat_mdl: LLM聊天模型实例
        - content (str): 需要生成问题的文本内容
        - topn (int): 需要生成的问题数量，默认3个

        输出：
        - str: 换行分隔的问题字符串，生成失败时返回空字符串
        """

    # 构建提示词模板
    prompt = f"""
Role: You are a text analyzer.
Task: Propose {topn} questions about a given piece of text content.
Requirements:
  - Understand and summarize the text content, and propose the top {topn} important questions.
  - The questions SHOULD NOT have overlapping meanings.
  - The questions SHOULD cover the main content of the text as much as possible.
  - The questions MUST be in the same language as the given piece of text content.
  - One question per line.
  - Output questions ONLY.

### Text Content
{content}

"""
    # 准备消息并适配模型长度限制
    msg = [{"role": "system", "content": prompt}, {"role": "user", "content": "Output: "}]
    _, msg = message_fit_in(msg, chat_mdl.max_length)
    # 调用LLM生成问题
    kwd = chat_mdl.chat(prompt, msg[1:], {"temperature": 0.2})
    if isinstance(kwd, tuple):
        kwd = kwd[0]

    # 清理输出结果
    kwd = re.sub(r"^.*</think>", "", kwd, flags=re.DOTALL)
    if kwd.find("**ERROR**") >= 0:
        return ""
    return kwd


def full_question(tenant_id, llm_id, messages, language=None):
    """基于对话历史生成完整问题

        处理目的：
        分析对话历史，将用户的不完整问题扩展为完整、独立的问题，处理上下文依赖

        处理步骤：
        1. 根据LLM类型选择合适的模型
        2. 构建对话历史上下文
        3. 生成包含时间处理规则的提示词
        4. 调用LLM生成完整问题
        5. 清理和返回结果

        输入：
        - tenant_id (str): 租户ID
        - llm_id (str): LLM模型ID
        - messages (list): 对话消息历史列表
        - language (str, optional): 指定输出语言

        输出：
        - str: 完整的问题字符串，处理失败时返回原始问题
        """
    from api.db.services.llm_service import LLMBundle

    # 根据模型类型选择合适的LLM bundle
    if llm_id2llm_type(llm_id) == "image2text":
        chat_mdl = LLMBundle(tenant_id, LLMType.IMAGE2TEXT, llm_id)
    else:
        chat_mdl = LLMBundle(tenant_id, LLMType.CHAT, llm_id)

    # 构建对话历史
    conv = []
    for m in messages:
        if m["role"] not in ["user", "assistant"]:
            continue
        conv.append("{}: {}".format(m["role"].upper(), m["content"]))
    conv = "\n".join(conv)

    # 准备时间相关的上下文信息
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    # 构建提示词模板
    prompt = f"""
Role: A helpful assistant

Task and steps:
    1. Generate a full user question that would follow the conversation.
    2. If the user's question involves relative date, you need to convert it into absolute date based on the current date, which is {today}. For example: 'yesterday' would be converted to {yesterday}.

Requirements & Restrictions:
  - If the user's latest question is already complete, don't do anything, just return the original question.
  - DON'T generate anything except a refined question."""

    # 添加语言要求
    if language:
        prompt += f"""
  - Text generated MUST be in {language}."""
    else:
        prompt += """
  - Text generated MUST be in the same language as the original user's question.
"""
    # 添加示例和实际数据
    prompt += f"""

######################
-Examples-
######################

# Example 1
## Conversation
USER: What is the name of Donald Trump's father?
ASSISTANT:  Fred Trump.
USER: And his mother?
###############
Output: What's the name of Donald Trump's mother?

------------
# Example 2
## Conversation
USER: What is the name of Donald Trump's father?
ASSISTANT:  Fred Trump.
USER: And his mother?
ASSISTANT:  Mary Trump.
User: What's her full name?
###############
Output: What's the full name of Donald Trump's mother Mary Trump?

------------
# Example 3
## Conversation
USER: What's the weather today in London?
ASSISTANT:  Cloudy.
USER: What's about tomorrow in Rochester?
###############
Output: What's the weather in Rochester on {tomorrow}?

######################
# Real Data
## Conversation
{conv}
###############
    """
    # 调用LLM生成完整问题
    ans = chat_mdl.chat(prompt, [{"role": "user", "content": "Output: "}], {"temperature": 0.2})
    ans = re.sub(r"^.*</think>", "", ans, flags=re.DOTALL)
    return ans if ans.find("**ERROR**") < 0 else messages[-1]["content"]


def cross_languages(tenant_id, llm_id, query, languages=[]):
    """跨语言翻译功能

        处理目的：
        将查询文本翻译成多种目标语言，支持批量翻译并保持格式

        处理步骤：
        1. 根据LLM类型选择合适的模型
        2. 构建多语言翻译的系统提示词
        3. 格式化用户输入和目标语言列表
        4. 调用LLM进行翻译
        5. 解析和格式化翻译结果

        输入：
        - tenant_id (str): 租户ID
        - llm_id (str): LLM模型ID
        - query (str): 需要翻译的原始文本
        - languages (list): 目标语言列表

        输出：
        - str: 换行分隔的多语言翻译结果，翻译失败时返回原始查询
        """
    from api.db.services.llm_service import LLMBundle

    # 选择合适的LLM模型
    if llm_id and llm_id2llm_type(llm_id) == "image2text":
        chat_mdl = LLMBundle(tenant_id, LLMType.IMAGE2TEXT, llm_id)
    else:
        chat_mdl = LLMBundle(tenant_id, LLMType.CHAT, llm_id)

    # 构建翻译系统提示词
    sys_prompt = """
Act as a streamlined multilingual translator. Strictly output translations separated by ### without any explanations or formatting. Follow these rules:

1. Accept batch translation requests in format:
[source text]
=== 
[target languages separated by commas]

2. Always maintain:
- Original formatting (tables/lists/spacing)
- Technical terminology accuracy
- Cultural context appropriateness

3. Output format:
[language1 translation] 
### 
[language1 translation]

**Examples:**
Input:
Hello World! Let's discuss AI safety.
===
Chinese, French, Japanese

Output:
你好世界！让我们讨论人工智能安全问题。
###
Bonjour le monde ! Parlons de la sécurité de l'IA.
###
こんにちは世界！AIの安全性について話し合いましょう。
"""
    user_prompt = f"""
Input:
{query}
===
{", ".join(languages)}

Output:
"""
    # 调用LLM进行翻译
    ans = chat_mdl.chat(sys_prompt, [{"role": "user", "content": user_prompt}], {"temperature": 0.2})
    ans = re.sub(r"^.*</think>", "", ans, flags=re.DOTALL)

    # 处理翻译失败的情况
    if ans.find("**ERROR**") >= 0:
        return query

    # 格式化翻译结果
    return "\n".join([a for a in re.sub(r"(^Output:|\n+)", "", ans, flags=re.DOTALL).split("===") if a.strip()])


def content_tagging(chat_mdl, content, all_tags, examples, topn=3):
    """为文本内容添加标签

        处理目的：
        基于预定义标签集合和示例，为文本内容自动分配最相关的标签和相关性评分

        处理步骤：
        1. 构建包含标签集合和示例的提示词
        2. 设置标签数量和评分要求
        3. 调用LLM进行标签分配
        4. 解析JSON格式的输出结果
        5. 处理解析错误并标准化结果

        输入：
        - chat_mdl: LLM聊天模型实例
        - content (str): 需要标记的文本内容
        - all_tags (list): 可用的标签集合
        - examples (list): 标签分配的示例列表
        - topn (int): 需要分配的标签数量，默认3个

        输出：
        - dict: 标签名称到相关性评分的映射字典，评分范围1-10

        异常：
        - Exception: JSON解析失败时抛出异常
        """
    # 构建提示词模板
    prompt = f"""
Role: You are a text analyzer.

Task: Add tags (labels) to a given piece of text content based on the examples and the entire tag set.

Steps:
  - Review the tag/label set.
  - Review examples which all consist of both text content and assigned tags with relevance score in JSON format.
  - Summarize the text content, and tag it with the top {topn} most relevant tags from the set of tags/labels and the corresponding relevance score.

Requirements:
  - The tags MUST be from the tag set.
  - The output MUST be in JSON format only, the key is tag and the value is its relevance score.
  - The relevance score must range from 1 to 10.
  - Output keywords ONLY.

# TAG SET
{", ".join(all_tags)}

"""
    # 添加示例到提示词
    for i, ex in enumerate(examples):
        prompt += """
# Examples {}
### Text Content
{}

Output:
{}

        """.format(i, ex["content"], json.dumps(ex[TAG_FLD], indent=2, ensure_ascii=False))

    # 添加实际数据部分
    prompt += f"""
# Real Data
### Text Content
{content}

"""
    # 准备消息并适配模型长度限制
    msg = [{"role": "system", "content": prompt}, {"role": "user", "content": "Output: "}]
    _, msg = message_fit_in(msg, chat_mdl.max_length)
    # 调用LLM进行标签分配
    kwd = chat_mdl.chat(prompt, msg[1:], {"temperature": 0.5})
    if isinstance(kwd, tuple):
        kwd = kwd[0]
    # 清理输出结果
    kwd = re.sub(r"^.*</think>", "", kwd, flags=re.DOTALL)
    if kwd.find("**ERROR**") >= 0:
        raise Exception(kwd)

    # 解析JSON输出
    try:
        obj = json_repair.loads(kwd)
    except json_repair.JSONDecodeError:
        try:
            result = kwd.replace(prompt[:-1], "").replace("user", "").replace("model", "").strip()
            result = "{" + result.split("{")[1].split("}")[0] + "}"
            obj = json_repair.loads(result)
        except Exception as e:
            logging.exception(f"JSON parsing error: {result} -> {e}")
            raise e
    # 标准化结果格式
    res = {}
    for k, v in obj.items():
        try:
            res[str(k)] = int(v)
        except Exception:
            pass
    return res


def vision_llm_describe_prompt(page=None) -> str:
    """生成视觉LLM图像描述的提示词

        处理目的：
        为视觉LLM提供标准化的图像转文本提示词，用于PDF页面图像的内容转录

        处理步骤：
        1. 定义基础的转录指令和规则
        2. 设置Markdown格式要求
        3. 添加页面标识符（如果提供）
        4. 定义失败处理机制

        输入：
        - page (int, optional): 页面编号，用于添加页面分隔符

        输出：
        - str: 完整的视觉LLM提示词，包含转录规则和格式要求
        """

    prompt_en = """
INSTRUCTION:
Transcribe the content from the provided PDF page image into clean Markdown format.
- Only output the content transcribed from the image.
- Do NOT output this instruction or any other explanation.
- If the content is missing or you do not understand the input, return an empty string.

RULES:
1. Do NOT generate examples, demonstrations, or templates.
2. Do NOT output any extra text such as 'Example', 'Example Output', or similar.
3. Do NOT generate any tables, headings, or content that is not explicitly present in the image.
4. Transcribe content word-for-word. Do NOT modify, translate, or omit any content.
5. Do NOT explain Markdown or mention that you are using Markdown.
6. Do NOT wrap the output in ```markdown or ``` blocks.
7. Only apply Markdown structure to headings, paragraphs, lists, and tables, strictly based on the layout of the image. Do NOT create tables unless an actual table exists in the image.
8. Preserve the original language, information, and order exactly as shown in the image.
"""

    # 如果提供页面编号，添加页面分隔符
    if page is not None:
        prompt_en += f"\nAt the end of the transcription, add the page divider: `--- Page {page} ---`."

    # 添加失败处理说明
    prompt_en += """
FAILURE HANDLING:
- If you do not detect valid content in the image, return an empty string.
"""
    return prompt_en


def vision_llm_figure_describe_prompt() -> str:
    """生成视觉LLM图表描述的提示词
        处理目的：
        为视觉LLM提供专门的图表和数据可视化分析提示词，用于提取图表中的结构化信息

        处理步骤：
        1. 定义图表分析的专家角色
        2. 列出具体的分析任务要求
        3. 设置结构化的输出格式
        4. 强调准确性和完整性要求

        输入：
        - 无

        输出：
        - str: 专门用于图表分析的视觉LLM提示词
        """
    prompt = """
You are an expert visual data analyst. Analyze the image and provide a comprehensive description of its content. Focus on identifying the type of visual data representation (e.g., bar chart, pie chart, line graph, table, flowchart), its structure, and any text captions or labels included in the image.

Tasks:
1. Describe the overall structure of the visual representation. Specify if it is a chart, graph, table, or diagram.
2. Identify and extract any axes, legends, titles, or labels present in the image. Provide the exact text where available.
3. Extract the data points from the visual elements (e.g., bar heights, line graph coordinates, pie chart segments, table rows and columns).
4. Analyze and explain any trends, comparisons, or patterns shown in the data.
5. Capture any annotations, captions, or footnotes, and explain their relevance to the image.
6. Only include details that are explicitly present in the image. If an element (e.g., axis, legend, or caption) does not exist or is not visible, do not mention it.

Output format (include only sections relevant to the image content):
- Visual Type: [Type]
- Title: [Title text, if available]
- Axes / Legends / Labels: [Details, if available]
- Data Points: [Extracted data]
- Trends / Insights: [Analysis and interpretation]
- Captions / Annotations: [Text and relevance, if available]

Ensure high accuracy, clarity, and completeness in your analysis, and include only the information present in the image. Avoid unnecessary statements about missing elements.
"""
    return prompt
