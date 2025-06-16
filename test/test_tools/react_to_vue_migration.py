"""
optimized_migration_script.py

全面优化的React + Ant Design Pro + Umi到Vue3 + Vite + TypeScript + ant-design-vue + Pinia迁移工具

主要改进：
1. 智能依赖解析和模块映射
2. 健壮的错误处理和重试机制
3. 专业的技术栈转换规则
4. 分阶段渐进式迁移
5. 智能提示词管理
6. 详细的日志和进度跟踪

使用方法:
python optimized_migration_script.py --src ./react-project --dest ./vue-project --phase all
"""

import os
import shutil
import json
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import networkx as nx
import tiktoken
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- 配置 ---
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

openai.api_key = OPENAI_API_KEY
MODEL = 'gpt-4'
MAX_TOKENS = 100000  # 更保守的token限制
CHUNK_SIZE = 80000  # 单个提示词的最大token数

# 初始化tokenizer
tokenizer = tiktoken.get_encoding('cl100k_base')


class MigrationPhase(Enum):
    INFRASTRUCTURE = "infrastructure"
    STORES = "stores"
    COMPONENTS = "components"
    LAYOUTS = "layouts"
    PAGES = "pages"
    ALL = "all"


@dataclass
class FileInfo:
    path: str
    relative_path: str
    content: str
    imports: Dict[str, List[str]]
    exports: List[str]
    file_type: str
    phase: MigrationPhase
    dependencies: List[str] = None
    dependents: List[str] = None


@dataclass
class MigrationResult:
    success: bool
    original_file: str
    new_file: str
    content: str = ""
    error: str = ""
    warnings: List[str] = None
    api_summary: Dict = None


# --- 技术栈映射配置 ---
TECH_STACK_MAPPING = {
    'ui_frameworks': {
        '@ant-design/pro-components': 'ant-design-vue',
        '@ant-design/pro-layout': '@ant-design-vue/pro-layout',
        '@ant-design/pro-table': 'ant-design-vue (需要自定义扩展)',
        '@ant-design/pro-form': 'ant-design-vue + @ant-design-vue/pro-form',
        '@ant-design/icons': '@ant-design/icons-vue',
        'antd': 'ant-design-vue'
    },
    'form_libraries': {
        'react-hook-form': 'vee-validate + @vee-validate/rules',
        '@hookform/resolvers': '@vee-validate/rules',
        'rc-form': 'ant-design-vue内置表单'
    },
    'editor_libraries': {
        '@lexical/react': '@tiptap/vue-3',
        '@monaco-editor/react': '@monaco-editor/vue',
        'react-ace': 'vue3-ace-editor'
    },
    'chart_libraries': {
        '@antv/g2': '@antv/g2 (兼容)',
        '@antv/g6': '@antv/g6 (兼容)',
        'bizcharts': '@antv/g2 + Vue包装'
    },
    'state_management': {
        'dva': 'pinia',
        'umi/plugin-model': 'pinia stores',
        '@umijs/plugin-model': 'pinia stores'
    },
    'routing': {
        'umi': 'vue-router',
        '@umijs/router': 'vue-router',
        'umi/router': 'vue-router'
    },
    'request_libraries': {
        'umi-request': 'axios',
        '@umijs/request': 'axios'
    },
    'utils': {
        'umi/locale': 'vue-i18n',
        '@umijs/locale': 'vue-i18n'
    }
}

# --- 迁移阶段配置 ---
MIGRATION_PHASES = {
    MigrationPhase.INFRASTRUCTURE: {
        'includes': ['utils', 'constants', 'types', 'services', 'hooks'],
        'priority': 1,
        'depends_on': []
    },
    MigrationPhase.STORES: {
        'includes': ['models', 'stores'],
        'priority': 2,
        'depends_on': [MigrationPhase.INFRASTRUCTURE]
    },
    MigrationPhase.COMPONENTS: {
        'includes': ['components'],
        'priority': 3,
        'depends_on': [MigrationPhase.INFRASTRUCTURE]
    },
    MigrationPhase.LAYOUTS: {
        'includes': ['layouts'],
        'priority': 4,
        'depends_on': [MigrationPhase.COMPONENTS, MigrationPhase.STORES]
    },
    MigrationPhase.PAGES: {
        'includes': ['pages'],
        'priority': 5,
        'depends_on': [MigrationPhase.LAYOUTS, MigrationPhase.COMPONENTS, MigrationPhase.STORES]
    }
}

