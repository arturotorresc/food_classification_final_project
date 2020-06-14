# Proyecto final para la clase de tecnologías emergentes

## Datos

El proyecto consiste en clasificar cinco tipos de alimentos:
* vino
* chicles
* sandwiches
* pizza
* dumplings

Para obtener los datos se utilizó image-net.org para descargar los urls de las distintas categorías y creamos un script para descargarlas y almacenarlas.


## Modelos

Terminamos con dos modelos diferentes porcentajes de precisión.
* Uno fue entrenado con Transfer Learning y obtuvo **96%** de precisión (basado en VGGA 16)
  * Se utilizaron *10 epochs*.
  * El código para entrenar el modelo utilizando transfer learning se encuentra en el branch *jmp-CNNModel*
* Uno fue entrenado desde cero y obtuvo **78.4%** de precisión
  * Se utilizaron *75 epochs*.
  * Este código es el que se encuentra en el branch *master*
