import logging
import sys
from datetime import datetime
import os

def setup_logging():
    """Nastavení logování pro celého bota"""
    
    # Vytvoření složky pro logy pokud neexistuje
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Formát logů
    log_format = "[{asctime}] [{levelname:>8}] {name}: {message}"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Konfigurace loggeru
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        style="{",
        handlers=[
            # Console handler - pouze INFO a vyšší
            logging.StreamHandler(sys.stdout),
            # File handler - všechny logy
            logging.FileHandler(
                filename=os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y-%m-%d')}.log"),
                encoding='utf-8',
                mode='a'
            )
        ]
    )
    
    # Nastavení úrovně pro různé loggery
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
    
    # Vlastní logger pro VeltrixAPP
    logger = logging.getLogger('VeltrixAPP')
    logger.setLevel(logging.DEBUG)
    
    logger.info("=== Veltrix APP spuštěn ===")
    return logger

def get_logger(name):
    """Získá logger pro konkrétní modul"""
    return logging.getLogger(f"Veltrix.{name}")
