"""Run once: python -m app.seed_demo_registry. Uses entirely synthetic records."""
from app.database import initialize, backend_mode
from app.demo_registry import seed
if __name__ == '__main__':
    initialize()
    print(f'Added {seed()} fictional land records into {backend_mode()} demo database.')
