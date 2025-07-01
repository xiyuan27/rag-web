import authorizationUtil from '@/utils/authorization-util';
import { message } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'umi';

export const useOAuthCallback = () => {
  const [currentQueryParameters, setSearchParams] = useSearchParams();
  const error = currentQueryParameters.get('error');
  const newQueryParameters: URLSearchParams = useMemo(
    () => new URLSearchParams(currentQueryParameters.toString()),
    [currentQueryParameters],
  );
  const navigate = useNavigate();

  useEffect(() => {
    if (error) {
      message.error(error);
      setTimeout(() => {
        navigate('/rag/login');
        newQueryParameters.delete('error');
        setSearchParams(newQueryParameters);
      }, 1000);
      return;
    }

    const auth = currentQueryParameters.get('auth');
    if (auth) {
      authorizationUtil.setAuthorization(auth);
      newQueryParameters.delete('auth');
      setSearchParams(newQueryParameters);
      navigate('/rag/knowledge');
    }
  }, [
    error,
    currentQueryParameters,
    newQueryParameters,
    navigate,
    setSearchParams,
  ]);

  console.debug(currentQueryParameters.get('auth'));
  return currentQueryParameters.get('auth');
};

export const useAuth = () => {
  const auth = useOAuthCallback();
  const [isLogin, setIsLogin] = useState<Nullable<boolean>>(null);

  useEffect(() => {
    // 添加延迟检查，确保localStorage操作完成
    const checkAuth = () => {
      setIsLogin(!!authorizationUtil.getAuthorization() || !!auth);
    };

    // 立即检查
    checkAuth();

    // 短延迟后再次检查，处理清除操作的时序问题
    const timer = setTimeout(checkAuth, 50);

    return () => clearTimeout(timer);
  }, [auth]);

  return { isLogin };
};
