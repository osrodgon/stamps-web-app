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

# Issues Extraction API - Success Response
ISSUES_EXTRACTION_RESPONSE_200_SUCCESS = {
  "success": True,
  "message": "Request successful",
  "errors": None,
  "data": {
    "issue_name": "Paisajes y Monumentos",
    "description": "La serie 'Paisajes y Monumentos' de 1967 forma parte de una de las emisiones definitivas más longevas y populares de la filatelia española, dedicada a la riqueza cultural, arquitectónica y natural de España. Esta emisión en particular, lanzada el 26 de julio de 1967, coincidió con el 'Año Internacional del Turismo', un evento promovido por las Naciones Unidas, lo que se refleja en uno de los motivos de la serie. El objetivo principal de estas emisiones era promover el turismo y el conocimiento del patrimonio español, así como cubrir las necesidades postales del país. Los sellos, impresos mediante la técnica de huecograbado por la Fábrica Nacional de Moneda y Timbre, presentan una variedad de paisajes, monumentos históricos y tradiciones culturales, destacando la diversidad geográfica y cultural de España.",
    "issue_date": "1967-07-26",
    "artist": "n/a",
    "printer": "Fábrica Nacional de Moneda y Timbre",
    "print_type": "Huecograbado",
    "perforation": "13 1/4",
    "paper_type": "Estucado",
    "stamp_type": "Correo ordinario",
    "notes": "Esta serie, con una tirada muy elevada, es común en el mercado filatélico. Destaca la inclusión de un sello conmemorativo del 'Año Internacional del Turismo' de 1967, que le otorga un contexto histórico particular dentro de la serie general de 'Paisajes y Monumentos'. No se conocen errores significativos en esta emisión.",
    "total_printed": 10000000,
    "market_value_mnh": 3.5,
    "market_value_used": 1.5,
    "stamps": [
      {
        "edifil_code": "1802",
        "fesofi_code": "1802",
        "motive": "Betanzos (La Coruña)",
        "face_value": "10 cts",
        "description": "La Iglesia de San Francisco en Betanzos (La Coruña) es un magnífico ejemplo del gótico mendicante gallego. Su construcción se inició en 1387 bajo el patrocinio del Conde D. Fernán Pérez de Andrade 'O Bo'. Tras la desamortización del siglo XIX, el convento franciscano quedó abandonado, aunque la iglesia ha sido restaurada y es hoy uno de los monumentos más emblemáticos de la ciudad, destacando por sus sepulcros góticos y su rosetón.",
        "amount_printed": 10000000,
        "color": "azul y negro",
        "market_value_mnh": 0.2,
        "market_value_used": 0.1
      },
      {
        "edifil_code": "1803",
        "fesofi_code": "1803",
        "motive": "Torre San Miguel (Palencia)",
        "face_value": "1 pta",
        "description": "La Torre de la Iglesia de San Miguel es uno de los símbolos más reconocibles de Palencia. Esta imponente torre, de estilo románico de transición al gótico, data del siglo XIII y se caracteriza por su estructura calada y su robustez. Se cree que pudo tener un uso defensivo además del religioso. La iglesia, declarada Bien de Interés Cultural, es famosa por su leyenda de la boda del Cid Campeador.",
        "amount_printed": 10000000,
        "color": "pizarra y azul",
        "market_value_mnh": 0.3,
        "market_value_used": 0.15
      },
      {
        "edifil_code": "1804",
        "fesofi_code": "1804",
        "motive": "Castellers",
        "face_value": "1,50 pta",
        "description": "Los 'castells', o torres humanas, son una tradición cultural única de Cataluña, reconocida como Patrimonio Cultural Inmaterial de la Humanidad por la UNESCO. Su origen se remonta a las Fiestas Decenales de la Candela de Valls en 1791, evolucionando a partir de los 'ball de valencians'. Los castillos humanos se construyen por 'colles castelleres' y varían en altura y complejidad, simbolizando la fuerza, el equilibrio, el valor y la cordura de la comunidad.",
        "amount_printed": 10000000,
        "color": "pizarra y ocre",
        "market_value_mnh": 0.3,
        "market_value_used": 0.15
      },
      {
        "edifil_code": "1805",
        "fesofi_code": "1805",
        "motive": "Monumento Colón (Huelva)",
        "face_value": "2,50 pta",
        "description": "El Monumento a la Fe Descubridora, popularmente conocido como Monumento a Colón, se erige en la Punta del Sebo de Huelva, en la confluencia de los ríos Tinto y Odiel. Fue donado por la Columbus Memorial Fund y realizado por la escultora estadounidense Gertrude Vanderbilt Whitney, inaugurándose en 1929. La imponente figura, de estilo cubista, representa a un monje franciscano con los brazos cruzados, simbolizando la figura de Colón y la gesta del Descubrimiento de América, con Huelva como punto de partida.",
        "amount_printed": 10000000,
        "color": "azul oscuro y azul",
        "market_value_mnh": 0.4,
        "market_value_used": 0.2
      },
      {
        "edifil_code": "1806",
        "fesofi_code": "1806",
        "motive": "Año Internacional del Turismo",
        "face_value": "3,50 pta",
        "description": "Este sello conmemora el 'Año Internacional del Turismo', declarado por las Naciones Unidas en 1967. La emisión de este sello por parte de España subraya la importancia del turismo para la economía y la imagen del país en aquella época. El diseño del sello probablemente incorpora elementos gráficos que simbolizan el viaje y la hospitalidad, en línea con los objetivos de la campaña internacional para promover el entendimiento cultural a través del turismo.",
        "amount_printed": 10000000,
        "color": "azul y violeta",
        "market_value_mnh": 0.4,
        "market_value_used": 0.2
      },
      {
        "edifil_code": "1807",
        "fesofi_code": "1807",
        "motive": "Ciudad Encantada (Cuenca)",
        "face_value": "5 pta",
        "description": "La Ciudad Encantada de Cuenca es un paraje natural de formaciones rocosas calizas o 'karst' modeladas caprichosamente por la erosión del agua, el viento y el hielo a lo largo de millones de años. Ubicada en la Serranía de Cuenca, dentro del Parque Natural de la Serranía de Cuenca, este Monumento Natural de Interés Nacional ofrece un paisaje laberíntico donde las rocas adoptan formas que recuerdan a animales, objetos o figuras humanas, como el 'Tormo Alto' o 'Los Barcos', creando un escenario de gran belleza y singularidad.",
        "amount_printed": 10000000,
        "color": "negro y verde",
        "market_value_mnh": 0.5,
        "market_value_used": 0.25
      },
      {
        "edifil_code": "1808",
        "fesofi_code": "1808",
        "motive": "Iglesia de Nuestra Señora de la O en Sanlúcar de Barrameda (Cádiz)",
        "face_value": "6 pta",
        "description": "La Iglesia de Nuestra Señora de la O, en Sanlúcar de Barrameda (Cádiz), es uno de los templos más significativos de la ciudad. Fundada en el siglo XIV, presenta una mezcla de estilos gótico-mudéjar, con elementos renacentistas y barrocos añadidos en reformas posteriores. Se sitúa junto al Palacio de los Duques de Medina Sidonia y destaca por su portada mudéjar, su artesonado y su retablo mayor. Es un testimonio de la rica historia de Sanlúcar, ligada a la Casa de Medina Sidonia y a la Carrera de Indias.",
        "amount_printed": 10000000,
        "color": "malva y castaño",
        "market_value_mnh": 0.5,
        "market_value_used": 0.25
      }
    ]
  }
}

