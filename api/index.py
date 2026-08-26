import os
import sys
from pathlib import Path

# Add project root to sys.path so 'apps' and 'core' packages can be imported
PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
    if Path(__file__).resolve().parent.name == 'api'
    else Path(__file__).resolve().parent
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.main import app
