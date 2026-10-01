#@title Escritura de services.py
"""Servicios de Book Manager: lógica de negocio del sistema.

Los servicios reciben datos simples (ids, textos, números y fechas),
construyen las entidades, aplican las reglas de negocio y la integridad
referencial, y usan los repositorios para persistir. También resuelven la
conversión de precios con la cotización del dólar y los reportes.
"""
import abc
import datetime
from typing import (
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
)

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
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioJsonBase,
    RepositorioStock,
)

T = TypeVar("T", bound=EntidadBase)
R = TypeVar("R")
FilaInventario = Tuple[Stock, Optional[float], Optional[float]]

CODIGO_PESO: str = "ARS"
CODIGO_DOLAR: str = "USD"


def _normalizar(texto: str) -> str:
    """Normaliza un texto para comparaciones sin distinguir mayúsculas.

    Args:
        texto (str): Texto a normalizar.

    Returns:
        str: El texto sin espacios extremos y en minúsculas (casefold).
    """
    return texto.strip().casefold()


def _exigir(entidad: Optional[R], nombre: str, id: int) -> R:
    """Verifica que una entidad buscada por id exista.

    Args:
        entidad (Optional[R]): Resultado de la búsqueda.
        nombre (str): Nombre de la entidad, para el mensaje.
        id (int): Id buscado, para el mensaje.

    Returns:
        R: La entidad encontrada.

    Raises:
        ValueError: Si la entidad no existe.
    """
    if entidad is None:
        raise ValueError(f"No existe {nombre} con id {id}.")
    return entidad


def _contar(elementos: Iterable[R], condicion: Callable[[R], bool]) -> int:
    """Cuenta los elementos que cumplen una condición.

    Args:
        elementos (Iterable[R]): Elementos a recorrer.
        condicion (Callable[[R], bool]): Condición a evaluar.

    Returns:
        int: Cantidad de elementos que cumplen la condición.
    """
    return sum(1 for elemento in elementos if condicion(elemento))


def _validar_cantidad_movimiento(cantidad: int) -> int:
    """Valida la cantidad de un movimiento de stock.

    Args:
        cantidad (int): Unidades del movimiento.

    Returns:
        int: La cantidad validada.

    Raises:
        TypeError: Si la cantidad no es int (se rechaza también bool).
        ValueError: Si la cantidad no es mayor a 0.
    """
    if isinstance(cantidad, bool) or not isinstance(cantidad, int):
        raise TypeError("La cantidad del movimiento debe ser de tipo int.")
    if cantidad <= 0:
        raise ValueError("La cantidad del movimiento debe ser mayor a 0.")
    return cantidad


class ServicioEntidad(abc.ABC, Generic[T]):
    """Base abstracta de los servicios de entidades identificadas por id.

    Implementa listar, obtener y eliminar. La eliminación sigue el patrón
    Template Method: cada subclase define sus restricciones en
    _validar_eliminacion.

    Args:
        repositorio (RepositorioJsonBase[T]): Repositorio de la entidad.
        nombre_entidad (str): Nombre de la entidad para los mensajes.
    """

    def __init__(
        self, repositorio: RepositorioJsonBase[T], nombre_entidad: str
    ) -> None:
        self._repositorio: RepositorioJsonBase[T] = repositorio
        self.__nombre_entidad: str = nombre_entidad

    def listar(self) -> List[T]:
        """Lista todas las entidades, ordenadas por id.

        Returns:
            List[T]: Las entidades registradas.
        """
        return self._repositorio.leer_todos()

    def obtener(self, id: int) -> T:
        """Obtiene una entidad por su id.

        Args:
            id (int): Id de la entidad.

        Returns:
            T: La entidad encontrada.

        Raises:
            ValueError: Si no existe una entidad con ese id.
        """
        return _exigir(
            self._repositorio.leer_por_id(id), self.__nombre_entidad, id
        )

    def eliminar(self, id: int) -> None:
        """Elimina una entidad si no tiene dependientes.

        Args:
            id (int): Id de la entidad a eliminar.

        Raises:
            ValueError: Si la entidad no existe o tiene dependientes.
        """
        entidad: T = self.obtener(id)
        self._validar_eliminacion(entidad)
        self._repositorio.eliminar(id)

    def _siguiente_id(self) -> int:
        """Obtiene del repositorio el próximo id disponible.

        Returns:
            int: El próximo id.
        """
        return self._repositorio.siguiente_id()

    def _validar_unico(
        self,
        entidad: T,
        obtener_valor: Callable[[T], str],
        campo: str,
    ) -> None:
        """Verifica que ninguna otra entidad tenga el mismo valor.

        La comparación no distingue mayúsculas ni espacios extremos.

        Args:
            entidad (T): Entidad a verificar.
            obtener_valor (Callable[[T], str]): Función que extrae el
                valor a comparar.
            campo (str): Nombre del campo, para el mensaje.

        Raises:
            ValueError: Si otra entidad ya tiene ese valor.
        """
        valor: str = obtener_valor(entidad)
        for otra in self.listar():
            mismo_valor: bool = (
                _normalizar(obtener_valor(otra)) == _normalizar(valor)
            )
            if otra.id != entidad.id and mismo_valor:
                raise ValueError(
                    f"Ya existe un registro de {self.__nombre_entidad} "
                    f"con {campo} '{valor}'."
                )

    @abc.abstractmethod
    def _validar_eliminacion(self, entidad: T) -> None:
        """Verifica que la entidad se pueda eliminar.

        Args:
            entidad (T): Entidad a eliminar.

        Raises:
            ValueError: Si la entidad tiene dependientes.
        """