# Issues Extraction API - Not Found Response
ISSUES_EXTRACTION_RESPONSE_404_NOT_FOUND = {
    "success": False,
    "message": "No information was found for the provided search criteria",
    "errors": None,
    "data": None
}

# Issues Extraction API - Validation Error Response
ISSUES_EXTRACTION_RESPONSE_400_VALIDATION_ERROR = {
    "success": False,
    "message": "Validation error in the provided data",
    "errors": [
        {"field": "name", "message": "The series name is required"}
    ],
    "data": None
}

# Issues Collections (Create) API - Success Response
ISSUES_COLLECTIONS_RESPONSE_201_CREATED = {
    "success": True,
    "message": "Stamp collection created successfully",
    "errors": None,
    "data": {
        "id": 100,
        "country": "Spain",
        "date": "1967-07-26",
        "name": "Landscapes and Monuments",
        "perforation": "13 1/4",
        "stamp_type": "Standard mail",
        "print_type": "Photogravure",
        "total_printed": 10000000,
        "market_value": 3.5,
        "description": "The 1967 'Landscapes and Monuments' series...",
        "note": None,
        "stamps_count": 7
    }
}

# Issues Collections (Create) API - Validation Error Response
ISSUES_COLLECTIONS_RESPONSE_400_ERROR = {
    "success": False,
    "message": "Validation error",
    "errors": [
        {"field": "issue_name", "message": "The issue name is required"},
        {"field": "issue_date", "message": "The emission date is required"}
    ],
    "data": None
}
