"""
Nichos comerciais baseados em categorias do Google Business
e classificações comerciais padrão
"""

# Mapeamento de nichos para tags OSM
NICHOS_COMERCIAIS = {
    "Saúde e Bem-estar": {
        "categorias": [
            "Clínicas médicas",
            "Consultórios odontológicos",
            "Farmácias",
            "Laboratórios",
            "Hospitais",
            "Fisioterapia",
            "Psicologia",
            "Nutrição",
            "Academias",
            "Pilates e yoga",
            "Estética e spa",
            "Clínicas veterinárias",
        ],
        "tags_osm": ["amenity=clinic", "amenity=doctors", "amenity=dentist", 
                     "amenity=pharmacy", "amenity=hospital", "leisure=fitness_centre",
                     "amenity=veterinary"]
    },
    
    "Alimentação": {
        "categorias": [
            "Restaurantes",
            "Cafeterias",
            "Lanchonetes e fast-food",
            "Pizzarias",
            "Padarias",
            "Bares e pubs",
            "Sorveterias",
            "Confeitarias",
            "Açougues",
            "Hortifruti",
            "Distribuidoras de alimentos",
        ],
        "tags_osm": ["amenity=restaurant", "amenity=cafe", "amenity=fast_food",
                     "amenity=bar", "shop=bakery", "shop=butcher", "shop=greengrocer"]
    },
    
    "Educação": {
        "categorias": [
            "Escolas",
            "Cursos profissionalizantes",
            "Escolas de idiomas",
            "Cursos preparatórios",
            "Universidades",
            "Escolas de música",
            "Escolas de dança",
            "Auto escolas",
        ],
        "tags_osm": ["amenity=school", "amenity=college", "amenity=university",
                     "amenity=language_school", "amenity=music_school", "amenity=driving_school"]
    },
    
    "Serviços Profissionais": {
        "categorias": [
            "Escritórios de advocacia",
            "Contabilidade",
            "Arquitetura",
            "Engenharia",
            "Imobiliárias",
            "Seguros",
            "Consultorias",
            "Marketing e publicidade",
            "Design e criação",
            "TI e desenvolvimento",
        ],
        "tags_osm": ["office=lawyer", "office=accountant", "office=architect",
                     "office=engineer", "office=estate_agent", "office=insurance",
                     "office=it"]
    },
    
    "Beleza e Estética": {
        "categorias": [
            "Salões de beleza",
            "Barbearias",
            "Clínicas de estética",
            "Manicure e pedicure",
            "Depilação",
            "Sobrancelhas",
            "Clínicas de emagrecimento",
        ],
        "tags_osm": ["shop=beauty", "shop=hairdresser", "shop=beauty_salon"]
    },
    
    "Varejo e Comércio": {
        "categorias": [
            "Lojas de roupas",
            "Calçados",
            "Joias e acessórios",
            "Eletrônicos",
            "Móveis e decoração",
            "Materiais de construção",
            "Autopeças",
            "Farmácias",
            "Livrarias",
            "Pet shops",
            "Lojas de presentes",
        ],
        "tags_osm": ["shop=clothes", "shop=shoes", "shop=jewelry", "shop=electronics",
                     "shop=furniture", "shop=hardware", "shop=car_parts", "shop=books",
                     "shop=pet", "shop=gift"]
    },
    
    "Automotivo": {
        "categorias": [
            "Oficinas mecânicas",
            "Concessionárias",
            "Lava-jatos",
            "Autopeças",
            "Funilaria e pintura",
            "Auto elétricas",
            "Borracharias",
        ],
        "tags_osm": ["shop=car_repair", "shop=car", "amenity=car_wash",
                     "shop=car_parts", "shop=tyres"]
    },
    
    "Entretenimento e Lazer": {
        "categorias": [
            "Cinemas",
            "Teatros",
            "Eventos e festas",
            "Parques e recreação",
            "Clubes",
            "Casas de show",
            "Boates",
        ],
        "tags_osm": ["amenity=cinema", "amenity=theatre", "amenity=nightclub",
                     "leisure=park"]
    },
    
    "Hotelaria e Turismo": {
        "categorias": [
            "Hotéis",
            "Pousadas",
            "Hostels",
            "Agências de viagem",
            "Aluguel de veículos",
            "Guias turísticos",
        ],
        "tags_osm": ["tourism=hotel", "tourism=hostel", "tourism=guest_house",
                     "shop=travel_agency", "amenity=car_rental"]
    },
    
    "Casa e Construção": {
        "categorias": [
            "Materiais de construção",
            "Móveis planejados",
            "Marcenarias",
            "Serralheria",
            "Vidraçarias",
            "Pintores",
            "Eletricistas",
            "Encanadores",
            "Arquitetura",
        ],
        "tags_osm": ["shop=hardware", "shop=furniture", "craft=carpenter",
                     "craft=painter", "craft=plumber"]
    },
    
    "Tecnologia": {
        "categorias": [
            "Assistência técnica",
            "Lojas de informática",
            "Desenvolvimento de software",
            "Consultoria em TI",
            "Segurança eletrônica",
        ],
        "tags_osm": ["shop=computer", "shop=electronics", "office=it"]
    },
    
    "Finanças": {
        "categorias": [
            "Bancos",
            "Cooperativas de crédito",
            "Seguradoras",
            "Corretoras",
            "Casas de câmbio",
        ],
        "tags_osm": ["amenity=bank", "office=financial", "office=insurance",
                     "amenity=bureau_de_change"]
    },
}


def obter_todos_nichos():
    """Retorna lista de todos os nichos principais"""
    return list(NICHOS_COMERCIAIS.keys())


def obter_categorias_nicho(nicho):
    """Retorna categorias específicas de um nicho"""
    return NICHOS_COMERCIAIS.get(nicho, {}).get("categorias", [])


def obter_tags_osm_nicho(nicho):
    """Retorna tags OSM para busca de um nicho"""
    return NICHOS_COMERCIAIS.get(nicho, {}).get("tags_osm", [])


def obter_todas_categorias():
    """Retorna todas as categorias de todos os nichos"""
    todas = []
    for nicho_data in NICHOS_COMERCIAIS.values():
        todas.extend(nicho_data["categorias"])
    return sorted(todas)
