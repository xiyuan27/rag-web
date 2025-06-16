import { Outlet } from 'umi';
import { Header } from './next-header';
import { ChatOnlyHeader } from './chat-only-header';
import authorizationUtil from '@/utils/authorization-util';


export default function NextLayout() {
  const simpleMode = authorizationUtil.isNormalRole();

  return (
    <section className="h-full flex flex-col text-colors-text-neutral-strong">
      {simpleMode ? <ChatOnlyHeader /> : <Header />}
      <Outlet />
    </section>
  );
}
