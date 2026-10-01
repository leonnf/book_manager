#@title Escritura de preload_data.py
"""Carga de datos iniciales de Book Manager desde archivos CSV.

Lee los CSV de migrations/csv y crea los registros a través de los
servicios, así los datos iniciales cumplen las mismas reglas de negocio que
un alta manual. En los CSV, las relaciones se expresan por clave natural
(nombre, código o ISBN) y se traducen a ids durante la carga.
"""
import csv
import datetime
import os
from typing import Callable, Dict, Iterator, Optional, Tuple

from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioStock,
    ServicioTipoCotizacion,
)

CARPETA_PAQUETE: str = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
CARPETA_CSV: str = os.path.join(CARPETA_PAQUETE, "migrations", "csv")
CARPETA_DATOS: str = os.path.join(CARPETA_PAQUETE, "data")

FilaCsv = Dict[str, Optional[str]]
Indice = Dict[str, int]


def limpiar_datos(carpeta_datos: str = CARPETA_DATOS) -> int:
    """Borra los archivos JSON de la carpeta de datos.

    Los demás archivos (por ejemplo, .gitkeep) se conservan.

    Args:
        carpeta_datos (str): Carpeta donde persisten los repositorios.

    Returns:
        int: Cantidad de archivos JSON borrados.
    """
    if not os.path.isdir(carpeta_datos):
        return 0
    borrados: int = 0
    for nombre_archivo in sorted(os.listdir(carpeta_datos)):
        if nombre_archivo.endswith(".json"):
            os.remove(os.path.join(carpeta_datos, nombre_archivo))
            borrados += 1
    return borrados


def _normalizar_clave(clave: str) -> str:
    """Normaliza una clave natural para buscarla sin distinguir mayúsculas.

    Args:
        clave (str): Clave a normalizar.

    Returns:
        str: La clave sin espacios extremos y en minúsculas (casefold).
    """
    return clave.strip().casefold()


def _obligatorio(fila: FilaCsv, campo: str) -> str:
    """Obtiene el valor de un campo obligatorio de una fila CSV.

    Args:
        fila (FilaCsv): Fila leída del CSV.
        campo (str): Nombre de la columna.

    Returns:
        str: El valor sin espacios extremos.

    Raises:
        ValueError: Si el campo falta o está vacío.
    """
    valor: Optional[str] = fila.get(campo)
    if valor is None or not valor.strip():
        raise ValueError(f"Falta el valor del campo '{campo}'.")
    return valor.strip()


def _opcional(fila: FilaCsv, campo: str) -> Optional[str]:
    """Obtiene el valor de un campo opcional de una fila CSV.

    Args:
        fila (FilaCsv): Fila leída del CSV.
        campo (str): Nombre de la columna.

    Returns:
        Optional[str]: El valor sin espacios extremos, o None si está vacío.
    """
    valor: Optional[str] = fila.get(campo)
    if valor is None or not valor.strip():
        return None
    return valor.strip()


def _a_entero(valor: str, campo: str) -> int:
    """Convierte un texto a entero.

    Args:
        valor (str): Texto a convertir.
        campo (str): Nombre del campo, para el mensaje.

    Returns:
        int: El valor convertido.

    Raises:
        ValueError: Si el texto no representa un entero.
    """
    try:
        return int(valor)
    except ValueError as error:
        raise ValueError(
            f"El campo '{campo}' debe ser un número entero y se recibió "
            f"'{valor}'."
        ) from error


def _a_entero_opcional(valor: Optional[str], campo: str) -> Optional[int]:
    """Convierte un texto opcional a entero.

    Args:
        valor (Optional[str]): Texto a convertir, o None.
        campo (str): Nombre del campo, para el mensaje.

    Returns:
        Optional[int]: El valor convertido, o None.

    Raises:
        ValueError: Si el texto no representa un entero.
    """
    if valor is None:
        return None
    return _a_entero(valor, campo)


