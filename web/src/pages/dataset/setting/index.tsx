import { ButtonLoading } from '@/components/ui/button';
import { Form } from '@/components/ui/form';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DocumentParserType } from '@/constants/knowledge';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';
import { TopTitle } from '../dataset-title';
import CategoryPanel from './category-panel';
import { ChunkMethodForm } from './chunk-method-form';
import { formSchema } from './form-schema';
import { GeneralForm } from './general-form';
import { useFetchKnowledgeConfigurationOnMount } from './hooks';

const enum DocumentType {
  DeepDOC = 'DeepDOC',
  PlainText = 'Plain Text',
}

const initialEntityTypes = [
  'organization',
  'person',
  'geo',
  'event',
  'category',
];

const enum MethodValue {
  General = 'general',
  Light = 'light',
}

export default function DatasetSettings() {
  console.log('🔥🔥🔥 DatasetSettings 组件已渲染 - VERSION 004 🔥🔥🔥');
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      description: '',
      avatar: undefined,
      parser_id: DocumentParserType.Naive,
      embd_id: '',
      permission: 'me',
      parser_config: {
        layout_recognize: true,
        chunk_token_num: 512,
        delimiter: `\n`,
        auto_keywords: 0,
        auto_questions: 0,
        html4excel: false,
        tag_kb_ids: [],
        topn_tags: 3,
        raptor: {
          use_raptor: false,
        },
        graphrag: {
          use_graphrag: false,
        },
      },
      pagerank: 0,
    },
  });

  useFetchKnowledgeConfigurationOnMount(form);

  const parserId = useWatch({
    control: form.control,
    name: 'parser_id',
  });

  async function onSubmit(data: z.infer<typeof formSchema>) {
    console.log('🚀 ~ DatasetSettings ~ data:', data);
  }

  return (
    <section className="p-5 ">
      <div style={{ background: 'lime', padding: '10px', margin: '10px 0' }}>
        TEST VERSION 003 - 代码已更新
      </div>
      <TopTitle
        title={'Configuration'}
        description={`  Update your knowledge base configuration here, particularly the chunk
          method.`}
      ></TopTitle>
      <div className="flex gap-14">
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-6 basis-full"
          >
            <Tabs defaultValue="account">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="account">Account</TabsTrigger>
                <TabsTrigger value="password">Password</TabsTrigger>
              </TabsList>
              <TabsContent value="account">
                <GeneralForm></GeneralForm>
              </TabsContent>
              <TabsContent value="password">
                <ChunkMethodForm></ChunkMethodForm>
              </TabsContent>
            </Tabs>
            <div className="text-right">
              <ButtonLoading type="submit">Submit</ButtonLoading>
            </div>
          </form>
        </Form>

        <CategoryPanel chunkMethod={parserId}></CategoryPanel>
      </div>
    </section>
  );
}
