import { Col, Divider, Row, Spin, Typography } from 'antd';
import CategoryPanel from './category-panel';
import { ConfigurationForm } from './configuration';
import {
  useHandleChunkMethodChange,
  useSelectKnowledgeDetailsLoading,
} from './hooks';

import { useTranslate } from '@/hooks/common-hooks';
import styles from './index.less';

const { Title } = Typography;

const Configuration = () => {
  console.log('🔥🔥🔥 Configuration 组件已渲染 - VERSION 005 🔥🔥🔥');
  console.log('[mdChapter问题排查] Configuration 组件开始');
  const loading = useSelectKnowledgeDetailsLoading();
  const { form, chunkMethod } = useHandleChunkMethodChange();
  console.log('[mdChapter问题排查] chunkMethod 值:', chunkMethod);
  const { t } = useTranslate('knowledgeConfiguration');

  return (
    <div className={styles.configurationWrapper}>
      <Title level={5}>
        {t('configuration', { keyPrefix: 'knowledgeDetails' })}
      </Title>
      <p>{t('titleDescription')}</p>
      <Divider></Divider>
      <Spin spinning={loading}>
        <Row gutter={32}>
          <Col span={8}>
            <ConfigurationForm form={form}></ConfigurationForm>
          </Col>
          <Col span={16}>
            <CategoryPanel chunkMethod={chunkMethod}></CategoryPanel>
          </Col>
        </Row>
      </Spin>
    </div>
  );
};

export default Configuration;
