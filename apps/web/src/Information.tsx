import { Link } from "react-router-dom";
import { ArrowUpRight, Database } from "lucide-react";
import { useApi } from "./api";
import { date, number, type DataSource } from "./models";
import { Busy, Empty, Err, External, PageTitle, Tag } from "./ui";
export function Sources() {
  const q = useApi<DataSource[]>("/sources");
  return (
    <>
      <PageTitle
        title="Fontes de dados"
        description="Origem, cobertura e atualização dos dados utilizados no observatório."
      />
      <section className="source-grid">
        {q.isLoading ? (
          <Busy />
        ) : q.error ? (
          <Err error={q.error} retry={q.refetch} />
        ) : q.data?.length ? (
          q.data.map((s) => (
            <article className="panel prose" key={s.id}>
              <div className="inline-between">
                <span className="metric-icon forest">
                  <Database size={19} />
                </span>
                <Tag tone={s.status === "active" && !s.stale ? "green" : "amber"}>
                  {s.stale ? "Cache anterior" : {
                    active: "Disponível",
                    requires_configuration: "A configurar",
                    unavailable: "Indisponível",
                  }[s.status] || s.status}
                </Tag>
              </div>
              <h2>{s.name}</h2>
              <small>{s.organization}</small>
              <p>{s.description}</p>
              <dl className="details">
                <dt>Referência</dt>
                <dd>{s.reference || "Indisponível"}</dd>
                <dt>Escala</dt>
                <dd>
                  {s.granularity === "municipality"
                    ? "Municipal"
                    : s.granularity || "Indisponível"}
                </dd>
                <dt>Última coleta</dt>
                <dd>{date(s.last_synced)}</dd>
                <dt>Registros</dt>
                <dd>
                  {s.records == null ? "Indisponível" : number(s.records)}
                </dd>
              </dl>
              {s.notes && <p>{s.notes}</p>}
              <External url={s.url}>Consultar fonte</External>
            </article>
          ))
        ) : (
          <Empty
            title="Catálogo de fontes indisponível"
            text="Nenhuma fonte foi carregada no catálogo."
            action={false}
          />
        )}
      </section>
    </>
  );
}
const content = {
  metodologia: {
    title: "Metodologia",
    desc: "Como os registros são organizados, verificados e comparados.",
    sections: [
      [
        "Problemas e relatos",
        "Um problema representa uma situação localizada. Cada relato preserva a descrição enviada pela pessoa e pode adicionar evidências, referências ou uma atualização ao dossiê. A moderação decide o que publicar.",
      ],
      [
        "Possíveis duplicidades",
        "A comparação considera o município, a distância entre pontos, a categoria, o texto e a proximidade temporal. A pessoa pode reconhecer o mesmo problema ou propor um novo registro. A equipe revisa o vínculo antes da publicação.",
      ],
      [
        "Verificação e acompanhamento",
        "A situação operacional descreve o andamento do problema. O grau de verificação identifica a evidência disponível. Os votos de resolvido e não resolvido representam percepções individuais e podem ser alterados ou retirados.",
      ],
      [
        "Indicadores e prioridade",
        "Cada indicador informa a fonte, a unidade, o período de referência e a escala municipal. Dados ausentes aparecem como indisponíveis. A avaliação de prioridade exige dados sobre gravidade, população afetada e vulnerabilidade. Quando faltam elementos, o registro fica sem pontuação.",
      ],
      [
        "Cenários de investimento",
        "O simulador divide o orçamento pelo custo unitário hipotético e seleciona registros elegíveis segundo a estratégia escolhida. Cada cenário conserva seus parâmetros e resultados. A comparação não constitui previsão de impacto ou orçamento oficial.",
      ],
    ],
  },
  sobre: {
    title: "Sobre o INVISIVEL",
    desc: "Inteligência territorial e participação cidadã.",
    sections: [
      [
        "Um observatório para acompanhar o território",
        "O INVISIVEL reúne dados públicos e contribuições da comunidade em um mapa de problemas coletivos. Cada registro tem localização, fontes, histórico e espaço para acompanhar mudanças.",
      ],
      [
        "Cobertura do projeto",
        "A navegação utiliza códigos municipais do IBGE. Serra e Vitória, no Espírito Santo, são os municípios piloto. A disponibilidade dos indicadores, dos limites e dos relatos varia conforme o território.",
      ],
      [
        "Participação aberta",
        "O mapa, os dossiês e os indicadores são públicos. Uma conta permite enviar relatos, acrescentar evidências e votar. O modo de demonstração utiliza registros ilustrativos identificados e mantém a origem dos indicadores oficiais.",
      ],
    ],
  },
  privacidade: {
    title: "Privacidade",
    desc: "Como a participação e a visibilidade dos dados funcionam.",
    sections: [
      [
        "Conta e identificação pública",
        "A plataforma utiliza e-mail e nome público ou pseudônimo para autenticação e atribuição de contribuições. Você pode ocultar seu nome ao enviar um relato. A equipe de moderação mantém o vínculo interno necessário para revisar o envio.",
      ],
      [
        "Localização e imagens",
        "O formulário solicita a localização do problema. Você pode informar as coordenadas manualmente ou conceder acesso à localização do dispositivo. Imagens ficam privadas até a aprovação. Evite divulgar rostos, placas, endereços pessoais ou outros dados identificáveis.",
      ],
      [
        "Acesso e exclusão",
        "Em Meu perfil é possível exportar os dados da conta e solicitar a exclusão. Os registros públicos e o histórico de moderação podem ser preservados com anonimização.",
      ],
      [
        "Armazenamento no dispositivo",
        "O PWA guarda os arquivos públicos da interface para abrir o aplicativo sem conexão. A consulta de dados, o acesso à conta e o envio de relatos exigem conexão. A base cartográfica é fornecida pelo OpenStreetMap quando o mapa é aberto.",
      ],
      [
        "Conteúdo sensível",
        "Para situações de risco imediato, procure os serviços oficiais de emergência da sua região. Evite incluir denúncias sigilosas ou dados de vítimas nos relatos públicos.",
      ],
    ],
  },
};
export function Info({ page }: { page: keyof typeof content }) {
  const data = content[page];
  return (
    <>
      <PageTitle title={data.title} description={data.desc} />
      <section className="panel prose article">
        {data.sections.map(([heading, p]) => (
          <section key={heading}>
            <h2>{heading}</h2>
            <p>{p}</p>
          </section>
        ))}
        <div className="actions">
          <Link
            className="btn secondary"
            to={page === "privacidade" ? "/perfil" : "/fontes"}
          >
            {page === "privacidade" ? "Meu perfil" : "Consultar fontes"}
            <ArrowUpRight size={15} />
          </Link>
        </div>
      </section>
    </>
  );
}
