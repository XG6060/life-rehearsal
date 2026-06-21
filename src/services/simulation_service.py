"""模拟服务 — 编排完整模拟流程

1. 人格测评计分 → BigFive
2. 两条路径（A/B）各跑一次 SimulatorEngine
3. 构建 EmotionalCurve
4. 包装为 SimulationResult
"""

from __future__ import annotations

import time
from typing import Optional

from src.core.simulator.curve_builder import build_emotional_curve
from src.core.simulator.engine import SimulatorEngine
from src.llm.client import get_llm_client
from src.models.decision import Decision
from src.models.simulation import SimulationResult, SimulationStatus
from src.models.user import BigFive
from src.utils.logger import logger


class SimulationService:
    """模拟服务 — 编排完整模拟流程"""

    def __init__(self):
        llm = get_llm_client()
        self.engine = SimulatorEngine(llm_client=llm)

    def run(
        self,
        decision: Decision,
        big_five: BigFive,
        option_labels: list[str] | None = None,
        total_weeks: int = 12,
    ) -> SimulationResult:
        """运行完整模拟（每个选项各跑 12 周）

        Args:
            decision: 用户的决策信息
            big_five: 大五人格
            option_labels: 各选项标签（从 decision 提取或手动传入）
            total_weeks: 模拟总周数

        Returns:
            SimulationResult — 完整的模拟结果
        """
        labels = option_labels or self._extract_labels(decision)
        start = time.time()
        self.engine.llm.start_tracking()
        result = SimulationResult(
            decision_id=decision.id,
            decision_title=decision.title,
            big_five=big_five,
            option_labels=labels,
            status=SimulationStatus.RUNNING,
        )

        try:
            for i, label in enumerate(labels):
                logger.info(f"Simulating option {i + 1}/{len(labels)}: {label}")
                state = self.engine.simulate(
                    decision=decision,
                    option_label=label,
                    big_five=big_five,
                    total_weeks=total_weeks,
                )
                result.states.append(state)
                result.curves.append(build_emotional_curve(state.timeline))
                logger.info(f"Option {i + 1} completed: {len(state.timeline)} weeks")

            result.status = SimulationStatus.COMPLETED

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            result.status = SimulationStatus.FAILED

        token_info = self.engine.llm.stop_tracking()
        self.token_info = token_info  # store for retrieval
        result.timing_ms = int((time.time() - start) * 1000)
        logger.info(f"Simulation complete in {result.timing_ms}ms")
        return result

    @staticmethod
    def _extract_labels(decision: Decision) -> list[str]:
        """从 Decision 中提取选项标签"""
        if decision.options:
            return [o.label for o in decision.options]
        return ["选项 A", "选项 B"]
