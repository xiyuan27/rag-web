import { RAGFlowAvatar } from '@/components/ragflow-avatar';
import { useTranslate } from '@/hooks/common-hooks';
import User from './components/user';
import { useTheme } from '@/components/theme-provider';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Flex, Radio } from 'antd';
import headerStyles from './components/header/index.less';
import type { MouseEventHandler } from 'react';
import { LanguageList, LanguageMap } from '@/constants/common';
import { useChangeLanguage } from '@/hooks/logic-hooks';
import { useFetchAppConf } from '@/hooks/logic-hooks';
import { useNavigateWithFromState } from '@/hooks/route-hook';
import { useFetchUserInfo, useListTenant } from '@/hooks/user-setting-hooks';
import authorizationUtil from '@/utils/authorization-util';
import { TenantRole } from '@/pages/user-setting/constants';
import { Routes } from '@/routes';
import { camelCase } from 'lodash';
import { ChevronDown, CircleHelp, MessageSquareText, Moon, Sun } from 'lucide-react';
import React, { useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'umi';
import styles from './index.less';

const handleDocHelpCLick = () => {
  window.open('https://ragflow.io/docs/dev/category/guides', 'target');
};

export function ChatOnlyHeader() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const navigate = useNavigateWithFromState();
  const handleProfileClick = useCallback(() => {
    navigate('/user-setting');
  }, [navigate]);

  const changeLanguage = useChangeLanguage();
  const { setTheme, theme } = useTheme();

  const {
    data: { language = 'English', avatar, nickname },
  } = useFetchUserInfo();

  const savedInfo = authorizationUtil.getUserInfoObject() || {};
  const profileAvatar = avatar || savedInfo.avatar;
  const profileName = nickname || savedInfo.name;

  const handleItemClick = (key: string) => () => {
    changeLanguage(key);
  };

  const { data } = useListTenant();

  const showBell = useMemo(() => {
    return data.some((x) => x.role === TenantRole.Invite);
  }, [data]);

  const items = LanguageList.map((x) => ({
    key: x,
    label: <span>{LanguageMap[x as keyof typeof LanguageMap]}</span>,
  }));

  const onThemeClick = React.useCallback(() => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  }, [setTheme, theme]);
  const appConf = useFetchAppConf();

  const tagsData = useMemo(
    () => [
      { path: '/chat', name: t('header.chat'), icon: MessageSquareText },
    ],
    [t],
  );

  const currentPath = useMemo(() => {
    return tagsData.find((x) => pathname.startsWith(x.path))?.name || t('header.chat');
  }, [pathname, tagsData, t]);

  const handleChange = useCallback(
    (path: string): MouseEventHandler =>
      (e) => {
        e.preventDefault();
        navigate(path as Routes);
      },
    [navigate],
  );

  const handleLogoClick = useCallback(() => {
    navigate(Routes.SimpleHome);
  }, [navigate]);

  return (
    <section className="p-5 pr-14 flex justify-between items-center ">
      <div className="flex items-center gap-4">
        <img
          src={'/logo.svg'}
          alt="logo"
          className="size-10 mr-[12]"
          onClick={handleLogoClick}
        />
	<span className={styles.appName}>{appConf.appName}</span>
      </div>
      <Radio.Group
        buttonStyle="solid"
        className={
          theme === 'dark' ? headerStyles.radioGroupDark : headerStyles.radioGroup
        }
        value={currentPath}
      >
        {tagsData.map((item) => (
          <Radio.Button
            className={`${theme === 'dark' ? 'dark' : 'light'} first last`}
            value={item.name}
            key={item.name}
          >
            <a href={item.path}>
              <Flex
                align="center"
                gap={8}
                onClick={handleChange(item.path)}
                className="cursor-pointer"
              >
                <item.icon
                  className={headerStyles.radioButtonIcon}
                  stroke={item.name === currentPath ? 'black' : 'white'}
                ></item.icon>
                {item.name}
              </Flex>
            </a>
          </Radio.Button>
        ))}
      </Radio.Group>
      <div className="flex items-center gap-5 text-text-badge">
        <DropdownMenu>
          <DropdownMenuTrigger>
            <div className="flex items-center gap-1">
              {t(`common.${camelCase(language)}`)}
              <ChevronDown className="size-4" />
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {items.map((x) => (
              <DropdownMenuItem key={x.key} onClick={handleItemClick(x.key)}>
                {x.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button variant={'ghost'} onClick={onThemeClick}>
          {theme === 'light' ? <Sun /> : <Moon />}
        </Button>
        <div className="relative">
          
        {showBell && (
          <Circle>
            <div className="relative" onClick={handleBellClick}>
              <BellRing className="size-4 " />
              <span className="absolute size-1 rounded -right-1 -top-1 bg-red-600"></span>
            </div>
          </Circle>
        )}
	<User></User>
        </div>
      </div>
    </section>
  );
}