class ServicioGenero(ServicioEntidad[Genero]):
    """Lógica de negocio de los géneros.

    Args:
        repositorio (RepositorioJsonBase[Genero]): Repositorio de géneros.
        repositorio_libros (RepositorioJsonBase[Libro]): Repositorio de
            libros, para verificar la integridad al eliminar.
    """

    def __init__(
        self,
        repositorio: RepositorioJsonBase[Genero],
        repositorio_libros: RepositorioJsonBase[Libro],
    ) -> None:
        super().__init__(repositorio, "género")
        self.__repositorio_libros: RepositorioJsonBase[Libro] = (
            repositorio_libros
        )

    def crear(self, nombre: str, descripcion: str) -> Genero:
        """Crea un género con nombre único.

        Args:
            nombre (str): Nombre del género.
            descripcion (str): Descripción del género.

        Returns:
            Genero: El género creado.

        Raises:
            ValueError: Si el nombre ya existe o algún dato es inválido.
        """
        genero: Genero = Genero(self._siguiente_id(), nombre, descripcion)
        self._validar_unico(genero, lambda g: g.nombre, "nombre")
        return self._repositorio.crear(genero)

    def actualizar(self, id: int, nombre: str, descripcion: str) -> Genero:
        """Actualiza un género existente.

        Args:
            id (int): Id del género.
            nombre (str): Nuevo nombre.
            descripcion (str): Nueva descripción.

        Returns:
            Genero: El género actualizado.

        Raises:
            ValueError: Si no existe, si el nombre ya lo usa otro género o
                si algún dato es inválido.
        """
        genero: Genero = self.obtener(id)
        genero.nombre = nombre
        genero.descripcion = descripcion
        self._validar_unico(genero, lambda g: g.nombre, "nombre")
        return self._repositorio.actualizar(genero)

    def _validar_eliminacion(self, entidad: Genero) -> None:
        """Impide eliminar un género con libros asociados.

        Args:
            entidad (Genero): Género a eliminar.

        Raises:
            ValueError: Si el género tiene libros asociados.
        """
        cantidad: int = _contar(
            self.__repositorio_libros.leer_todos(),
            lambda libro: libro.genero.id == entidad.id,
        )
        if cantidad:
            raise ValueError(
                f"No se puede eliminar el género '{entidad.nombre}': "
                f"tiene {cantidad} libro(s) asociado(s)."
            )


class ServicioEditorial(ServicioEntidad[Editorial]):
    """Lógica de negocio de las editoriales.

    Args:
        repositorio (RepositorioJsonBase[Editorial]): Repositorio de
            editoriales.
        repositorio_libros (RepositorioJsonBase[Libro]): Repositorio de
            libros, para verificar la integridad al eliminar.
    """

    def __init__(
        self,
        repositorio: RepositorioJsonBase[Editorial],
        repositorio_libros: RepositorioJsonBase[Libro],
    ) -> None:
        super().__init__(repositorio, "editorial")
        self.__repositorio_libros: RepositorioJsonBase[Libro] = (
            repositorio_libros
        )

    def crear(
        self,
        nombre: str,
        pais_origen: str,
        email_contacto: Optional[str] = None,
    ) -> Editorial:
        """Crea una editorial con nombre único.

        Args:
            nombre (str): Nombre de la editorial.
            pais_origen (str): País de origen.
            email_contacto (Optional[str]): Email de contacto, opcional.

        Returns:
            Editorial: La editorial creada.

        Raises:
            ValueError: Si el nombre ya existe o algún dato es inválido.
        """
        editorial: Editorial = Editorial(
            self._siguiente_id(), nombre, pais_origen, email_contacto
        )
        self._validar_unico(editorial, lambda e: e.nombre, "nombre")
        return self._repositorio.crear(editorial)

    def actualizar(
        self,
        id: int,
        nombre: str,
        pais_origen: str,
        email_contacto: Optional[str] = None,
    ) -> Editorial:
        """Actualiza una editorial existente.

        Args:
            id (int): Id de la editorial.
            nombre (str): Nuevo nombre.
            pais_origen (str): Nuevo país de origen.
            email_contacto (Optional[str]): Nuevo email, opcional.

        Returns:
            Editorial: La editorial actualizada.

        Raises:
            ValueError: Si no existe, si el nombre ya lo usa otra editorial
                o si algún dato es inválido.
        """
        editorial: Editorial = self.obtener(id)
        editorial.nombre = nombre
        editorial.pais_origen = pais_origen
        editorial.email_contacto = email_contacto
        self._validar_unico(editorial, lambda e: e.nombre, "nombre")
        return self._repositorio.actualizar(editorial)

    def _validar_eliminacion(self, entidad: Editorial) -> None:
        """Impide eliminar una editorial con libros asociados.

        Args:
            entidad (Editorial): Editorial a eliminar.

        Raises:
            ValueError: Si la editorial tiene libros asociados.
        """
        cantidad: int = _contar(
            self.__repositorio_libros.leer_todos(),
            lambda libro: libro.editorial.id == entidad.id,
        )
        if cantidad:
            raise ValueError(
                f"No se puede eliminar la editorial '{entidad.nombre}': "
                f"tiene {cantidad} libro(s) asociado(s)."
            )


