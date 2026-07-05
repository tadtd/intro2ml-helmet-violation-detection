import sys
import pathlib

# Add this directory to sys.path so that absolute imports of generated files resolve correctly
proto_dir = str(pathlib.Path(__file__).parent.resolve())
if proto_dir not in sys.path:
    sys.path.insert(0, proto_dir)
