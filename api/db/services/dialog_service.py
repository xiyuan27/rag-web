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
import binascii
import logging
import re
import time
from copy import deepcopy
from datetime import datetime
from functools import partial
from timeit import default_timer as timer

from langfuse import Langfuse

from agentic_reasoning import DeepResearcher
from api import settings
from api.db import LLMType, ParserType, StatusEnum
from api.db.db_models import DB, Dialog
from api.db.services.common_service import CommonService
from api.db.services.knowledgebase_service import KnowledgebaseService
from api.db.services.langfuse_service import TenantLangfuseService
from api.db.services.llm_service import LLMBundle, TenantLLMService
from api.utils import current_timestamp, datetime_format
from rag.app.resume import forbidden_select_fields4resume
from rag.app.tag import label_question
from rag.nlp.search import index_name
from rag.prompts import chunks_format, citation_prompt, cross_languages, full_question, kb_prompt, keyword_extraction, \
    llm_id2llm_type, message_fit_in
from rag.utils import num_tokens_from_string, rmSpace
from rag.utils.tavily_conn import Tavily


class DialogService(CommonService):
    model = Dialog

    @classmethod
    def save(cls, **kwargs):
        """Save a new record to database.

        This method creates a new record in the database with the provided field values,
        forcing an insert operation rather than an update.

        Args:
            **kwargs: Record field values as keyword arguments.

        Returns:
            Model instance: The created record object.
        """
        sample_obj = cls.model(**kwargs).save(force_insert=True)
        return sample_obj

    @classmethod
    def update_many_by_id(cls, data_list):
        """Update multiple records by their IDs.

        This method updates multiple records in the database, identified by their IDs.
        It automatically updates the update_time and update_date fields for each record.

        Args:
            data_list (list): List of dictionaries containing record data to update.
                             Each dictionary must include an 'id' field.
        """
        with DB.atomic():
            for data in data_list:
                data["update_time"] = current_timestamp()
                data["update_date"] = datetime_format(datetime.now())
                cls.model.update(data).where(cls.model.id == data["id"]).execute()

    @classmethod
    @DB.connection_context()
    def get_list(cls, tenant_id, page_number, items_per_page, orderby, desc, id, name):
        chats = cls.model.select()
        if id:
            chats = chats.where(cls.model.id == id)
        if name:
            chats = chats.where(cls.model.name == name)
        chats = chats.where((cls.model.tenant_id == tenant_id) & (cls.model.status == StatusEnum.VALID.value))
        if desc:
            chats = chats.order_by(cls.model.getter_by(orderby).desc())
        else:
            chats = chats.order_by(cls.model.getter_by(orderby).asc())

        chats = chats.paginate(page_number, items_per_page)

        return list(chats.dicts())


def chat_solo(dialog, messages, stream=True):
    """
       纯纯聊天模式（不使用知识库检索）
    """
    print("纯纯聊天模式（不使用知识库检索）")
    if llm_id2llm_type(dialog.llm_id) == "image2text":
        chat_mdl = LLMBundle(dialog.tenant_id, LLMType.IMAGE2TEXT, dialog.llm_id)
    else:
        chat_mdl = LLMBundle(dialog.tenant_id, LLMType.CHAT, dialog.llm_id)

    prompt_config = dialog.prompt_config
    tts_mdl = None
    if prompt_config.get("tts"):
        tts_mdl = LLMBundle(dialog.tenant_id, LLMType.TTS)
    msg = [{"role": m["role"], "content": re.sub(r"##\d+\$\$", "", m["content"])} for m in messages if
           m["role"] != "system"]
    if stream:
        last_ans = ""
        delta_ans = ""
        print("chat_solo--调用大模型，流式逐步生成答案")
        for ans in chat_mdl.chat_streamly(prompt_config.get("system", ""), msg, dialog.llm_setting):
            answer = ans
            delta_ans = ans[len(last_ans):]
            if num_tokens_from_string(delta_ans) < 16:
                continue
            last_ans = answer
            yield {"answer": answer, "reference": {}, "audio_binary": tts(tts_mdl, delta_ans), "prompt": "",
                   "created_at": time.time()}
            delta_ans = ""
        if delta_ans:
            yield {"answer": answer, "reference": {}, "audio_binary": tts(tts_mdl, delta_ans), "prompt": "",
                   "created_at": time.time()}
    else:
        answer = chat_mdl.chat(prompt_config.get("system", ""), msg, dialog.llm_setting)
        user_content = msg[-1].get("content", "[content not available]")
        logging.debug("User: {}|Assistant: {}".format(user_content, answer))
        yield {"answer": answer, "reference": {}, "audio_binary": tts(tts_mdl, answer), "prompt": "",
               "created_at": time.time()}


