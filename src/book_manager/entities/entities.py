#@title Escritura de entities.py
"""Entidades del dominio de Book Manager.

Define las clases que representan los conceptos del negocio de la librería:
libros, géneros, editoriales, monedas, precios, stock y cotizaciones del
dólar. Todas encapsulan sus atributos y validan los datos en sus setters.
"""
import abc
import datetime
from typing import Optional

ANIO_PRIMER_LIBRO_IMPRESO: int = 1450


def _validar_texto(valor: str, campo: str) -> str:
    """Valida que un valor sea un texto no vacío.

    Args:
        valor (str): Valor a validar.
        campo (str): Nombre del campo, para el mensaje de error.

    Returns:
        str: El texto sin espacios al principio ni al final.

    Raises:
        TypeError: Si el valor no es de tipo str.
        ValueError: Si el texto está vacío.
    """
    if not isinstance(valor, str):
        raise TypeError(f"El campo '{campo}' debe ser de tipo str.")
    texto: str = valor.strip()
    if not texto:
        raise ValueError(f"El campo '{campo}' no puede estar vacío.")
    return texto


def _validar_entero(
    valor: int,
    campo: str,
    minimo: int,
    maximo: Optional[int] = None,
) -> int:
    """Valida que un valor sea un entero dentro de un rango.

    Args:
        valor (int): Valor a validar.
        campo (str): Nombre del campo, para el mensaje de error.
        minimo (int): Valor mínimo permitido (inclusive).
        maximo (Optional[int]): Valor máximo permitido (inclusive), o None
            si no hay límite superior.

    Returns:
        int: El valor validado.

    Raises:
        TypeError: Si el valor no es int (se rechaza también bool).
        ValueError: Si el valor está fuera del rango permitido.
    """
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"El campo '{campo}' debe ser de tipo int.")
    if valor < minimo:
        raise ValueError(
            f"El campo '{campo}' debe ser mayor o igual a {minimo}."
        )
    if maximo is not None and valor > maximo:
        raise ValueError(
            f"El campo '{campo}' debe ser menor o igual a {maximo}."
        )
    return valor


def _validar_monto(valor: float, campo: str) -> float:
    """Valida que un valor sea un monto numérico mayor a cero.

    Args:
        valor (float): Valor a validar (se aceptan int y float).
        campo (str): Nombre del campo, para el mensaje de error.

    Returns:
        float: El monto redondeado a 2 decimales.

    Raises:
        TypeError: Si el valor no es numérico (se rechaza también bool).
        ValueError: Si el valor es menor o igual a cero.
    """
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise TypeError(f"El campo '{campo}' debe ser numérico.")
    if valor <= 0:
        raise ValueError(f"El campo '{campo}' debe ser mayor a 0.")
    return round(float(valor), 2)


def _validar_fecha(
    valor: datetime.date,
    campo: str,
    permitir_futura: bool = True,
) -> datetime.date:
    """Valida que un valor sea una fecha (sin hora).

    Args:
        valor (datetime.date): Valor a validar.
        campo (str): Nombre del campo, para el mensaje de error.
        permitir_futura (bool): Si es False, rechaza fechas posteriores a hoy.

    Returns:
        datetime.date: La fecha validada.

    Raises:
        TypeError: Si el valor no es datetime.date (se rechaza datetime).
        ValueError: Si la fecha es futura y no está permitido.
    """
    es_fecha: bool = isinstance(valor, datetime.date)
    if not es_fecha or isinstance(valor, datetime.datetime):
        raise TypeError(
            f"El campo '{campo}' debe ser de tipo datetime.date."
        )
    if not permitir_futura and valor > datetime.date.today():
        raise ValueError(
            f"El campo '{campo}' no puede ser una fecha futura."
        )
    return valor


def _validar_instancia(valor: object, clase: type, campo: str) -> None:
    """Valida que un valor sea instancia de una clase determinada.

    Args:
        valor (object): Valor a validar.
        clase (type): Clase esperada.
        campo (str): Nombre del campo, para el mensaje de error.

    Raises:
        TypeError: Si el valor no es instancia de la clase esperada.
    """
    if not isinstance(valor, clase):
        raise TypeError(
            f"El campo '{campo}' debe ser de tipo {clase.__name__}."
        )


