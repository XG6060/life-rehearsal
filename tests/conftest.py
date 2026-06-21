"""pytest 配置：确保 src/ 和 config/ 可导入"""

import sys
from pathlib import Path

# 把项目根目录加到 sys.path，让 tests/ 里的 import 能找到 src/ 和 config/
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
