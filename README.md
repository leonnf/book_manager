# Book Manager

**Trabajo Práctico Integrador — CLCD 182 Seminario de Actualización I**
Licenciatura en Ciencia de Datos — Universidad del Gran Rosario

## Sprint actual: Sprint 1

## Grupo N° 39

- Fabian Leon
- Sebastian Luna
- Marco Fouad
- Gabriel Gallardo

Repositorio: https://github.com/leonnf/book_manager

## Objetivo

Aplicar los conocimientos adquiridos en programación orientada a objetos y en
almacenamiento de datos en archivos para su persistencia.

## Introducción y contexto del Sprint 1

Una librería con venta al público necesita modernizar su sistema de gestión de
inventario de libros. Por la fluctuación en los costos de importación de
material bibliográfico, el sistema debe gestionar precios en diferentes monedas
y seguir la cotización del dólar para actualizar sus valores.

En este sprint se desarrolla una aplicación de consola (CLI) en Python que
permite gestionar el inventario de la librería con CRUD completo sobre cada
entidad y persistencia en archivos. Se toma como referencia el sitio de
[Cúspide](https://www.cuspide.com/).

### Entidades

- **Libro**: título del catálogo (ISBN, título, autor, editorial, género, etc.).
- **Genero**: categoría literaria del libro.
- **Editorial**: proveedor o distribuidora de los libros.
- **Moneda**: monedas en las que se expresa un precio (ARS, USD, etc.).
- **TipoCotizacion**: tipos de cotización del dólar (Oficial, Blue, MEP, etc.).
- **Precio**: valor de un libro en una moneda determinada.
- **Stock**: cantidad disponible de cada libro.
- **CotizacionDolar**: registro histórico de cotizaciones por tipo y fecha
  (corresponde a la entidad "Cotizacion" del enunciado).

### Alcance y decisiones del sprint

- Las cotizaciones se cargan desde archivos CSV o por consola. La consulta en
  tiempo real y la comparación con la competencia web quedan para sprints
  posteriores.
- Los datos iniciales se importan desde `migrations/csv` y los datos operativos
  se persisten en archivos JSON dentro de `data/`.
- Solo se utiliza la biblioteca estándar de Python.

## Estructura del proyecto

```
book_manager/
├── src/
│   └── book_manager/
│       ├── entities/          # clases entidad
│       ├── repositories/      # persistencia (CRUD sobre archivos)
│       ├── services/          # lógica de negocio y validaciones
│       ├── preload_data/      # carga inicial desde migrations/csv
│       ├── migrations/csv/    # datos iniciales (CSV)
│       ├── data/              # datos persistidos (JSON)
│       ├── ui/                # interfaz de consola
│       └── main.py            # punto de entrada
├── CHANGELOG.md
├── README.md
└── requirements.txt
```
