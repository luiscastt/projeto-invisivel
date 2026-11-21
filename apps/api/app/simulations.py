from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import get_db, uid, now
from .models import Issue, Simulation
from .schemas import SimulationInput
from .territories import municipality
from .issues import issue_json
from .algorithms import allocate

router = APIRouter(tags=["Simulações"])
DISCLAIMER = "Resultado hipotético. Não representa uma previsão oficial nem substitui estudos técnicos. Nenhum problema real foi alterado."


@router.get("/interventions")
def interventions():
    return [{"id": "infrastructure", "name": "Intervenção genérica em infraestrutura urbana", "category": "infrastructure", "unit": "problema", "default_unit_cost": 1500, "assumption": "Custo hipotético editável e igual por registro para exercício educativo; não é cotação, SINAPI ou orçamento de obra."}]


@router.post("/simulations", status_code=201)
def simulate(body: SimulationInput, request: Request, db: Session = Depends(get_db, scope="function")):
    municipality(request, body.municipality_code)
    candidates = [issue_json(db, i, request) for i in db.scalars(select(Issue).where(Issue.municipality_code == body.municipality_code, Issue.category == body.category, Issue.is_demo == body.demo, Issue.merged_into.is_(None), Issue.operational_status != "verified_resolved"))]
    allocation = allocate(candidates, body.budget, body.unit_cost, body.strategy)
    id_ = uid()
    result = {"id": id_, **body.model_dump(mode="json"), "budget": float(body.budget), "unit_cost": float(body.unit_cost), **allocation, "issues": [next(i for i in candidates if i["id"] == id_) for id_ in allocation["issue_ids"]], "created_at": now(), "disclaimer": DISCLAIMER, "assumptions": ["Custo unitário igual e hipotético para cada problema; uma intervenção por registro.", "Capacidade = parte inteira do orçamento dividido pelo custo unitário; valores calculados em centavos.", "A quantidade selecionada é limitada aos problemas publicados nesta categoria e município.", "Estratégia prioridade: sem dados verificados suficientes para um índice, usa ordem estável por identificador; não representa prioridade oficial.", "Relatos contam contribuições revisadas, não pessoas afetadas nem comprovação de verdade.", "Não são estimadas melhorias causais em indicadores sociais, nem população beneficiada."]}
    db.add(Simulation(id=id_, result=result))
    return result


@router.get("/simulations/{scenario_id}")
def scenario(scenario_id: str, db: Session = Depends(get_db, scope="function")):
    item = db.get(Simulation, scenario_id)
    if item is None:
        raise HTTPException(404, "Cenário não encontrado.")
    return item.result
