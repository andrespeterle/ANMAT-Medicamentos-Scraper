#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script wrapper para ejecutar el scraper de forma robusta
"""
import sys
import time
import subprocess
import re
from pathlib import Path

def extract_last_processed(log_text):
    """Extrae el último laboratorio procesado del log"""
    match = re.search(r"start_from='([^']+)'", log_text)
    if match:
        return match.group(1)
    return None

def run_scraper(start_from=None):
    """Ejecuta el scraper"""
    script_dir = Path(__file__).parent
    script_path = script_dir / "anmat_scraper_v2.py"
    
    if not script_path.exists():
        print(f"Error: No se encontró {script_path}")
        return False
    
    # Crear comando de Python
    if start_from:
        cmd = f"""
import sys
sys.path.insert(0, r'{script_dir}')
from anmat_scraper_v2 import ANMATScraperV2
scraper = ANMATScraperV2(headless=True, delay=0.5)
scraper.run(start_from='{start_from.replace("'", "")}')
"""
    else:
        cmd = f"""
import sys
sys.path.insert(0, r'{script_dir}')
from anmat_scraper_v2 import ANMATScraperV2
scraper = ANMATScraperV2(headless=True, delay=0.5)
scraper.run()
"""
    
    print(f"Ejecutando scraper{' desde: ' + start_from if start_from else ''}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", cmd],
            cwd=str(script_dir),
            capture_output=True,
            text=True,
            timeout=7200  # 2 horas
        )
        
        output = result.stdout + result.stderr
        print(output)
        
        return extract_last_processed(output)
        
    except subprocess.TimeoutExpired:
        print("Script excedió el timeout de 2 horas")
        return None
    except Exception as e:
        print(f"Error ejecutando script: {e}")
        return None

def main():
    print("=" * 70)
    print("ANMAT Scraper - Ejecutor Robusto")
    print("=" * 70)
    
    max_retries = 10
    current_start = None
    
    for attempt in range(1, max_retries + 1):
        print(f"\nIntento {attempt}/{max_retries}")
        last_processed = run_scraper(current_start)
        
        if last_processed:
            print(f"Se completó hasta: {last_processed}")
            print("Reanudando desde ese punto...")
            current_start = last_processed
            time.sleep(5)  # Pequeña pausa entre reintentos
        else:
            print("Scraper completado exitosamente!")
            break
    
    print("\n" + "=" * 70)
    print("Ejecución finalizada")
    print("=" * 70)

if __name__ == "__main__":
    main()