def get_models(dialog):
    print("根据对话配置初始化所需的模型实例")
    embd_mdl, chat_mdl, rerank_mdl, tts_mdl = None, None, None, None
    kbs = KnowledgebaseService.get_by_ids(dialog.kb_ids)
    embedding_list = list(set([kb.embd_id for kb in kbs]))
    if len(embedding_list) > 1:
        raise Exception("**ERROR**: Knowledge bases use different embedding models.")

    if embedding_list:
        embd_mdl = LLMBundle(dialog.tenant_id, LLMType.EMBEDDING, embedding_list[0])
        if not embd_mdl:
            raise LookupError("Embedding model(%s) not found" % embedding_list[0])

    if llm_id2llm_type(dialog.llm_id) == "image2text":
        chat_mdl = LLMBundle(dialog.tenant_id, LLMType.IMAGE2TEXT, dialog.llm_id)
    else:
        chat_mdl = LLMBundle(dialog.tenant_id, LLMType.CHAT, dialog.llm_id)

    if dialog.rerank_id:
        rerank_mdl = LLMBundle(dialog.tenant_id, LLMType.RERANK, dialog.rerank_id)

    if dialog.prompt_config.get("tts"):
        tts_mdl = LLMBundle(dialog.tenant_id, LLMType.TTS)
    return kbs, embd_mdl, rerank_mdl, chat_mdl, tts_mdl


BAD_CITATION_PATTERNS = [
    re.compile(r"\(\s*ID\s*[: ]*\s*(\d+)\s*\)"),  # (ID: 12)
    re.compile(r"\[\s*ID\s*[: ]*\s*(\d+)\s*\]"),  # [ID: 12]
    re.compile(r"【\s*ID\s*[: ]*\s*(\d+)\s*】"),  # 【ID: 12】
    re.compile(r"ref\s*(\d+)", flags=re.IGNORECASE),  # ref12、REF 12
]


def repair_bad_citation_formats(answer: str, kbinfos: dict, idx: set):
    max_index = len(kbinfos["chunks"])

    def safe_add(i):
        if 0 <= i < max_index:
            idx.add(i)
            return True
        return False

    def find_and_replace(pattern, group_index=1, repl=lambda i: f"ID:{i}", flags=0):
        nonlocal answer

        def replacement(match):
            try:
                i = int(match.group(group_index))
                if safe_add(i):
                    return f"[{repl(i)}]"
            except Exception:
                pass
            return match.group(0)

        answer = re.sub(pattern, replacement, answer, flags=flags)

    for pattern in BAD_CITATION_PATTERNS:
        find_and_replace(pattern)

    return answer, idx


