#!/bin/bash

apt-get install git unzip curl

mkdir -p /opt/odoo/10
mkdir -p /opt/odoo/odoo10
echo 'copiando archivos a /opt/odoo/10'
cp -r /opt/odoo/odoo10/odoo/* /opt/odoo/10
echo 'eliminando directorio temporal /opt/odoo/odoo10'
rm -r /opt/odoo/odoo10

echo 'Creando usuarios odoo'
adduser --system --home=/opt/odoo --group odoo
chown -R odoo: /opt/odoo
chmod 770 -R /opt/odoo/

echo 'instalar librerias python 2.7'
apt-get install postgresql-client postgresql python-pip python-all-dev python-dev python-setuptools libxml2-dev libxslt1-dev libevent-dev libsasl2-dev libldap2-dev pkg-config libtiff5-dev libjpeg8-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev liblcms2-utils libwebp-dev tcl8.6-dev tk8.6-dev python-tk libyaml-dev fontconfig

pip install -r /opt/odoo/10/doc/requirements.txt
pip install -r /opt/odoo/10/requirements.txt

pip --version
pip install pyserial
pip install pyusb==1.0.0b1
pip install qrcode


curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash -
apt install -y nodejs
npm install -g less less-plugin-clean-css

sudo -u postgres createuser -s odoo

echo 'copiar archivo de configuracion /etc/odoo/odoo-server.conf'
mkdir -p /etc/odoo
cp config/odoo-server.conf /etc/odoo/odoo-server.conf
sudo chown odoo: /etc/odoo
sudo chmod 640 /etc/odoo/odoo-server.conf

echo 'crear directorios de logs /var/log/odoo'
mkdir -p /var/log/odoo
chown odoo:root /var/log/odoo
chmod -R 755 /var/log/odoo

echo 'crear daemon servidor odoo'
cp daemon/odoo-server /etc/init.d/odoo-server
chmod 755 /etc/init.d/odoo-server
chown root: /etc/init.d/odoo-server

echo 'asignar permisos puertos USD, udev-rules'
cp udev-rule/99-usbusers.rules /etc/udev/rules.d/99-usbusers.rules

echo 'crear grupo usbusers'
groupadd usbusers
echo 'agregar el usurio odoo al grupo usbusers'
usermod -a -G usbusers odoo

echo 'iniciar servidor odoo al iniciar SO'
update-rc.d odoo-server defaults
echo 'inicar servidor odoo'
/etc/init.d/odoo-server start

echo "Ejecute en su navegador el siguinte link http://localhost:8069/hw_proxy/status"
echo "Debes reinicar tu maquina para que los cambios de apliquen:"
read -rsp $'Precione enter para reinicar su equipo...\n'
reboot







