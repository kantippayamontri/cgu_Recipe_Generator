"""Pytest configuration for test suite."""
import sys
from pathlib import Path

# Add project root to Python path for imports
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
