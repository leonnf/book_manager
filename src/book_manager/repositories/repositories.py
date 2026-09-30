#@title Escritura de repositories.py
"""Repositorios de Book Manager: persistencia de entidades en archivos JSON.

Contiene las interfaces definidas por la cátedra y sus implementaciones.
Cada repositorio guarda una entidad en su propio archivo JSON. En disco, las
relaciones se guardan como ids. Al leer, se rehidratan como objetos usando
los repositorios que cada uno recibe por constructor.
"""
import abc
import datetime
import json
import os
from typing import Any, Dict, Generic, List, Optional, TypeVar

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    EntidadBase,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)

T = TypeVar('T', bound=EntidadBase)
R = TypeVar("R")
Registro = Dict[str, Any]


class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios que manejan entidades con operaciones CRUD básicas."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea una nueva entidad en el repositorio.

        Args:
            entidad (T): La entidad a crear.

        Returns:
            T: La entidad creada.

        Raises:
            ValueError: Si ya existe una entidad con el mismo ID.
        """
        pass

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a leer.

        Returns:
            Optional[T]: La entidad si se encuentra, None en caso contrario.
        """
        pass

    @abc.abstractmethod
    def leer_todos(self) -> List[T]:
        """Lee todas las entidades del repositorio.

        Returns:
            List[T]: Una lista de todas las entidades.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en el repositorio.

        Args:
            entidad (T): La entidad a actualizar (debe tener un ID existente).

        Returns:
            T: La entidad actualizada.

        Raises:
            ValueError: Si no se encuentra la entidad para actualizar.
        """
        pass

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        """Elimina una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a eliminar.

        Returns:
            bool: True si la entidad fue eliminada, False si no se encontró.
        """
        pass