def chat(dialog, messages, stream=True, **kwargs):
    """
       实现完整的RAG对话流程
       Args:
           dialog: 智能助手配置信息
           messages: 消息历史列表
           stream: 是否流式输出
           **kwargs: 其他参数
       """
    logging.info("=" * 80)
    logging.info(" RAG对话流程开始")
    logging.info("=" * 80)

    logging.info("\n [阶段1] 开始 - 初始化和验证")
    assert messages[-1]["role"] == "user", "The last content of this conversation is not from user."
    logging.info(f" 验证通过 - 最后一条消息来自用户: {messages[-1]['content'][:50]}...")

    # 如果没有知识库且没有Tavily API密钥，则使用简单对话模式
    if not dialog.kb_ids and not dialog.prompt_config.get("tavily_api_key"):
        logging.info(" 使用简单对话模式（因为无知识库，且无联网搜索-tavily_api_key为空.）")
        for ans in chat_solo(dialog, messages, stream):
            yield ans
        return
    logging.info(" [阶段1] 完成 - 初始化和验证")

    chat_start_ts = timer()  # 对话开始时间

    # ===== 阶段2: 模型配置获取 =====
    logging.info("[阶段2] 开始 - 模型配置获取")
    # 根据LLM类型获取模型配置(图片解读模型/聊天模型)
    if llm_id2llm_type(dialog.llm_id) == "image2text":
        llm_model_config = TenantLLMService.get_model_config(dialog.tenant_id, LLMType.IMAGE2TEXT, dialog.llm_id)
        logging.info(f"🖼使用图像转文本模型: {dialog.llm_id}")
    else:
        llm_model_config = TenantLLMService.get_model_config(dialog.tenant_id, LLMType.CHAT, dialog.llm_id)
        logging.info(f"使用聊天模型: {dialog.llm_id}")

    max_tokens = llm_model_config.get("max_tokens", 8192)  # 获取模型最大token数限制，默认8192
    logging.info(f" 最大token限制: {max_tokens}")
    logging.info("[阶段2] 完成 - 模型配置获取")


    check_llm_ts = timer()  # llm开始时间

    # ===== 阶段3: Langfuse监控初始化 =====
    logging.info("[阶段3] 开始 - Langfuse监控初始化")
    # 初始化Langfuse追踪器（用于监控和分析）
    langfuse_tracer = None
    # 从数据库查询Langfuse密钥, 我们目前tenant_langfuse表无数据，所以langfuse_keys为空。
    langfuse_keys = TenantLangfuseService.filter_by_tenant(tenant_id=dialog.tenant_id)
    if langfuse_keys:
        print("Langfuse keys found")
        langfuse = Langfuse(public_key=langfuse_keys.public_key, secret_key=langfuse_keys.secret_key,
                            host=langfuse_keys.host)
        if langfuse.auth_check():
            langfuse_tracer = langfuse
            langfuse.trace = langfuse_tracer.trace(name=f"{dialog.name}-{llm_model_config['llm_name']}")

    check_langfuse_tracer_ts = timer()

    # ===== 阶段4: 模型绑定 =====
    logging.info(" [阶段4] 开始 - 模型绑定")
    # 根据智能助理（dialog）配置，获取模型实例
    # - kbs: 知识库对象列表，embd_mdl: 嵌入模型， rerank_mdl: 重排序模型，chat_mdl: 聊天模型，tts_mdl: 语音合成模型
    kbs, embd_mdl, rerank_mdl, chat_mdl, tts_mdl = get_models(dialog)
    # 获取工具调用会话和工具列表
    toolcall_session, tools = kwargs.get("toolcall_session"), kwargs.get("tools")
    if toolcall_session and tools:
        # 如果有工具，则绑定到聊天模型
        logging.info(f"🔧 绑定工具数量: {len(tools)}")
        chat_mdl.bind_tools(toolcall_session, tools)
    bind_models_ts = timer()

    # ===== 阶段5: 问题预处理 =====
    logging.info(" [阶段5] 开始 - 问题预处理")
    # # 获取检索器实例(即召回系统)
    retriever = settings.retrievaler
    # 提取最近3条用户消息作为问题列表
    questions = [m["content"] for m in messages if m["role"] == "user"][-3:]
    logging.info(f"提取用户问题数量: {len(questions)}")
    logging.info(f"最新问题: {questions[-1][:100]}...")
    # 处理文档附件ID
    attachments = kwargs["doc_ids"].split(",") if "doc_ids" in kwargs else None
    if "doc_ids" in messages[-1]:
        attachments = messages[-1]["doc_ids"]

    # 获取提示配置和字段映射
    prompt_config = dialog.prompt_config
    field_map = KnowledgebaseService.get_field_map(dialog.kb_ids)
    # 尝试使用SQL检索（如果字段映射可用）
    if field_map:
        logging.debug("Use SQL to retrieval:{}".format(questions[-1]))  # 使用SQL查询获取答案
        ans = use_sql(questions[-1], field_map, dialog.tenant_id, chat_mdl, prompt_config.get("quote", True))
        if ans:
            yield ans
            return

    # 检查必需参数是否存在
    for p in prompt_config["parameters"]:
        if p["key"] == "knowledge":
            continue
        # 检查非optional参数是否齐备
        if p["key"] not in kwargs and not p["optional"]:
            raise KeyError("Miss parameter: " + p["key"])
        # 如果可选参数(optional)缺失，用空格替换占位符
        if p["key"] not in kwargs:
            prompt_config["system"] = prompt_config["system"].replace("{%s}" % p["key"], " ")

    # ===== 阶段6: 问题精化 =====
    logging.info(" [阶段6] 开始 - 问题精化")
    #  处理多轮对话的问题精化
    if len(questions) > 1 and prompt_config.get("refine_multiturn"):
        # 多轮对话模式：将历史对话上下文合并为一个完整、独立的问题
        # 例如：用户问"特朗普的父亲叫什么?" -> "Fred Trump" -> "他的母亲呢?" 会被精化为："特朗普的母亲叫什么名字?"
        questions = [full_question(dialog.tenant_id, dialog.llm_id, messages)]
    else:
        # 单轮对话模式：只使用用户的最新问题，忽略历史上下文
        questions = questions[-1:]

    # 跨语言查询扩展
    if prompt_config.get("cross_languages"):
        # 将问题翻译成多种语言以提升检索覆盖率
        # 例如：英文问题同时生成中文、日文版本进行检索, 这样可以检索到不同语言的相关文档
        questions = [cross_languages(dialog.tenant_id, dialog.llm_id, questions[0], prompt_config["cross_languages"])]

    # 关键词提取增强查询
    if prompt_config.get("keyword", False):
        # 从用户问题中提取关键词并追加到原问题后
        # 例如："如何使用Python进行数据分析?" + "Python, 数据分析, 机器学习", 这样可以提升向量检索的召回率
        questions[-1] += keyword_extraction(chat_mdl, questions[-1])

    logging.info(questions)
    refine_question_ts = timer()

    # ===== 阶段7: 知识检索 =====
    logging.info(" [阶段7] 开始 - 知识检索")
    # 初始化推理思考过程和知识库检索结果
    thought = ""  # 存储推理模式下的思考过程文本
    # 知识库检索结果的标准化格式
    # total:检索到的总文档数 chunks:文档片段列表，每个片段包含内容、向量、元数据等
    # doc_aggs:文档聚合信息，包含文档级别的统计和元数据
    kbinfos = {"total": 0, "chunks": [], "doc_aggs": []}
    # 检查知识检索配置：判断是否需要进行知识库检索
    if "knowledge" not in [p["key"] for p in prompt_config["parameters"]]:
        # 如果prompt配置中没有"knowledge"参数，说明这是纯聊天模式
        # 不需要检索外部知识，直接使用LLM的内置知识回答
        knowledges = []
    else:
        # 需要进行知识检索的模式,获取所有相关知识库的租户ID（去重处理）
        tenant_ids = list(set([kb.tenant_id for kb in kbs]))
        knowledges = []  # 初始化知识内容列表
        # 智能推理(reasoning)模式 vs 标准检索模式的分支处理
        if prompt_config.get("reasoning", False):
            # == = 智能推理模式 == =
            # 使用DeepResearcher进行多步骤推理和知识检索, 这种模式会进行更深入的分析，类似于AI研究助手
            reasoner = DeepResearcher(
                chat_mdl,  # 聊天模型，用于推理分析
                prompt_config,  # 提示配置
                # 创建检索函数的偏函数，预设所有检索参数
                #   retriever.retrieval 检索器的检索方法;  embd_mdl:嵌入模型; tenant_ids:租户ID列表;kb_ids:知识库ID列表
                #   similarity_threshold:相似度阈值（0.2较低，召回更多）; vector_similarity_weight:向量相似度权重
                partial(retriever.retrieval, embd_mdl=embd_mdl, tenant_ids=tenant_ids, kb_ids=dialog.kb_ids, page=1,
                        page_size=dialog.top_n, similarity_threshold=0.2, vector_similarity_weight=0.3),
            )
            # 执行推理思考循环
            for think in reasoner.thinking(kbinfos, " ".join(questions)):
                # 如果返回的是字符串，说明是最终的思考结果
                if isinstance(think, str):
                    thought = think  # 保存完整思考过程
                    knowledges = [t for t in think.split("\n") if t]  # 按行分割并过滤空行
                elif stream:
                    # 如果返回的是流式数据且开启了流式输出,实时向用户展示推理过程（如"正在分析..."）
                    yield think
        else:
            # === 标准检索模式 ===
            # 传统的向量检索 + 可选的多源检索增强
            # 1. 向量检索（核心检索）
            if embd_mdl:
                # 执行语义向量检索(向量召回)
                kbinfos = retriever.retrieval(
                    " ".join(questions),  # 合并后的查询文本
                    embd_mdl,  # 嵌入模型（将文本转为向量）
                    tenant_ids,  # 租户范围限制
                    dialog.kb_ids,  # 知识库范围限制
                    1,  # 分页：第1页
                    dialog.top_n,  # 返回片段数量（如50个片段）
                    dialog.similarity_threshold,  # 相似度阈值（如0.7，过滤不相关内容）
                    dialog.vector_similarity_weight,  # 向量vs关键词权重平衡（如0.7表示70%向量+30%关键词）
                    doc_ids=attachments,  # 如果用户上传了特定文档，优先检索这些文档
                    top=dialog.top_k,  # 重排序后保留的最终结果数（如10个）
                    aggs=False,  # 不进行聚合统计
                    rerank_mdl=rerank_mdl,  # 重排序模型（提升检索精度）
                    rank_feature=label_question(" ".join(questions), kbs),  # 问题分类特征，辅助排序
                )
            # 2. 网络搜索增强（可选）
            if prompt_config.get("tavily_api_key"):
                # 使用Tavily进行实时网络搜索，获取最新信息, 适用于需要最新数据的问题（如"今天的股价"、"最新新闻"等）
                tav = Tavily(prompt_config["tavily_api_key"])
                tav_res = tav.retrieve_chunks(" ".join(questions))  # 检索网络内容块
                # 将网络搜索结果合并到知识库结果中
                kbinfos["chunks"].extend(tav_res["chunks"])  # 添加内容片段
                kbinfos["doc_aggs"].extend(tav_res["doc_aggs"])  # 添加文档统计

            # 3. 知识图谱检索增强（可选）
            if prompt_config.get("use_kg"):
                # 使用知识图谱进行结构化知识检索, 知识图谱适合处理实体关系、概念层次等结构化问题
                ck = settings.kg_retrievaler.retrieval(
                    " ".join(questions),  # 查询文本
                    tenant_ids,  # 租户范围
                    dialog.kb_ids,  # 知识库范围
                    embd_mdl,  # 嵌入模型
                    LLMBundle(dialog.tenant_id, LLMType.CHAT))  # LLM模型束
                if ck["content_with_weight"]:
                    # 如果知识图谱检索到了加权内容，插入到结果最前面
                    # 知识图谱的结果通常更准确，所以优先级更高
                    kbinfos["chunks"].insert(0, ck)

            # 4. 生成最终的知识提示文本
            # 将检索到的所有知识片段格式化为LLM可理解的提示文本
            # 同时考虑token限制，避免超出模型的上下文长度
            knowledges = kb_prompt(kbinfos, max_tokens)

    # 记录调试信息：问题和对应的知识
    logging.debug("{}->{}".format(" ".join(questions), "\n->".join(knowledges)))

    # ===== 阶段8: 消息构建 =====
    logging.info(" [阶段8] 开始 - 消息构建")
    retrieval_ts = timer()
    # 如果没有检索到知识且配置了空响应
    if not knowledges and prompt_config.get("empty_response"):
        empty_res = prompt_config["empty_response"]
        # 返回空响应结果
        yield {"answer": empty_res, "reference": kbinfos, "prompt": "\n\n### Query:\n%s" % " ".join(questions),
               "audio_binary": tts(tts_mdl, empty_res)}
        return {"answer": prompt_config["empty_response"], "reference": kbinfos}

    # 将知识内容添加到kwargs中
    kwargs["knowledge"] = "\n------\n" + "\n\n------\n\n".join(knowledges)
    # 获取生成配置
    gen_conf = dialog.llm_setting
    # 构建消息列表，添加系统提示
    msg = [{"role": "system", "content": prompt_config["system"].format(**kwargs)}]
    # 初始化引用提示
    prompt4citation = ""
    # 如果有知识且需要引用
    if knowledges and (prompt_config.get("quote", True) and kwargs.get("quote", True)):
        prompt4citation = citation_prompt()
    # 添加历史消息，移除系统消息和引用标记
    msg.extend([{"role": m["role"], "content": re.sub(r"##\d+\$\$", "", m["content"])} for m in messages if
                m["role"] != "system"])
    # 确保消息在token限制内
    used_token_count, msg = message_fit_in(msg, int(max_tokens * 0.95))
    # 确保至少有系统消息和用户消息
    assert len(msg) >= 2, f"message_fit_in has bug: {msg}"
    # 获取最终的提示内容
    prompt = msg[0]["content"]

    # 调整生成配置中的最大token数
    if "max_tokens" in gen_conf:
        gen_conf["max_tokens"] = min(gen_conf["max_tokens"], max_tokens - used_token_count)

    # ===== 阶段9: 答案生成 =====
    logging.info(" [阶段9] 开始 - 答案生成")
    def decorate_answer(answer):
        """
            装饰答案，添加引用、统计信息等.
            这个函数实际上是一个**"后处理+报告生成器"**，主要做三件事：
            1. 装饰答案内容。（处理引用、修复引用格式）
            2. 生成性能报告。（计算各阶段耗时、构建报告文本 prompt += ...  注意这个prompt是给展示给用户的调试信息，不是给LLM的提示）
            3. 返回完整的调试信息
        """
        nonlocal embd_mdl, prompt_config, knowledges, kwargs, kbinfos, prompt, retrieval_ts, questions, langfuse_tracer
        # 初始化引用列表
        refs = []
        # 分离思考过程和答案
        ans = answer.split("</think>")
        think = ""
        if len(ans) == 2:
            think = ans[0] + "</think>"
            answer = ans[1]

        # 处理引用和参考文献
        if knowledges and (prompt_config.get("quote", True) and kwargs.get("quote", True)):
            idx = set([])
            # 如果没有现有引用，自动插入引用
            if embd_mdl and not re.search(r"\[ID:([0-9]+)\]", answer):
                answer, idx = retriever.insert_citations(
                    answer,
                    [ck["content_ltks"] for ck in kbinfos["chunks"]],  # 内容tokens
                    [ck["vector"] for ck in kbinfos["chunks"]],  # 向量
                    embd_mdl,  # 嵌入模型
                    tkweight=1 - dialog.vector_similarity_weight,  # token权重
                    vtweight=dialog.vector_similarity_weight,  # 向量权重
                )
            else:
                # 提取现有引用ID
                for match in re.finditer(r"\[ID:([0-9]+)\]", answer):
                    i = int(match.group(1))
                    if i < len(kbinfos["chunks"]):
                        idx.add(i)
            # 修复错误的引用格式
            answer, idx = repair_bad_citation_formats(answer, kbinfos, idx)
            # 获取被引用的文档ID
            idx = set([kbinfos["chunks"][int(i)]["doc_id"] for i in idx])
            # 筛选被引用的文档
            recall_docs = [d for d in kbinfos["doc_aggs"] if d["doc_id"] in idx]
            if not recall_docs:
                recall_docs = kbinfos["doc_aggs"]
            kbinfos["doc_aggs"] = recall_docs
            # 创建引用信息的深拷贝
            refs = deepcopy(kbinfos)
            # 移除向量信息以减少输出大小
            for c in refs["chunks"]:
                if c.get("vector"):
                    del c["vector"]
        # 检查API密钥相关错误
        if answer.lower().find("invalid key") >= 0 or answer.lower().find("invalid api") >= 0:
            answer += " Please set LLM API-Key in 'User Setting -> Model providers -> API-Key'"
        finish_chat_ts = timer()

        # 计算各阶段耗时（毫秒）
        total_time_cost = (finish_chat_ts - chat_start_ts) * 1000
        check_llm_time_cost = (check_llm_ts - chat_start_ts) * 1000
        check_langfuse_tracer_cost = (check_langfuse_tracer_ts - check_llm_ts) * 1000
        bind_embedding_time_cost = (bind_models_ts - check_langfuse_tracer_ts) * 1000
        refine_question_time_cost = (refine_question_ts - bind_models_ts) * 1000
        retrieval_time_cost = (retrieval_ts - refine_question_ts) * 1000
        generate_result_time_cost = (finish_chat_ts - retrieval_ts) * 1000
        # 计算生成的token数量
        tk_num = num_tokens_from_string(think + answer)
        # 构建完整的提示信息
        prompt += "\n\n### Query:\n%s" % " ".join(questions)
        prompt = (
            f"{prompt}\n\n"
            "## Time elapsed:\n"
            f"  - Total: {total_time_cost:.1f}ms\n"
            f"  - Check LLM: {check_llm_time_cost:.1f}ms\n"
            f"  - Check Langfuse tracer: {check_langfuse_tracer_cost:.1f}ms\n"
            f"  - Bind models: {bind_embedding_time_cost:.1f}ms\n"
            f"  - Query refinement(LLM): {refine_question_time_cost:.1f}ms\n"
            f"  - Retrieval: {retrieval_time_cost:.1f}ms\n"
            f"  - Generate answer: {generate_result_time_cost:.1f}ms\n\n"
            "## Token usage:\n"
            f"  - Generated tokens(approximately): {tk_num}\n"
            f"  - Token speed: {int(tk_num / (generate_result_time_cost / 1000.0))}/s"
        )
        # 准备Langfuse输出信息
        langfuse_output = "\n" + re.sub(r"^.*?(### Query:.*)", r"\1", prompt, flags=re.DOTALL)
        langfuse_output = {"time_elapsed:": re.sub(r"\n", "  \n", langfuse_output), "created_at": time.time()}

        # Add a condition check to call the end method only if langfuse_tracer exists
        # 结束Langfuse追踪（如果存在）
        if langfuse_tracer and "langfuse_generation" in locals():
            langfuse_generation.end(output=langfuse_output)
        # 返回最终结果
        return {"answer": think + answer, "reference": refs, "prompt": re.sub(r"\n", "  \n", prompt),
                "created_at": time.time()}

    # 开始Langfuse生成追踪
    if langfuse_tracer:
        langfuse_generation = langfuse_tracer.trace.generation(name="chat", model=llm_model_config["llm_name"],
                                                               input={"prompt": prompt,
                                                                      "prompt4citation": prompt4citation,
                                                                      "messages": msg})
    # 根据stream参数选择流式或非流式输出
    if stream:
        last_ans = ""
        answer = ""
        # 调用大模型，流式逐步生成答案
        print("chat 调用大模型，流式逐步生成答案")
        for ans in chat_mdl.chat_streamly(prompt + prompt4citation, msg[1:], gen_conf):
            if thought:
                # 移除思考标签后的内容
                ans = re.sub(r"^.*</think>", "", ans, flags=re.DOTALL)
            answer = ans
            # 计算增量答案
            delta_ans = ans[len(last_ans):]
            # 如果增量太小，跳过输出
            if num_tokens_from_string(delta_ans) < 16:
                continue
            last_ans = answer
            # 流式输出包含TTS音频
            yield {"answer": thought + answer, "reference": {}, "audio_binary": tts(tts_mdl, delta_ans)}
        # 输出最后的增量
        delta_ans = answer[len(last_ans):]
        if delta_ans:
            yield {"answer": thought + answer, "reference": {}, "audio_binary": tts(tts_mdl, delta_ans)}

        # 输出最终装饰后的答案
        yield decorate_answer(thought + answer)
    else:
        # 调用大模型，非流式输出
        print("调用大模型，非流式输出")
        answer = chat_mdl.chat(prompt + prompt4citation, msg[1:], gen_conf)
        # 记录用户和助手的对话
        user_content = msg[-1].get("content", "[content not available]")
        logging.debug("User: {}|Assistant: {}".format(user_content, answer))
        # 装饰答案并添加TTS音频
        res = decorate_answer(answer)
        res["audio_binary"] = tts(tts_mdl, answer)
        yield res


