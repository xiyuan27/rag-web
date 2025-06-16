import { Divider, Layout, theme } from 'antd';
import React from 'react';
import { Outlet } from 'umi';
import authorizationUtil from '@/utils/authorization-util';
import '../locales/config';
import Header from './components/header';
import { ChatOnlyHeader } from './chat-only-header';

import styles from './index.less';

const { Content } = Layout;

const App: React.FC = () => {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const simpleMode = authorizationUtil.isNormalRole();
  return (
    <Layout className={styles.layout}>
      <Layout>
        {simpleMode ? <ChatOnlyHeader /> : <Header />}
        <Divider orientationMargin={0} className={styles.divider} />
        <Content
          style={{
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
            overflow: 'auto',
            display: 'flex',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;
