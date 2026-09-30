# Changelog

Registro de cambios del proyecto. Lo más reciente se encuentra arriba.

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