# --- 文件类型识别 ---
RESOURCE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
                       '.css', '.less', '.scss', '.sass', '.json', '.md',
                       '.ttf', '.woff', '.woff2', '.eot'}

CODE_EXTENSIONS = {'.js', '.ts', '.jsx', '.tsx'}


class EnhancedDependencyAnalyzer:
    """增强的依赖分析器"""

    def __init__(self, src_dir: Path):
        self.src_dir = src_dir
        self.file_info_cache: Dict[str, FileInfo] = {}

    def get_file_phase(self, file_path: str) -> MigrationPhase:
        """根据文件路径确定迁移阶段"""
        for phase, config in MIGRATION_PHASES.items():
            for include_pattern in config['includes']:
                if include_pattern in file_path:
                    return phase
        return MigrationPhase.INFRASTRUCTURE

    def parse_imports_and_exports(self, file_path: Path) -> Tuple[Dict[str, List[str]], List[str]]:
        """解析文件的导入和导出"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"无法读取文件 {file_path}: {e}")
            return {'relative': [], 'absolute': [], 'assets': []}, []

        imports = {'relative': [], 'absolute': [], 'assets': []}
        exports = []

        # 导入模式
        import_patterns = [
            r"import\s+.*?from\s+['\"](.+?)['\"]",  # ES6 import
            r"import\s*\(\s*['\"](.+?)['\"]\s*\)",  # Dynamic import
            r"require\s*\(\s*['\"](.+?)['\"]\s*\)",  # CommonJS require
        ]

        # 导出模式
        export_patterns = [
            r"export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)",
            r"export\s+\{\s*([^}]+)\s*\}",
            r"export\s+default\s+(\w+)",
        ]

        # 解析导入
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if match.startswith('.'):
                    # 相对路径导入
                    resolved = self.resolve_relative_import(file_path, match)
                    if resolved:
                        imports['relative'].append(resolved)
                elif match.startswith('@/') or match.startswith('~/'):
                    # 别名路径
                    imports['absolute'].append(match)
                elif any(match.endswith(ext) for ext in RESOURCE_EXTENSIONS):
                    # 资源文件导入
                    imports['assets'].append(match)
                else:
                    # npm包导入
                    imports['absolute'].append(match)

        # 解析导出
        for pattern in export_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            exports.extend([m.strip() for m in matches if m.strip()])

        return imports, exports

    def resolve_relative_import(self, from_file: Path, import_path: str) -> Optional[str]:
        """解析相对路径导入"""
        try:
            # 处理相对路径
            if import_path.startswith('./'):
                import_path = import_path[2:]
            elif import_path.startswith('../'):
                pass  # 保持原样

            base_dir = from_file.parent
            target_path = (base_dir / import_path).resolve()

            # 尝试不同的扩展名
            possible_extensions = ['', '.ts', '.tsx', '.js', '.jsx', '.vue']
            possible_files = [str(target_path) + ext for ext in possible_extensions]

            # 如果是目录，查找index文件
            if target_path.is_dir():
                for ext in ['.ts', '.tsx', '.js', '.jsx']:
                    index_file = target_path / f'index{ext}'
                    if index_file.exists():
                        possible_files.append(str(index_file))

            for file_path in possible_files:
                path_obj = Path(file_path)
                if path_obj.exists() and path_obj.is_relative_to(self.src_dir):
                    return str(path_obj.relative_to(self.src_dir))

            return None
        except Exception as e:
            logger.debug(f"解析导入失败 {import_path}: {e}")
            return None

    def analyze_project(self) -> Dict[str, FileInfo]:
        """分析整个项目的文件依赖关系"""
        logger.info("开始分析项目依赖关系...")
        file_infos = {}

        # 遍历所有代码文件
        for file_path in self.src_dir.rglob('*'):
            if (file_path.is_file() and
                    file_path.suffix in CODE_EXTENSIONS and
                    not self.is_resource_file(file_path)):

                relative_path = str(file_path.relative_to(self.src_dir))

                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    imports, exports = self.parse_imports_and_exports(file_path)
                    phase = self.get_file_phase(relative_path)

                    file_info = FileInfo(
                        path=str(file_path),
                        relative_path=relative_path,
                        content=content,
                        imports=imports,
                        exports=exports,
                        file_type=file_path.suffix,
                        phase=phase
                    )

                    file_infos[relative_path] = file_info

                except Exception as e:
                    logger.warning(f"分析文件失败 {file_path}: {e}")

        # 构建依赖图
        self.build_dependency_graph(file_infos)

        logger.info(f"分析完成，共找到 {len(file_infos)} 个代码文件")
        return file_infos

    def build_dependency_graph(self, file_infos: Dict[str, FileInfo]):
        """构建依赖图并计算依赖关系"""
        graph = nx.DiGraph()

        # 添加所有节点
        for relative_path in file_infos.keys():
            graph.add_node(relative_path)

        # 添加边（依赖关系）
        for relative_path, file_info in file_infos.items():
            for dep in file_info.imports['relative']:
                if dep in file_infos:
                    graph.add_edge(relative_path, dep)  # relative_path 依赖 dep

        # 计算每个文件的依赖和被依赖关系
        for relative_path, file_info in file_infos.items():
            file_info.dependencies = list(graph.successors(relative_path))
            file_info.dependents = list(graph.predecessors(relative_path))

    def is_resource_file(self, file_path: Path) -> bool:
        """判断是否为资源文件"""
        if file_path.suffix.lower() in RESOURCE_EXTENSIONS:
            return True

        if file_path.suffix in CODE_EXTENSIONS:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')[:1000]
                # 如果没有import/export关键字，可能是配置文件
                if not re.search(r'\b(import|export)\b', content):
                    return True
            except:
                pass

        return False


class PromptManager:
    """智能提示词管理器"""

    def __init__(self, max_tokens: int = CHUNK_SIZE):
        self.max_tokens = max_tokens
        self.tokenizer = tokenizer

    def count_tokens(self, text: str) -> int:
        """计算文本的token数量"""
        return len(self.tokenizer.encode(text))

    def smart_truncate(self, text: str, max_tokens: int) -> str:
        """智能截断文本，保持结构完整"""
        if self.count_tokens(text) <= max_tokens:
            return text

        # 按行分割，优先保留前面的内容
        lines = text.split('\n')
        truncated_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = self.count_tokens(line + '\n')
            if current_tokens + line_tokens <= max_tokens:
                truncated_lines.append(line)
                current_tokens += line_tokens
            else:
                break

        result = '\n'.join(truncated_lines)
        if len(truncated_lines) < len(lines):
            result += '\n\n# ... (内容因长度限制被截断) ...'

        return result

    def build_tech_mapping_context(self) -> str:
        """构建技术栈映射上下文"""
        context = "# 技术栈映射参考\n\n"
        for category, mappings in TECH_STACK_MAPPING.items():
            context += f"## {category}\n"
            for old, new in mappings.items():
                context += f"- {old} → {new}\n"
            context += "\n"
        return context

    def build_migration_prompt(self, file_info: FileInfo, context: Dict[str, Any]) -> str:
        """构建迁移提示词"""

        # 基础提示词模板
        base_prompt = f"""# React到Vue3代码迁移任务