class IRepositorioStock(abc.ABC):
    """Interfaz para repositorios del tipo Stock."""

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro de stock.

        Args:
            stock (Stock): El objeto Stock a crear.

        Returns:
            Stock: El objeto Stock creado.

        Raises:
            ValueError: Si ya existe un registro de stock para el mismo libro.
        """
        pass

    @abc.abstractmethod
    def leer_por_libro(self, libro_id: int) -> Optional['Stock']:
        """Lee un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock.

        Returns:
            Optional[Stock]: El objeto Stock si se encuentra, None en caso contrario.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, stock: 'Stock') -> 'Stock':
        """Actualiza un registro de stock existente.

        Args:
            stock (Stock): El objeto Stock a actualizar (debe tener un libro_id existente).

        Returns:
            Stock: El objeto Stock actualizado.

        Raises:
            ValueError: Si no se encuentra el stock para actualizar.
        """
        pass

    @abc.abstractmethod
    def eliminar(self, libro_id: int) -> bool:
        """Elimina un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock a eliminar.

        Returns:
            bool: True si el stock fue eliminado, False si no se encontró.
        """
        pass


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para repositorios del tipo RepositorioCotizacionDolar."""

    @abc.abstractmethod
    def crear(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
        """Crea una nueva cotización de dólar.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a crear.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar creado.

        Raises:
            ValueError: Si ya existe una cotización para el mismo tipo y fecha.
        """
        pass

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: datetime.date) -> Optional['CotizacionDolar']:
        """Lee una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización (e.g., 'Oficial', 'Blue').
            fecha (datetime.date): La fecha de la cotización.

        Returns:
            Optional[CotizacionDolar]: La cotización si se encuentra, None en caso contrario.
        """
        pass

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> List['CotizacionDolar']:
        """Lee el histórico de cotizaciones para un tipo específico.

        Args:
            tipo_id (int): El ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Una lista de cotizaciones históricas para el tipo dado.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
        """Actualiza una cotización de dólar existente.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a actualizar.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar actualizado.
        """
        pass

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Elimina una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización.
            fecha (datetime.date): La fecha de la cotización a eliminar.

        Returns:
            bool: True si la cotización fue eliminada, False si no se encontró.
        """
        pass


def _exigir_relacionado(entidad: Optional[R], nombre: str, id: int) -> R:
    """Verifica que exista la entidad relacionada al rehidratar un registro.

    Args:
        entidad (Optional[R]): Entidad obtenida del repositorio relacionado.
        nombre (str): Nombre de la clase relacionada, para el mensaje.
        id (int): Id buscado, para el mensaje.

    Returns:
        R: La entidad relacionada.

    Raises:
        ValueError: Si la entidad relacionada no existe.
    """
    if entidad is None:
        raise ValueError(
            f"Datos inconsistentes: no existe {nombre} con id {id}."
        )
    return entidad


class ArchivoJson:
    """Acceso a un archivo JSON que contiene una lista de registros.

    Args:
        ruta (str): Ruta del archivo JSON.

    Raises:
        TypeError: Si la ruta no es un texto.
        ValueError: Si la ruta está vacía.
    """

    def __init__(self, ruta: str) -> None:
        if not isinstance(ruta, str):
            raise TypeError("La ruta del archivo debe ser de tipo str.")
        if not ruta.strip():
            raise ValueError("La ruta del archivo no puede estar vacía.")
        self.__ruta: str = ruta

    @property
    def ruta(self) -> str:
        """str: Ruta del archivo JSON."""
        return self.__ruta

    def leer(self) -> List[Registro]:
        """Lee todos los registros del archivo.

        Returns:
            List[Registro]: Los registros guardados, o una lista vacía si el
                archivo todavía no existe.

        Raises:
            ValueError: Si el archivo no contiene una lista JSON válida.
        """
        if not os.path.exists(self.__ruta):
            return []
        try:
            with open(self.__ruta, "r", encoding="utf-8") as archivo:
                datos: Any = json.load(archivo)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"El archivo '{self.__ruta}' no contiene JSON válido."
            ) from error
        if not isinstance(datos, list):
            raise ValueError(
                f"El archivo '{self.__ruta}' debe contener una lista."
            )
        return datos

    def escribir(self, registros: List[Registro]) -> None:
        """Reemplaza el contenido del archivo con los registros recibidos.

        Crea la carpeta contenedora si todavía no existe.

        Args:
            registros (List[Registro]): Registros a guardar.
        """
        carpeta: str = os.path.dirname(self.__ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(self.__ruta, "w", encoding="utf-8") as archivo:
            json.dump(registros, archivo, indent=2, ensure_ascii=False)
            archivo.write("\n")


class RepositorioJsonBase(IRepositorio[T]):
    """Repositorio genérico que implementa el CRUD sobre un archivo JSON.

    Las subclases solo definen cómo convertir su entidad a diccionario y
    viceversa (patrón Template Method).

    Args:
        ruta_archivo (str): Ruta del archivo JSON de la entidad.
    """

    def __init__(self, ruta_archivo: str) -> None:
        self.__archivo: ArchivoJson = ArchivoJson(ruta_archivo)

    @abc.abstractmethod
    def _a_dict(self, entidad: T) -> Registro:
        """Convierte una entidad en un diccionario serializable.

        Args:
            entidad (T): Entidad a convertir.

        Returns:
            Registro: Diccionario con los datos de la entidad.
        """

    @abc.abstractmethod
    def _desde_dict(self, registro: Registro) -> T:
        """Reconstruye una entidad a partir de un diccionario.

        Args:
            registro (Registro): Diccionario leído del archivo.

        Returns:
            T: La entidad reconstruida.
        """

    def crear(self, entidad: T) -> T:
        """Crea una nueva entidad en el repositorio.

        Args:
            entidad (T): La entidad a crear.

        Returns:
            T: La entidad creada.

        Raises:
            ValueError: Si ya existe una entidad con el mismo ID.
        """
        registros: List[Registro] = self.__archivo.leer()
        if any(registro["id"] == entidad.id for registro in registros):
            raise ValueError(
                f"Ya existe un {type(entidad).__name__} con id {entidad.id}."
            )
        registros.append(self._a_dict(entidad))
        self.__archivo.escribir(registros)
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a leer.

        Returns:
            Optional[T]: La entidad si se encuentra, None en caso contrario.
        """
        for registro in self.__archivo.leer():
            if registro["id"] == id:
                return self._desde_dict(registro)
        return None

    def leer_todos(self) -> List[T]:
        """Lee todas las entidades del repositorio, ordenadas por id.

        Returns:
            List[T]: Una lista de todas las entidades.
        """
        registros: List[Registro] = sorted(
            self.__archivo.leer(), key=lambda registro: registro["id"]
        )
        return [self._desde_dict(registro) for registro in registros]

    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en el repositorio.

        Args:
            entidad (T): La entidad a actualizar (debe tener un ID existente).

        Returns:
            T: La entidad actualizada.

        Raises:
            ValueError: Si no se encuentra la entidad para actualizar.
        """
        registros: List[Registro] = self.__archivo.leer()
        for indice, registro in enumerate(registros):
            if registro["id"] == entidad.id:
                registros[indice] = self._a_dict(entidad)
                self.__archivo.escribir(registros)
                return entidad
        raise ValueError(
            f"No existe un {type(entidad).__name__} con id {entidad.id} "
            "para actualizar."
        )

    def eliminar(self, id: int) -> bool:
        """Elimina una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a eliminar.

        Returns:
            bool: True si la entidad fue eliminada, False si no se encontró.
        """
        registros: List[Registro] = self.__archivo.leer()
        restantes: List[Registro] = [
            registro for registro in registros if registro["id"] != id
        ]
        if len(restantes) == len(registros):
            return False
        self.__archivo.escribir(restantes)
        return True

    def siguiente_id(self) -> int:
        """Calcula el próximo id disponible.

        Returns:
            int: El id máximo guardado más uno, o 1 si no hay registros.
        """
        registros: List[Registro] = self.__archivo.leer()
        if not registros:
            return 1
        return max(registro["id"] for registro in registros) + 1


class RepositorioGenero(RepositorioJsonBase[Genero]):
    """Repositorio de géneros persistidos en JSON."""

    def _a_dict(self, entidad: Genero) -> Registro:
        """Convierte un género en diccionario.

        Args:
            entidad (Genero): Género a convertir.

        Returns:
            Registro: Datos del género.
        """
        return {
            "id": entidad.id,
            "nombre": entidad.nombre,
            "descripcion": entidad.descripcion,
        }

    def _desde_dict(self, registro: Registro) -> Genero:
        """Reconstruye un género a partir de un diccionario.

        Args:
            registro (Registro): Datos del género.

        Returns:
            Genero: El género reconstruido.
        """
        return Genero(
            registro["id"], registro["nombre"], registro["descripcion"]
        )


class RepositorioEditorial(RepositorioJsonBase[Editorial]):
    """Repositorio de editoriales persistidas en JSON."""

    def _a_dict(self, entidad: Editorial) -> Registro:
        """Convierte una editorial en diccionario.

        Args:
            entidad (Editorial): Editorial a convertir.

        Returns:
            Registro: Datos de la editorial.
        """
        return {
            "id": entidad.id,
            "nombre": entidad.nombre,
            "pais_origen": entidad.pais_origen,
            "email_contacto": entidad.email_contacto,
        }

    def _desde_dict(self, registro: Registro) -> Editorial:
        """Reconstruye una editorial a partir de un diccionario.

        Args:
            registro (Registro): Datos de la editorial.

        Returns:
            Editorial: La editorial reconstruida.
        """
        return Editorial(
            registro["id"],
            registro["nombre"],
            registro["pais_origen"],
            registro.get("email_contacto"),
        )


class RepositorioMoneda(RepositorioJsonBase[Moneda]):
    """Repositorio de monedas persistidas en JSON."""

    def _a_dict(self, entidad: Moneda) -> Registro:
        """Convierte una moneda en diccionario.

        Args:
            entidad (Moneda): Moneda a convertir.

        Returns:
            Registro: Datos de la moneda.
        """
        return {
            "id": entidad.id,
            "codigo": entidad.codigo,
            "nombre": entidad.nombre,
            "simbolo": entidad.simbolo,
        }

    def _desde_dict(self, registro: Registro) -> Moneda:
        """Reconstruye una moneda a partir de un diccionario.

        Args:
            registro (Registro): Datos de la moneda.

        Returns:
            Moneda: La moneda reconstruida.
        """
        return Moneda(
            registro["id"],
            registro["codigo"],
            registro["nombre"],
            registro["simbolo"],
        )


class RepositorioTipoCotizacion(RepositorioJsonBase[TipoCotizacion]):
    """Repositorio de tipos de cotización persistidos en JSON."""

    def _a_dict(self, entidad: TipoCotizacion) -> Registro:
        """Convierte un tipo de cotización en diccionario.

        Args:
            entidad (TipoCotizacion): Tipo de cotización a convertir.

        Returns:
            Registro: Datos del tipo de cotización.
        """
        return {
            "id": entidad.id,
            "nombre": entidad.nombre,
            "descripcion": entidad.descripcion,
        }

    def _desde_dict(self, registro: Registro) -> TipoCotizacion:
        """Reconstruye un tipo de cotización a partir de un diccionario.

        Args:
            registro (Registro): Datos del tipo de cotización.

        Returns:
            TipoCotizacion: El tipo de cotización reconstruido.
        """
        return TipoCotizacion(
            registro["id"], registro["nombre"], registro["descripcion"]
        )


class RepositorioLibro(RepositorioJsonBase[Libro]):
    """Repositorio de libros persistidos en JSON.

    Guarda el género y la editorial como ids y los rehidrata como objetos
    con los repositorios recibidos.

    Args:
        ruta_archivo (str): Ruta del archivo JSON de libros.
        repositorio_generos (IRepositorio[Genero]): Repositorio de géneros.
        repositorio_editoriales (IRepositorio[Editorial]): Repositorio de
            editoriales.
    """

    def __init__(
        self,
        ruta_archivo: str,
        repositorio_generos: IRepositorio[Genero],
        repositorio_editoriales: IRepositorio[Editorial],
    ) -> None:
        super().__init__(ruta_archivo)
        self.__repositorio_generos: IRepositorio[Genero] = (
            repositorio_generos
        )
        self.__repositorio_editoriales: IRepositorio[Editorial] = (
            repositorio_editoriales
        )

    def _a_dict(self, entidad: Libro) -> Registro:
        """Convierte un libro en diccionario, con sus relaciones como ids.

        Args:
            entidad (Libro): Libro a convertir.

        Returns:
            Registro: Datos del libro.
        """
        return {
            "id": entidad.id,
            "isbn": entidad.isbn,
            "titulo": entidad.titulo,
            "autor": entidad.autor,
            "anio_publicacion": entidad.anio_publicacion,
            "genero_id": entidad.genero.id,
            "editorial_id": entidad.editorial.id,
            "idioma": entidad.idioma,
            "paginas": entidad.paginas,
            "url_referencia": entidad.url_referencia,
        }

    def _desde_dict(self, registro: Registro) -> Libro:
        """Reconstruye un libro y sus relaciones a partir de un diccionario.

        Args:
            registro (Registro): Datos del libro.

        Returns:
            Libro: El libro reconstruido.

        Raises:
            ValueError: Si el género o la editorial referenciados no existen.
        """
        genero: Genero = _exigir_relacionado(
            self.__repositorio_generos.leer_por_id(registro["genero_id"]),
            "Genero",
            registro["genero_id"],
        )
        editorial: Editorial = _exigir_relacionado(
            self.__repositorio_editoriales.leer_por_id(
                registro["editorial_id"]
            ),
            "Editorial",
            registro["editorial_id"],
        )
        return Libro(
            registro["id"],
            registro["isbn"],
            registro["titulo"],
            registro["autor"],
            registro["anio_publicacion"],
            genero,
            editorial,
            idioma=registro["idioma"],
            paginas=registro.get("paginas"),
            url_referencia=registro.get("url_referencia"),
        )


class RepositorioPrecio(RepositorioJsonBase[Precio]):
    """Repositorio de precios persistidos en JSON.

    Args:
        ruta_archivo (str): Ruta del archivo JSON de precios.
        repositorio_libros (IRepositorio[Libro]): Repositorio de libros.
        repositorio_monedas (IRepositorio[Moneda]): Repositorio de monedas.
    """

    def __init__(
        self,
        ruta_archivo: str,
        repositorio_libros: IRepositorio[Libro],
        repositorio_monedas: IRepositorio[Moneda],
    ) -> None:
        super().__init__(ruta_archivo)
        self.__repositorio_libros: IRepositorio[Libro] = repositorio_libros
        self.__repositorio_monedas: IRepositorio[Moneda] = (
            repositorio_monedas
        )

    def _a_dict(self, entidad: Precio) -> Registro:
        """Convierte un precio en diccionario, con sus relaciones como ids.

        Args:
            entidad (Precio): Precio a convertir.

        Returns:
            Registro: Datos del precio.
        """
        return {
            "id": entidad.id,
            "libro_id": entidad.libro.id,
            "moneda_id": entidad.moneda.id,
            "monto": entidad.monto,
            "fecha_vigencia": entidad.fecha_vigencia.isoformat(),
        }

    def _desde_dict(self, registro: Registro) -> Precio:
        """Reconstruye un precio y sus relaciones a partir de un diccionario.

        Args:
            registro (Registro): Datos del precio.

        Returns:
            Precio: El precio reconstruido.

        Raises:
            ValueError: Si el libro o la moneda referenciados no existen.
        """
        libro: Libro = _exigir_relacionado(
            self.__repositorio_libros.leer_por_id(registro["libro_id"]),
            "Libro",
            registro["libro_id"],
        )
        moneda: Moneda = _exigir_relacionado(
            self.__repositorio_monedas.leer_por_id(registro["moneda_id"]),
            "Moneda",
            registro["moneda_id"],
        )
        return Precio(
            registro["id"],
            libro,
            moneda,
            registro["monto"],
            datetime.date.fromisoformat(registro["fecha_vigencia"]),
        )


class RepositorioStock(IRepositorioStock):
    """Repositorio de stock persistido en JSON, identificado por libro_id.

    Args:
        ruta_archivo (str): Ruta del archivo JSON de stock.
        repositorio_libros (IRepositorio[Libro]): Repositorio de libros.
    """

    def __init__(
        self, ruta_archivo: str, repositorio_libros: IRepositorio[Libro]
    ) -> None:
        self.__archivo: ArchivoJson = ArchivoJson(ruta_archivo)
        self.__repositorio_libros: IRepositorio[Libro] = repositorio_libros

    def _a_dict(self, stock: Stock) -> Registro:
        """Convierte un stock en diccionario.

        Args:
            stock (Stock): Stock a convertir.

        Returns:
            Registro: Datos del stock.
        """
        return {
            "libro_id": stock.libro_id,
            "cantidad": stock.cantidad,
            "stock_minimo": stock.stock_minimo,
        }

    def _desde_dict(self, registro: Registro) -> Stock:
        """Reconstruye un stock y su libro a partir de un diccionario.

        Args:
            registro (Registro): Datos del stock.

        Returns:
            Stock: El stock reconstruido.

        Raises:
            ValueError: Si el libro referenciado no existe.
        """
        libro: Libro = _exigir_relacionado(
            self.__repositorio_libros.leer_por_id(registro["libro_id"]),
            "Libro",
            registro["libro_id"],
        )
        return Stock(libro, registro["cantidad"], registro["stock_minimo"])

    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro de stock.

        Args:
            stock (Stock): El objeto Stock a crear.

        Returns:
            Stock: El objeto Stock creado.

        Raises:
            ValueError: Si ya existe un registro de stock para el mismo libro.
        """
        registros: List[Registro] = self.__archivo.leer()
        if any(r["libro_id"] == stock.libro_id for r in registros):
            raise ValueError(
                f"Ya existe stock para el libro con id {stock.libro_id}."
            )
        registros.append(self._a_dict(stock))
        self.__archivo.escribir(registros)
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Lee un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock.

        Returns:
            Optional[Stock]: El stock si se encuentra, None en caso contrario.
        """
        for registro in self.__archivo.leer():
            if registro["libro_id"] == libro_id:
                return self._desde_dict(registro)
        return None

    def leer_todos(self) -> List[Stock]:
        """Lee todos los registros de stock, ordenados por libro_id.

        Returns:
            List[Stock]: Una lista con todos los registros de stock.
        """
        registros: List[Registro] = sorted(
            self.__archivo.leer(), key=lambda registro: registro["libro_id"]
        )
        return [self._desde_dict(registro) for registro in registros]

    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza un registro de stock existente.

        Args:
            stock (Stock): El stock a actualizar (con libro_id existente).

        Returns:
            Stock: El stock actualizado.

        Raises:
            ValueError: Si no se encuentra el stock para actualizar.
        """
        registros: List[Registro] = self.__archivo.leer()
        for indice, registro in enumerate(registros):
            if registro["libro_id"] == stock.libro_id:
                registros[indice] = self._a_dict(stock)
                self.__archivo.escribir(registros)
                return stock
        raise ValueError(
            f"No existe stock para el libro con id {stock.libro_id}."
        )

    def eliminar(self, libro_id: int) -> bool:
        """Elimina un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock a eliminar.

        Returns:
            bool: True si el stock fue eliminado, False si no se encontró.
        """
        registros: List[Registro] = self.__archivo.leer()
        restantes: List[Registro] = [
            r for r in registros if r["libro_id"] != libro_id
        ]
        if len(restantes) == len(registros):
            return False
        self.__archivo.escribir(restantes)
        return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Repositorio de cotizaciones del dólar, identificadas por tipo y fecha.

    Args:
        ruta_archivo (str): Ruta del archivo JSON de cotizaciones.
        repositorio_tipos (IRepositorio[TipoCotizacion]): Repositorio de
            tipos de cotización.
    """

    def __init__(
        self,
        ruta_archivo: str,
        repositorio_tipos: IRepositorio[TipoCotizacion],
    ) -> None:
        self.__archivo: ArchivoJson = ArchivoJson(ruta_archivo)
        self.__repositorio_tipos: IRepositorio[TipoCotizacion] = (
            repositorio_tipos
        )

    @staticmethod
    def _coincide(
        registro: Registro, tipo_id: int, fecha: datetime.date
    ) -> bool:
        """Indica si un registro corresponde a un tipo y una fecha.

        Args:
            registro (Registro): Registro leído del archivo.
            tipo_id (int): Id del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.

        Returns:
            bool: True si coinciden tipo y fecha.
        """
        return (
            registro["tipo_id"] == tipo_id
            and registro["fecha"] == fecha.isoformat()
        )

    def _a_dict(self, cotizacion: CotizacionDolar) -> Registro:
        """Convierte una cotización en diccionario.

        Args:
            cotizacion (CotizacionDolar): Cotización a convertir.

        Returns:
            Registro: Datos de la cotización.
        """
        return {
            "tipo_id": cotizacion.tipo_id,
            "fecha": cotizacion.fecha.isoformat(),
            "compra": cotizacion.compra,
            "venta": cotizacion.venta,
        }

    def _desde_dict(self, registro: Registro) -> CotizacionDolar:
        """Reconstruye una cotización y su tipo a partir de un diccionario.

        Args:
            registro (Registro): Datos de la cotización.

        Returns:
            CotizacionDolar: La cotización reconstruida.

        Raises:
            ValueError: Si el tipo de cotización referenciado no existe.
        """
        tipo: TipoCotizacion = _exigir_relacionado(
            self.__repositorio_tipos.leer_por_id(registro["tipo_id"]),
            "TipoCotizacion",
            registro["tipo_id"],
        )
        return CotizacionDolar(
            tipo,
            datetime.date.fromisoformat(registro["fecha"]),
            registro["compra"],
            registro["venta"],
        )

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una nueva cotización de dólar.

        Args:
            cotizacion (CotizacionDolar): La cotización a crear.

        Returns:
            CotizacionDolar: La cotización creada.

        Raises:
            ValueError: Si ya existe una cotización para el mismo tipo y
                fecha.
        """
        registros: List[Registro] = self.__archivo.leer()
        if any(
            self._coincide(r, cotizacion.tipo_id, cotizacion.fecha)
            for r in registros
        ):
            raise ValueError(
                f"Ya existe una cotización del tipo {cotizacion.tipo_id} "
                f"para el {cotizacion.fecha:%d/%m/%Y}."
            )
        registros.append(self._a_dict(cotizacion))
        self.__archivo.escribir(registros)
        return cotizacion

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        """Lee una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización.
            fecha (datetime.date): La fecha de la cotización.

        Returns:
            Optional[CotizacionDolar]: La cotización si se encuentra, None en
                caso contrario.
        """
        for registro in self.__archivo.leer():
            if self._coincide(registro, tipo_id, fecha):
                return self._desde_dict(registro)
        return None

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Lee el histórico de un tipo, ordenado por fecha ascendente.

        Args:
            tipo_id (int): El ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Las cotizaciones del tipo indicado.
        """
        registros: List[Registro] = sorted(
            (r for r in self.__archivo.leer() if r["tipo_id"] == tipo_id),
            key=lambda registro: registro["fecha"],
        )
        return [self._desde_dict(registro) for registro in registros]

    def leer_todos(self) -> List[CotizacionDolar]:
        """Lee todas las cotizaciones, ordenadas por tipo y fecha.

        Returns:
            List[CotizacionDolar]: Una lista con todas las cotizaciones.
        """
        registros: List[Registro] = sorted(
            self.__archivo.leer(),
            key=lambda registro: (registro["tipo_id"], registro["fecha"]),
        )
        return [self._desde_dict(registro) for registro in registros]

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza una cotización de dólar existente.

        Args:
            cotizacion (CotizacionDolar): La cotización a actualizar.

        Returns:
            CotizacionDolar: La cotización actualizada.

        Raises:
            ValueError: Si no existe una cotización con ese tipo y fecha.
        """
        registros: List[Registro] = self.__archivo.leer()
        for indice, registro in enumerate(registros):
            if self._coincide(registro, cotizacion.tipo_id, cotizacion.fecha):
                registros[indice] = self._a_dict(cotizacion)
                self.__archivo.escribir(registros)
                return cotizacion
        raise ValueError(
            f"No existe una cotización del tipo {cotizacion.tipo_id} "
            f"para el {cotizacion.fecha:%d/%m/%Y}."
        )

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Elimina una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización.
            fecha (datetime.date): La fecha de la cotización a eliminar.

        Returns:
            bool: True si la cotización fue eliminada, False si no se
                encontró.
        """
        registros: List[Registro] = self.__archivo.leer()
        restantes: List[Registro] = [
            r for r in registros if not self._coincide(r, tipo_id, fecha)
        ]
        if len(restantes) == len(registros):
            return False
        self.__archivo.escribir(restantes)
        return True
