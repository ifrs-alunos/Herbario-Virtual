SENSOR_TYPE_CHOICES = [
    (
        "Dht11",
        (
            ("dht_h", "Umidade DHT"),
            ("dht_t", "Temperatura DHT"),
            ("dht_hi", "Sensação Térmica DHT"),
        ),
    ),
    (
        "Bmp280",
        (
            ("bmp_t", "Temperatura BMP"),
            ("bmp_p", "Pressão BMP"),
            ("bmp_a", "Altitude BMP"),
        ),
    ),
    ("ldr", "Luz LDR"),
    ("rain", "Chuva"),
    ("soil", "Umidade do solo"),
    ("uv", "Luz UV"),
]

RELATIONAL_TYPE_CHOICES = [
    (">", "Maior que"),
    ("<", "Menor que"),
    (">=", "Maior ou igual que"),
    ("<=", "Menor ou igual que"),
    ("==", "Igual que"),
    ("!=", "Diferente que"),
]

METRIC_TYPE_CHOICES = [
    ("mm", "Milímetros"),
    ("C", "Graus ºC"),
    ("CS", "Graus ºC Solo"),
    ("human", "Sensor Humano"),
    ("bool", "Booleano"),
    ("ur", "Umidade Relativa %"),
    # não sei quão importante isso é mas é preferivel não usar caractere especial como chave
    ("%", "Umidade % (depreciado)"),
    ("wm2", "Wm2"),
    ("K", "Graus ºK"),
    ("m/s", "m/s (depreciado)"),
    ("m_s", "m/s"),
    ("mbar", "Milibares"),
    ("v", "Volts"),
    ("pct", "Porcentagem"),
    ("int", "Inteiro"),
]
