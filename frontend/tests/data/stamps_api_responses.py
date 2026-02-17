"""
Test data for StampsService API responses.
"""

# Years API response
YEARS_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {"year": 1850},
        {"year": 1851},
        {"year": 1852},
        {"year": 1950},
        {"year": 1951},
        {"year": 2020},
        {"year": 2021},
        {"year": 2022},
        {"year": 2023},
        {"year": 2024}
    ]
}

# Issues API response
ISSUES_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {
            "id": 1,
            "country": "Spain",
            "date": "1950-01-01",
            "name": "Test Series 1",
            "perforation": "12.5",
            "stamp_type": "Definitive",
            "print_type": "Lithography",
            "total_printed": 100000,
            "market_value": 25.50,
            "description": "Test description",
            "note": "Test note"
        },
        {
            "id": 2,
            "country": "France",
            "date": "1951-03-15",
            "name": "Test Series 2",
            "perforation": "14",
            "stamp_type": "Commemorative",
            "print_type": "Engraving",
            "total_printed": 50000,
            "market_value": 15.75,
            "description": "Another test description",
            "note": "Another test note"
        }
    ]
}

# Print Types API response
PRINT_TYPES_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {"name": "Lithography"},
        {"name": "Engraving"},
        {"name": "Photogravure"},
        {"name": "Offset"},
        {"name": "Letterpress"}
    ]
}

# Stamp Types API response
STAMP_TYPES_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {"name": "Definitive"},
        {"name": "Commemorative"},
        {"name": "Postage Due"},
        {"name": "Airmail"},
        {"name": "Revenue"}
    ]
}

# Stamps API response
STAMPS_RESPONSE_200_SUCCESS = {
    "success": True,
    "data": [
        {
            "id": 101,
            "issue_id": 1,
            "name": "Stamp 1",
            "edifil_code": "1234",
            "face_value": "0.05",
            "market_value": 12.50,
            "colors": ["Red", "Blue"],
            "image": "stamps/101.jpg"
        },
        {
            "id": 102,
            "issue_id": 1,
            "name": "Stamp 2",
            "edifil_code": "1235",
            "face_value": "0.10",
            "market_value": 8.25,
            "colors": ["Green"],
            "image": "stamps/102.jpg"
        },
        {
            "id": 103,
            "issue_id": 1,
            "name": "Stamp 3",
            "edifil_code": "1236",
            "face_value": "0.25",
            "market_value": 25.00,
            "colors": ["Purple", "Yellow"],
            "image": "stamps/103.jpg"
        }
    ]
}