def _a_decimal(valor: str, campo: str) -> float:
    """Convierte un texto con punto decimal a float.

    Args:
        valor (str): Texto a convertir.
        campo (str): Nombre del campo, para el mensaje.

    Returns:
        float: El valor convertido.

    Raises:
        ValueError: Si el texto no representa un número.
    """
    try:
        return float(valor)
    except ValueError as error:
        raise ValueError(
            f"El campo '{campo}' debe ser un número con punto decimal y se "
            f"recibió '{valor}'."
        ) from error


def _a_fecha(valor: str, campo: str) -> datetime.date:
    """Convierte un texto en formato ISO (AAAA-MM-DD) a fecha.

    Args:
        valor (str): Texto a convertir.
        campo (str): Nombre del campo, para el mensaje.

    Returns:
        datetime.date: La fecha convertida.

    Raises:
        ValueError: Si el texto no tiene formato AAAA-MM-DD.
    """
    try:
        return datetime.date.fromisoformat(valor)
    except ValueError as error:
        raise ValueError(
            f"El campo '{campo}' debe tener formato AAAA-MM-DD y se recibió "
            f"'{valor}'."
        ) from error


def _buscar_id(indice: Indice, clave: str, entidad: str) -> int:
    """Traduce una clave natural al id de la entidad correspondiente.

    Args:
        indice (Indice): Diccionario de clave normalizada a id.
        clave (str): Clave natural leída del CSV.
        entidad (str): Nombre de la entidad, para el mensaje.

    Returns:
        int: El id encontrado.

    Raises:
        ValueError: Si la clave no existe en el índice.
    """
    id_encontrado: Optional[int] = indice.get(_normalizar_clave(clave))
    if id_encontrado is None:
        raise ValueError(f"No existe {entidad} '{clave}'.")
    return id_encontrado