## 迁移目标
将以下React/TypeScript代码迁移到Vue3 + TypeScript + Composition API + ant-design-vue

## 源文件信息
- 文件路径: {file_info.relative_path}
- 文件类型: {file_info.file_type}
- 迁移阶段: {file_info.phase.value}

## 源代码内容
```{file_info.file_type[1:]}
{file_info.content}
```

## 技术栈转换规则
{self.build_tech_mapping_context()}

## 依赖信息
### 当前文件依赖的模块:
{json.dumps(file_info.dependencies or [], indent=2)}

### 依赖此文件的模块:
{json.dumps(file_info.dependents or [], indent=2)}

## 转换要求
1. 使用Vue3 Composition API (setup语法糖)
2. 保持TypeScript类型定义
3. 将React组件转换为Vue单文件组件(.vue)
4. 将React hooks转换为Vue composables
5. 将Ant Design组件转换为ant-design-vue等价组件
6. 将dva/model转换为Pinia stores
7. 保持业务逻辑不变
8. 保持接口和props的一致性

## 输出要求
请输出完整的Vue3代码，包括:
- <template>部分 (对应JSX)
- <script setup lang="ts">部分 (对应组件逻辑)
- <style>部分 (如果需要)

如果有无法直接转换的部分，请在注释中说明替代方案。
"""

        # 检查并截断prompt
        if self.count_tokens(base_prompt) > self.max_tokens:
            # 截断文件内容部分
            content_limit = self.max_tokens - self.count_tokens(base_prompt.replace(file_info.content, ""))
            truncated_content = self.smart_truncate(file_info.content, content_limit)
            base_prompt = base_prompt.replace(file_info.content, truncated_content)

        return base_prompt


class MigrationExecutor:
    """迁移执行器"""

    def __init__(self):
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 2,
            'retry_exceptions': (
                openai.error.RateLimitError,
                openai.error.APIError,
                openai.error.APIConnectionError,
                openai.error.Timeout
            )
        }
        self.prompt_manager = PromptManager()

    def migrate_file(self, file_info: FileInfo, context: Dict[str, Any]) -> MigrationResult:
        """迁移单个文件"""
        logger.info(f"开始迁移文件: {file_info.relative_path}")

        try:
            prompt = self.prompt_manager.build_migration_prompt(file_info, context)
            response = self.call_openai_with_retry(prompt)

            if response['success']:
                # 提取Vue代码
                vue_content = self.extract_vue_content(response['content'])

                result = MigrationResult(
                    success=True,
                    original_file=file_info.relative_path,
                    new_file=self.get_target_path(file_info.relative_path),
                    content=vue_content
                )

                logger.info(f"文件迁移成功: {file_info.relative_path}")
                return result
            else:
                logger.error(f"文件迁移失败: {file_info.relative_path} - {response['error']}")
                return MigrationResult(
                    success=False,
                    original_file=file_info.relative_path,
                    new_file="",
                    error=response['error']
                )

        except Exception as e:
            logger.error(f"文件迁移异常: {file_info.relative_path} - {str(e)}")
            return MigrationResult(
                success=False,
                original_file=file_info.relative_path,
                new_file="",
                error=str(e)
            )

    def call_openai_with_retry(self, prompt: str) -> Dict[str, Any]:
        """带重试机制的OpenAI API调用"""
        for attempt in range(self.retry_config['max_retries']):
            try:
                response = openai.ChatCompletion.create(
                    model=MODEL,
                    messages=[{
                        'role': 'user',
                        'content': prompt
                    }],
                    temperature=0.1,
                    max_tokens=4000
                )

                content = response.choices[0].message.content
                return {'success': True, 'content': content}

            except self.retry_config['retry_exceptions'] as e:
                if attempt == self.retry_config['max_retries'] - 1:
                    return {'success': False, 'error': f"API调用失败 (重试{attempt + 1}次): {str(e)}"}

                sleep_time = (2 ** attempt) * self.retry_config['backoff_factor']
                logger.warning(f"API调用失败，{sleep_time}秒后重试 (第{attempt + 1}次): {str(e)}")
                time.sleep(sleep_time)

            except Exception as e:
                return {'success': False, 'error': f"未知错误: {str(e)}"}

        return {'success': False, 'error': "重试次数超限"}

    def extract_vue_content(self, response_content: str) -> str:
        """从LLM响应中提取Vue代码"""
        # 尝试提取代码块
        vue_patterns = [
            r'```vue\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'<template>(.*?)</script>',
        ]

        for pattern in vue_patterns:
            match = re.search(pattern, response_content, re.DOTALL)
            if match:
                return match.group(1).strip()

        # 如果没有找到代码块，返回原始内容
        return response_content.strip()

    def get_target_path(self, source_path: str) -> str:
        """获取目标文件路径"""
        # 路径映射规则
        path_mappings = {
            'src/pages': 'src/views',
            'src/models': 'src/stores',
            'src/layouts': 'src/layouts',
            'src/components': 'src/components',
            'src/services': 'src/services',
            'src/utils': 'src/utils',
            'src/hooks': 'src/composables'
        }

        target_path = source_path
        for old_prefix, new_prefix in path_mappings.items():
            if source_path.startswith(old_prefix):
                target_path = source_path.replace(old_prefix, new_prefix, 1)
                break

        # 修改文件扩展名
        if target_path.endswith(('.jsx', '.tsx')):
            target_path = target_path.rsplit('.', 1)[0] + '.vue'
        elif target_path.endswith('.js'):
            target_path = target_path.rsplit('.', 1)[0] + '.ts'

        return target_path


class ProjectSetup:
    """项目设置和脚手架生成"""

    def __init__(self, dest_dir: Path):
        self.dest_dir = dest_dir

    def create_vue_project_structure(self):
        """创建Vue3项目结构"""
        logger.info("创建Vue3项目结构...")

        # 创建目录结构
        directories = [
            'src/views',
            'src/components',
            'src/layouts',
            'src/stores',
            'src/services',
            'src/utils',
            'src/composables',
            'src/types',
            'src/assets/images',
            'src/assets/styles',
            'src/router',
            'public'
        ]

        for dir_path in directories:
            (self.dest_dir / dir_path).mkdir(parents=True, exist_ok=True)

        # 创建基础文件
        self.create_package_json()
        self.create_vite_config()
        self.create_main_ts()
        self.create_app_vue()
        self.create_router()
        self.create_basic_store()

    def create_package_json(self):
        """创建package.json"""
        package_json = {
            "name": "vue3-migrated-project",
            "version": "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vue-tsc && vite build",
                "preview": "vite preview",
                "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx",
                "lint:fix": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx --fix"
            },
            "dependencies": {
                "vue": "^3.3.0",
                "vue-router": "^4.2.0",
                "pinia": "^2.1.0",
                "ant-design-vue": "^4.0.0",
                "@ant-design/icons-vue": "^7.0.0",
                "axios": "^1.4.0",
                "vue-i18n": "^9.2.0"
            },
            "devDependencies": {
                "@vitejs/plugin-vue": "^4.2.0",
                "vite": "^4.3.0",
                "vue-tsc": "^1.6.0",
                "typescript": "^5.0.0",
                "@types/node": "^18.16.0",
                "eslint": "^8.42.0",
                "@typescript-eslint/eslint-plugin": "^5.59.0",
                "@typescript-eslint/parser": "^5.59.0",
                "eslint-plugin-vue": "^9.14.0"
            }
        }

        with open(self.dest_dir / 'package.json', 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2, ensure_ascii=False)

    def create_vite_config(self):
        """创建vite.config.ts"""
        vite_config = '''import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    open: true,
  },
})
'''
        (self.dest_dir / 'vite.config.ts').write_text(vite_config, encoding='utf-8')

    def create_main_ts(self):
        """创建main.ts"""
        main_ts = '''import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Antd)

app.mount('#app')
'''
        (self.dest_dir / 'src/main.ts').write_text(main_ts, encoding='utf-8')

    def create_app_vue(self):
        """创建App.vue"""
        app_vue = '''<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 根组件
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
'''
        (self.dest_dir / 'src/App.vue').write_text(app_vue, encoding='utf-8')

    def create_router(self):
        """创建路由配置"""
        router_index = '''import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/Home.vue')
    }
  ]
})

export default router
'''
        (self.dest_dir / 'src/router/index.ts').write_text(router_index, encoding='utf-8')

    def create_basic_store(self):
        """创建基础store"""
        store_content = '''import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const loading = ref(false)

  const setLoading = (status: boolean) => {
    loading.value = status
  }

  return {
    loading,
    setLoading
  }
})
'''
        (self.dest_dir / 'src/stores/app.ts').write_text(store_content, encoding='utf-8')


class MigrationPipeline:
    """迁移管道"""

    def __init__(self, src_dir: str, dest_dir: str):
        self.src_dir = Path(src_dir)
        self.dest_dir = Path(dest_dir)
        self.analyzer = EnhancedDependencyAnalyzer(self.src_dir)
        self.executor = MigrationExecutor()
        self.project_setup = ProjectSetup(self.dest_dir)

        # 创建输出目录
        self.dest_dir