"""人格测评逻辑测试"""

import pytest
from src.core.simulator.personality_quiz import get_questions, score


class TestPersonalityQuiz:
    def test_all_dimensions_covered(self):
        """12 题覆盖所有 5 个维度"""
        questions = get_questions()
        dims = {q.dimension for q in questions}
        assert dims == {"O", "C", "E", "A", "N"}

    def test_each_dimension_at_least_2(self):
        """每维度至少 2 题"""
        questions = get_questions()
        for dim in ["O", "C", "E", "A", "N"]:
            count = sum(1 for q in questions if q.dimension == dim)
            assert count >= 2, f"{dim} 只有 {count} 题"

    def test_exactly_12_questions(self):
        assert len(get_questions()) == 12

    def test_all_middle_answers(self):
        """全答 4（中立）→ 所有维度约 0.5"""
        bf = score([4] * 12)
        for val in [bf.openness, bf.conscientiousness, bf.extraversion,
                     bf.agreeableness, bf.neuroticism]:
            assert 0.45 <= val <= 0.55

    def test_all_max_scores(self):
        """全答 7（非常同意）"""
        bf = score([7] * 12)
        # 反向题答 7 → 0.0
        assert bf.openness <= 0.67  # 3 题中 2 正 1 反
        assert bf.neuroticism <= 0.67  # 3 题中 2 正 1 反

    def test_all_min_scores(self):
        """全答 1（非常不同意）"""
        bf = score([1] * 12)
        # 反向题答 1 → 1.0
        assert bf.openness >= 0.33  # 3 题中 2 正 1 反
        assert bf.neuroticism >= 0.33

    def test_score_range(self):
        """所有维度得分在 0-1 范围"""
        bf = score([7] * 12)
        for val in [bf.openness, bf.conscientiousness, bf.extraversion,
                     bf.agreeableness, bf.neuroticism]:
            assert 0 <= val <= 1

    def test_wrong_answer_count(self):
        """答案数量不对应报错"""
        with pytest.raises(ValueError):
            score([1, 2, 3])  # 只有 3 个答案

    def test_answer_out_of_range(self):
        """答案超出 1-7 报错"""
        with pytest.raises(ValueError):
            score([8] * 12)
