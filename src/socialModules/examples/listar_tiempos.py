import os
import glob
import pickle
from datetime import datetime

# El directorio de datos, según lo definido en configMod.py
DATADIR = os.path.expanduser("~/.mySocial/data")


def read_next_times():
    """
    Busca y lee todos los archivos .timeNext en el directorio de datos
    y muestra la información de tiempo de publicación.
    """
    print(f"Buscando archivos *.timeNext en: {DATADIR}\n")

    # Patrón para encontrar los archivos de tiempo
    time_files_pattern = os.path.join(DATADIR, "*.timeNext")
    time_files = glob.glob(time_files_pattern)

    if not time_files:
        print("No se encontraron archivos de tiempo de publicación.")
        return

    print(f"Se encontraron {len(time_files)} archivos de tiempo:\n")

    for file_path in time_files:
        try:
            with open(file_path, "rb") as f:
                # Cargar los datos del archivo pickle
                tNow, tSleep = pickle.load(f)

                # tNow es un timestamp, lo convertimos a formato legible
                next_publication_time = datetime.fromtimestamp(tNow + tSleep)

                # Extraer un nombre identificable del archivo
                file_name = os.path.basename(file_path).replace(".timeNext", "")

                print(f"Servicio: {file_name}")
                print(
                    f"  -> Próxima publicación programada para: {next_publication_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                print(f"  -> Tiempo de espera (tSleep): {tSleep/60:.2f} minutos")
                print("-" * 40)

        except (pickle.UnpicklingError, EOFError, TypeError) as e:
            print(f"Error al leer el archivo {os.path.basename(file_path)}: {e}")
        except Exception as e:
            print(
                f"Ocurrió un error inesperado con el archivo {os.path.basename(file_path)}: {e}"
            )


if __name__ == "__main__":
    read_next_times()
