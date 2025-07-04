import {
  AutoKeywordsItem,
  AutoQuestionsItem,
} from '@/components/auto-keywords-item';
import { DatasetConfigurationContainer } from '@/components/dataset-configuration-container';
import Delimiter from '@/components/delimiter';
import ExcelToHtml from '@/components/excel-to-html';
import LayoutRecognize from '@/components/layout-recognize';
import MaxTokenNumber from '@/components/max-token-number';
import PageRank from '@/components/page-rank';
import ParseConfiguration from '@/components/parse-configuration';
import GraphRagItems from '@/components/parse-configuration/graph-rag-items';
import { Divider } from 'antd';
import { TagItems } from '../tag-item';
import { ChunkMethodItem, EmbeddingModelItem } from './common-item';

export function MdChapterConfiguration() {
  console.log('[mdChapter问题排查] MdChapterConfiguration 组件开始渲染');
  
  try {
    console.log('[mdChapter问题排查] MdChapterConfiguration 渲染成功');
    return (
      <section className="space-y-4 mb-4">
        <DatasetConfigurationContainer>
          <LayoutRecognize></LayoutRecognize>
          <EmbeddingModelItem></EmbeddingModelItem>
          <ChunkMethodItem></ChunkMethodItem>
          <MaxTokenNumber></MaxTokenNumber>
          <Delimiter></Delimiter>
        </DatasetConfigurationContainer>
        <Divider></Divider>
        <DatasetConfigurationContainer>
          <PageRank></PageRank>
          <AutoKeywordsItem></AutoKeywordsItem>
          <AutoQuestionsItem></AutoQuestionsItem>
          <ExcelToHtml></ExcelToHtml>
          <TagItems></TagItems>
        </DatasetConfigurationContainer>
        <Divider></Divider>
        <DatasetConfigurationContainer>
          <ParseConfiguration></ParseConfiguration>
        </DatasetConfigurationContainer>
        <Divider></Divider>
        <GraphRagItems></GraphRagItems>
      </section>
    );
  } catch (error) {
    console.error('[mdChapter问题排查] MdChapterConfiguration 渲染失败:', error);
    throw error;
  }
}