class ServicioMoneda(ServicioEntidad[Moneda]):
    """Lógica de negocio de las monedas.

    Args:
        repositorio (RepositorioJsonBase[Moneda]): Repositorio de monedas.
        repositorio_precios (RepositorioJsonBase[Precio]): Repositorio de
            precios, para verificar la integridad al eliminar.
    """

    def __init__(
        self,
        repositorio: RepositorioJsonBase[Moneda],
        repositorio_precios: RepositorioJsonBase[Precio],
    ) -> None:
        super().__init__(repositorio, "moneda")
        self.__repositorio_precios: RepositorioJsonBase[Precio] = (
            repositorio_precios
        )

    def crear(self, codigo: str, nombre: str, simbolo: str) -> Moneda:
        """Crea una moneda con código único.

        Args:
            codigo (str): Código ISO 4217.
            nombre (str): Nombre de la moneda.
            simbolo (str): Símbolo de la moneda.

        Returns:
            Moneda: La moneda creada.

        Raises:
            ValueError: Si el código ya existe o algún dato es inválido.
        """
        moneda: Moneda = Moneda(self._siguiente_id(), codigo, nombre, simbolo)
        self._validar_unico(moneda, lambda m: m.codigo, "código")
        return self._repositorio.crear(moneda)

    def actualizar(
        self, id: int, codigo: str, nombre: str, simbolo: str
    ) -> Moneda:
        """Actualiza una moneda existente.

        Args:
            id (int): Id de la moneda.
            codigo (str): Nuevo código ISO 4217.
            nombre (str): Nuevo nombre.
            simbolo (str): Nuevo símbolo.

        Returns:
            Moneda: La moneda actualizada.

        Raises:
            ValueError: Si no existe, si el código ya lo usa otra moneda o
                si algún dato es inválido.
        """
        moneda: Moneda = self.obtener(id)
        moneda.codigo = codigo
        moneda.nombre = nombre
        moneda.simbolo = simbolo
        self._validar_unico(moneda, lambda m: m.codigo, "código")
        return self._repositorio.actualizar(moneda)

    def _validar_eliminacion(self, entidad: Moneda) -> None:
        """Impide eliminar una moneda con precios asociados.

        Args:
            entidad (Moneda): Moneda a eliminar.

        Raises:
            ValueError: Si la moneda tiene precios asociados.
        """
        cantidad: int = _contar(
            self.__repositorio_precios.leer_todos(),
            lambda precio: precio.moneda.id == entidad.id,
        )
        if cantidad:
            raise ValueError(
                f"No se puede eliminar la moneda '{entidad.codigo}': "
                f"tiene {cantidad} precio(s) asociado(s)."
            )


class ServicioTipoCotizacion(ServicioEntidad[TipoCotizacion]):
    """Lógica de negocio de los tipos de cotización.

    Args:
        repositorio (RepositorioJsonBase[TipoCotizacion]): Repositorio de
            tipos de cotización.
        repositorio_cotizaciones (RepositorioCotizacionDolar): Repositorio
            de cotizaciones, para verificar la integridad al eliminar.
    """

    def __init__(
        self,
        repositorio: RepositorioJsonBase[TipoCotizacion],
        repositorio_cotizaciones: RepositorioCotizacionDolar,
    ) -> None:
        super().__init__(repositorio, "tipo de cotización")
        self.__repositorio_cotizaciones: RepositorioCotizacionDolar = (
            repositorio_cotizaciones
        )

    def crear(self, nombre: str, descripcion: str) -> TipoCotizacion:
        """Crea un tipo de cotización con nombre único.

        Args:
            nombre (str): Nombre del tipo.
            descripcion (str): Descripción del tipo.

        Returns:
            TipoCotizacion: El tipo creado.

        Raises:
            ValueError: Si el nombre ya existe o algún dato es inválido.
        """
        tipo: TipoCotizacion = TipoCotizacion(
            self._siguiente_id(), nombre, descripcion
        )
        self._validar_unico(tipo, lambda t: t.nombre, "nombre")
        return self._repositorio.crear(tipo)

    def actualizar(
        self, id: int, nombre: str, descripcion: str
    ) -> TipoCotizacion:
        """Actualiza un tipo de cotización existente.

        Args:
            id (int): Id del tipo.
            nombre (str): Nuevo nombre.
            descripcion (str): Nueva descripción.

        Returns:
            TipoCotizacion: El tipo actualizado.

        Raises:
            ValueError: Si no existe, si el nombre ya lo usa otro tipo o si
                algún dato es inválido.
        """
        tipo: TipoCotizacion = self.obtener(id)
        tipo.nombre = nombre
        tipo.descripcion = descripcion
        self._validar_unico(tipo, lambda t: t.nombre, "nombre")
        return self._repositorio.actualizar(tipo)

    def _validar_eliminacion(self, entidad: TipoCotizacion) -> None:
        """Impide eliminar un tipo de cotización con cotizaciones.

        Args:
            entidad (TipoCotizacion): Tipo a eliminar.

        Raises:
            ValueError: Si el tipo tiene cotizaciones registradas.
        """
        cantidad: int = len(
            self.__repositorio_cotizaciones.leer_historico_por_tipo(
                entidad.id
            )
        )
        if cantidad:
            raise ValueError(
                f"No se puede eliminar el tipo '{entidad.nombre}': "
                f"tiene {cantidad} cotización(es) asociada(s)."
            )


