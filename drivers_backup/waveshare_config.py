# Configuration Pinout pour Waveshare Triple LCD HAT (Mode BCM)

# Ecran 1 : 1.3 inch (Centre) - Utilise SPI1
LCD_1_3 = {
    "name": "1.3 inch (Center)",
    "spi_bus": 1,
    "spi_device": 0,
    "rst": 27,
    "dc": 22,
    "bl": 19,
    "cs": 18,
    "madctl": 0x00, # RGB mode
    "width": 240,
    "height": 240,
    "col_start": 0,
    "row_start": 0,
    "rotation": 180
}

# Ecran 2 : 0.96 inch (SPI0 CE0)
LCD_0_96_1 = {
    "name": "0.96 inch (1)",
    "spi_bus": 0,
    "spi_device": 0,
    "rst": 24,
    "dc": 4,
    "bl": 13,
    "cs": 8,
    "madctl": 0x08, # BGR mode (Fix for blue/red swap)
    "width": 160,
    "height": 80,
    "col_start": 0,
    "row_start": 24,
    "rotation": 0
}

# Ecran 3 : 0.96 inch (SPI0 CE1)
LCD_0_96_2 = {
    "name": "0.96 inch (2)",
    "spi_bus": 0,
    "spi_device": 1,
    "rst": 23,
    "dc": 5,
    "bl": 12,
    "cs": 7,
    "madctl": 0x08, # BGR mode (Fix for blue/red swap)
    "width": 160,
    "height": 80,
    "col_start": 0,
    "row_start": 24,
    "rotation": 0
}

# Boutons Utilisateur
KEYS = {
    "KEY1": 25,
    "KEY2": 26
}

CONFIGS = [LCD_1_3, LCD_0_96_1, LCD_0_96_2]
