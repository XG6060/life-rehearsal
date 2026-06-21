"""决策分析 API 路由

Phase 0 实现：同步分析，后续可改为异步任务队列。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.models.decision import Decision, DecisionCreate, DecisionResponse, Option, Factor
from src.models.report import ReportResponse
from src.services.decision_service import DecisionService

router = APIRouter(prefix="/api/v1", tags=["analyze"])


class AnalyzeResponse(BaseModel):
    """完整分析响应"""
    decision_id: str
    report_id: str
    narrative_text: str
    llm_stats: dict
    timing_ms: int


@router.post("/analyze", response_model=AnalyzeResponse)
async def create_analysis(input_data: DecisionCreate):
    """创建决策分析 — 同步执行"""
    service = DecisionService()
    result = service.analyze_from_input(input_data)

    return AnalyzeResponse(
        decision_id=result.report.decision_id,
        report_id=result.report.id,
        narrative_text=result.narrative_text,
        llm_stats=result.llm_stats,
        timing_ms=result.timing_ms,
    )


@router.get("/analyze/{decision_id}")
async def get_analysis(decision_id: str):
    """获取已有分析结果（功能开发中）"""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/analyze/history")
async def list_history(limit: int = 10):
    """获取分析历史列表（功能开发中）"""
    raise HTTPException(status_code=501, detail="Not implemented yet")
