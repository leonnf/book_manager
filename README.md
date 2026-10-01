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

## Datos iniciales

### Origen

Los géneros, las editoriales, los libros (título, autor, ISBN, editorial,
género, año y URL) y los precios en pesos provienen de una muestra del sitio
de [Cúspide](https://www.cuspide.com/), relevada el **28/09/2026**. Los
precios en ARS se registran vigentes desde esa fecha.

### Correcciones aplicadas a la muestra

- Autor de *Sempiterno*: `JOANA, MARCÚS` se corrigió a `MARCÚS, JOANA`, igual
  que en *Antes de diciembre*.
- Autor de *Blanco*: `BRET EASTON ELLIS` se corrigió a `ELLIS, BRET EASTON`
  (formato `APELLIDO, NOMBRE`).
- Editorial: `PLAZA & JANES` se unificó como `PLAZA & JANÉS`.
- Stock: el valor `99999` de Cúspide es un marcador de disponibilidad online;
  se reemplazó por cantidades realistas para una librería física.

### Datos complementarios

- **Monedas**: 10 monedas con su código ISO 4217.
- **Tipos de cotización**: 10 tipos. Ahorro, Turista y Lujo existieron
  históricamente y se incluyen para completar el mínimo de registros.
- **Precios**: *Binding 13* (edición española importada) tiene precio solo en
  USD, para mostrar la conversión con la cotización del dólar. *La noche de la
  usina* y *Ser feliz era esto* tienen además un precio anterior (agosto de
  2026), para mostrar que se toma el precio vigente más reciente.
- **Páginas y emails de contacto**: quedan vacíos porque la muestra no los
  incluye.

### Cotizaciones ilustrativas

Las cotizaciones del dólar (Oficial, Blue y MEP, del 21 al 25/09/2026) son
**valores ilustrativos, no oficiales**. La consulta de cotizaciones en tiempo
real queda fuera del alcance del Sprint 1.

### Carga

Los CSV de `migrations/csv` se cargan con `preload_data.py` a través de los
servicios, así cumplen las mismas reglas de negocio que un alta manual. El
resultado queda en los JSON de `data/`, que se versionan en el repositorio.
Con `main(import_default_data=True)` los datos se limpian y se recargan desde
los CSV.

## Cómo ejecutar

Requisitos: Python 3.10 o superior. No hace falta instalar dependencias:
el proyecto usa solo la biblioteca estándar.

```bash
git clone https://github.com/leonnf/book_manager.git
cd book_manager
git checkout Sprint_1
cd src
python -m book_manager.main
```

- `python -m book_manager.main` abre la consola con los datos de `data/`.
- Para recargar los datos iniciales desde los CSV:

```bash
  python -c "from book_manager.main import main; main(import_default_data=True)"
```

- Las operaciones de la consola modifican los JSON de `data/`. Para volver al
  estado del repositorio: `git checkout -- book_manager/data`.


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
