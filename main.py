import uvicorn
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    print('=' * 65)
    print('  FACT KNOWLEDGE LAYER (Superjoin VIT 2026 Hiring Challenge)  ')
    print('=' * 65)
    print('Starting web server on http://localhost:8000 ...')
    print('Open your browser and navigate to: http://localhost:8000')
    print('Interactive API docs available at: http://localhost:8000/docs')
    print('=' * 65)
    uvicorn.run('backend.app:app', host='127.0.0.1', port=8000, reload=False)
