"""
ANMAT Vademecum Scraper V2
Extrae todos los medicamentos usando la lista de laboratorios
"""

import time
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys


class ANMATScraperV2:
    def __init__(self, laboratorios_file='LaboratoriosANMAT.txt', output_file='medicamentos_anmat_completo.csv',
                 headless=False, delay=2):
        """
        Inicializa el scraper V2

        Args:
            laboratorios_file: Archivo CSV con la lista de laboratorios
            output_file: Nombre del archivo CSV de salida
            headless: Si True, ejecuta Chrome en modo sin interfaz gráfica
            delay: Tiempo de espera en segundos entre solicitudes
        """
        self.url = "https://servicios.pami.org.ar/vademecum/views/consultaPublica/listado.zul"
        self.laboratorios_file = laboratorios_file
        self.output_file = output_file
        self.delay = delay
        self.results_count = 0
        self.laboratorios_procesados = 0
        self.laboratorios_con_resultados = 0

        # Cargar lista de laboratorios
        self.laboratorios = self._load_laboratorios()

        # Configurar opciones de Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # Inicializar driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

        # Crear archivo CSV con encabezados
        self._init_csv()

    def _load_laboratorios(self):
        """Carga la lista de laboratorios desde el archivo CSV"""
        laboratorios = []
        import os
        # Si el archivo no existe en la ruta actual, buscar en el mismo directorio del script
        file_path = self.laboratorios_file
        if not os.path.exists(file_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, self.laboratorios_file)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Saltar encabezado
            for row in reader:
                if len(row) >= 3:
                    # El tercer campo es la Razón Social
                    razon_social = row[2].strip().replace('"', '')
                    laboratorios.append(razon_social)
        return laboratorios

    def _init_csv(self):
        """Inicializa el archivo CSV con encabezados"""
        with open(self.output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Nombre_Comercial_Presentacion',
                'Monodroga_Generico',
                'Laboratorio',
                'Forma_Farmaceutica',
                'Numero_Certificado',
                'GTIN',
                'Disponibilidad',
                'Timestamp_Extraccion'
            ])

    def _reiniciar_driver(self):
        """Reinicia el navegador Chrome"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        print("    [INFO] Driver reiniciado")

    def search_by_laboratorio(self, laboratorio_nombre):
        """
        Realiza una búsqueda por laboratorio

        Args:
            laboratorio_nombre: Nombre del laboratorio a buscar

        Returns:
            Lista de medicamentos encontrados
        """
        try:
            # Navegar a la página
            self.driver.get(self.url)
            time.sleep(3)

            # Encontrar el campo Laboratorio (bandbox)
            laboratorio_bandbox = self.wait.until(
                EC.presence_of_element_located((By.ID, "zk_comp_40-real"))
            )

            # Hacer clic para abrir el popup
            laboratorio_bandbox.click()
            time.sleep(1)

            # Esperar a que aparezca el popup
            popup_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "zk_comp_53"))
            )

            # Escribir el nombre del laboratorio en el campo de búsqueda del popup
            popup_input.clear()
            popup_input.send_keys(laboratorio_nombre[:30])  # Primeros 30 caracteres
            time.sleep(0.5)

            # Presionar Enter o hacer clic en la lupa de búsqueda
            try:
                lupita = self.driver.find_element(By.ID, "zk_comp_54")
                lupita.click()
            except:
                popup_input.send_keys(Keys.ENTER)

            time.sleep(2)

            # Buscar resultados en el listbox del popup
            try:
                # Esperar a que aparezcan resultados
                listbox = self.wait.until(
                    EC.presence_of_element_located((By.ID, "zk_comp_56"))
                )

                # Buscar filas en el listbox
                list_items = self.driver.find_elements(By.XPATH, "//div[@id='zk_comp_56']//tr[contains(@class, 'z-listitem')]")

                if not list_items:
                    print(f"    No se encontro el laboratorio: {laboratorio_nombre}")
                    # Cerrar popup
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    return []

                # Hacer clic en el primer resultado (debería ser el exacto)
                list_items[0].click()
                time.sleep(1)

            except Exception as e:
                print(f"    Error seleccionando laboratorio: {str(e)}")
                return []

            # Ahora hacer clic en el botón Buscar principal
            buscar_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "zk_comp_80"))
            )
            buscar_btn.click()

            # Esperar a que carguen los resultados
            time.sleep(self.delay)

            # Verificar si hay resultados
            try:
                empty_msg = self.driver.find_element(
                    By.XPATH,
                    "//td[@id='zk_comp_86-empty' and contains(text(), 'No se han encontrado resultados')]"
                )
                if empty_msg.is_displayed():
                    print(f"    No hay medicamentos para: {laboratorio_nombre}")
                    return []
            except NoSuchElementException:
                pass

            # Extraer resultados
            return self._extract_results(laboratorio_nombre)

        except TimeoutException:
            print(f"    Timeout en busqueda: {laboratorio_nombre}")
            return []
        except Exception as e:
            print(f"    Error en busqueda {laboratorio_nombre}: {str(e)}")
            return []

    def _extract_results(self, laboratorio_nombre):
        """
        Extrae los resultados de la tabla de medicamentos

        Returns:
            Lista de diccionarios con datos de medicamentos
        """
        results = []

        try:
            # Procesar todas las páginas de resultados
            page_num = 1
            while True:
                print(f"      Procesando pagina {page_num}...")

                # Esperar a que la tabla esté lista
                time.sleep(1)

                # Extraer filas de la tabla
                rows = self.driver.find_elements(
                    By.XPATH,
                    "//div[@id='zk_comp_86-body']//tbody[@id='zk_comp_109']/tr[contains(@class, 'z-row')]"
                )

                if not rows:
                    break

                print(f"      Encontradas {len(rows)} filas en esta pagina")

                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")

                        if len(cells) >= 9:
                            # Extraer datos de cada celda
                            # 0: Envase Secundario (imagen)
                            # 1: Número Certificado
                            # 2: Laboratorio
                            # 3: Nombre Comercial
                            # 4: Forma Farmacéutica
                            # 5: Presentación
                            # 6: GTIN (oculto)
                            # 7: Genérico
                            # 8: Detalle (lupa)
                            # 9: Disponibilidad (ojo)

                            numero_certificado = cells[1].text.strip()
                            laboratorio = cells[2].text.strip()
                            nombre_comercial = cells[3].text.strip()
                            forma_farmaceutica = cells[4].text.strip()
                            presentacion = cells[5].text.strip()
                            generico = cells[7].text.strip()

                            # GTIN puede estar en celda oculta
                            try:
                                gtin_cell = cells[6] if len(cells) > 6 else None
                                gtin = gtin_cell.text.strip() if gtin_cell else ""
                            except:
                                gtin = ""

                            # Disponibilidad - buscar el icono del ojo
                            disponibilidad = "Desconocido"
                            try:
                                if len(cells) > 9:
                                    disp_cell = cells[9]
                                    # Buscar imagen dentro de la celda
                                    imgs = disp_cell.find_elements(By.TAG_NAME, "img")
                                    if imgs:
                                        disponibilidad = "Disponible"
                                    else:
                                        disponibilidad = "No disponible"
                            except:
                                pass

                            # Combinar nombre comercial con presentación
                            nombre_completo = f"{nombre_comercial} - {presentacion}"

                            resultado = {
                                'Nombre_Comercial_Presentacion': nombre_completo,
                                'Monodroga_Generico': generico,
                                'Laboratorio': laboratorio,
                                'Forma_Farmaceutica': forma_farmaceutica,
                                'Numero_Certificado': numero_certificado,
                                'GTIN': gtin,
                                'Disponibilidad': disponibilidad,
                                'Timestamp_Extraccion': datetime.now().isoformat()
                            }

                            results.append(resultado)

                    except Exception as e:
                        print(f"        Error extrayendo fila: {str(e)}")
                        continue

                # Verificar si hay más páginas
                try:
                    # Buscar el botón "Siguiente" en el paginador
                    try:
                        next_button = self.driver.find_element(
                            By.XPATH,
                            "//div[@id='zk_comp_98']//a[@name='zk_comp_98-next']"
                        )
                    except NoSuchElementException:
                        print(f"      Boton siguiente no encontrado - fin de paginacion")
                        break

                    # Verificar si está deshabilitado
                    disabled_attr = next_button.get_attribute('disabled')
                    if disabled_attr is not None and (disabled_attr == 'true' or disabled_attr == 'disabled'):
                        print(f"      No hay mas paginas")
                        break

                    # Verificar si tiene clase de deshabilitado
                    class_attr = next_button.get_attribute('class')
                    if class_attr and 'disabled' in class_attr.lower():
                        print(f"      No hay mas paginas")
                        break

                    next_button.click()
                    time.sleep(self.delay)
                    page_num += 1

                except Exception as e:
                    error_str = str(e).lower()
                    if 'no such element' in error_str or 'not found' in error_str:
                        print(f"      Fin de paginacion")
                    else:
                        print(f"        Error en paginacion: {str(e)}")
                    break

            return results

        except Exception as e:
            error_str = str(e).lower()
            if 'invalid session id' in error_str or 'disconnected' in error_str:
                print(f"      Error de sesión: reintentar la búsqueda")
                raise  # Re-lanzar para que sea manejado en el nivel superior
            else:
                print(f"      Error extrayendo resultados: {str(e)}")
            return results

    def save_results(self, results):
        """
        Guarda los resultados en el archivo CSV

        Args:
            results: Lista de diccionarios con datos de medicamentos
        """
        if not results:
            return

        with open(self.output_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Nombre_Comercial_Presentacion',
                'Monodroga_Generico',
                'Laboratorio',
                'Forma_Farmaceutica',
                'Numero_Certificado',
                'GTIN',
                'Disponibilidad',
                'Timestamp_Extraccion'
            ])

            for result in results:
                writer.writerow(result)
                self.results_count += 1

    def run(self, start_from=None, max_labs=None):
        """
        Ejecuta el scraper con todos los laboratorios

        Args:
            start_from: Nombre del laboratorio desde el cual empezar (para reanudar)
            max_labs: Número máximo de laboratorios a procesar (None = todos)
        """
        print("=" * 70)
        print("ANMAT Vademecum Scraper V2 - Busqueda por Laboratorios")
        print("=" * 70)
        print(f"URL: {self.url}")
        print(f"Archivo de salida: {self.output_file}")
        print(f"Total de laboratorios: {len(self.laboratorios)}")
        print(f"Delay entre solicitudes: {self.delay}s")
        print("=" * 70)

        start_searching = start_from is None
        labs_procesados = 0

        try:
            for idx, laboratorio in enumerate(self.laboratorios, 1):
                # Si hay un punto de inicio, esperar hasta llegar a él
                if not start_searching:
                    if laboratorio == start_from:
                        start_searching = True
                    else:
                        continue

                labs_procesados += 1
                self.laboratorios_procesados = labs_procesados

                print(f"\n[{idx}/{len(self.laboratorios)}] Laboratorio: {laboratorio[:60]}")

                # Reintentar hasta 3 veces si hay error de sesión
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        results = self.search_by_laboratorio(laboratorio)

                        if results:
                            print(f"    [OK] Encontrados {len(results)} medicamentos")
                            self.save_results(results)
                            self.laboratorios_con_resultados += 1
                            print(f"    Total acumulado: {self.results_count} medicamentos")
                        
                        break  # Salir del loop de reintentos si fue exitoso
                        
                    except Exception as e:
                        error_str = str(e).lower()
                        if 'invalid session id' in error_str or 'disconnected' in error_str:
                            print(f"    [REINTENTAR] Error de sesión (intento {attempt + 1}/{max_retries})")
                            if attempt < max_retries - 1:
                                self._reiniciar_driver()
                                time.sleep(2)
                            else:
                                print(f"    [ERROR] No se pudo procesar después de {max_retries} intentos")
                                break
                        else:
                            print(f"    Error: {str(e)}")
                            break

                # Verificar límite de laboratorios
                if max_labs and labs_procesados >= max_labs:
                    print(f"\nAlcanzado limite de {max_labs} laboratorios")
                    break

                # Pequeña pausa entre búsquedas
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\nInterrupcion detectada. Guardando progreso...")
            print(f"Ultimo laboratorio procesado: {laboratorio}")
            print(f"Para reanudar, usa: start_from='{laboratorio}'")

        finally:
            print("\n" + "=" * 70)
            print(f"Scraping finalizado")
            print(f"Laboratorios procesados: {self.laboratorios_procesados}/{len(self.laboratorios)}")
            print(f"Laboratorios con medicamentos: {self.laboratorios_con_resultados}")
            print(f"Total de medicamentos extraidos: {self.results_count}")
            print(f"Archivo guardado: {self.output_file}")
            print("=" * 70)
            self.close()

    def close(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    # Configuración
    scraper = ANMATScraperV2(
        laboratorios_file='LaboratoriosANMAT.txt',
        output_file='medicamentos_anmat_completo.csv',
        headless=True,  # Cambiar a True para ejecutar sin ventana visible
        delay=0.5  # Segundos de espera entre solicitudes
    )

    # Para hacer una prueba con los primeros 5 laboratorios:
    # scraper.run(max_labs=5)

    # Para ejecutar completo (todos los laboratorios):
    scraper.run()

    # Para reanudar desde un laboratorio específico:
    # scraper.run(start_from='INMUNOLAB SA')