class ServicioLibro(ServicioEntidad[Libro]):
    """Lógica de negocio de los libros.

    Args:
        repositorio (RepositorioJsonBase[Libro]): Repositorio de libros.
        repositorio_generos (RepositorioJsonBase[Genero]): Repositorio de
            géneros.
        repositorio_editoriales (RepositorioJsonBase[Editorial]):
            Repositorio de editoriales.
        repositorio_precios (RepositorioJsonBase[Precio]): Repositorio de
            precios, para verificar la integridad al eliminar.
        repositorio_stocks (RepositorioStock): Repositorio de stock, para
            verificar la integridad al eliminar.
    """

    def __init__(
        self,
        repositorio: RepositorioJsonBase[Libro],
        repositorio_generos: RepositorioJsonBase[Genero],
        repositorio_editoriales: RepositorioJsonBase[Editorial],
        repositorio_precios: RepositorioJsonBase[Precio],
        repositorio_stocks: RepositorioStock,
    ) -> None:
        super().__init__(repositorio, "libro")
        self.__repositorio_generos: RepositorioJsonBase[Genero] = (
            repositorio_generos
        )
        self.__repositorio_editoriales: RepositorioJsonBase[Editorial] = (
            repositorio_editoriales
        )
        self.__repositorio_precios: RepositorioJsonBase[Precio] = (
            repositorio_precios
        )
        self.__repositorio_stocks: RepositorioStock = repositorio_stocks

    def crear(
        self,
        isbn: str,
        titulo: str,
        autor: str,
        anio_publicacion: int,
        genero_id: int,
        editorial_id: int,
        idioma: str = "Español",
        paginas: Optional[int] = None,
        url_referencia: Optional[str] = None,
    ) -> Libro:
        """Crea un libro con ISBN único, género y editorial existentes.

        Args:
            isbn (str): ISBN de 13 dígitos.
            titulo (str): Título de la obra.
            autor (str): Autor de la obra.
            anio_publicacion (int): Año de publicación.
            genero_id (int): Id del género.
            editorial_id (int): Id de la editorial.
            idioma (str): Idioma de la obra.
            paginas (Optional[int]): Cantidad de páginas, opcional.
            url_referencia (Optional[str]): URL de la ficha en Cúspide.

        Returns:
            Libro: El libro creado.

        Raises:
            ValueError: Si el género o la editorial no existen, si el ISBN
                ya está registrado o si algún dato es inválido.
        """
        libro: Libro = Libro(
            self._siguiente_id(),
            isbn,
            titulo,
            autor,
            anio_publicacion,
            self.__obtener_genero(genero_id),
            self.__obtener_editorial(editorial_id),
            idioma,
            paginas,
            url_referencia,
        )
        self._validar_unico(libro, lambda l: l.isbn, "ISBN")
        return self._repositorio.crear(libro)

    def actualizar(
        self,
        id: int,
        isbn: str,
        titulo: str,
        autor: str,
        anio_publicacion: int,
        genero_id: int,
        editorial_id: int,
        idioma: str = "Español",
        paginas: Optional[int] = None,
        url_referencia: Optional[str] = None,
    ) -> Libro:
        """Actualiza un libro existente.

        Args:
            id (int): Id del libro.
            isbn (str): Nuevo ISBN.
            titulo (str): Nuevo título.
            autor (str): Nuevo autor.
            anio_publicacion (int): Nuevo año de publicación.
            genero_id (int): Id del nuevo género.
            editorial_id (int): Id de la nueva editorial.
            idioma (str): Nuevo idioma.
            paginas (Optional[int]): Nueva cantidad de páginas, opcional.
            url_referencia (Optional[str]): Nueva URL, opcional.

        Returns:
            Libro: El libro actualizado.

        Raises:
            ValueError: Si no existe, si el ISBN ya lo usa otro libro, si
                el género o la editorial no existen o si algún dato es
                inválido.
        """
        libro: Libro = self.obtener(id)
        libro.isbn = isbn
        libro.titulo = titulo
        libro.autor = autor
        libro.anio_publicacion = anio_publicacion
        libro.genero = self.__obtener_genero(genero_id)
        libro.editorial = self.__obtener_editorial(editorial_id)
        libro.idioma = idioma
        libro.paginas = paginas
        libro.url_referencia = url_referencia
        self._validar_unico(libro, lambda l: l.isbn, "ISBN")
        return self._repositorio.actualizar(libro)

    def __obtener_genero(self, genero_id: int) -> Genero:
        """Busca un género por id.

        Args:
            genero_id (int): Id del género.

        Returns:
            Genero: El género encontrado.

        Raises:
            ValueError: Si el género no existe.
        """
        return _exigir(
            self.__repositorio_generos.leer_por_id(genero_id),
            "género",
            genero_id,
        )

    def __obtener_editorial(self, editorial_id: int) -> Editorial:
        """Busca una editorial por id.

        Args:
            editorial_id (int): Id de la editorial.

        Returns:
            Editorial: La editorial encontrada.

        Raises:
            ValueError: Si la editorial no existe.
        """
        return _exigir(
            self.__repositorio_editoriales.leer_por_id(editorial_id),
            "editorial",
            editorial_id,
        )

    def _validar_eliminacion(self, entidad: Libro) -> None:
        """Impide eliminar un libro con precios o stock asociados.

        Args:
            entidad (Libro): Libro a eliminar.

        Raises:
            ValueError: Si el libro tiene precios o stock asociados.
        """
        motivos: List[str] = []
        cantidad_precios: int = _contar(
            self.__repositorio_precios.leer_todos(),
            lambda precio: precio.libro.id == entidad.id,
        )
        if cantidad_precios:
            motivos.append(f"{cantidad_precios} precio(s)")
        if self.__repositorio_stocks.leer_por_libro(entidad.id) is not None:
            motivos.append("un registro de stock")
        if motivos:
            raise ValueError(
                f"No se puede eliminar el libro '{entidad.titulo}': "
                f"tiene {' y '.join(motivos)} asociado(s)."
            )


