#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple para ejecutar el scraper con reintentos
"""
import sys
import os
import time

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from anmat_scraper_v2 import ANMATScraperV2

def main():
    print("=" * 70)
    print("ANMAT Medicamentos Scraper - Versión Simple")
    print("=" * 70)
    
    try:
        scraper = ANMATScraperV2(
            laboratorios_file='LaboratoriosANMAT.txt',
            output_file='medicamentos_anmat_completo.csv',
            headless=True,
            delay=0.5
        )
        
        # Ejecutar scraper
        print("\nIniciando scraper...")
        scraper.run()
        
        print("\n¡Scraper completado exitosamente!")
        
    except KeyboardInterrupt:
        print("\n\nScraper interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
