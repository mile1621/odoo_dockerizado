FROM odoo:17.0

# Instala dependencias adicionales si es necesario
USER root
RUN apt-get update && apt-get install -y \
    python3-pip \
    libsasl2-dev \
    python3-dev \
    libldap2-dev \
    libssl-dev \
    build-essential

# Copia el archivo requirements.txt en el contenedor
COPY requirements.txt /tmp/requirements.txt
USER odoo

# Instala las dependencias especificadas en requirements.txt
RUN pip install -r /tmp/requirements.txt

# Copia los archivos del módulo a la carpeta de addons
COPY ./custom_addons /mnt/extra-addons
