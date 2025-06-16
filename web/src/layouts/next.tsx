import { Outlet, useSearchParams } from 'umi';
import { Header } from './next-header';
import { ChatOnlyHeader } from './chat-only-header';


export default function NextLayout() {
  const [searchParams] = useSearchParams();
  const simpleMode = searchParams.get('simple') === '1';

  return (
    <section className="h-full flex flex-col text-colors-text-neutral-strong">
      {simpleMode ? <ChatOnlyHeader /> : <Header />}
      <Outlet />
    </section>
  );
}