class CargadorDatosIniciales:
    """Carga los datos iniciales desde CSV a través de los servicios.

    Args:
        carpeta_csv (str): Carpeta que contiene los CSV de migración.
        servicio_generos (ServicioGenero): Servicio de géneros.
        servicio_editoriales (ServicioEditorial): Servicio de editoriales.
        servicio_monedas (ServicioMoneda): Servicio de monedas.
        servicio_tipos (ServicioTipoCotizacion): Servicio de tipos de
            cotización.
        servicio_libros (ServicioLibro): Servicio de libros.
        servicio_precios (ServicioPrecio): Servicio de precios.
        servicio_stock (ServicioStock): Servicio de stock.
        servicio_cotizaciones (ServicioCotizacionDolar): Servicio de
            cotizaciones.

    Raises:
        ValueError: Si la carpeta de CSV no existe.
    """

    def __init__(
        self,
        carpeta_csv: str,
        servicio_generos: ServicioGenero,
        servicio_editoriales: ServicioEditorial,
        servicio_monedas: ServicioMoneda,
        servicio_tipos: ServicioTipoCotizacion,
        servicio_libros: ServicioLibro,
        servicio_precios: ServicioPrecio,
        servicio_stock: ServicioStock,
        servicio_cotizaciones: ServicioCotizacionDolar,
    ) -> None:
        if not os.path.isdir(carpeta_csv):
            raise ValueError(f"No existe la carpeta de CSV '{carpeta_csv}'.")
        self.__carpeta_csv: str = carpeta_csv
        self.__servicio_generos: ServicioGenero = servicio_generos
        self.__servicio_editoriales: ServicioEditorial = servicio_editoriales
        self.__servicio_monedas: ServicioMoneda = servicio_monedas
        self.__servicio_tipos: ServicioTipoCotizacion = servicio_tipos
        self.__servicio_libros: ServicioLibro = servicio_libros
        self.__servicio_precios: ServicioPrecio = servicio_precios
        self.__servicio_stock: ServicioStock = servicio_stock
        self.__servicio_cotizaciones: ServicioCotizacionDolar = (
            servicio_cotizaciones
        )

    def cargar_todo(self) -> Dict[str, int]:
        """Carga todas las entidades respetando el orden de dependencias.

        Returns:
            Dict[str, int]: Cantidad de registros cargados por entidad.

        Raises:
            ValueError: Si algún CSV falta o tiene un registro inválido.
        """
        return {
            "generos": self.cargar_generos(),
            "editoriales": self.cargar_editoriales(),
            "monedas": self.cargar_monedas(),
            "tipos_cotizacion": self.cargar_tipos_cotizacion(),
            "libros": self.cargar_libros(),
            "precios": self.cargar_precios(),
            "stocks": self.cargar_stocks(),
            "cotizaciones_dolar": self.cargar_cotizaciones(),
        }

    def cargar_generos(self) -> int:
        """Carga los géneros desde generos.csv.

        Returns:
            int: Cantidad de géneros cargados.
        """

        def crear(fila: FilaCsv) -> None:
            self.__servicio_generos.crear(
                _obligatorio(fila, "nombre"),
                _obligatorio(fila, "descripcion"),
            )

        return self.__cargar("generos.csv", crear)

    def cargar_editoriales(self) -> int:
        """Carga las editoriales desde editoriales.csv.

        Returns:
            int: Cantidad de editoriales cargadas.
        """

        def crear(fila: FilaCsv) -> None:
            self.__servicio_editoriales.crear(
                _obligatorio(fila, "nombre"),
                _obligatorio(fila, "pais_origen"),
                _opcional(fila, "email_contacto"),
            )

        return self.__cargar("editoriales.csv", crear)

    def cargar_monedas(self) -> int:
        """Carga las monedas desde monedas.csv.

        Returns:
            int: Cantidad de monedas cargadas.
        """

        def crear(fila: FilaCsv) -> None:
            self.__servicio_monedas.crear(
                _obligatorio(fila, "codigo"),
                _obligatorio(fila, "nombre"),
                _obligatorio(fila, "simbolo"),
            )

        return self.__cargar("monedas.csv", crear)

    def cargar_tipos_cotizacion(self) -> int:
        """Carga los tipos de cotización desde tipos_cotizacion.csv.

        Returns:
            int: Cantidad de tipos cargados.
        """

        def crear(fila: FilaCsv) -> None:
            self.__servicio_tipos.crear(
                _obligatorio(fila, "nombre"),
                _obligatorio(fila, "descripcion"),
            )

        return self.__cargar("tipos_cotizacion.csv", crear)

    def cargar_libros(self) -> int:
        """Carga los libros desde libros.csv.

        El género y la editorial se indican por nombre.

        Returns:
            int: Cantidad de libros cargados.
        """
        generos: Indice = {
            _normalizar_clave(genero.nombre): genero.id
            for genero in self.__servicio_generos.listar()
        }
        editoriales: Indice = {
            _normalizar_clave(editorial.nombre): editorial.id
            for editorial in self.__servicio_editoriales.listar()
        }

        def crear(fila: FilaCsv) -> None:
            self.__servicio_libros.crear(
                _obligatorio(fila, "isbn"),
                _obligatorio(fila, "titulo"),
                _obligatorio(fila, "autor"),
                _a_entero(
                    _obligatorio(fila, "anio_publicacion"),
                    "anio_publicacion",
                ),
                _buscar_id(generos, _obligatorio(fila, "genero"), "género"),
                _buscar_id(
                    editoriales, _obligatorio(fila, "editorial"), "editorial"
                ),
                _opcional(fila, "idioma") or "Español",
                _a_entero_opcional(_opcional(fila, "paginas"), "paginas"),
                _opcional(fila, "url_referencia"),
            )

        return self.__cargar("libros.csv", crear)

    def cargar_precios(self) -> int:
        """Carga los precios desde precios.csv.

        El libro se indica por ISBN y la moneda por código.

        Returns:
            int: Cantidad de precios cargados.
        """
        libros: Indice = self.__indice_libros()
        monedas: Indice = {
            _normalizar_clave(moneda.codigo): moneda.id
            for moneda in self.__servicio_monedas.listar()
        }

        def crear(fila: FilaCsv) -> None:
            self.__servicio_precios.crear(
                _buscar_id(libros, _obligatorio(fila, "isbn"), "libro"),
                _buscar_id(monedas, _obligatorio(fila, "moneda"), "moneda"),
                _a_decimal(_obligatorio(fila, "monto"), "monto"),
                _a_fecha(
                    _obligatorio(fila, "fecha_vigencia"), "fecha_vigencia"
                ),
            )

        return self.__cargar("precios.csv", crear)

    def cargar_stocks(self) -> int:
        """Carga el stock desde stocks.csv.

        El libro se indica por ISBN.

        Returns:
            int: Cantidad de registros de stock cargados.
        """
        libros: Indice = self.__indice_libros()

        def crear(fila: FilaCsv) -> None:
            self.__servicio_stock.crear(
                _buscar_id(libros, _obligatorio(fila, "isbn"), "libro"),
                _a_entero(_obligatorio(fila, "cantidad"), "cantidad"),
                _a_entero(
                    _obligatorio(fila, "stock_minimo"), "stock_minimo"
                ),
            )

        return self.__cargar("stocks.csv", crear)

    def cargar_cotizaciones(self) -> int:
        """Carga las cotizaciones desde cotizaciones_dolar.csv.

        El tipo de cotización se indica por nombre.

        Returns:
            int: Cantidad de cotizaciones cargadas.
        """
        tipos: Indice = {
            _normalizar_clave(tipo.nombre): tipo.id
            for tipo in self.__servicio_tipos.listar()
        }

        def crear(fila: FilaCsv) -> None:
            self.__servicio_cotizaciones.crear(
                _buscar_id(
                    tipos, _obligatorio(fila, "tipo"), "tipo de cotización"
                ),
                _a_fecha(_obligatorio(fila, "fecha"), "fecha"),
                _a_decimal(_obligatorio(fila, "compra"), "compra"),
                _a_decimal(_obligatorio(fila, "venta"), "venta"),
            )

        return self.__cargar("cotizaciones_dolar.csv", crear)

    def __indice_libros(self) -> Indice:
        """Arma el índice de ISBN a id de libro.

        Returns:
            Indice: Diccionario de ISBN normalizado a id.
        """
        return {
            _normalizar_clave(libro.isbn): libro.id
            for libro in self.__servicio_libros.listar()
        }

    def __leer_filas(
        self, nombre_archivo: str
    ) -> Iterator[Tuple[int, FilaCsv]]:
        """Recorre las filas de un CSV junto con su número de línea.

        Args:
            nombre_archivo (str): Nombre del CSV dentro de la carpeta.

        Yields:
            Tuple[int, FilaCsv]: Número de línea y fila como diccionario.

        Raises:
            ValueError: Si el archivo no existe.
        """
        ruta: str = os.path.join(self.__carpeta_csv, nombre_archivo)
        if not os.path.exists(ruta):
            raise ValueError(f"No se encontró el archivo '{ruta}'.")
        with open(ruta, "r", encoding="utf-8", newline="") as archivo:
            lector: csv.DictReader = csv.DictReader(archivo)
            for fila in lector:
                yield lector.line_num, fila

    def __cargar(
        self,
        nombre_archivo: str,
        crear_desde_fila: Callable[[FilaCsv], None],
    ) -> int:
        """Aplica una función de alta a cada fila de un CSV.

        Args:
            nombre_archivo (str): Nombre del CSV dentro de la carpeta.
            crear_desde_fila (Callable[[FilaCsv], None]): Función que da de
                alta un registro a partir de una fila.

        Returns:
            int: Cantidad de registros cargados.

        Raises:
            ValueError: Si el archivo no existe o alguna fila es inválida;
                el mensaje indica archivo y número de línea.
        """
        cantidad: int = 0
        for linea, fila in self.__leer_filas(nombre_archivo):
            try:
                crear_desde_fila(fila)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"{nombre_archivo}, línea {linea}: {error}"
                ) from error
            cantidad += 1
        return cantidad
