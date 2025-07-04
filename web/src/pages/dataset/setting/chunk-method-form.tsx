import { useFormContext, useWatch } from 'react-hook-form';

import { DocumentParserType } from '@/constants/knowledge';
import { useMemo } from 'react';
import { AudioConfiguration } from './configuration/audio';
import { BookConfiguration } from './configuration/book';
import { EmailConfiguration } from './configuration/email';
import { KnowledgeGraphConfiguration } from './configuration/knowledge-graph';
import { LawsConfiguration } from './configuration/laws';
import { ManualConfiguration } from './configuration/manual';
import { MdChapterConfiguration } from './configuration/mdchapter';
import { NaiveConfiguration } from './configuration/naive';
import { OneConfiguration } from './configuration/one';
import { PaperConfiguration } from './configuration/paper';
import { PictureConfiguration } from './configuration/picture';
import { PresentationConfiguration } from './configuration/presentation';
import { QAConfiguration } from './configuration/qa';
import { ResumeConfiguration } from './configuration/resume';
import { TableConfiguration } from './configuration/table';
import { TagConfiguration } from './configuration/tag';

const ConfigurationComponentMap = {
  [DocumentParserType.Naive]: NaiveConfiguration,
  [DocumentParserType.Qa]: QAConfiguration,
  [DocumentParserType.Resume]: ResumeConfiguration,
  [DocumentParserType.Manual]: ManualConfiguration,
  [DocumentParserType.Table]: TableConfiguration,
  [DocumentParserType.Paper]: PaperConfiguration,
  [DocumentParserType.Book]: BookConfiguration,
  [DocumentParserType.Laws]: LawsConfiguration,
  [DocumentParserType.Presentation]: PresentationConfiguration,
  [DocumentParserType.Picture]: PictureConfiguration,
  [DocumentParserType.One]: OneConfiguration,
  [DocumentParserType.Audio]: AudioConfiguration,
  [DocumentParserType.Email]: EmailConfiguration,
  [DocumentParserType.Tag]: TagConfiguration,
  [DocumentParserType.KnowledgeGraph]: KnowledgeGraphConfiguration,
  [DocumentParserType.MdChapter]: MdChapterConfiguration,
};

function EmptyComponent() {
  return <div></div>;
}

export function ChunkMethodForm() {
  const form = useFormContext();

  const finalParserId: DocumentParserType = useWatch({
    control: form.control,
    name: 'parser_id',
  });

  console.log('[mdChapter问题排查] ChunkMethodForm parserId:', finalParserId);

  const ConfigurationComponent = useMemo(() => {
    const component = finalParserId
      ? ConfigurationComponentMap[finalParserId]
      : EmptyComponent;
    
    console.log('[mdChapter问题排查] ConfigurationComponent:', component, 'for parserId:', finalParserId);
    console.log('[mdChapter问题排查] Available keys:', Object.keys(ConfigurationComponentMap));
    
    return component;
  }, [finalParserId]);

  return (
    <section className="overflow-auto max-h-[76vh]">
      <ConfigurationComponent></ConfigurationComponent>
    </section>
  );
}
