import { z } from 'zod';

export const formSchema = z.object({
  name: z.string().min(1, {
    message: 'Username must be at least 2 characters.',
  }),
  description: z.string().optional(),
  avatar: z.any().optional(),
  permission: z.string(),
  parser_id: z.string(),
  embd_id: z.string(),
  parser_config: z.object({
    layout_recognize: z.boolean().optional(),
    chunk_token_num: z.number().optional(),
    delimiter: z.string().optional(),
    auto_keywords: z.number().optional(),
    auto_questions: z.number().optional(),
    html4excel: z.boolean().optional(),
    tag_kb_ids: z.array(z.string()).optional(),
    topn_tags: z.number().optional(),
    raptor: z.object({
      use_raptor: z.boolean(),
    }).optional(),
    graphrag: z.object({
      use_graphrag: z.boolean().optional(),
    }).optional(),
    from_page: z.number().optional(),
    to_page: z.number().optional(),
  }),
  pagerank: z.number(),
  // icon: z.array(z.instanceof(File)),
});
