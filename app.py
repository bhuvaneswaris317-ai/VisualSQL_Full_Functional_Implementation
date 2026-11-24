import os
import sys

# Automatically route execution into the VisualSQL project directory
project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VisualSQL")
os.chdir(project_dir)
sys.path.insert(0, project_dir)

import app

if __name__ == "__main__":
    app.app.run(host="127.0.0.1", port=5000, debug=False)
