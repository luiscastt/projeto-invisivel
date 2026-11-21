import { useState } from "react";
import { Link } from "react-router-dom";
import { Database, ExternalLink } from "lucide-react";
import { useApp } from "./context";
import { useApi } from "./api";
import { money, number, date } from "./models";
import { Busy, Empty, Err, External, PageTitle, Tag } from "./ui";

type Item={id:string;name:string;latitude?:number|null;longitude?:number|null;attends_sus?:boolean|null;status?:string|null;planned_investment?:number|null;amount?:number|null;released?:number|null;source_url?:string;updated_at?:string;start?:string;end?:string};
type Collection={available:boolean;items:Item[];total:number|null;notes:string;fetched_at?:string};
export type OfficialContext={municipality_code:string;health:Collection;education:Collection;works:Collection;funding:Collection;sanitation_management:{available:boolean;notes:string;record:null|{reference_year:string;responded:boolean;information:{code:string;label:string;value:string|number|boolean|null;unit?:string}[]};manifest:Record<string,unknown>};ombudsman:{available:boolean;total:number|null;year?:string;notes:string;source_url?:string;quality?:{unmapped_rows:number};by_type:Record<string,number>;by_status:Record<string,number>};falabr:{available:boolean;notes:string;public_dashboard_url:string}};
const tabs={health:"Saúde",education:"Educação",works:"Obras",funding:"Convênios",sanitation_management:"Saneamento",ombudsman:"Ouvidoria"};
type Tab=keyof typeof tabs;
export default function OfficialData(){
 const {city}=useApp();const q=useApi<OfficialContext>(`/territories/${city.code}/context`);
 const [tab,setTab]=useState<Tab>('health'),[search,setSearch]=useState(''),[page,setPage]=useState(1),[sus,setSus]=useState(false);
 const data=q.data;
 const collection=data&&(['health','education','works','funding'].includes(tab)?data[tab as 'health'|'education'|'works'|'funding']:null);
 const all=(collection?.items||[]).filter(i=>(!search||i.name.toLocaleLowerCase().includes(search.toLocaleLowerCase()))&&(!sus||tab!=='health'||i.attends_sus===true));
 const list=all.slice((page-1)*20,page*20);
 return <><PageTitle title="Dados e serviços públicos" description={`Contexto oficial de ${city.name}, com origem, cobertura e período preservados.`}><Link className="btn secondary" to="/fontes"><Database size={16}/>Catálogo de fontes</Link></PageTitle>
 {q.isLoading?<Busy/>:q.error?<Err error={q.error} retry={q.refetch}/>:data&&<>
 <p className="notice">Cadastros e estatísticas oficiais são contexto territorial. Eles não são denúncias nem comprovam, por si, um problema específico.</p>
 <div className="metrics official-metrics">{(['health','education','works','funding'] as const).map(k=><div className="metric" key={k}><div><strong>{data[k].total==null?'—':number(data[k].total)}</strong><span>{tabs[k]}{k==='education'?' · rede estadual':''}</span></div></div>)}</div>
 <div className="tab-row" role="tablist" aria-label="Setores de dados oficiais">{Object.entries(tabs).map(([key,name])=><button key={key} role="tab" aria-selected={tab===key} className={'btn '+(tab===key?'primary':'secondary')} onClick={()=>{setTab(key as Tab);setSearch('');setPage(1);setSus(false)}}>{name}</button>)}</div>
 {collection&&<section className="panel prose" role="tabpanel"><h2>{tabs[tab]} · {city.name}</h2><p>{collection.notes}</p>{collection.fetched_at&&<small>Coleta: {date(collection.fetched_at)} · Escala municipal</small>}
 {!collection.available?<Empty title="Dados não disponíveis para este município" text="A integração ainda não possui uma coleta válida para este território." action={false}/>:<>
 <div className="filters"><label>Pesquisar cadastro<input value={search} onChange={e=>{setSearch(e.target.value);setPage(1)}} placeholder="Nome ou descrição"/></label>{tab==='health'&&<label className="check-row"><input type="checkbox" checked={sus} onChange={e=>{setSus(e.target.checked);setPage(1)}}/>Somente atendimento ambulatorial ao SUS declarado</label>}</div>
 <p>{number(all.length)} registros neste filtro. A lista inclui itens sem coordenadas ou com pontos incompatíveis com os limites oficiais; eles não recebem marcadores inventados.</p>
 {list.map(i=><article className="record" key={i.id}><div className="inline-between"><h3>{i.name}</h3>{i.status&&<Tag>{i.status}</Tag>}</div><small>{tab==='health'?'CNES':tab==='education'?'Código INEP · rede estadual':tab==='works'?'Projeto Obrasgov':'Convênio federal'} {i.id}</small>
 {tab==='health'&&<p>SUS ambulatorial: {i.attends_sus==null?'não informado':i.attends_sus?'sim':'não'}{i.updated_at?' · atualização cadastral '+date(i.updated_at):''}</p>}
 {tab==='works'&&<p>Investimento previsto: {i.planned_investment==null?'não informado':money(i.planned_investment)} · Valor declarado por fonte, não execução financeira.</p>}
 {tab==='funding'&&<p>Valor do convênio: {i.amount==null?'não informado':money(i.amount)} · Liberado: {i.released==null?'não informado':money(i.released)}<br/>Vigência: {date(i.start)} a {date(i.end)}</p>}
 {i.source_url&&<External url={i.source_url}>Consultar registro oficial</External>}</article>)}
 {!list.length&&<p>Nenhum cadastro corresponde ao filtro.</p>}
 {all.length>20&&<div className="actions"><button className="btn secondary" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Anterior</button><span>Página {page} de {Math.ceil(all.length/20)}</span><button className="btn secondary" disabled={page*20>=all.length} onClick={()=>setPage(p=>p+1)}>Próxima</button></div>}
 </>}
 </section>}
 {tab==='sanitation_management'&&<section className="panel prose" role="tabpanel"><h2>SINISA · Gestão Municipal</h2><p>{data.sanitation_management.notes}</p>{data.sanitation_management.record?<><Tag>Referência {data.sanitation_management.record.reference_year}</Tag><p>Município respondeu à coleta: {data.sanitation_management.record.responded?'Sim':'Não'}</p><dl className="official-information">{data.sanitation_management.record.information.map(i=><div key={i.code}><dt>{i.label}<small>{i.code}{i.unit?' · '+i.unit:''}</small></dt><dd>{i.value==null?'Não informado':String(i.value)}</dd></div>)}</dl></>:<Empty title="Sem declaração municipal importada" text="A ausência não indica inexistência de serviços." action={false}/>}</section>}
 {tab==='ombudsman'&&<section className="panel prose" role="tabpanel"><h2>Ouvidoria estadual · {data.ombudsman.year||'sem período'}</h2><p>{data.ombudsman.notes}</p>{data.ombudsman.available?<><p><strong>{number(data.ombudsman.total||0)}</strong> manifestações com este município informado. Essa contagem não representa problemas cadastrados no INVISIVEL.</p><div className="result-grid">{(['by_type','by_status'] as const).map(k=><div key={k}><h3>{k==='by_type'?'Por tipo':'Por situação'}</h3><dl className="details">{Object.entries(data.ombudsman[k]).map(([name,value])=><div key={name}><dt>{name}</dt><dd>{number(value)}</dd></div>)}</dl></div>)}</div><p>{number(data.ombudsman.quality?.unmapped_rows||0)} registros estaduais sem vínculo municipal ficaram fora das contagens locais.</p>{data.ombudsman.source_url&&<External url={data.ombudsman.source_url}>Fonte estadual</External>}</>:<p>Não há base estadual importada para este município.</p>}<hr/><h3>Fala.BR e Painel Resolveu?</h3><p>{data.falabr.notes}</p><External url={data.falabr.public_dashboard_url}>Abrir Painel Resolveu? da CGU <ExternalLink size={14}/></External></section>}
 </>}
 </>;
}