def use_sql(question, field_map, tenant_id, chat_mdl, quota=True):
    sys_prompt = "You are a Database Administrator. You need to check the fields of the following tables based on the user's list of questions and write the SQL corresponding to the last question."
    user_prompt = """
Table name: {};
Table of database fields are as follows:
{}

Question are as follows:
{}
Please write the SQL, only SQL, without any other explanations or text.
""".format(index_name(tenant_id), "\n".join([f"{k}: {v}" for k, v in field_map.items()]), question)
    tried_times = 0

    def get_table():
        nonlocal sys_prompt, user_prompt, question, tried_times
        sql = chat_mdl.chat(sys_prompt, [{"role": "user", "content": user_prompt}], {"temperature": 0.06})
        sql = re.sub(r"^.*</think>", "", sql, flags=re.DOTALL)
        logging.debug(f"{question} ==> {user_prompt} get SQL: {sql}")
        sql = re.sub(r"[\r\n]+", " ", sql.lower())
        sql = re.sub(r".*select ", "select ", sql.lower())
        sql = re.sub(r" +", " ", sql)
        sql = re.sub(r"([;；]|```).*", "", sql)
        if sql[: len("select ")] != "select ":
            return None, None
        if not re.search(r"((sum|avg|max|min)\(|group by )", sql.lower()):
            if sql[: len("select *")] != "select *":
                sql = "select doc_id,docnm_kwd," + sql[6:]
            else:
                flds = []
                for k in field_map.keys():
                    if k in forbidden_select_fields4resume:
                        continue
                    if len(flds) > 11:
                        break
                    flds.append(k)
                sql = "select doc_id,docnm_kwd," + ",".join(flds) + sql[8:]

        logging.debug(f"{question} get SQL(refined): {sql}")
        tried_times += 1
        return settings.retrievaler.sql_retrieval(sql, format="json"), sql

    tbl, sql = get_table()
    if tbl is None:
        return None
    if tbl.get("error") and tried_times <= 2:
        user_prompt = """
        Table name: {};
        Table of database fields are as follows:
        {}

        Question are as follows:
        {}
        Please write the SQL, only SQL, without any other explanations or text.


        The SQL error you provided last time is as follows:
        {}

        Error issued by database as follows:
        {}

        Please correct the error and write SQL again, only SQL, without any other explanations or text.
        """.format(index_name(tenant_id), "\n".join([f"{k}: {v}" for k, v in field_map.items()]), question, sql,
                   tbl["error"])
        tbl, sql = get_table()
        logging.debug("TRY it again: {}".format(sql))

    logging.debug("GET table: {}".format(tbl))
    if tbl.get("error") or len(tbl["rows"]) == 0:
        return None

    docid_idx = set([ii for ii, c in enumerate(tbl["columns"]) if c["name"] == "doc_id"])
    doc_name_idx = set([ii for ii, c in enumerate(tbl["columns"]) if c["name"] == "docnm_kwd"])
    column_idx = [ii for ii in range(len(tbl["columns"])) if ii not in (docid_idx | doc_name_idx)]

    # compose Markdown table
    columns = (
            "|" + "|".join(
        [re.sub(r"(/.*|（[^（）]+）)", "", field_map.get(tbl["columns"][i]["name"], tbl["columns"][i]["name"])) for i in
         column_idx]) + ("|Source|" if docid_idx and docid_idx else "|")
    )

    line = "|" + "|".join(["------" for _ in range(len(column_idx))]) + ("|------|" if docid_idx and docid_idx else "")

    rows = ["|" + "|".join([rmSpace(str(r[i])) for i in column_idx]).replace("None", " ") + "|" for r in tbl["rows"]]
    rows = [r for r in rows if re.sub(r"[ |]+", "", r)]
    if quota:
        rows = "\n".join([r + f" ##{ii}$$ |" for ii, r in enumerate(rows)])
    else:
        rows = "\n".join([r + f" ##{ii}$$ |" for ii, r in enumerate(rows)])
    rows = re.sub(r"T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+Z)?\|", "|", rows)

    if not docid_idx or not doc_name_idx:
        logging.warning("SQL missing field: " + sql)
        return {"answer": "\n".join([columns, line, rows]), "reference": {"chunks": [], "doc_aggs": []},
                "prompt": sys_prompt}

    docid_idx = list(docid_idx)[0]
    doc_name_idx = list(doc_name_idx)[0]
    doc_aggs = {}
    for r in tbl["rows"]:
        if r[docid_idx] not in doc_aggs:
            doc_aggs[r[docid_idx]] = {"doc_name": r[doc_name_idx], "count": 0}
        doc_aggs[r[docid_idx]]["count"] += 1
    return {
        "answer": "\n".join([columns, line, rows]),
        "reference": {
            "chunks": [{"doc_id": r[docid_idx], "docnm_kwd": r[doc_name_idx]} for r in tbl["rows"]],
            "doc_aggs": [{"doc_id": did, "doc_name": d["doc_name"], "count": d["count"]} for did, d in
                         doc_aggs.items()],
        },
        "prompt": sys_prompt,
    }


