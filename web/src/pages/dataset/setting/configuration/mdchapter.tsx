import {
  AutoKeywordsFormField,
  AutoQuestionsFormField,
} from '@/components/auto-keywords-form-field';
import { DelimiterFormField } from '@/components/delimiter-form-field';
import { ExcelToHtmlFormField } from '@/components/excel-to-html-form-field';
import { LayoutRecognizeFormField } from '@/components/layout-recognize-form-field';
import { MaxTokenNumberFormField } from '@/components/max-token-number-from-field';
import PageRankFormField from '@/components/page-rank-form-field';
import GraphRagItems from '@/components/parse-configuration/graph-rag-form-fields';
import RaptorFormFields from '@/components/parse-configuration/raptor-form-fields';
import {
  ConfigurationFormContainer,
  MainContainer,
} from '../configuration-form-container';
import { TagItems } from '../tag-item';
import { ChunkMethodItem, EmbeddingModelItem } from './common-item';

export function MdChapterConfiguration() {
  console.log('[mdChapter问题排查] MdChapterConfiguration 组件开始渲染');
  
  try {
    console.log('[mdChapter问题排查] MdChapterConfiguration 渲染成功');
    return (
      <div>
        <h1>✅ MdChapter组件已加载</h1>
      </div>
    );
  } catch (error) {
    console.error('[mdChapter问题排查] MdChapterConfiguration 渲染失败:', error);
    throw error;
  }
}