import { Outlet } from 'umi';
import { ChatOnlyHeader } from './chat-only-header';

export default function ChatOnlyLayout() {
  return (
    <section className="h-full flex flex-col text-colors-text-neutral-strong">
      <ChatOnlyHeader></ChatOnlyHeader>
      <Outlet />
    </section>
  );
}
