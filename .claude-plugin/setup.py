#!/usr/bin/env python3
"""Setup script for opticode plugin - downloads model if needed."""
from pathlib import Path
import sys

PLUGIN_ROOT = Path(__file__).parent
sys.path.insert(0, str(PLUGIN_ROOT / "src"))

def setup():
    """Download model if not present."""
    from opticode.intent_model import TinyIntentModel
    
    model = TinyIntentModel()
    status = model.get_model_status()
    
    if status["available"]:
        print(f"✓ Model already available: {status['model_file']}")
        return 0
    else:
        print("Model not found. Downloading...")
        print(f"Download URL: {status['download_url']}")
        print(f"Target: {status['model_file']}")
        print("\nRun this command to download:")
        print(f"mkdir -p ~/.opticode/models && curl -L -o ~/.opticode/models/{status['model_name']} '{status['download_url']}'")
        return 1

if __name__ == "__main__":
    raise SystemExit(setup())
