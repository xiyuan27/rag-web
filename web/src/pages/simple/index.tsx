import { useEffect } from 'react';
import { history } from 'umi';

export default function SimpleHome() {
  useEffect(() => {
    history.replace('/chat?simple=1');
  }, []);
  return null;
}