class ServicioCotizacionDolar:
    """Lógica de negocio de las cotizaciones del dólar.

    Args:
        repositorio (RepositorioCotizacionDolar): Repositorio de
            cotizaciones.
        repositorio_tipos (RepositorioJsonBase[TipoCotizacion]):
            Repositorio de tipos de cotización.
    """

    def __init__(
        self,
        repositorio: RepositorioCotizacionDolar,
        repositorio_tipos: RepositorioJsonBase[TipoCotizacion],
    ) -> None:
        self.__repositorio: RepositorioCotizacionDolar = repositorio
        self.__repositorio_tipos: RepositorioJsonBase[TipoCotizacion] = (
            repositorio_tipos
        )

    def listar(self) -> List[CotizacionDolar]:
        """Lista todas las cotizaciones, ordenadas por tipo y fecha.

        Returns:
            List[CotizacionDolar]: Las cotizaciones registradas.
        """
        return self.__repositorio.leer_todos()

    def obtener(
        self, tipo_id: int, fecha: datetime.date
    ) -> CotizacionDolar:
        """Obtiene una cotización por tipo y fecha.

        Args:
            tipo_id (int): Id del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.

        Returns:
            CotizacionDolar: La cotización encontrada.

        Raises:
            ValueError: Si el tipo o la cotización no existen.
        """
        tipo: TipoCotizacion = self.__obtener_tipo(tipo_id)
        cotizacion: Optional[CotizacionDolar] = (
            self.__repositorio.leer_por_tipo_y_fecha(tipo_id, fecha)
        )
        if cotizacion is None:
            raise ValueError(
                f"No existe una cotización {tipo.nombre} para el "
                f"{fecha:%d/%m/%Y}."
            )
        return cotizacion

    def crear(
        self,
        tipo_id: int,
        fecha: datetime.date,
        compra: float,
        venta: float,
    ) -> CotizacionDolar:
        """Crea una cotización única por tipo y fecha.

        Args:
            tipo_id (int): Id del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.
            compra (float): Valor de compra en ARS.
            venta (float): Valor de venta en ARS.

        Returns:
            CotizacionDolar: La cotización creada.

        Raises:
            ValueError: Si el tipo no existe, si ya hay una cotización para
                ese tipo y fecha o si algún dato es inválido.
        """
        tipo: TipoCotizacion = self.__obtener_tipo(tipo_id)
        cotizacion: CotizacionDolar = CotizacionDolar(
            tipo, fecha, compra, venta
        )
        existente: Optional[CotizacionDolar] = (
            self.__repositorio.leer_por_tipo_y_fecha(tipo_id, fecha)
        )
        if existente is not None:
            raise ValueError(
                f"Ya existe una cotización {tipo.nombre} para el "
                f"{fecha:%d/%m/%Y}."
            )
        return self.__repositorio.crear(cotizacion)

    def actualizar(
        self,
        tipo_id: int,
        fecha: datetime.date,
        compra: float,
        venta: float,
    ) -> CotizacionDolar:
        """Actualiza los valores de una cotización existente.

        Args:
            tipo_id (int): Id del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.
            compra (float): Nuevo valor de compra.
            venta (float): Nuevo valor de venta.

        Returns:
            CotizacionDolar: La cotización actualizada.

        Raises:
            ValueError: Si la cotización no existe o los valores son
                inválidos.
        """
        cotizacion: CotizacionDolar = self.obtener(tipo_id, fecha)
        cotizacion.actualizar_valores(compra, venta)
        return self.__repositorio.actualizar(cotizacion)

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> None:
        """Elimina una cotización por tipo y fecha.

        Args:
            tipo_id (int): Id del tipo de cotización.
            fecha (datetime.date): Fecha de la cotización.

        Raises:
            ValueError: Si la cotización no existe.
        """
        self.obtener(tipo_id, fecha)
        self.__repositorio.eliminar(tipo_id, fecha)

    def historico(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve el histórico de un tipo en orden cronológico.

        Args:
            tipo_id (int): Id del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Las cotizaciones del tipo.

        Raises:
            ValueError: Si el tipo no existe.
        """
        self.__obtener_tipo(tipo_id)
        return self.__repositorio.leer_historico_por_tipo(tipo_id)

    def obtener_vigente(self, tipo_id: int) -> CotizacionDolar:
        """Devuelve la cotización más reciente de un tipo.

        Es el único punto a reemplazar para obtener cotizaciones online.

        Args:
            tipo_id (int): Id del tipo de cotización.

        Returns:
            CotizacionDolar: La cotización de fecha más reciente.

        Raises:
            ValueError: Si el tipo no existe o no tiene cotizaciones.
        """
        tipo: TipoCotizacion = self.__obtener_tipo(tipo_id)
        historico: List[CotizacionDolar] = (
            self.__repositorio.leer_historico_por_tipo(tipo_id)
        )
        if not historico:
            raise ValueError(
                f"No hay cotizaciones registradas para el tipo "
                f"'{tipo.nombre}'."
            )
        return historico[-1]

    def __obtener_tipo(self, tipo_id: int) -> TipoCotizacion:
        """Busca un tipo de cotización por id.

        Args:
            tipo_id (int): Id del tipo.

        Returns:
            TipoCotizacion: El tipo encontrado.

        Raises:
            ValueError: Si el tipo no existe.
        """
        return _exigir(
            self.__repositorio_tipos.leer_por_id(tipo_id),
            "tipo de cotización",
            tipo_id,
        )


class ServicioPrecio(ServicioEntidad[Precio]):
    """Lógica de negocio de los precios y su conversión de moneda.

    Args:
        repositorio (RepositorioJsonBase[Precio]): Repositorio de precios.
        repositorio_libros (RepositorioJsonBase[Libro]): Repositorio de
            libros.
        repositorio_monedas (RepositorioJsonBase[Moneda]): Repositorio de
            monedas.
        servicio_cotizaciones (ServicioCotizacionDolar): Servicio de
            cotizaciones, para obtener la cotización vigente.
    """

    def __init__(
        self,
        repositorio: RepositorioJsonBase[Precio],
        repositorio_libros: RepositorioJsonBase[Libro],
        repositorio_monedas: RepositorioJsonBase[Moneda],
        servicio_cotizaciones: ServicioCotizacionDolar,
    ) -> None:
        super().__init__(repositorio, "precio")
        self.__repositorio_libros: RepositorioJsonBase[Libro] = (
            repositorio_libros
        )
        self.__repositorio_monedas: RepositorioJsonBase[Moneda] = (
            repositorio_monedas
        )
        self.__servicio_cotizaciones: ServicioCotizacionDolar = (
            servicio_cotizaciones
        )

    def crear(
        self,
        libro_id: int,
        moneda_id: int,
        monto: float,
        fecha_vigencia: datetime.date,
    ) -> Precio:
        """Crea un precio único por libro, moneda y fecha de vigencia.

        Args:
            libro_id (int): Id del libro.
            moneda_id (int): Id de la moneda.
            monto (float): Monto del precio.
            fecha_vigencia (datetime.date): Fecha desde la que rige.

        Returns:
            Precio: El precio creado.

        Raises:
            ValueError: Si el libro o la moneda no existen, si el precio ya
                existe o si algún dato es inválido.
        """
        precio: Precio = Precio(
            self._siguiente_id(),
            self.__obtener_libro(libro_id),
            self.__obtener_moneda(moneda_id),
            monto,
            fecha_vigencia,
        )
        self.__validar_combinacion_unica(precio)
        return self._repositorio.crear(precio)

    def actualizar(
        self,
        id: int,
        libro_id: int,
        moneda_id: int,
        monto: float,
        fecha_vigencia: datetime.date,
    ) -> Precio:
        """Actualiza un precio existente.

        Args:
            id (int): Id del precio.
            libro_id (int): Id del libro.
            moneda_id (int): Id de la moneda.
            monto (float): Nuevo monto.
            fecha_vigencia (datetime.date): Nueva fecha de vigencia.

        Returns:
            Precio: El precio actualizado.

        Raises:
            ValueError: Si no existe, si la combinación ya la usa otro
                precio o si algún dato es inválido.
        """
        precio: Precio = self.obtener(id)
        precio.libro = self.__obtener_libro(libro_id)
        precio.moneda = self.__obtener_moneda(moneda_id)
        precio.monto = monto
        precio.fecha_vigencia = fecha_vigencia
        self.__validar_combinacion_unica(precio)
        return self._repositorio.actualizar(precio)

    def listar_por_libro(self, libro_id: int) -> List[Precio]:
        """Lista los precios de un libro.

        Args:
            libro_id (int): Id del libro.

        Returns:
            List[Precio]: Los precios del libro.
        """
        return [p for p in self.listar() if p.libro.id == libro_id]

    def obtener_vigente(
        self, libro_id: int, codigo_moneda: str
    ) -> Optional[Precio]:
        """Obtiene el precio vigente de un libro en una moneda.

        El precio vigente es el de fecha de vigencia más reciente que no sea
        futura.

        Args:
            libro_id (int): Id del libro.
            codigo_moneda (str): Código ISO de la moneda.

        Returns:
            Optional[Precio]: El precio vigente, o None si no hay.
        """
        hoy: datetime.date = datetime.date.today()
        codigo: str = codigo_moneda.strip().upper()
        candidatos: List[Precio] = [
            precio
            for precio in self.listar_por_libro(libro_id)
            if precio.moneda.codigo == codigo
            and precio.fecha_vigencia <= hoy
        ]
        if not candidatos:
            return None
        return max(candidatos, key=lambda precio: precio.fecha_vigencia)

    def precio_en_ars(
        self, libro_id: int, cotizacion: CotizacionDolar
    ) -> Optional[float]:
        """Calcula el precio de un libro en ARS.

        Si hay precio vigente en ARS se usa directo; si solo hay en USD, se
        convierte con el valor de venta de la cotización.

        Args:
            libro_id (int): Id del libro.
            cotizacion (CotizacionDolar): Cotización a aplicar.

        Returns:
            Optional[float]: El precio en ARS, o None si no hay precio
                convertible.
        """
        precio_ars: Optional[Precio] = self.obtener_vigente(
            libro_id, CODIGO_PESO
        )
        if precio_ars is not None:
            return precio_ars.monto
        precio_usd: Optional[Precio] = self.obtener_vigente(
            libro_id, CODIGO_DOLAR
        )
        if precio_usd is not None:
            return round(precio_usd.monto * cotizacion.venta, 2)
        return None

    def cotizar_libro(self, libro_id: int, tipo_id: int) -> Tuple[float, float]:
        """Cotiza un libro en ARS y USD con la cotización vigente.

        Args:
            libro_id (int): Id del libro.
            tipo_id (int): Id del tipo de cotización.

        Returns:
            Tuple[float, float]: Precio en ARS y precio en USD.

        Raises:
            ValueError: Si el libro no existe, si el tipo no tiene
                cotizaciones o si el libro no tiene precio en ARS ni USD.
        """
        libro: Libro = self.__obtener_libro(libro_id)
        cotizacion: CotizacionDolar = (
            self.__servicio_cotizaciones.obtener_vigente(tipo_id)
        )
        monto_ars: Optional[float] = self.precio_en_ars(libro_id, cotizacion)
        if monto_ars is None:
            raise ValueError(
                f"El libro '{libro.titulo}' no tiene precio vigente en "
                f"{CODIGO_PESO} ni en {CODIGO_DOLAR}."
            )
        return monto_ars, round(monto_ars / cotizacion.venta, 2)

    def _validar_eliminacion(self, entidad: Precio) -> None:
        """Un precio no tiene dependientes: siempre se puede eliminar.

        Args:
            entidad (Precio): Precio a eliminar.
        """

    def __validar_combinacion_unica(self, precio: Precio) -> None:
        """Verifica que no haya otro precio con igual libro, moneda y fecha.

        Args:
            precio (Precio): Precio a verificar.

        Raises:
            ValueError: Si otro precio tiene la misma combinación.
        """
        for otro in self.listar():
            misma_combinacion: bool = (
                otro.libro.id == precio.libro.id
                and otro.moneda.id == precio.moneda.id
                and otro.fecha_vigencia == precio.fecha_vigencia
            )
            if otro.id != precio.id and misma_combinacion:
                raise ValueError(
                    f"Ya existe un precio en {precio.moneda.codigo} para "
                    f"'{precio.libro.titulo}' vigente desde "
                    f"{precio.fecha_vigencia:%d/%m/%Y}."
                )

    def __obtener_libro(self, libro_id: int) -> Libro:
        """Busca un libro por id.

        Args:
            libro_id (int): Id del libro.

        Returns:
            Libro: El libro encontrado.

        Raises:
            ValueError: Si el libro no existe.
        """
        return _exigir(
            self.__repositorio_libros.leer_por_id(libro_id), "libro", libro_id
        )

    def __obtener_moneda(self, moneda_id: int) -> Moneda:
        """Busca una moneda por id.

        Args:
            moneda_id (int): Id de la moneda.

        Returns:
            Moneda: La moneda encontrada.

        Raises:
            ValueError: Si la moneda no existe.
        """
        return _exigir(
            self.__repositorio_monedas.leer_por_id(moneda_id),
            "moneda",
            moneda_id,
        )


class ServicioStock:
    """Lógica de negocio del stock y sus movimientos.

    Args:
        repositorio (RepositorioStock): Repositorio de stock.
        repositorio_libros (RepositorioJsonBase[Libro]): Repositorio de
            libros.
    """

    def __init__(
        self,
        repositorio: RepositorioStock,
        repositorio_libros: RepositorioJsonBase[Libro],
    ) -> None:
        self.__repositorio: RepositorioStock = repositorio
        self.__repositorio_libros: RepositorioJsonBase[Libro] = (
            repositorio_libros
        )

    def listar(self) -> List[Stock]:
        """Lista todos los registros de stock, ordenados por libro.

        Returns:
            List[Stock]: Los registros de stock.
        """
        return self.__repositorio.leer_todos()

    def obtener(self, libro_id: int) -> Stock:
        """Obtiene el stock de un libro.

        Args:
            libro_id (int): Id del libro.

        Returns:
            Stock: El registro de stock.

        Raises:
            ValueError: Si el libro no existe o no tiene stock registrado.
        """
        libro: Libro = self.__obtener_libro(libro_id)
        stock: Optional[Stock] = self.__repositorio.leer_por_libro(libro_id)
        if stock is None:
            raise ValueError(
                f"El libro '{libro.titulo}' no tiene stock registrado: "
                "primero hay que dar de alta el stock."
            )
        return stock

    def crear(
        self, libro_id: int, cantidad: int, stock_minimo: int = 0
    ) -> Stock:
        """Da de alta el stock de un libro existente.

        Args:
            libro_id (int): Id del libro.
            cantidad (int): Unidades disponibles.
            stock_minimo (int): Unidades mínimas deseadas.

        Returns:
            Stock: El stock creado.

        Raises:
            ValueError: Si el libro no existe, si ya tiene stock o si algún
                dato es inválido.
        """
        stock: Stock = Stock(
            self.__obtener_libro(libro_id), cantidad, stock_minimo
        )
        return self.__repositorio.crear(stock)

    def actualizar(
        self, libro_id: int, cantidad: int, stock_minimo: int
    ) -> Stock:
        """Actualiza la cantidad y el mínimo del stock de un libro.

        Args:
            libro_id (int): Id del libro.
            cantidad (int): Nueva cantidad disponible.
            stock_minimo (int): Nuevo stock mínimo.

        Returns:
            Stock: El stock actualizado.

        Raises:
            ValueError: Si el libro no tiene stock o algún dato es inválido.
        """
        stock: Stock = self.obtener(libro_id)
        stock.cantidad = cantidad
        stock.stock_minimo = stock_minimo
        return self.__repositorio.actualizar(stock)

    def eliminar(self, libro_id: int) -> None:
        """Elimina el registro de stock de un libro.

        Args:
            libro_id (int): Id del libro.

        Raises:
            ValueError: Si el libro no tiene stock registrado.
        """
        self.obtener(libro_id)
        self.__repositorio.eliminar(libro_id)

    def registrar_ingreso(self, libro_id: int, cantidad: int) -> Stock:
        """Suma unidades al stock de un libro.

        Args:
            libro_id (int): Id del libro.
            cantidad (int): Unidades que ingresan (mayor a 0).

        Returns:
            Stock: El stock actualizado.

        Raises:
            TypeError: Si la cantidad no es int.
            ValueError: Si la cantidad no es positiva o el libro no tiene
                stock registrado.
        """
        unidades: int = _validar_cantidad_movimiento(cantidad)
        stock: Stock = self.obtener(libro_id)
        stock.cantidad = stock.cantidad + unidades
        return self.__repositorio.actualizar(stock)

    def registrar_egreso(self, libro_id: int, cantidad: int) -> Stock:
        """Resta unidades al stock de un libro sin dejarlo negativo.

        Args:
            libro_id (int): Id del libro.
            cantidad (int): Unidades que egresan (mayor a 0).

        Returns:
            Stock: El stock actualizado.

        Raises:
            TypeError: Si la cantidad no es int.
            ValueError: Si la cantidad no es positiva, si el libro no tiene
                stock registrado o si el stock es insuficiente.
        """
        unidades: int = _validar_cantidad_movimiento(cantidad)
        stock: Stock = self.obtener(libro_id)
        if unidades > stock.cantidad:
            raise ValueError(
                f"Stock insuficiente para '{stock.libro.titulo}': "
                f"disponible {stock.cantidad}, solicitado {unidades}."
            )
        stock.cantidad = stock.cantidad - unidades
        return self.__repositorio.actualizar(stock)

    def __obtener_libro(self, libro_id: int) -> Libro:
        """Busca un libro por id.

        Args:
            libro_id (int): Id del libro.

        Returns:
            Libro: El libro encontrado.

        Raises:
            ValueError: Si el libro no existe.
        """
        return _exigir(
            self.__repositorio_libros.leer_por_id(libro_id), "libro", libro_id
        )


class ServicioReportes:
    """Reportes del sistema, construidos a partir de otros servicios.

    Args:
        servicio_precios (ServicioPrecio): Servicio de precios.
        servicio_stock (ServicioStock): Servicio de stock.
        servicio_cotizaciones (ServicioCotizacionDolar): Servicio de
            cotizaciones.
    """

    def __init__(
        self,
        servicio_precios: ServicioPrecio,
        servicio_stock: ServicioStock,
        servicio_cotizaciones: ServicioCotizacionDolar,
    ) -> None:
        self.__servicio_precios: ServicioPrecio = servicio_precios
        self.__servicio_stock: ServicioStock = servicio_stock
        self.__servicio_cotizaciones: ServicioCotizacionDolar = (
            servicio_cotizaciones
        )

    def filas_inventario_valorizado(
        self, tipo_id: int
    ) -> Iterator[FilaInventario]:
        """Devuelve las filas del inventario valorizado en ARS.

        Valida la cotización vigente de inmediato y después devuelve un
        generador. Si la validación estuviera dentro del generador, el
        error recién aparecería al iterar.

        Args:
            tipo_id (int): Id del tipo de cotización a aplicar.

        Returns:
            Iterator[FilaInventario]: Filas (stock, precio unitario en ARS,
                subtotal en ARS); precio y subtotal son None si el libro no
                tiene precio convertible.

        Raises:
            ValueError: Si el tipo no existe o no tiene cotizaciones.
        """
        cotizacion: CotizacionDolar = (
            self.__servicio_cotizaciones.obtener_vigente(tipo_id)
        )
        return self.__generar_filas(cotizacion)

    def __generar_filas(
        self, cotizacion: CotizacionDolar
    ) -> Iterator[FilaInventario]:
        """Genera una fila de inventario por cada registro de stock.

        Args:
            cotizacion (CotizacionDolar): Cotización a aplicar a los precios
                en USD.

        Yields:
            FilaInventario: (stock, precio unitario en ARS, subtotal en ARS).
        """
        for stock in self.__servicio_stock.listar():
            precio_ars: Optional[float] = (
                self.__servicio_precios.precio_en_ars(
                    stock.libro_id, cotizacion
                )
            )
            subtotal: Optional[float] = None
            if precio_ars is not None:
                subtotal = round(precio_ars * stock.cantidad, 2)
            yield stock, precio_ars, subtotal

    def total_inventario_valorizado(self, tipo_id: int) -> float:
        """Suma los subtotales del inventario valorizado en ARS.

        Args:
            tipo_id (int): Id del tipo de cotización a aplicar.

        Returns:
            float: Total en ARS de los libros con precio convertible.

        Raises:
            ValueError: Si el tipo no existe o no tiene cotizaciones.
        """
        return round(
            sum(
                subtotal
                for _, _, subtotal in self.filas_inventario_valorizado(
                    tipo_id
                )
                if subtotal is not None
            ),
            2,
        )

    def libros_bajo_stock_minimo(self) -> List[Stock]:
        """Lista los stocks por debajo del mínimo, del mayor faltante al menor.

        Returns:
            List[Stock]: Los registros de stock bajo el mínimo.
        """
        bajos: List[Stock] = [
            stock
            for stock in self.__servicio_stock.listar()
            if stock.esta_por_debajo_del_minimo()
        ]
        return sorted(
            bajos,
            key=lambda stock: stock.stock_minimo - stock.cantidad,
            reverse=True,
        )

    def historico_cotizacion(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve el histórico de un tipo de cotización.

        Args:
            tipo_id (int): Id del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Cotizaciones en orden cronológico.

        Raises:
            ValueError: Si el tipo no existe.
        """
        return self.__servicio_cotizaciones.historico(tipo_id)

    def variacion_porcentual(self, tipo_id: int) -> Optional[float]:
        """Calcula la variación de la venta entre la primera y la última.

        Args:
            tipo_id (int): Id del tipo de cotización.

        Returns:
            Optional[float]: Variación porcentual redondeada a 2 decimales,
                o None si hay menos de dos cotizaciones.

        Raises:
            ValueError: Si el tipo no existe.
        """
        historico: List[CotizacionDolar] = self.historico_cotizacion(tipo_id)
        if len(historico) < 2:
            return None
        inicial: float = historico[0].venta
        final: float = historico[-1].venta
        return round((final - inicial) / inicial * 100, 2)
