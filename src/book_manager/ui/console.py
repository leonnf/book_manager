#@title Escritura de console.py
"""Interfaz de consola (CLI) de Book Manager.

Presenta los menús de cada entidad con su CRUD completo, la cotización de
libros y los reportes. Solo se comunica con la capa de servicios: lee los
datos del usuario, llama al servicio correspondiente y muestra el resultado
o el mensaje de error.
"""
import datetime
from typing import Callable, Dict, Optional, Sequence, Tuple, TypeVar

from book_manager.entities.entities import EntidadBase
from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioEntidad,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioReportes,
    ServicioStock,
    ServicioTipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)
V = TypeVar("V")
Accion = Callable[[], None]
OpcionesMenu = Dict[str, Tuple[str, Accion]]

FORMATO_FECHA: str = "%d/%m/%Y"


def formatear_monto(monto: float) -> str:
    """Formatea un monto con el estilo argentino (por ejemplo, 48.899,00).

    Args:
        monto (float): Monto a formatear.

    Returns:
        str: El monto con punto de miles y coma decimal.
    """
    texto: str = f"{monto:,.2f}"
    return texto.replace(",", "#").replace(".", ",").replace("#", ".")


def formatear_fecha(fecha: datetime.date) -> str:
    """Formatea una fecha como DD/MM/AAAA.

    Args:
        fecha (datetime.date): Fecha a formatear.

    Returns:
        str: La fecha formateada.
    """
    return fecha.strftime(FORMATO_FECHA)


def formatear_porcentaje(valor: float) -> str:
    """Formatea un porcentaje con signo y coma decimal (por ejemplo, +1,03 %).

    Args:
        valor (float): Porcentaje a formatear.

    Returns:
        str: El porcentaje formateado.
    """
    return f"{valor:+.2f} %".replace(".", ",")


def _convertir_texto(texto: str) -> str:
    """Devuelve el texto ingresado sin cambios.

    Args:
        texto (str): Texto ingresado.

    Returns:
        str: El mismo texto.
    """
    return texto


def _convertir_entero(texto: str) -> int:
    """Convierte el texto ingresado a entero.

    Args:
        texto (str): Texto ingresado.

    Returns:
        int: El número convertido.

    Raises:
        ValueError: Si el texto no representa un entero.
    """
    return int(texto)


def _convertir_decimal(texto: str) -> float:
    """Convierte a float un número escrito con coma o punto decimal.

    Args:
        texto (str): Texto ingresado (por ejemplo, 1465,50 o 1465.50).

    Returns:
        float: El número convertido.

    Raises:
        ValueError: Si el texto no representa un número.
    """
    return float(texto.replace(",", "."))


def _convertir_fecha(texto: str) -> datetime.date:
    """Convierte a fecha un texto con formato DD/MM/AAAA.

    Args:
        texto (str): Texto ingresado.

    Returns:
        datetime.date: La fecha convertida.

    Raises:
        ValueError: Si el texto no tiene formato DD/MM/AAAA.
    """
    return datetime.datetime.strptime(texto, FORMATO_FECHA).date()


