#@title Escritura de main.py
"""Punto de entrada de Book Manager.

Arma las capas del sistema (repositorios, servicios y consola) sobre la
carpeta de datos, importa opcionalmente los datos iniciales desde los CSV y
ejecuta la interfaz de consola.
"""
import os
from typing import Callable, Dict

from book_manager.preload_data.preload_data import (
    CARPETA_CSV,
    CARPETA_DATOS,
    CargadorDatosIniciales,
    limpiar_datos,
)
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
    RepositorioTipoCotizacion,
)
from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioReportes,
    ServicioStock,
    ServicioTipoCotizacion,
)
from book_manager.ui.console import ConsolaBookManager


class ServiciosBookManager:
    """Raíz de composición: arma repositorios y servicios sobre una carpeta.

    Es el único lugar del sistema donde se decide qué implementación concreta
    recibe cada capa.

    Args:
        carpeta_datos (str): Carpeta donde persisten los archivos JSON.
    """

    def __init__(self, carpeta_datos: str = CARPETA_DATOS) -> None:

        def ruta(nombre_archivo: str) -> str:
            return os.path.join(carpeta_datos, nombre_archivo)

        repo_generos: RepositorioGenero = RepositorioGenero(
            ruta("generos.json")
        )
        repo_editoriales: RepositorioEditorial = RepositorioEditorial(
            ruta("editoriales.json")
        )
        repo_monedas: RepositorioMoneda = RepositorioMoneda(
            ruta("monedas.json")
        )
        repo_tipos: RepositorioTipoCotizacion = RepositorioTipoCotizacion(
            ruta("tipos_cotizacion.json")
        )
        repo_libros: RepositorioLibro = RepositorioLibro(
            ruta("libros.json"), repo_generos, repo_editoriales
        )
        repo_precios: RepositorioPrecio = RepositorioPrecio(
            ruta("precios.json"), repo_libros, repo_monedas
        )
        repo_stocks: RepositorioStock = RepositorioStock(
            ruta("stocks.json"), repo_libros
        )
        repo_cotizaciones: RepositorioCotizacionDolar = (
            RepositorioCotizacionDolar(
                ruta("cotizaciones_dolar.json"), repo_tipos
            )
        )

        self.__generos: ServicioGenero = ServicioGenero(
            repo_generos, repo_libros
        )
        self.__editoriales: ServicioEditorial = ServicioEditorial(
            repo_editoriales, repo_libros
        )
        self.__monedas: ServicioMoneda = ServicioMoneda(
            repo_monedas, repo_precios
        )
        self.__tipos: ServicioTipoCotizacion = ServicioTipoCotizacion(
            repo_tipos, repo_cotizaciones
        )
        self.__libros: ServicioLibro = ServicioLibro(
            repo_libros, repo_generos, repo_editoriales, repo_precios,
            repo_stocks,
        )
        self.__cotizaciones: ServicioCotizacionDolar = (
            ServicioCotizacionDolar(repo_cotizaciones, repo_tipos)
        )
        self.__precios: ServicioPrecio = ServicioPrecio(
            repo_precios, repo_libros, repo_monedas, self.__cotizaciones
        )
        self.__stock: ServicioStock = ServicioStock(repo_stocks, repo_libros)
        self.__reportes: ServicioReportes = ServicioReportes(
            self.__precios, self.__stock, self.__cotizaciones
        )

    @property
    def generos(self) -> ServicioGenero:
        """ServicioGenero: Servicio de géneros."""
        return self.__generos

    @property
    def editoriales(self) -> ServicioEditorial:
        """ServicioEditorial: Servicio de editoriales."""
        return self.__editoriales

    @property
    def monedas(self) -> ServicioMoneda:
        """ServicioMoneda: Servicio de monedas."""
        return self.__monedas

    @property
    def tipos(self) -> ServicioTipoCotizacion:
        """ServicioTipoCotizacion: Servicio de tipos de cotización."""
        return self.__tipos

    @property
    def libros(self) -> ServicioLibro:
        """ServicioLibro: Servicio de libros."""
        return self.__libros

    @property
    def cotizaciones(self) -> ServicioCotizacionDolar:
        """ServicioCotizacionDolar: Servicio de cotizaciones."""
        return self.__cotizaciones

    @property
    def precios(self) -> ServicioPrecio:
        """ServicioPrecio: Servicio de precios."""
        return self.__precios

    @property
    def stock(self) -> ServicioStock:
        """ServicioStock: Servicio de stock."""
        return self.__stock

    @property
    def reportes(self) -> ServicioReportes:
        """ServicioReportes: Servicio de reportes."""
        return self.__reportes

    def crear_cargador(
        self, carpeta_csv: str = CARPETA_CSV
    ) -> CargadorDatosIniciales:
        """Crea el cargador de datos iniciales conectado a los servicios.

        Args:
            carpeta_csv (str): Carpeta con los CSV de migración.

        Returns:
            CargadorDatosIniciales: El cargador listo para usar.
        """
        return CargadorDatosIniciales(
            carpeta_csv,
            self.__generos,
            self.__editoriales,
            self.__monedas,
            self.__tipos,
            self.__libros,
            self.__precios,
            self.__stock,
            self.__cotizaciones,
        )

    def crear_consola(
        self, entrada: Callable[[str], str] = input
    ) -> ConsolaBookManager:
        """Crea la consola conectada a los servicios.

        Args:
            entrada (Callable[[str], str]): Función de lectura de respuestas.

        Returns:
            ConsolaBookManager: La consola lista para ejecutar.
        """
        return ConsolaBookManager(
            self.__libros,
            self.__generos,
            self.__editoriales,
            self.__monedas,
            self.__tipos,
            self.__precios,
            self.__stock,
            self.__cotizaciones,
            self.__reportes,
            entrada,
        )


def main(
    import_default_data: bool = False,
    carpeta_datos: str = CARPETA_DATOS,
    carpeta_csv: str = CARPETA_CSV,
    entrada: Callable[[str], str] = input,
) -> None:
    """Ejecuta Book Manager.

    Args:
        import_default_data (bool): Si es True, borra los datos persistidos y
            los recarga desde los CSV antes de abrir la consola.
        carpeta_datos (str): Carpeta de los archivos JSON (por defecto,
            data/).
        carpeta_csv (str): Carpeta de los CSV de migración.
        entrada (Callable[[str], str]): Función de lectura de respuestas
            (por defecto, input).
    """
    servicios: ServiciosBookManager = ServiciosBookManager(carpeta_datos)
    if import_default_data:
        borrados: int = limpiar_datos(carpeta_datos)
        try:
            resumen: Dict[str, int] = (
                servicios.crear_cargador(carpeta_csv).cargar_todo()
            )
        except ValueError as error:
            print(f"No se pudieron importar los datos iniciales: {error}")
            return
        print(
            "Datos iniciales importados desde CSV "
            f"({borrados} archivos JSON reemplazados):"
        )
        for entidad, cantidad in resumen.items():
            print(f"  {entidad}: {cantidad}")
    servicios.crear_consola(entrada).ejecutar()


if __name__ == "__main__":
    main()
