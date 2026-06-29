# Cómo instalar COMPScrapper

COMPScrapper es una aplicación gratuita y de código abierto. Como todavía no está
firmada con un certificado de pago, la **primera vez** tu sistema te va a pedir que
confirmes que querés abrirla. Es un paso normal y se hace una sola vez; después se
abre como cualquier programa.

## 1. Descargar

Entrá a la página de descargas (Releases):
**https://github.com/ccenturion-econ/COMPScrapper/releases**

En la versión más reciente, descargá según tu sistema:

- **macOS:** `COMPScrapper.dmg`
- **Windows:** `COMPScrapper-setup.exe`

---

## 2. macOS

### Instalar
1. Abrí `COMPScrapper.dmg` (doble clic).
2. Arrastrá el ícono de **COMPScrapper** sobre la carpeta **Aplicaciones**.
3. Expulsá el disco (el ícono que aparece en el Finder) y abrí **COMPScrapper** desde **Aplicaciones**.

### La primera vez: permitir que se abra
Al abrirla por primera vez vas a ver un aviso de seguridad. Según tu versión de macOS,
usá una de estas dos vías.

**Vía A — desde Configuración del Sistema (macOS Sequoia / 15 y posteriores):**
1. Hacé doble clic en **COMPScrapper**. Aparece un aviso de que no se pudo verificar la app; cerralo.
2. Abrí **Configuración del Sistema**.
3. En la barra lateral, elegí **Privacidad y seguridad**.
4. Bajá hasta el final, a la sección **Seguridad**. Vas a ver un mensaje diciendo que "COMPScrapper" fue bloqueada, con un botón **Abrir de todos modos**.
5. Hacé clic en **Abrir de todos modos**.
6. Autenticá con Touch ID o tu contraseña.
7. Se abre una ventana de confirmación: hacé clic otra vez en **Abrir de todos modos**.
8. La app se abre. Las próximas veces se abre normal, sin pasos extra.

**Vía B — con clic derecho (macOS Sonoma / 14 y anteriores):**
1. En **Aplicaciones**, hacé **clic derecho** (o Control + clic) sobre **COMPScrapper** y elegí **Abrir**.
2. En el cuadro que aparece, hacé clic en **Abrir**.

> Si la Vía B no te muestra la opción de abrir (pasa en las versiones nuevas de macOS), usá la **Vía A**.

---

## 3. Windows

1. Hacé doble clic en `COMPScrapper-setup.exe`.
2. Si aparece **"Windows protegió su PC"** (SmartScreen): hacé clic en **Más información** y luego en **Ejecutar de todas formas**.
3. Si Windows pregunta si permitís que la app haga cambios en el dispositivo, elegí **Sí**.
4. Seguí el instalador (está en español); podés marcar la opción de crear un acceso directo en el escritorio.
5. Al terminar, abrí **COMPScrapper** desde el menú Inicio o el escritorio.

---

## ¿Por qué aparecen estos avisos?

La app no está firmada con un certificado de pago (Apple cobra ~USD 99/año; Windows
~USD 200+/año). Esto **no afecta su funcionamiento**: es solo la advertencia que
muestran macOS y Windows para programas de desarrolladores no certificados.

El código es abierto y se puede revisar en el repositorio. Además, cada versión publica
el **checksum SHA-256** de los instaladores, para que puedas verificar que el archivo
descargado es idéntico al publicado.
