import { navigate as umiNavigate } from 'umi';

/**
 * 统一导航工具 - 自动处理路径前缀
 * 
 * 使用示例：
 * - navigate('/login') -> 自动转为 /rag/login
 * - navigate('/rag/login') -> 保持不变
 * - navigate('/user-setting') -> 自动转为 /rag/user-setting
 */

// 当前项目的base路径
const BASE_PATH = '/rag';

/**
 * 智能导航函数 - 自动添加base路径前缀
 * @param path 目标路径
 * @param options 导航选项（可选）
 */
export const navigate = (path: string, options?: any) => {
  // 如果已经包含base路径，直接使用
  if (path.startsWith(BASE_PATH + '/') || path === BASE_PATH) {
    return umiNavigate(path, options);
  }
  
  // 如果是根路径 /，转换为 base路径
  if (path === '/') {
    return umiNavigate(BASE_PATH + '/', options);
  }
  
  // 如果是绝对路径但不包含base，自动添加base前缀
  if (path.startsWith('/')) {
    return umiNavigate(BASE_PATH + path, options);
  }
  
  // 相对路径直接使用
  return umiNavigate(path, options);
};

/**
 * 获取当前base路径
 */
export const getBasePath = () => BASE_PATH;

/**
 * 构建完整路径（用于其他需要完整路径的场景）
 * @param path 原始路径
 */
export const buildPath = (path: string) => {
  if (path.startsWith(BASE_PATH + '/') || path === BASE_PATH) {
    return path;
  }
  if (path === '/') {
    return BASE_PATH + '/';
  }
  if (path.startsWith('/')) {
    return BASE_PATH + path;
  }
  return path;
};

// 兼容性：导出为默认导出
export default navigate;