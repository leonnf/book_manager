# Changelog

Registro de cambios del proyecto. Lo más reciente se encuentra arriba.

[Ejercicio 04]
- Creación de `services.py` con la clase abstracta genérica
  `ServicioEntidad[T]` (listar, obtener y eliminar con hook abstracto
  `_validar_eliminacion`).
- Servicios de `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro`,
  `Precio`, `Stock` y `CotizacionDolar` con CRUD completo a partir de datos
  simples.
- Reglas de unicidad: nombre de género, editorial y tipo; código de moneda;
  ISBN; precio por libro, moneda y fecha; cotización por tipo y fecha.
- Integridad referencial: no se eliminan géneros ni editoriales con libros,
  libros con precios o stock, monedas con precios ni tipos con cotizaciones.
- Movimientos de stock (ingreso y egreso) sin permitir stock negativo ni
  movimientos sobre libros sin stock registrado.
- Conversión de precios con la última cotización del tipo elegido: precio en
  ARS directo y precio en USD convertido con el valor de venta.
- `ServicioReportes`: inventario valorizado en ARS (generador con validación
  previa de la cotización), libros con stock bajo el mínimo e histórico de
  cotizaciones con variación porcentual.
- Celda de prueba de servicios en una carpeta temporal.

[Ejercicio 03]
- Creación de `repositories.py` con las interfaces de la cátedra
  (`IRepositorio[T]`, `IRepositorioStock`, `IRepositorioCotizacionDolar`)
  sin cambios en sus firmas.
- Clase `ArchivoJson` para leer y escribir listas de registros en JSON,
  reutilizada por composición en todos los repositorios.
- `RepositorioJsonBase` genérico con CRUD completo y `siguiente_id()`; cada
  subclase implementa `_a_dict` y `_desde_dict` (Template Method).
- Repositorios de `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro`
  y `Precio`.
- `RepositorioStock` y `RepositorioCotizacionDolar` con claves `libro_id` y
  (`tipo_id`, `fecha`), más `leer_todos()` para los listados.
- Relaciones persistidas como ids y rehidratadas como objetos mediante
  repositorios inyectados por constructor.
- Celda de prueba del CRUD en una carpeta temporal que se limpia en cada
  ejecución.

[Ejercicio 02]
- Creación de `entities.py` con la clase abstracta `EntidadBase` (id de solo
  lectura, igualdad y hash por clase e id, `__str__` abstracto).
- Entidades `Genero`, `Editorial`, `Moneda`, `TipoCotizacion`, `Libro` y
  `Precio` con atributos privados, properties y validación en setters.
- `Libro` con atributos tomados de la ficha de Cúspide: ISBN de 13 dígitos,
  título y autor normalizados a mayúsculas, idioma, páginas y URL de
  referencia.
- `Stock` y `CotizacionDolar` con claves de solo lectura (`libro_id`;
  `tipo_id` y `fecha`).
- `CotizacionDolar` con compra y venta de solo lectura, modificables solo con
  `actualizar_valores`, que garantiza venta >= compra.
- Celda de prueba de entidades, relaciones y validaciones.

[Ejercicio 01]
- Inicialización del repositorio y creación de la rama Sprint_1.
- Creación de la estructura de carpetas con sus paquetes (`__init__.py`).
- Carpetas `migrations/csv` y `data` versionadas mediante `.gitkeep`.
- README.md con el sprint actual, el objetivo, la introducción y el contexto.
- CHANGELOG.md inicial.
- requirements.txt (el proyecto usa solo la biblioteca estándar).
- .gitignore para excluir cachés de Python y checkpoints de Jupyter.
- Invitación como colaboradores a lcd-sa182@ugr.edu.ar, fpasinato@ugr.edu.ar
  y srobadorpapich@ugr.edu.ar.
