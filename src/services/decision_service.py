"""决策分析服务 — 编排分析全流程

协调以下模块完成一次完整的决策分析：
1. Deconstructor — 拆解决策树
2. BiasDetector — 检测认知偏误
3. StyleClassifier — 分类决策风格
4. Questioner — 生成追问
5. ReportBuilder — 组装报告
"""

from __future__ import annotations

import time
from typing import Optional

from pydantic import BaseModel

from src.core.analyzer.bias_detector import BiasDetector
from src.core.analyzer.deconstructor import Deconstructor
from src.core.analyzer.questioner import Questioner
from src.core.analyzer.style_classifier import StyleClassifier
from src.core.report.builder import ReportBuilder
from src.llm.client import get_llm_client
from src.models.decision import Decision, DecisionCreate
from src.models.report import AnalysisReport
from src.models.user import DecisionStyle, UserProfile
from src.utils.logger import logger


class AnalysisResult(BaseModel):
    """一次完整分析的结果"""
    report: AnalysisReport
    narrative_text: str
    llm_stats: dict
    timing_ms: int


class DecisionService:
    """决策分析服务 — 编排完整分析流程"""

    def __init__(self):
        llm = get_llm_client()
        self.deconstructor = Deconstructor(llm_client=llm)
        self.bias_detector = BiasDetector(llm_client=llm)
        self.style_classifier = StyleClassifier(llm_client=llm)
        self.questioner = Questioner(llm_client=llm)
        self.report_builder = ReportBuilder(llm_client=llm)
        self.llm = llm

    def analyze(self, decision: Decision) -> AnalysisResult:
        """执行完整的决策分析 Pipeline

        流程：
        1. 拆解决策树
        2. 检测认知偏误（LLM + 规则双重检测）
        3. 分类决策风格
        4. 生成追问
        5. 构建结构化报告
        6. 生成叙事化报告文本
        """
        start = time.time()
        self.llm.start_tracking()

        # Step 1: 决策树拆解
        logger.info(f"Step 1/5: Deconstructing decision tree for {decision.id}")
        tree, tree_response = self.deconstructor.deconstruct(decision)
        if tree:
            decision.decision_tree = tree
            tree_summary = tree.root_question
            # 如果用户没有手动填选项，用 LLM 提取的选项
            if not decision.options:
                decision.options = tree.options
        else:
            tree_summary = decision.title

        # Step 2: 偏误检测（LLM + 规则）
        logger.info(f"Step 2/5: Detecting cognitive biases")
        llm_biases, bias_response = self.bias_detector.detect(decision)
        rule_biases = self.bias_detector.detect_with_rule(decision)

        # 合并偏误，按严重度排序，去重
        all_biases = llm_biases + rule_biases
        seen_types = set()
        unique_biases = []
        for b in all_biases:
            if b.bias_type not in seen_types:
                seen_types.add(b.bias_type)
                unique_biases.append(b)
            else:
                # 如果已存在同类型偏误，保留严重度更高的
                for existing in unique_biases:
                    if existing.bias_type == b.bias_type and b.severity > existing.severity:
                        existing.severity = b.severity
                        existing.explanation = b.explanation
                        existing.suggestion = b.suggestion
        unique_biases.sort(key=lambda b: b.severity, reverse=True)

        # Step 3: 风格分类
        logger.info(f"Step 3/5: Classifying decision style")
        style_analysis, _ = self.style_classifier.classify(
            title=decision.title,
            context=decision.context,
            age_range=getattr(decision, 'age_range', ""),
            occupation=getattr(decision, 'occupation_category', ""),
            city=getattr(decision, 'city_tier', ""),
        )

        # Step 4: 生成追问
        logger.info(f"Step 4/5: Generating questions")
        questions, _ = self.questioner.generate(
            decision=decision,
            biases=unique_biases,
        )

        # Step 5: 构建报告
        logger.info(f"Step 5/5: Building report")
        report = self.report_builder.build(
            decision=decision,
            tree_summary=tree_summary,
            biases=unique_biases,
            style=style_analysis,
            questions=questions,
        )

        # Step 6: 生成叙事化报告文本
        narrative = self.report_builder.build_narrative_report(
            decision=decision,
            report=report,
        )

        elapsed = int((time.time() - start) * 1000)
        logger.info(f"Analysis complete in {elapsed}ms — "
                    f"biases={len(unique_biases)}, "
                    f"questions={len(questions)}, "
                    f"style={style_analysis.style if style_analysis else 'unknown'}")

        token_info = self.llm.stop_tracking()
        return AnalysisResult(
            report=report,
            narrative_text=narrative,
            llm_stats={**self.llm.get_stats(), **token_info},
            timing_ms=elapsed,
        )

    def analyze_from_input(self, input_data: DecisionCreate) -> AnalysisResult:
        """从 API 输入数据创建 Decision 并执行分析"""
        # 创建决策对象
        options = []
        for opt in (input_data.options or []):
            options.append(type("Option", (), {
                "label": opt.get("label", "选项"),
                "description": opt.get("description", ""),
                "pros": opt.get("pros", []),
                "cons": opt.get("cons", []),
            })())

        factors = []
        for fac in (input_data.factors or []):
            factors.append(type("Factor", (), {
                "name": fac.get("name", ""),
                "importance": float(fac.get("importance", 0.5)),
                "uncertainty": float(fac.get("uncertainty", 0.5)),
            })())

        decision = Decision(
            title=input_data.title,
            category=input_data.category,
            context=input_data.context,
            options=options,
            factors=factors,
            age_range=input_data.age_range,
            occupation_category=input_data.occupation_category,
            city_tier=input_data.city_tier,
        )

        return self.analyze(decision)

    def get_llm_stats(self) -> dict:
        """获取 LLM 使用统计"""
        return self.llm.get_stats()