def _formatear_monto(monto: float) -> str:
    """Formatea un monto con el estilo argentino (por ejemplo, 48.899,00).

    Args:
        monto (float): Monto a formatear.

    Returns:
        str: El monto con punto de miles y coma decimal.
    """
    texto: str = f"{monto:,.2f}"
    return texto.replace(",", "#").replace(".", ",").replace("#", ".")


class EntidadBase(abc.ABC):
    """Clase base abstracta para las entidades identificadas por un id.

    El id es de solo lectura. Lo genera el repositorio (siguiente_id) y el
    servicio lo usa antes de instanciar la entidad.

    Args:
        id (int): Identificador único, entero mayor a 0.

    Raises:
        TypeError: Si el id no es un entero.
        ValueError: Si el id es menor a 1.
    """

    def __init__(self, id: int) -> None:
        self.__id: int = _validar_entero(id, "id", 1)

    @property
    def id(self) -> int:
        """int: Identificador único de la entidad (solo lectura)."""
        return self.__id

    def __eq__(self, otro: object) -> bool:
        """Compara dos entidades por clase e id.

        Args:
            otro (object): Objeto a comparar.

        Returns:
            bool: True si son de la misma clase y tienen el mismo id.
        """
        if not isinstance(otro, EntidadBase):
            return NotImplemented
        return type(self) is type(otro) and self.id == otro.id

    def __hash__(self) -> int:
        """Calcula el hash a partir de la clase y el id.

        Returns:
            int: Hash de la entidad.
        """
        return hash((type(self).__name__, self.id))

    def __repr__(self) -> str:
        """Devuelve una representación técnica de la entidad.

        Returns:
            str: Nombre de la clase y su id.
        """
        return f"{type(self).__name__}(id={self.id})"

    @abc.abstractmethod
    def __str__(self) -> str:
        """Devuelve la representación legible de la entidad para la consola.

        Returns:
            str: Texto descriptivo de la entidad.
        """


class Genero(EntidadBase):
    """Categoría literaria a la que pertenece un libro.

    Args:
        id (int): Identificador único.
        nombre (str): Nombre del género (por ejemplo, "Psicología").
        descripcion (str): Descripción breve del género.
    """

    def __init__(self, id: int, nombre: str, descripcion: str) -> None:
        super().__init__(id)
        self.nombre = nombre
        self.descripcion = descripcion

    @property
    def nombre(self) -> str:
        """str: Nombre del género."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre: str = _validar_texto(valor, "nombre")

    @property
    def descripcion(self) -> str:
        """str: Descripción breve del género."""
        return self.__descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        self.__descripcion: str = _validar_texto(valor, "descripcion")

    def __str__(self) -> str:
        """Devuelve el género en formato legible.

        Returns:
            str: Id, nombre y descripción.
        """
        return f"[{self.id}] {self.nombre}: {self.descripcion}"


class Editorial(EntidadBase):
    """Proveedor o distribuidora que provee los libros a la librería.

    Args:
        id (int): Identificador único.
        nombre (str): Nombre de la editorial.
        pais_origen (str): País de origen de la editorial.
        email_contacto (Optional[str]): Email de contacto, si se conoce.
    """

    def __init__(
        self,
        id: int,
        nombre: str,
        pais_origen: str,
        email_contacto: Optional[str] = None,
    ) -> None:
        super().__init__(id)
        self.nombre = nombre
        self.pais_origen = pais_origen
        self.email_contacto = email_contacto

    @property
    def nombre(self) -> str:
        """str: Nombre de la editorial."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre: str = _validar_texto(valor, "nombre")

    @property
    def pais_origen(self) -> str:
        """str: País de origen de la editorial."""
        return self.__pais_origen

    @pais_origen.setter
    def pais_origen(self, valor: str) -> None:
        self.__pais_origen: str = _validar_texto(valor, "pais_origen")

    @property
    def email_contacto(self) -> Optional[str]:
        """Optional[str]: Email de contacto en minúsculas, o None."""
        return self.__email_contacto

    @email_contacto.setter
    def email_contacto(self, valor: Optional[str]) -> None:
        email_validado: Optional[str] = None
        if valor is not None:
            email: str = _validar_texto(valor, "email_contacto").lower()
            usuario, arroba, dominio = email.partition("@")
            formato_invalido: bool = (
                not usuario
                or not arroba
                or "@" in dominio
                or "." not in dominio
                or " " in email
            )
            if formato_invalido:
                raise ValueError(
                    "El campo 'email_contacto' no tiene un formato válido."
                )
            email_validado = email
        self.__email_contacto: Optional[str] = email_validado

    def __str__(self) -> str:
        """Devuelve la editorial en formato legible.

        Returns:
            str: Id, nombre, país y email (si existe).
        """
        texto: str = f"[{self.id}] {self.nombre} ({self.pais_origen})"
        if self.email_contacto is not None:
            texto += f" - {self.email_contacto}"
        return texto


