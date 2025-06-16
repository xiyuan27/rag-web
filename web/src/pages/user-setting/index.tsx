import { Flex } from 'antd';
import React from 'react';
import { Outlet, history, useLocation } from 'umi';
import SideBar from './sidebar';

import styles from './index.less';

const UserSetting = () => {
  const location = useLocation();
  React.useEffect(() => {
       if (location.pathname === '/user-setting') {
         history.replace(`/user-setting/profile${location.search}`);
       }
  }, [location]);
  return (
    <Flex className={styles.settingWrapper}>
      <SideBar></SideBar>
      <Flex flex={1} className={styles.outletWrapper}>
        <Outlet></Outlet>
      </Flex>
    </Flex>
  );
};

export default UserSetting;
