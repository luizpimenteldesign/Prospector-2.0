"""
Módulo para buscar dados de localidades do IBGE
API pública e gratuita: https://servicodados.ibge.gov.br/api/docs/localidades
"""

import requests
import streamlit as st
from typing import List, Dict

@st.cache_data(ttl=86400)  # Cache por 24 horas
def buscar_estados() -> List[Dict]:
    """Retorna lista de todos os estados brasileiros"""
    try:
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
        response = requests.get(url, timeout=10)
        estados = response.json()
        
        # Ordena por sigla
        estados_ordenados = sorted(estados, key=lambda x: x['sigla'])
        
        return [
            {
                'id': estado['id'],
                'sigla': estado['sigla'],
                'nome': estado['nome']
            }
            for estado in estados_ordenados
        ]
    except Exception as e:
        st.error(f"Erro ao buscar estados: {e}")
        return []


@st.cache_data(ttl=86400)
def buscar_cidades_por_estado(uf: str) -> List[str]:
    """Retorna lista de cidades de um estado específico"""
    try:
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
        response = requests.get(url, timeout=10)
        municipios = response.json()
        
        # Retorna apenas os nomes, ordenados
        cidades = sorted([m['nome'] for m in municipios])
        return cidades
    except Exception as e:
        st.error(f"Erro ao buscar cidades: {e}")
        return []


@st.cache_data(ttl=86400)
def buscar_todas_cidades() -> List[Dict]:
    """Retorna todas as cidades do Brasil com suas UFs"""
    try:
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
        response = requests.get(url, timeout=15)
        municipios = response.json()
        
        return [
            {
                'nome': m['nome'],
                'uf': m['microrregiao']['mesorregiao']['UF']['sigla']
            }
            for m in municipios
        ]
    except Exception as e:
        st.error(f"Erro ao buscar todas as cidades: {e}")
        return []