def tts(tts_mdl, text):
    if not tts_mdl or not text:
        return
    bin = b""
    for chunk in tts_mdl.tts(text):
        bin += chunk
    return binascii.hexlify(bin).decode("utf-8")


def ask(question, kb_ids, tenant_id):
    print("======asking...")
    kbs = KnowledgebaseService.get_by_ids(kb_ids)
    embedding_list = list(set([kb.embd_id for kb in kbs]))

    is_knowledge_graph = all([kb.parser_id == ParserType.KG for kb in kbs])
    retriever = settings.retrievaler if not is_knowledge_graph else settings.kg_retrievaler

    embd_mdl = LLMBundle(tenant_id, LLMType.EMBEDDING, embedding_list[0])
    chat_mdl = LLMBundle(tenant_id, LLMType.CHAT)
    max_tokens = chat_mdl.max_length
    tenant_ids = list(set([kb.tenant_id for kb in kbs]))
    kbinfos = retriever.retrieval(question, embd_mdl, tenant_ids, kb_ids, 1, 12, 0.1, 0.3, aggs=False,
                                  rank_feature=label_question(question, kbs))
    knowledges = kb_prompt(kbinfos, max_tokens)
    prompt = """
    Role: You're a smart assistant. Your name is Miss R.
    Task: Summarize the information from knowledge bases and answer user's question.
    Requirements and restriction:
      - DO NOT make things up, especially for numbers.
      - If the information from knowledge is irrelevant with user's question, JUST SAY: Sorry, no relevant information provided.
      - Answer with markdown format text.
      - Answer in language of user's question.
      - DO NOT make things up, especially for numbers.

    ### Information from knowledge bases
    %s

    The above is information from knowledge bases.

    """ % "\n".join(knowledges)
    msg = [{"role": "user", "content": question}]

    def decorate_answer(answer):
        nonlocal knowledges, kbinfos, prompt
        answer, idx = retriever.insert_citations(answer, [ck["content_ltks"] for ck in kbinfos["chunks"]],
                                                 [ck["vector"] for ck in kbinfos["chunks"]], embd_mdl, tkweight=0.7,
                                                 vtweight=0.3)
        idx = set([kbinfos["chunks"][int(i)]["doc_id"] for i in idx])
        recall_docs = [d for d in kbinfos["doc_aggs"] if d["doc_id"] in idx]
        if not recall_docs:
            recall_docs = kbinfos["doc_aggs"]
        kbinfos["doc_aggs"] = recall_docs
        refs = deepcopy(kbinfos)
        for c in refs["chunks"]:
            if c.get("vector"):
                del c["vector"]

        if answer.lower().find("invalid key") >= 0 or answer.lower().find("invalid api") >= 0:
            answer += " Please set LLM API-Key in 'User Setting -> Model Providers -> API-Key'"
        refs["chunks"] = chunks_format(refs)
        return {"answer": answer, "reference": refs}

    answer = ""
    print("ask 调用大模型，流式逐步生成答案")
    for ans in chat_mdl.chat_streamly(prompt, msg, {"temperature": 0.1}):
        answer = ans
        yield {"answer": answer, "reference": {}}
    yield decorate_answer(answer)
