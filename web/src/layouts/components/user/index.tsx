import { useFetchUserInfo } from '@/hooks/user-setting-hooks';
import { Avatar } from 'antd';
import React from 'react';
import { useNavigate, useSearchParams } from 'umi';

import styles from '../../index.less';

const App: React.FC = () => {
  const { data: userInfo } = useFetchUserInfo();

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const toSetting = () => {
    const simple = searchParams.get('simple') === '1' ? '?simple=1' : '';
    navigate(`/user-setting${simple}`);
  };

  return (
    <Avatar
      size={32}
      onClick={toSetting}
      className={styles.clickAvailable}
      src={
        userInfo.avatar ??
        'https://zos.alipayobjects.com/rmsportal/jkjgkEfvpUPVyRjUImniVslZfWPnJuuZ.png'
      }
    />
  );
};

export default App;
