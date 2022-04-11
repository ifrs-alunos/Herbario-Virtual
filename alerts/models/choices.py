SENSOR_TYPE_CHOICES = [
    ('Dht11', (
        ('dht_h', 'Umidade DHT'),
        ('dht_t', 'Temperatura DHT'),
        ('dht_hi', 'Sensação Térmica DHT'),
    )
     ),
    ('Bmp280', (
        ('bmp_t', 'Temperatura BMP'),
        ('bmp_p', 'Pressão BMP'),
        ('bmp_a', 'Altitude BMP'),
    )
     ),
    ('ldr', 'Luz LDR'),
    ('rain', 'Chuva'),
    ('soil', 'Umidade do solo'),
    ('uv', 'Luz UV'),
]
