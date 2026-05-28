import sys
import os

# Adiciona o diretório raiz ao path do Python para que as importações funcionem no Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