class Moneda(EntidadBase):
    """Moneda en la que se puede expresar un precio.

    Args:
        id (int): Identificador único.
        codigo (str): Código ISO 4217 de 3 letras (por ejemplo, "ARS").
        nombre (str): Nombre de la moneda.
        simbolo (str): Símbolo de la moneda (por ejemplo, "$" o "U$s").
    """

    def __init__(
        self, id: int, codigo: str, nombre: str, simbolo: str
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.nombre = nombre
        self.simbolo = simbolo

    @property
    def codigo(self) -> str:
        """str: Código ISO 4217 en mayúsculas."""
        return self.__codigo

    @codigo.setter
    def codigo(self, valor: str) -> None:
        texto: str = _validar_texto(valor, "codigo").upper()
        if len(texto) != 3 or not texto.isalpha():
            raise ValueError(
                "El campo 'codigo' debe tener 3 letras (ISO 4217)."
            )
        self.__codigo: str = texto

    @property
    def nombre(self) -> str:
        """str: Nombre de la moneda."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre: str = _validar_texto(valor, "nombre")

    @property
    def simbolo(self) -> str:
        """str: Símbolo de la moneda."""
        return self.__simbolo

    @simbolo.setter
    def simbolo(self, valor: str) -> None:
        self.__simbolo: str = _validar_texto(valor, "simbolo")

    def __str__(self) -> str:
        """Devuelve la moneda en formato legible.

        Returns:
            str: Id, código, nombre y símbolo.
        """
        return f"[{self.id}] {self.codigo} - {self.nombre} ({self.simbolo})"


class TipoCotizacion(EntidadBase):
    """Tipo de cotización del dólar (Oficial, Blue, MEP, etc.).

    Args:
        id (int): Identificador único.
        nombre (str): Nombre del tipo de cotización.
        descripcion (str): Descripción breve del tipo de cotización.
    """

    def __init__(self, id: int, nombre: str, descripcion: str) -> None:
        super().__init__(id)
        self.nombre = nombre
        self.descripcion = descripcion

    @property
    def nombre(self) -> str:
        """str: Nombre del tipo de cotización."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre: str = _validar_texto(valor, "nombre")

    @property
    def descripcion(self) -> str:
        """str: Descripción breve del tipo de cotización."""
        return self.__descripcion

    @descripcion.setter
    def descripcion(self, valor: str) -> None:
        self.__descripcion: str = _validar_texto(valor, "descripcion")

    def __str__(self) -> str:
        """Devuelve el tipo de cotización en formato legible.

        Returns:
            str: Id, nombre y descripción.
        """
        return f"[{self.id}] {self.nombre}: {self.descripcion}"


class Libro(EntidadBase):
    """Título del catálogo de la librería.

    Args:
        id (int): Identificador único.
        isbn (str): ISBN de 13 dígitos (se aceptan guiones y espacios).
        titulo (str): Título de la obra (se guarda en mayúsculas).
        autor (str): Autor de la obra (se guarda en mayúsculas).
        anio_publicacion (int): Año de publicación.
        genero (Genero): Género al que pertenece el libro.
        editorial (Editorial): Editorial que provee el libro.
        idioma (str): Idioma de la obra.
        paginas (Optional[int]): Cantidad de páginas, si se conoce.
        url_referencia (Optional[str]): URL de la ficha en Cúspide.
    """

    def __init__(
        self,
        id: int,
        isbn: str,
        titulo: str,
        autor: str,
        anio_publicacion: int,
        genero: Genero,
        editorial: Editorial,
        idioma: str = "Español",
        paginas: Optional[int] = None,
        url_referencia: Optional[str] = None,
    ) -> None:
        super().__init__(id)
        self.isbn = isbn
        self.titulo = titulo
        self.autor = autor
        self.anio_publicacion = anio_publicacion
        self.genero = genero
        self.editorial = editorial
        self.idioma = idioma
        self.paginas = paginas
        self.url_referencia = url_referencia

    @property
    def isbn(self) -> str:
        """str: ISBN de 13 dígitos, sin guiones."""
        return self.__isbn

    @isbn.setter
    def isbn(self, valor: str) -> None:
        texto: str = _validar_texto(valor, "isbn")
        isbn_limpio: str = texto.replace("-", "").replace(" ", "")
        if len(isbn_limpio) != 13 or not isbn_limpio.isdigit():
            raise ValueError("El campo 'isbn' debe tener 13 dígitos.")
        self.__isbn: str = isbn_limpio

    @property
    def titulo(self) -> str:
        """str: Título de la obra en mayúsculas."""
        return self.__titulo

    @titulo.setter
    def titulo(self, valor: str) -> None:
        self.__titulo: str = _validar_texto(valor, "titulo").upper()

    @property
    def autor(self) -> str:
        """str: Autor de la obra en mayúsculas."""
        return self.__autor

    @autor.setter
    def autor(self, valor: str) -> None:
        self.__autor: str = _validar_texto(valor, "autor").upper()

    @property
    def anio_publicacion(self) -> int:
        """int: Año de publicación."""
        return self.__anio_publicacion

    @anio_publicacion.setter
    def anio_publicacion(self, valor: int) -> None:
        self.__anio_publicacion: int = _validar_entero(
            valor,
            "anio_publicacion",
            ANIO_PRIMER_LIBRO_IMPRESO,
            datetime.date.today().year,
        )

    @property
    def genero(self) -> Genero:
        """Genero: Género al que pertenece el libro."""
        return self.__genero

    @genero.setter
    def genero(self, valor: Genero) -> None:
        _validar_instancia(valor, Genero, "genero")
        self.__genero: Genero = valor

    @property
    def editorial(self) -> Editorial:
        """Editorial: Editorial que provee el libro."""
        return self.__editorial

    @editorial.setter
    def editorial(self, valor: Editorial) -> None:
        _validar_instancia(valor, Editorial, "editorial")
        self.__editorial: Editorial = valor

    @property
    def idioma(self) -> str:
        """str: Idioma de la obra."""
        return self.__idioma

    @idioma.setter
    def idioma(self, valor: str) -> None:
        self.__idioma: str = _validar_texto(valor, "idioma")

    @property
    def paginas(self) -> Optional[int]:
        """Optional[int]: Cantidad de páginas, o None si no se conoce."""
        return self.__paginas

    @paginas.setter
    def paginas(self, valor: Optional[int]) -> None:
        paginas_validadas: Optional[int] = None
        if valor is not None:
            paginas_validadas = _validar_entero(valor, "paginas", 1)
        self.__paginas: Optional[int] = paginas_validadas

    @property
    def url_referencia(self) -> Optional[str]:
        """Optional[str]: URL de la ficha en Cúspide, o None."""
        return self.__url_referencia

    @url_referencia.setter
    def url_referencia(self, valor: Optional[str]) -> None:
        url_validada: Optional[str] = None
        if valor is not None:
            url: str = _validar_texto(valor, "url_referencia")
            if not url.startswith(("http://", "https://")):
                raise ValueError(
                    "El campo 'url_referencia' debe empezar con "
                    "http:// o https://."
                )
            url_validada = url
        self.__url_referencia: Optional[str] = url_validada

    def __str__(self) -> str:
        """Devuelve el libro en formato legible.

        Returns:
            str: Id, título, autor, año, ISBN, género y editorial.
        """
        return (
            f"[{self.id}] {self.titulo} - {self.autor} "
            f"({self.anio_publicacion}) | ISBN {self.isbn} | "
            f"{self.genero.nombre} | {self.editorial.nombre}"
        )


class Precio(EntidadBase):
    """Valor monetario de un libro en una moneda determinada.

    Args:
        id (int): Identificador único.
        libro (Libro): Libro al que corresponde el precio.
        moneda (Moneda): Moneda en la que se expresa el precio.
        monto (float): Monto mayor a cero (se redondea a 2 decimales).
        fecha_vigencia (datetime.date): Fecha desde la que rige el precio.
    """

    def __init__(
        self,
        id: int,
        libro: Libro,
        moneda: Moneda,
        monto: float,
        fecha_vigencia: datetime.date,
    ) -> None:
        super().__init__(id)
        self.libro = libro
        self.moneda = moneda
        self.monto = monto
        self.fecha_vigencia = fecha_vigencia

    @property
    def libro(self) -> Libro:
        """Libro: Libro al que corresponde el precio."""
        return self.__libro

    @libro.setter
    def libro(self, valor: Libro) -> None:
        _validar_instancia(valor, Libro, "libro")
        self.__libro: Libro = valor

    @property
    def moneda(self) -> Moneda:
        """Moneda: Moneda en la que se expresa el precio."""
        return self.__moneda

    @moneda.setter
    def moneda(self, valor: Moneda) -> None:
        _validar_instancia(valor, Moneda, "moneda")
        self.__moneda: Moneda = valor

    @property
    def monto(self) -> float:
        """float: Monto del precio, redondeado a 2 decimales."""
        return self.__monto

    @monto.setter
    def monto(self, valor: float) -> None:
        self.__monto: float = _validar_monto(valor, "monto")

    @property
    def fecha_vigencia(self) -> datetime.date:
        """datetime.date: Fecha desde la que rige el precio."""
        return self.__fecha_vigencia

    @fecha_vigencia.setter
    def fecha_vigencia(self, valor: datetime.date) -> None:
        self.__fecha_vigencia: datetime.date = _validar_fecha(
            valor, "fecha_vigencia"
        )

    def __str__(self) -> str:
        """Devuelve el precio en formato legible.

        Returns:
            str: Id, título del libro, monto, moneda y fecha de vigencia.
        """
        return (
            f"[{self.id}] {self.libro.titulo}: {self.moneda.simbolo} "
            f"{_formatear_monto(self.monto)} ({self.moneda.codigo}) "
            f"vigente desde {self.fecha_vigencia:%d/%m/%Y}"
        )


class Stock:
    """Cantidad disponible de un libro. Su clave es el id del libro.

    Args:
        libro (Libro): Libro al que corresponde el stock (solo lectura).
        cantidad (int): Unidades disponibles (mayor o igual a 0).
        stock_minimo (int): Unidades mínimas deseadas (mayor o igual a 0).

    Raises:
        TypeError: Si libro no es un Libro o las cantidades no son int.
        ValueError: Si alguna cantidad es negativa.
    """

    def __init__(
        self, libro: Libro, cantidad: int, stock_minimo: int = 0
    ) -> None:
        _validar_instancia(libro, Libro, "libro")
        self.__libro: Libro = libro
        self.cantidad = cantidad
        self.stock_minimo = stock_minimo

    @property
    def libro(self) -> Libro:
        """Libro: Libro al que corresponde el stock (solo lectura)."""
        return self.__libro

    @property
    def libro_id(self) -> int:
        """int: Id del libro, clave del registro de stock."""
        return self.__libro.id

    @property
    def cantidad(self) -> int:
        """int: Unidades disponibles."""
        return self.__cantidad

    @cantidad.setter
    def cantidad(self, valor: int) -> None:
        self.__cantidad: int = _validar_entero(valor, "cantidad", 0)

    @property
    def stock_minimo(self) -> int:
        """int: Unidades mínimas deseadas."""
        return self.__stock_minimo

    @stock_minimo.setter
    def stock_minimo(self, valor: int) -> None:
        self.__stock_minimo: int = _validar_entero(valor, "stock_minimo", 0)

    def esta_por_debajo_del_minimo(self) -> bool:
        """Indica si la cantidad disponible es menor al stock mínimo.

        Returns:
            bool: True si cantidad < stock_minimo.
        """
        return self.cantidad < self.stock_minimo

    def __repr__(self) -> str:
        """Devuelve una representación técnica del stock.

        Returns:
            str: Nombre de la clase, id del libro y cantidad.
        """
        return f"Stock(libro_id={self.libro_id}, cantidad={self.cantidad})"

    def __str__(self) -> str:
        """Devuelve el stock en formato legible.

        Returns:
            str: Libro, cantidad disponible y stock mínimo.
        """
        return (
            f"[Libro {self.libro_id}] {self.libro.titulo}: "
            f"{self.cantidad} unidades (mínimo {self.stock_minimo})"
        )


class CotizacionDolar:
    """Cotización del dólar para un tipo y una fecha determinados.

    La clave es (tipo_id, fecha). Compra y venta son de solo lectura y se
    modifican únicamente con actualizar_valores, que garantiza que la venta
    nunca sea menor que la compra.

    Args:
        tipo (TipoCotizacion): Tipo de cotización (solo lectura).
        fecha (datetime.date): Fecha de la cotización, no futura (solo
            lectura).
        compra (float): Valor de compra en ARS, mayor a cero.
        venta (float): Valor de venta en ARS, mayor o igual a la compra.

    Raises:
        TypeError: Si algún dato no tiene el tipo esperado.
        ValueError: Si algún valor es inválido.
    """

    def __init__(
        self,
        tipo: TipoCotizacion,
        fecha: datetime.date,
        compra: float,
        venta: float,
    ) -> None:
        _validar_instancia(tipo, TipoCotizacion, "tipo")
        self.__tipo: TipoCotizacion = tipo
        self.__fecha: datetime.date = _validar_fecha(
            fecha, "fecha", permitir_futura=False
        )
        self.actualizar_valores(compra, venta)

    @property
    def tipo(self) -> TipoCotizacion:
        """TipoCotizacion: Tipo de cotización (solo lectura)."""
        return self.__tipo

    @property
    def tipo_id(self) -> int:
        """int: Id del tipo de cotización, parte de la clave."""
        return self.__tipo.id

    @property
    def fecha(self) -> datetime.date:
        """datetime.date: Fecha de la cotización (solo lectura)."""
        return self.__fecha

    @property
    def compra(self) -> float:
        """float: Valor de compra en ARS (solo lectura)."""
        return self.__compra

    @property
    def venta(self) -> float:
        """float: Valor de venta en ARS (solo lectura)."""
        return self.__venta

    def actualizar_valores(self, compra: float, venta: float) -> None:
        """Valida y asigna los valores de compra y venta en conjunto.

        Si alguna validación falla, el objeto conserva los valores previos.

        Args:
            compra (float): Nuevo valor de compra, mayor a cero.
            venta (float): Nuevo valor de venta, mayor o igual a la compra.

        Raises:
            TypeError: Si algún valor no es numérico.
            ValueError: Si algún valor es menor o igual a cero o si la
                venta es menor que la compra.
        """
        compra_validada: float = _validar_monto(compra, "compra")
        venta_validada: float = _validar_monto(venta, "venta")
        if venta_validada < compra_validada:
            raise ValueError(
                "El valor de 'venta' no puede ser menor que el de 'compra'."
            )
        self.__compra: float = compra_validada
        self.__venta: float = venta_validada

    def __repr__(self) -> str:
        """Devuelve una representación técnica de la cotización.

        Returns:
            str: Nombre de la clase, id del tipo y fecha.
        """
        return (
            f"CotizacionDolar(tipo_id={self.tipo_id}, "
            f"fecha={self.fecha.isoformat()})"
        )

    def __str__(self) -> str:
        """Devuelve la cotización en formato legible.

        Returns:
            str: Tipo, fecha y valores de compra y venta.
        """
        return (
            f"{self.tipo.nombre} {self.fecha:%d/%m/%Y}: "
            f"compra $ {_formatear_monto(self.compra)} | "
            f"venta $ {_formatear_monto(self.venta)}"
        )