class ConsolaBookManager:
    """Interfaz de consola del sistema de gestión de la librería.

    Args:
        servicio_libros (ServicioLibro): Servicio de libros.
        servicio_generos (ServicioGenero): Servicio de géneros.
        servicio_editoriales (ServicioEditorial): Servicio de editoriales.
        servicio_monedas (ServicioMoneda): Servicio de monedas.
        servicio_tipos (ServicioTipoCotizacion): Servicio de tipos de
            cotización.
        servicio_precios (ServicioPrecio): Servicio de precios.
        servicio_stock (ServicioStock): Servicio de stock.
        servicio_cotizaciones (ServicioCotizacionDolar): Servicio de
            cotizaciones.
        servicio_reportes (ServicioReportes): Servicio de reportes.
        entrada (Callable[[str], str]): Función que lee una respuesta del
            usuario; por defecto, input. En las pruebas se inyecta una
            función con respuestas simuladas.
    """

    def __init__(
        self,
        servicio_libros: ServicioLibro,
        servicio_generos: ServicioGenero,
        servicio_editoriales: ServicioEditorial,
        servicio_monedas: ServicioMoneda,
        servicio_tipos: ServicioTipoCotizacion,
        servicio_precios: ServicioPrecio,
        servicio_stock: ServicioStock,
        servicio_cotizaciones: ServicioCotizacionDolar,
        servicio_reportes: ServicioReportes,
        entrada: Callable[[str], str] = input,
    ) -> None:
        self.__servicio_libros: ServicioLibro = servicio_libros
        self.__servicio_generos: ServicioGenero = servicio_generos
        self.__servicio_editoriales: ServicioEditorial = servicio_editoriales
        self.__servicio_monedas: ServicioMoneda = servicio_monedas
        self.__servicio_tipos: ServicioTipoCotizacion = servicio_tipos
        self.__servicio_precios: ServicioPrecio = servicio_precios
        self.__servicio_stock: ServicioStock = servicio_stock
        self.__servicio_cotizaciones: ServicioCotizacionDolar = (
            servicio_cotizaciones
        )
        self.__servicio_reportes: ServicioReportes = servicio_reportes
        self.__entrada: Callable[[str], str] = entrada

    def ejecutar(self) -> None:
        """Muestra el menú principal hasta que el usuario elige salir.

        Si la entrada termina (EOFError) o se interrumpe la ejecución
        (KeyboardInterrupt), la consola se cierra con un mensaje.
        """
        print("=" * 60)
        print("BOOK MANAGER - Gestión de inventario de la librería")
        print("=" * 60)
        try:
            self._ejecutar_menu(
                "MENÚ PRINCIPAL",
                {
                    "1": ("Libros", self._menu_libros),
                    "2": ("Géneros", self._menu_generos),
                    "3": ("Editoriales", self._menu_editoriales),
                    "4": ("Monedas", self._menu_monedas),
                    "5": ("Tipos de cotización", self._menu_tipos),
                    "6": ("Precios", self._menu_precios),
                    "7": ("Stock", self._menu_stock),
                    "8": ("Cotizaciones del dólar", self._menu_cotizaciones),
                    "9": ("Reportes", self._menu_reportes),
                },
                "Salir",
            )
        except (EOFError, KeyboardInterrupt):
            print("\nEntrada finalizada: se cierra Book Manager.")
            return
        print("\nHasta luego.")

    # ------------------------------------------------------------------
    # Menús y ejecución de acciones
    # ------------------------------------------------------------------

    def _ejecutar_menu(
        self, titulo: str, opciones: OpcionesMenu, texto_salida: str = "Volver"
    ) -> None:
        """Muestra un menú y ejecuta la acción elegida hasta volver.

        Los errores de negocio de cada acción se muestran como mensaje y el
        menú sigue funcionando.

        Args:
            titulo (str): Título del menú.
            opciones (OpcionesMenu): Opción, texto y acción de cada entrada.
            texto_salida (str): Texto de la opción 0.
        """
        while True:
            print(f"\n=== {titulo} ===")
            for clave, (texto, _) in opciones.items():
                print(f"  {clave}. {texto}")
            print(f"  0. {texto_salida}")
            opcion: str = self._leer("Opción: ")
            if opcion == "0":
                return
            if opcion not in opciones:
                print("  Opción inválida.")
                continue
            _, accion = opciones[opcion]
            try:
                accion()
            except (TypeError, ValueError) as error:
                print(f"  Error: {error}")

    def _menu_libros(self) -> None:
        """Muestra el menú de libros."""
        self._ejecutar_menu(
            "LIBROS",
            {
                "1": ("Listar", lambda: self._mostrar_listado(
                    "Libros", self.__servicio_libros.listar())),
                "2": ("Ver detalle", self._ver_libro),
                "3": ("Alta", self._alta_libro),
                "4": ("Modificación", self._modificar_libro),
                "5": ("Baja", lambda: self._baja(
                    self.__servicio_libros, "Id del libro")),
                "6": ("Cotizar libro", self._cotizar_libro),
            },
        )

    def _menu_generos(self) -> None:
        """Muestra el menú de géneros."""
        self._ejecutar_menu(
            "GÉNEROS",
            {
                "1": ("Listar", lambda: self._mostrar_listado(
                    "Géneros", self.__servicio_generos.listar())),
                "2": ("Ver detalle", lambda: self._ver(
                    self.__servicio_generos, "Id del género")),
                "3": ("Alta", self._alta_genero),
                "4": ("Modificación", self._modificar_genero),
                "5": ("Baja", lambda: self._baja(
                    self.__servicio_generos, "Id del género")),
            },
        )

    def _menu_editoriales(self) -> None:
        """Muestra el menú de editoriales."""
        self._ejecutar_menu(
            "EDITORIALES",
            {
                "1": ("Listar", lambda: self._mostrar_listado(
                    "Editoriales", self.__servicio_editoriales.listar())),
                "2": ("Ver detalle", lambda: self._ver(
                    self.__servicio_editoriales, "Id de la editorial")),
                "3": ("Alta", self._alta_editorial),
                "4": ("Modificación", self._modificar_editorial),
                "5": ("Baja", lambda: self._baja(
                    self.__servicio_editoriales, "Id de la editorial")),
            },
        )

    def _menu_monedas(self) -> None:
        """Muestra el menú de monedas."""
        self._ejecutar_menu(
            "MONEDAS",
            {
                "1": ("Listar", lambda: self._mostrar_listado(
                    "Monedas", self.__servicio_monedas.listar())),
                "2": ("Ver detalle", lambda: self._ver(
                    self.__servicio_monedas, "Id de la moneda")),
                "3": ("Alta", self._alta_moneda),
                "4": ("Modificación", self._modificar_moneda),
                "5": ("Baja", lambda: self._baja(
                    self.__servicio_monedas, "Id de la moneda")),
            },
        )

    def _menu_tipos(self) -> None:
        """Muestra el menú de tipos de cotización."""
        self._ejecutar_menu(
            "TIPOS DE COTIZACIÓN",
            {
                "1": ("Listar", lambda: self._mostrar_listado(
                    "Tipos de cotización", self.__servicio_tipos.listar())),
                "2": ("Ver detalle", lambda: self._ver(
                    self.__servicio_tipos, "Id del tipo de cotización")),
                "3": ("Alta", self._alta_tipo),
                "4": ("Modificación", self._modificar_tipo),
                "5": ("Baja", lambda: self._baja(
                    self.__servicio_tipos, "Id del tipo de cotización")),
            },
        )

    def _menu_precios(self) -> None:
        """Muestra el menú de precios."""
        self._ejecutar_menu(
            "PRECIOS",
            {
                "1": ("Listar", lambda: self._mostrar_listado(
                    "Precios", self.__servicio_precios.listar())),
                "2": ("Ver detalle", lambda: self._ver(
                    self.__servicio_precios, "Id del precio")),
                "3": ("Alta", self._alta_precio),
                "4": ("Modificación", self._modificar_precio),
                "5": ("Baja", lambda: self._baja(
                    self.__servicio_precios, "Id del precio")),
            },
        )

    def _menu_stock(self) -> None:
        """Muestra el menú de stock."""
        self._ejecutar_menu(
            "STOCK",
            {
                "1": ("Listar", lambda: self._mostrar_listado(
                    "Stock", self.__servicio_stock.listar())),
                "2": ("Ver detalle", self._ver_stock),
                "3": ("Alta", self._alta_stock),
                "4": ("Modificación", self._modificar_stock),
                "5": ("Baja", self._baja_stock),
                "6": ("Registrar ingreso", self._ingreso_stock),
                "7": ("Registrar egreso", self._egreso_stock),
            },
        )

    def _menu_cotizaciones(self) -> None:
        """Muestra el menú de cotizaciones del dólar."""
        self._ejecutar_menu(
            "COTIZACIONES DEL DÓLAR",
            {
                "1": ("Listar", lambda: self._mostrar_listado(
                    "Cotizaciones", self.__servicio_cotizaciones.listar())),
                "2": ("Ver detalle", self._ver_cotizacion),
                "3": ("Alta", self._alta_cotizacion),
                "4": ("Modificación", self._modificar_cotizacion),
                "5": ("Baja", self._baja_cotizacion),
            },
        )

    def _menu_reportes(self) -> None:
        """Muestra el menú de reportes."""
        self._ejecutar_menu(
            "REPORTES",
            {
                "1": ("Inventario valorizado en ARS",
                      self._reporte_inventario),
                "2": ("Libros con stock bajo el mínimo",
                      self._reporte_stock_bajo),
                "3": ("Histórico de un tipo de cotización",
                      self._reporte_historico),
            },
        )

    # ------------------------------------------------------------------
    # Lectura de datos
    # ------------------------------------------------------------------

    def _leer(self, mensaje: str) -> str:
        """Lee una respuesta del usuario sin espacios extremos.

        Args:
            mensaje (str): Pregunta a mostrar.

        Returns:
            str: La respuesta ingresada.
        """
        return self.__entrada(mensaje).strip()

    def _pedir(
        self,
        mensaje: str,
        convertir: Callable[[str], V],
        error: str,
        actual: Optional[V] = None,
        actual_visible: Optional[str] = None,
    ) -> V:
        """Pide un valor obligatorio hasta que tenga formato válido.

        Si hay un valor actual, se muestra entre corchetes y Enter lo
        conserva.

        Args:
            mensaje (str): Pregunta a mostrar.
            convertir (Callable[[str], V]): Conversión del texto al tipo
                esperado; lanza ValueError si el formato es inválido.
            error (str): Mensaje a mostrar ante un formato inválido.
            actual (Optional[V]): Valor actual, o None si no hay.
            actual_visible (Optional[str]): Cómo mostrar el valor actual.

        Returns:
            V: El valor ingresado o el actual.
        """
        pregunta: str = f"{mensaje}: "
        if actual is not None:
            visible: str = (
                actual_visible if actual_visible is not None else str(actual)
            )
            pregunta = f"{mensaje} [{visible}]: "
        while True:
            texto: str = self._leer(pregunta)
            if not texto:
                if actual is not None:
                    return actual
                print("  El valor es obligatorio.")
                continue
            try:
                return convertir(texto)
            except ValueError:
                print(f"  {error}")

    def _pedir_opcional(
        self,
        mensaje: str,
        convertir: Callable[[str], V],
        error: str,
        actual: Optional[V] = None,
        conservar: bool = False,
    ) -> Optional[V]:
        """Pide un valor opcional.

        En un alta, Enter deja el valor vacío. En una modificación
        (conservar=True), Enter conserva el valor actual y '-' lo borra.

        Args:
            mensaje (str): Pregunta a mostrar.
            convertir (Callable[[str], V]): Conversión del texto.
            error (str): Mensaje a mostrar ante un formato inválido.
            actual (Optional[V]): Valor actual, o None si no hay.
            conservar (bool): Si Enter conserva el valor actual.

        Returns:
            Optional[V]: El valor ingresado, el actual o None.
        """
        if conservar:
            visible: str = "vacío" if actual is None else str(actual)
            pregunta: str = (
                f"{mensaje} [{visible}] (Enter conserva, '-' borra): "
            )
        else:
            pregunta = f"{mensaje} (Enter para omitir): "
        while True:
            texto: str = self._leer(pregunta)
            if not texto:
                return actual if conservar else None
            if texto == "-":
                return None
            try:
                return convertir(texto)
            except ValueError:
                print(f"  {error}")

    def _pedir_texto(self, mensaje: str, actual: Optional[str] = None) -> str:
        """Pide un texto obligatorio.

        Args:
            mensaje (str): Pregunta a mostrar.
            actual (Optional[str]): Valor actual, que Enter conserva.

        Returns:
            str: El texto ingresado o el actual.
        """
        return self._pedir(mensaje, _convertir_texto, "", actual)

    def _pedir_entero(self, mensaje: str, actual: Optional[int] = None) -> int:
        """Pide un número entero obligatorio.

        Args:
            mensaje (str): Pregunta a mostrar.
            actual (Optional[int]): Valor actual, que Enter conserva.

        Returns:
            int: El número ingresado o el actual.
        """
        return self._pedir(
            mensaje, _convertir_entero, "Ingrese un número entero.", actual
        )

    def _pedir_decimal(
        self, mensaje: str, actual: Optional[float] = None
    ) -> float:
        """Pide un número decimal obligatorio (coma o punto decimal).

        Args:
            mensaje (str): Pregunta a mostrar.
            actual (Optional[float]): Valor actual, que Enter conserva.

        Returns:
            float: El número ingresado o el actual.
        """
        visible: Optional[str] = None
        if actual is not None:
            visible = f"{actual:.2f}".replace(".", ",")
        return self._pedir(
            mensaje,
            _convertir_decimal,
            "Ingrese un número con coma o punto decimal, sin separador de "
            "miles.",
            actual,
            visible,
        )

    def _pedir_fecha(
        self, mensaje: str, actual: Optional[datetime.date] = None
    ) -> datetime.date:
        """Pide una fecha obligatoria con formato DD/MM/AAAA.

        Args:
            mensaje (str): Pregunta a mostrar.
            actual (Optional[datetime.date]): Valor actual, que Enter
                conserva.

        Returns:
            datetime.date: La fecha ingresada o la actual.
        """
        visible: Optional[str] = None
        if actual is not None:
            visible = formatear_fecha(actual)
        return self._pedir(
            f"{mensaje} (DD/MM/AAAA)",
            _convertir_fecha,
            "Ingrese una fecha válida con formato DD/MM/AAAA.",
            actual,
            visible,
        )

    def _confirmar(self, mensaje: str) -> bool:
        """Pide una confirmación por sí o por no.

        Args:
            mensaje (str): Pregunta a mostrar.

        Returns:
            bool: True si el usuario confirma.
        """
        while True:
            respuesta: str = self._leer(f"{mensaje} (s/n): ").lower()
            if respuesta in ("s", "si", "sí"):
                return True
            if respuesta in ("n", "no"):
                return False
            print("  Responda 's' o 'n'.")

    def _pedir_id_con_listado(
        self,
        servicio: ServicioEntidad[T],
        titulo: str,
        etiqueta_id: str,
        actual: Optional[int] = None,
    ) -> int:
        """Muestra el listado de una entidad y pide uno de sus ids.

        Args:
            servicio (ServicioEntidad[T]): Servicio de la entidad.
            titulo (str): Título del listado.
            etiqueta_id (str): Pregunta para el id.
            actual (Optional[int]): Id actual, que Enter conserva.

        Returns:
            int: El id ingresado o el actual.
        """
        self._mostrar_listado(titulo, servicio.listar())
        return self._pedir_entero(etiqueta_id, actual)

    # ------------------------------------------------------------------
    # Acciones genéricas
    # ------------------------------------------------------------------

    @staticmethod
    def _mostrar_listado(titulo: str, elementos: Sequence[object]) -> None:
        """Imprime un listado con su cantidad de elementos.

        Args:
            titulo (str): Título del listado.
            elementos (Sequence[object]): Elementos a mostrar.
        """
        print(f"\n--- {titulo} ({len(elementos)}) ---")
        if not elementos:
            print("  (sin registros)")
        for elemento in elementos:
            print(f"  {elemento}")

    def _ver(self, servicio: ServicioEntidad[T], etiqueta_id: str) -> None:
        """Muestra una entidad buscada por id.

        Args:
            servicio (ServicioEntidad[T]): Servicio de la entidad.
            etiqueta_id (str): Pregunta para el id.
        """
        entidad: T = servicio.obtener(self._pedir_entero(etiqueta_id))
        print(f"  {entidad}")

    def _baja(self, servicio: ServicioEntidad[T], etiqueta_id: str) -> None:
        """Da de baja una entidad buscada por id, previa confirmación.

        Args:
            servicio (ServicioEntidad[T]): Servicio de la entidad.
            etiqueta_id (str): Pregunta para el id.
        """
        id_entidad: int = self._pedir_entero(etiqueta_id)
        entidad: T = servicio.obtener(id_entidad)
        print(f"  {entidad}")
        if self._confirmar("¿Confirma la baja?"):
            servicio.eliminar(id_entidad)
            print("  Baja realizada.")
        else:
            print("  Baja cancelada.")

    # ------------------------------------------------------------------
    # Libros
    # ------------------------------------------------------------------

    def _ver_libro(self) -> None:
        """Muestra todos los datos de un libro, sus precios y su stock."""
        libro = self.__servicio_libros.obtener(
            self._pedir_entero("Id del libro")
        )
        paginas: str = (
            "sin dato" if libro.paginas is None else str(libro.paginas)
        )
        url: str = (
            "sin dato" if libro.url_referencia is None
            else libro.url_referencia
        )
        print(f"\n  Id: {libro.id}")
        print(f"  ISBN: {libro.isbn}")
        print(f"  Título: {libro.titulo}")
        print(f"  Autor: {libro.autor}")
        print(f"  Año de publicación: {libro.anio_publicacion}")
        print(f"  Género: {libro.genero.nombre}")
        print(f"  Editorial: {libro.editorial.nombre}")
        print(f"  Idioma: {libro.idioma}")
        print(f"  Páginas: {paginas}")
        print(f"  URL de referencia: {url}")
        self._mostrar_listado(
            "Precios del libro",
            self.__servicio_precios.listar_por_libro(libro.id),
        )
        try:
            stock = self.__servicio_stock.obtener(libro.id)
            print(
                f"  Stock: {stock.cantidad} unidades "
                f"(mínimo {stock.stock_minimo})"
            )
        except ValueError:
            print("  Stock: sin registro de stock.")

    def _alta_libro(self) -> None:
        """Da de alta un libro."""
        isbn: str = self._pedir_texto("ISBN (13 dígitos)")
        titulo: str = self._pedir_texto("Título")
        autor: str = self._pedir_texto("Autor (APELLIDO, NOMBRE)")
        anio: int = self._pedir_entero("Año de publicación")
        genero_id: int = self._pedir_id_con_listado(
            self.__servicio_generos, "Géneros", "Id del género"
        )
        editorial_id: int = self._pedir_id_con_listado(
            self.__servicio_editoriales, "Editoriales", "Id de la editorial"
        )
        idioma: str = self._pedir_texto("Idioma", "Español")
        paginas: Optional[int] = self._pedir_opcional(
            "Páginas", _convertir_entero, "Ingrese un número entero."
        )
        url: Optional[str] = self._pedir_opcional(
            "URL de referencia", _convertir_texto, ""
        )
        libro = self.__servicio_libros.crear(
            isbn, titulo, autor, anio, genero_id, editorial_id, idioma,
            paginas, url,
        )
        print(f"  Libro creado: {libro}")

    def _modificar_libro(self) -> None:
        """Modifica un libro; Enter conserva cada valor actual."""
        libro = self.__servicio_libros.obtener(
            self._pedir_entero("Id del libro")
        )
        isbn: str = self._pedir_texto("ISBN", libro.isbn)
        titulo: str = self._pedir_texto("Título", libro.titulo)
        autor: str = self._pedir_texto("Autor", libro.autor)
        anio: int = self._pedir_entero(
            "Año de publicación", libro.anio_publicacion
        )
        genero_id: int = self._pedir_id_con_listado(
            self.__servicio_generos, "Géneros", "Id del género",
            libro.genero.id,
        )
        editorial_id: int = self._pedir_id_con_listado(
            self.__servicio_editoriales, "Editoriales", "Id de la editorial",
            libro.editorial.id,
        )
        idioma: str = self._pedir_texto("Idioma", libro.idioma)
        paginas: Optional[int] = self._pedir_opcional(
            "Páginas", _convertir_entero, "Ingrese un número entero.",
            libro.paginas, conservar=True,
        )
        url: Optional[str] = self._pedir_opcional(
            "URL de referencia", _convertir_texto, "",
            libro.url_referencia, conservar=True,
        )
        libro = self.__servicio_libros.actualizar(
            libro.id, isbn, titulo, autor, anio, genero_id, editorial_id,
            idioma, paginas, url,
        )
        print(f"  Libro actualizado: {libro}")

    def _cotizar_libro(self) -> None:
        """Muestra el precio de un libro en ARS y USD según la cotización."""
        libro = self.__servicio_libros.obtener(
            self._pedir_entero("Id del libro")
        )
        tipo_id: int = self._pedir_tipo_cotizacion()
        cotizacion = self.__servicio_cotizaciones.obtener_vigente(tipo_id)
        monto_ars, monto_usd = self.__servicio_precios.cotizar_libro(
            libro.id, tipo_id
        )
        print(f"\n  {libro.titulo}")
        print(f"  Cotización aplicada: {cotizacion}")
        print(f"  Precio en ARS: $ {formatear_monto(monto_ars)}")
        print(f"  Precio en USD: U$s {formatear_monto(monto_usd)}")

    # ------------------------------------------------------------------
    # Géneros, editoriales, monedas y tipos de cotización
    # ------------------------------------------------------------------

    def _alta_genero(self) -> None:
        """Da de alta un género."""
        genero = self.__servicio_generos.crear(
            self._pedir_texto("Nombre"), self._pedir_texto("Descripción")
        )
        print(f"  Género creado: {genero}")

    def _modificar_genero(self) -> None:
        """Modifica un género; Enter conserva cada valor actual."""
        genero = self.__servicio_generos.obtener(
            self._pedir_entero("Id del género")
        )
        genero = self.__servicio_generos.actualizar(
            genero.id,
            self._pedir_texto("Nombre", genero.nombre),
            self._pedir_texto("Descripción", genero.descripcion),
        )
        print(f"  Género actualizado: {genero}")

    def _alta_editorial(self) -> None:
        """Da de alta una editorial."""
        editorial = self.__servicio_editoriales.crear(
            self._pedir_texto("Nombre"),
            self._pedir_texto("País de origen"),
            self._pedir_opcional("Email de contacto", _convertir_texto, ""),
        )
        print(f"  Editorial creada: {editorial}")

    def _modificar_editorial(self) -> None:
        """Modifica una editorial; Enter conserva cada valor actual."""
        editorial = self.__servicio_editoriales.obtener(
            self._pedir_entero("Id de la editorial")
        )
        editorial = self.__servicio_editoriales.actualizar(
            editorial.id,
            self._pedir_texto("Nombre", editorial.nombre),
            self._pedir_texto("País de origen", editorial.pais_origen),
            self._pedir_opcional(
                "Email de contacto", _convertir_texto, "",
                editorial.email_contacto, conservar=True,
            ),
        )
        print(f"  Editorial actualizada: {editorial}")

    def _alta_moneda(self) -> None:
        """Da de alta una moneda."""
        moneda = self.__servicio_monedas.crear(
            self._pedir_texto("Código ISO (3 letras)"),
            self._pedir_texto("Nombre"),
            self._pedir_texto("Símbolo"),
        )
        print(f"  Moneda creada: {moneda}")

    def _modificar_moneda(self) -> None:
        """Modifica una moneda; Enter conserva cada valor actual."""
        moneda = self.__servicio_monedas.obtener(
            self._pedir_entero("Id de la moneda")
        )
        moneda = self.__servicio_monedas.actualizar(
            moneda.id,
            self._pedir_texto("Código ISO", moneda.codigo),
            self._pedir_texto("Nombre", moneda.nombre),
            self._pedir_texto("Símbolo", moneda.simbolo),
        )
        print(f"  Moneda actualizada: {moneda}")

    def _alta_tipo(self) -> None:
        """Da de alta un tipo de cotización."""
        tipo = self.__servicio_tipos.crear(
            self._pedir_texto("Nombre"), self._pedir_texto("Descripción")
        )
        print(f"  Tipo de cotización creado: {tipo}")

    def _modificar_tipo(self) -> None:
        """Modifica un tipo de cotización; Enter conserva cada valor."""
        tipo = self.__servicio_tipos.obtener(
            self._pedir_entero("Id del tipo de cotización")
        )
        tipo = self.__servicio_tipos.actualizar(
            tipo.id,
            self._pedir_texto("Nombre", tipo.nombre),
            self._pedir_texto("Descripción", tipo.descripcion),
        )
        print(f"  Tipo de cotización actualizado: {tipo}")

    # ------------------------------------------------------------------
    # Precios
    # ------------------------------------------------------------------

    def _alta_precio(self) -> None:
        """Da de alta un precio; Enter en la fecha usa la fecha de hoy."""
        libro_id: int = self._pedir_id_con_listado(
            self.__servicio_libros, "Libros", "Id del libro"
        )
        moneda_id: int = self._pedir_id_con_listado(
            self.__servicio_monedas, "Monedas", "Id de la moneda"
        )
        monto: float = self._pedir_decimal("Monto")
        fecha: datetime.date = self._pedir_fecha(
            "Vigente desde", datetime.date.today()
        )
        precio = self.__servicio_precios.crear(
            libro_id, moneda_id, monto, fecha
        )
        print(f"  Precio creado: {precio}")

    def _modificar_precio(self) -> None:
        """Modifica un precio; Enter conserva cada valor actual."""
        precio = self.__servicio_precios.obtener(
            self._pedir_entero("Id del precio")
        )
        libro_id: int = self._pedir_id_con_listado(
            self.__servicio_libros, "Libros", "Id del libro", precio.libro.id
        )
        moneda_id: int = self._pedir_id_con_listado(
            self.__servicio_monedas, "Monedas", "Id de la moneda",
            precio.moneda.id,
        )
        monto: float = self._pedir_decimal("Monto", precio.monto)
        fecha: datetime.date = self._pedir_fecha(
            "Vigente desde", precio.fecha_vigencia
        )
        precio = self.__servicio_precios.actualizar(
            precio.id, libro_id, moneda_id, monto, fecha
        )
        print(f"  Precio actualizado: {precio}")

    # ------------------------------------------------------------------
    # Stock
    # ------------------------------------------------------------------

    def _ver_stock(self) -> None:
        """Muestra el stock de un libro."""
        stock = self.__servicio_stock.obtener(
            self._pedir_entero("Id del libro")
        )
        print(f"  {stock}")

    def _alta_stock(self) -> None:
        """Da de alta el stock de un libro."""
        libro_id: int = self._pedir_id_con_listado(
            self.__servicio_libros, "Libros", "Id del libro"
        )
        stock = self.__servicio_stock.crear(
            libro_id,
            self._pedir_entero("Cantidad"),
            self._pedir_entero("Stock mínimo", 0),
        )
        print(f"  Stock creado: {stock}")

    def _modificar_stock(self) -> None:
        """Modifica cantidad y mínimo del stock; Enter conserva cada valor."""
        stock = self.__servicio_stock.obtener(
            self._pedir_entero("Id del libro")
        )
        stock = self.__servicio_stock.actualizar(
            stock.libro_id,
            self._pedir_entero("Cantidad", stock.cantidad),
            self._pedir_entero("Stock mínimo", stock.stock_minimo),
        )
        print(f"  Stock actualizado: {stock}")

    def _baja_stock(self) -> None:
        """Da de baja el stock de un libro, previa confirmación."""
        stock = self.__servicio_stock.obtener(
            self._pedir_entero("Id del libro")
        )
        print(f"  {stock}")
        if self._confirmar("¿Confirma la baja?"):
            self.__servicio_stock.eliminar(stock.libro_id)
            print("  Baja realizada.")
        else:
            print("  Baja cancelada.")

    def _ingreso_stock(self) -> None:
        """Registra el ingreso de unidades de un libro."""
        libro_id: int = self._pedir_entero("Id del libro")
        cantidad: int = self._pedir_entero("Unidades que ingresan")
        stock = self.__servicio_stock.registrar_ingreso(libro_id, cantidad)
        print(f"  Stock actualizado: {stock}")

    def _egreso_stock(self) -> None:
        """Registra el egreso de unidades de un libro."""
        libro_id: int = self._pedir_entero("Id del libro")
        cantidad: int = self._pedir_entero("Unidades que egresan")
        stock = self.__servicio_stock.registrar_egreso(libro_id, cantidad)
        print(f"  Stock actualizado: {stock}")

    # ------------------------------------------------------------------
    # Cotizaciones del dólar
    # ------------------------------------------------------------------

    def _pedir_tipo_cotizacion(self) -> int:
        """Muestra los tipos de cotización y pide uno.

        Returns:
            int: Id del tipo elegido.
        """
        return self._pedir_id_con_listado(
            self.__servicio_tipos, "Tipos de cotización",
            "Id del tipo de cotización",
        )

    def _ver_cotizacion(self) -> None:
        """Muestra una cotización buscada por tipo y fecha."""
        tipo_id: int = self._pedir_tipo_cotizacion()
        fecha: datetime.date = self._pedir_fecha("Fecha")
        print(f"  {self.__servicio_cotizaciones.obtener(tipo_id, fecha)}")

    def _alta_cotizacion(self) -> None:
        """Da de alta una cotización; Enter en la fecha usa hoy."""
        tipo_id: int = self._pedir_tipo_cotizacion()
        fecha: datetime.date = self._pedir_fecha(
            "Fecha", datetime.date.today()
        )
        cotizacion = self.__servicio_cotizaciones.crear(
            tipo_id,
            fecha,
            self._pedir_decimal("Compra"),
            self._pedir_decimal("Venta"),
        )
        print(f"  Cotización creada: {cotizacion}")

    def _modificar_cotizacion(self) -> None:
        """Modifica compra y venta de una cotización."""
        tipo_id: int = self._pedir_tipo_cotizacion()
        fecha: datetime.date = self._pedir_fecha("Fecha")
        cotizacion = self.__servicio_cotizaciones.obtener(tipo_id, fecha)
        cotizacion = self.__servicio_cotizaciones.actualizar(
            tipo_id,
            fecha,
            self._pedir_decimal("Compra", cotizacion.compra),
            self._pedir_decimal("Venta", cotizacion.venta),
        )
        print(f"  Cotización actualizada: {cotizacion}")

    def _baja_cotizacion(self) -> None:
        """Da de baja una cotización, previa confirmación."""
        tipo_id: int = self._pedir_tipo_cotizacion()
        fecha: datetime.date = self._pedir_fecha("Fecha")
        cotizacion = self.__servicio_cotizaciones.obtener(tipo_id, fecha)
        print(f"  {cotizacion}")
        if self._confirmar("¿Confirma la baja?"):
            self.__servicio_cotizaciones.eliminar(tipo_id, fecha)
            print("  Baja realizada.")
        else:
            print("  Baja cancelada.")

    # ------------------------------------------------------------------
    # Reportes
    # ------------------------------------------------------------------

    def _reporte_inventario(self) -> None:
        """Muestra el inventario valorizado en ARS con la cotización elegida."""
        tipo_id: int = self._pedir_tipo_cotizacion()
        cotizacion = self.__servicio_cotizaciones.obtener_vigente(tipo_id)
        filas = self.__servicio_reportes.filas_inventario_valorizado(tipo_id)
        print("\n--- Inventario valorizado en ARS ---")
        print(f"  Cotización aplicada: {cotizacion}")
        for stock, precio_ars, subtotal in filas:
            if precio_ars is None or subtotal is None:
                detalle: str = "sin precio en ARS ni en USD"
            else:
                detalle = (
                    f"{stock.cantidad} u. x $ {formatear_monto(precio_ars)}"
                    f" = $ {formatear_monto(subtotal)}"
                )
            print(f"  {stock.libro.titulo}: {detalle}")
        total: float = self.__servicio_reportes.total_inventario_valorizado(
            tipo_id
        )
        print(f"  TOTAL: $ {formatear_monto(total)}")

    def _reporte_stock_bajo(self) -> None:
        """Muestra los libros con stock por debajo del mínimo."""
        bajos = self.__servicio_reportes.libros_bajo_stock_minimo()
        print(f"\n--- Libros con stock bajo el mínimo ({len(bajos)}) ---")
        if not bajos:
            print("  (ningún libro por debajo del mínimo)")
        for stock in bajos:
            faltante: int = stock.stock_minimo - stock.cantidad
            print(
                f"  {stock.libro.titulo}: {stock.cantidad} u. "
                f"(mínimo {stock.stock_minimo}, faltan {faltante})"
            )

    def _reporte_historico(self) -> None:
        """Muestra el histórico de un tipo de cotización y su variación."""
        tipo_id: int = self._pedir_tipo_cotizacion()
        self._mostrar_listado(
            "Histórico de cotizaciones",
            self.__servicio_reportes.historico_cotizacion(tipo_id),
        )
        variacion: Optional[float] = (
            self.__servicio_reportes.variacion_porcentual(tipo_id)
        )
        if variacion is None:
            print("  Variación: se necesitan al menos dos cotizaciones.")
        else:
            print(
                "  Variación de la venta (primera a última): "
                f"{formatear_porcentaje(variacion)}"
            )
