import { Domain } from '@/constants/common';
import { useTranslate } from '@/hooks/common-hooks';
import { useLogout } from '@/hooks/login-hooks';
import { useSecondPathName } from '@/hooks/route-hook';
import { useFetchSystemVersion } from '@/hooks/user-setting-hooks';
import type { MenuProps } from 'antd';
import { Flex, Menu } from 'antd';
import React, { useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'umi';
import {
  UserSettingBaseKey,
  UserSettingIconMap,
  UserSettingRouteKey,
} from '../constants';
import styles from './index.less';

type MenuItem = Required<MenuProps>['items'][number];

const SideBar = () => {
  const navigate = useNavigate();
  const pathName = useSecondPathName();
  const [searchParams] = useSearchParams();
  const { logout } = useLogout();
  const { t } = useTranslate('setting');
  const { version, fetchSystemVersion } = useFetchSystemVersion();
  const simple = searchParams.get('simple') === '1';

  useEffect(() => {
    if (location.host !== Domain) {
      fetchSystemVersion();
    }
  }, [fetchSystemVersion]);

  function getItem(
    label: string,
    key: React.Key,
    icon?: React.ReactNode,
    children?: MenuItem[],
    type?: 'group',
  ): MenuItem {
    return {
      key,
      icon,
      children,
      label: (
        <Flex justify={'space-between'}>
          {t(label)}
          <span className={styles.version}>
            {label === 'system' && version}
          </span>
        </Flex>
      ),
      type,
    } as MenuItem;
  }

const items: MenuItem[] = useMemo(() => {
    const keys = simple
      ? [
          UserSettingRouteKey.Profile,
          UserSettingRouteKey.Password,
          UserSettingRouteKey.Logout,
        ]
      : Object.values(UserSettingRouteKey);
    return keys.map((value) => getItem(value, value, UserSettingIconMap[value]));
  }, [simple]);

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === UserSettingRouteKey.Logout) {
      logout();
    } else {
      const simpleParam = simple ? '?simple=1' : '';
      navigate(`/${UserSettingBaseKey}/${key}${simpleParam}`);
    }
  };

  const selectedKeys = useMemo(() => {
    return [pathName];
  }, [pathName]);

  return (
    <section className={styles.sideBarWrapper}>
      <Menu
        selectedKeys={selectedKeys}
        mode="inline"
        items={items}
        onClick={handleMenuClick}
        style={{ width: 312 }}
      />
    </section>
  );
};

export default SideBar;