SERIES_EXTRACTION_RESPONSE_200_SUCCESS = {
    "success": True,
    "message": "Request successful",
    "errors": None,
    "data": {
        "issue_name": "Forjadores de América",
        "description": "La serie \"Forjadores de América\", emitida en 1967, rinde homenaje a los exploradores y navegantes españoles que desempeñaron un papel crucial en el descubrimiento, exploración y cartografía de la costa noroeste del Pacífico de América durante el siglo XVIII. Esta emisión filatélica destaca la significativa contribución de España al conocimiento geográfico de regiones que hoy forman parte de Canadá y Estados Unidos, como Nutka, California y Alaska. A través de retratos de marinos ilustres y representaciones de lugares clave, la serie busca conmemorar la audacia y el legado de aquellos que expandieron las fronteras del conocimiento y la influencia española en el Nuevo Mundo.",
        "issue_date": "1967-10-12",
        "artist": "n/a",
        "printer": "Fábrica Nacional de Moneda y Timbre",
        "print_type": "Huecograbado",
        "perforation": "12 3/4",
        "paper_type": "n/a",
        "stamp_type": "Sello",
        "notes": "Esta serie conmemora la exploración española del Pacífico Norte, un tema de gran relevancia histórica pero con una tirada elevada para la época, lo que la hace accesible para los coleccionistas.",
        "total_printed": 6000000,
        "market_value_mnh": 7,
        "market_value_used": 3,
        "stamps": [
            {
                "edifil_code": "1819",
                "motive": "J. Francisco de la Bodega",
                "face_value": "40 cts",
                "description": "Juan Francisco de la Bodega y Quadra (Lima, 1743 - San Blas de California, 1794) fue un marino español de origen criollo. Participó en varias expediciones a la costa americana del Pacífico norte, desde la Alta California hasta Alaska, siendo uno de los exploradores más importantes de la región. Sus viajes contribuyeron significativamente al conocimiento geográfico y a la reclamación española de estos territorios, estableciendo contactos con las poblaciones indígenas y cartografiando extensas áreas desconocidas.",
                "amount_printed": 5000000,
                "color": "oliva y salmón",
                "market_value_mnh": 0.5,
                "market_value_used": 0.2
            },
            {
                "edifil_code": "1820",
                "motive": "Costa de Nutka",
                "face_value": "50 cts",
                "description": "La isla de Nutka (también escrito Nootka o Nuca) se encuentra separada de la Isla de Vancouver en Columbia Británica (Canadá) por el Estrecho de Nutka. Este estrecho fue un punto estratégico clave en las exploraciones españolas del Pacífico Norte. La región de Nutka fue escenario de importantes disputas territoriales entre España y Gran Bretaña a finales del siglo XVIII, que culminaron en las Convenciones de Nutka, estableciendo los derechos de navegación y asentamiento en la zona y marcando un hito en la diplomacia internacional de la época.",
                "amount_printed": 6000000,
                "color": "castaño y azul",
                "market_value_mnh": 0.5,
                "market_value_used": 0.2
            },
            {
                "edifil_code": "1821",
                "motive": "Francisco Antonio Mourelle",
                "face_value": "1 pta",
                "description": "Francisco Antonio Mourelle de la Rúa (La Coruña, 1750 - Cádiz, 1820) fue un destacado navegante y explorador español del siglo XVIII. Desde joven, sintió la llamada del mar y, a pesar de su origen humilde, se unió a la Armada. Participó en varias expediciones cruciales al Pacífico Norte, incluyendo la de 1775 con Bodega y Quadra, explorando las costas de Alaska y la Columbia Británica. Sus detallados mapas y diarios fueron fundamentales para el conocimiento geográfico de la región y para las reclamaciones españolas, siendo reconocido por su pericia náutica.",
                "amount_printed": 6000000,
                "color": "rojo y azul",
                "market_value_mnh": 0.6,
                "market_value_used": 0.25
            },
            {
                "edifil_code": "1822",
                "motive": "Poblado de Nutka",
                "face_value": "1,20 pta",
                "description": "El 5 de mayo de 1789, el navegante sevillano Esteban José Martínez, al mando de las naves 'Princesa' y 'San Carlos', tomó posesión de la Ensenada de Nutka, cuyo territorio pasó a formar parte del Virreinato de Nueva España. Este acto fue un hito en la presencia española en el Pacífico Norte y llevó a la construcción del Fuerte de San Miguel, el primer asentamiento europeo en la actual Columbia Británica. La imagen representa un poblado indígena de la zona, reflejando la interacción cultural y la vida en la costa del Pacífico en el momento de la llegada de los exploradores españoles.",
                "amount_printed": 6000000,
                "color": "pizarra y amarillo",
                "market_value_mnh": 0.6,
                "market_value_used": 0.25
            },
            {
                "edifil_code": "1823",
                "motive": "Esteban J. Martínez",
                "face_value": "1,50 pta",
                "description": "Esteban José Martínez Fernández de la Sierra (Sevilla, 1742 - San Blas, 1798) fue un marino y explorador español. Estudió pilotaje en el Colegio de San Telmo de Sevilla y se unió a la Armada. En 1773 fue nombrado segundo piloto y participó en numerosas expediciones a la costa del Pacífico Norte. Su expedición de 1789 a Nutka fue crucial, estableciendo una base española y desencadenando la 'Crisis de Nutka' con Gran Bretaña, un conflicto diplomático sobre la soberanía de la región que tuvo repercusiones internacionales.",
                "amount_printed": 6000000,
                "color": "verde y amarillo claro",
                "market_value_mnh": 0.7,
                "market_value_used": 0.3
            },
            {
                "edifil_code": "1824",
                "motive": "Costa de California",
                "face_value": "3 pta",
                "color": "negro grisáceo y amarillo",
                "description": "Los primeros exploradores europeos, enarbolando las banderas de España y de Inglaterra, navegaron a lo largo de la costa de California desde principios del siglo XVII hasta mediados del XVIII. Sin embargo, la presencia española fue predominante, estableciendo misiones y presidios a lo largo de la Alta California. Esta estampilla conmemora la exploración y el establecimiento de la soberanía española en esta vasta región, que formó parte del Virreinato de Nueva España antes de pasar a México y, finalmente, a Estados Unidos, dejando una profunda huella cultural y arquitectónica.",
                "amount_printed": 6000000,
                "market_value_mnh": 1,
                "market_value_used": 0.4
            },
            {
                "edifil_code": "1825",
                "motive": "Cayetano Valdés",
                "face_value": "3,50 pta",
                "color": "azul y salmón",
                "description": "Cayetano Valdés y Flores Bazán y Peón (Sevilla, 1767 - San Fernando, Cádiz, 1835) fue un distinguido marino y explorador español, llegando a ser Capitán General de la Real Armada Española. Participó en la expedición de Alejandro Malaspina (1789-1794) que exploró y cartografió extensamente las costas del Pacífico, incluyendo la costa noroeste de América. También tuvo una destacada participación en la Batalla del Cabo de San Vicente y en la Batalla de Trafalgar, demostrando su valía tanto en la exploración científica como en el combate naval, siendo una figura polifacética de la marina española.",
                "amount_printed": 6000000,
                "market_value_mnh": 1,
                "market_value_used": 0.4
            },
            {
                "edifil_code": "1826",
                "motive": "San Elías, Alaska",
                "face_value": "6 pta",
                "color": "castaño rojizo y azul",
                "description": "En 1779, Antonio Mourelle de la Rúa se embarcó en la fragata 'Favorita' como segundo oficial, bajo el mando de Juan Francisco de la Bodega y Quadra. Su misión era alcanzar la máxima latitud posible en las costas del Pacífico Norte. Durante esta expedición, avistaron y cartografiaron el Monte San Elías en la actual Alaska, un hito geográfico significativo que marcó el punto más septentrional de la exploración española en la región. Esta estampilla rinde homenaje a las audaces exploraciones españolas que extendieron el conocimiento geográfico hasta las remotas regiones de Alaska, contribuyendo a la cartografía mundial.",
                "amount_printed": 6000000,
                "market_value_mnh": 1.2,
                "market_value_used": 0.5
            }
        ]
    }
}