# STREAMING_CHUNK:Defining workflow trigger and release pipeline...

name: Compilar y Publicar Mascota Virtual 3D

on:
push:
tags:
\- 'v\*' # Se activa automáticamente al subir una etiqueta como v2.5.0, v2.6.0, etc.
workflow_dispatch: # Permite activar la compilación manualmente desde el panel de GitHub

jobs:
build-and-release:
runs-on: windows-latest

```
steps:
  # STREAMING_CHUNK:Checking out repository code in GitHub virtual environment...
  - name: Descargar Código del Repositorio
    uses: actions/checkout@v4

  # STREAMING_CHUNK:Setting up Python environment on Windows Server...
  - name: Configurar Python 3.11
    uses: actions/setup-python@v5
    with:
      python-version: '3.11'

  # STREAMING_CHUNK:Installing required Python libraries for Webview and PyInstaller...
  - name: Instalar Dependencias
    run: |
      python -m pip install --upgrade pip
      pip install pyinstaller pywebview

  # STREAMING_CHUNK:Running automatic PyInstaller executable build...
  - name: Compilar Ejecutable .EXE
    run: |
      python app_launcher.py --build

  # STREAMING_CHUNK:Creating automatic GitHub Release with attached executable...
  - name: Crear Release en GitHub y Adjuntar .EXE
    uses: softprops/action-gh-release@v1
    with:
      files: dist/MascotaVirtual3D.exe
      name: Mascota Virtual 3D ${{ github.ref_name }}
      body: |
        🎉 ¡Nueva versión de Mascota Virtual 3D disponible!
        
        - Descarga el ejecutable `MascotaVirtual3D.exe` a continuación.
        - Si ya tienes instalada la versión anterior, la app se actualizará automáticamente.
      draft: false
      prerelease: false
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

```