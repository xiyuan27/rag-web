import { Authorization, Token, UserInfo } from '@/constants/authorization';
import { getSearchValue } from './common-util';
const KeySet = [Authorization, Token, UserInfo];

const storage = {
  getAuthorization: () => {
    return localStorage.getItem(Authorization);
  },
  getToken: () => {
    return localStorage.getItem(Token);
  },
  getUserInfo: () => {
    return localStorage.getItem(UserInfo);
  },
  getUserInfoObject: () => {
    try {
      return JSON.parse(localStorage.getItem('userInfo') || '{}');
    } catch (e) {
      return {};
    }
  },
  getUserRole: (): string | undefined => {
    try {
      return JSON.parse(localStorage.getItem('userInfo') || '{}').role;
    } catch (e) {
      return undefined;
    }
  },
  isQueryRole: () => {
    return storage.getUserRole() === 'query';
  },
  setAuthorization: (value: string) => {
    localStorage.setItem(Authorization, value);
  },
  setToken: (value: string) => {
    localStorage.setItem(Token, value);
  },
  setUserInfo: (value: string | Record<string, unknown>) => {
    let valueStr = typeof value !== 'string' ? JSON.stringify(value) : value;
    localStorage.setItem(UserInfo, valueStr);
  },
  setItems: (pairs: Record<string, string>) => {
    Object.entries(pairs).forEach(([key, value]) => {
      localStorage.setItem(key, value);
    });
  },
  removeAuthorization: () => {
    localStorage.removeItem(Authorization);
  },
  removeAll: () => {
    KeySet.forEach((x) => {
      localStorage.removeItem(x);
    });
  },
  setLanguage: (lng: string) => {
    localStorage.setItem('lng', lng);
  },
  getLanguage: (): string => {
    return localStorage.getItem('lng') as string;
  },
};

export const getAuthorization = () => {
  const auth = getSearchValue('auth');
  const authorization = auth
    ? 'Bearer ' + auth
    : storage.getAuthorization() || '';

  return authorization;
};

export default storage;

// Will not jump to the login page
export function redirectToLogin() {
  window.location.href = location.origin + `/login`;
}
