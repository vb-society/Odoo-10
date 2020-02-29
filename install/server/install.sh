#!/bin/bash

us_app=odoo
install_path=/opt/odoo
temp_path=$1
currem_path=$(pwd)

#validar si ya la ruta de instalacion fue creada

#if  [ -z $1 ]; then
#  echo 'No se digito un path valido.\n'
#  exit 1
#fi

if [ ! -d $install_path ]; then
   echo 'El path de instalacion no existe.\n'
   exit 1
fi

apt-get install git unzip curl

#mkdir -p ${install_path}
#mkdir -p ${temp_path}
#echo 'copiando archivos a ' + ${install_path}
#cp -r ${temp_path}/* ${install_path}
#echo 'eliminando directorio temporal'
#rm -r /opt/odoo/odoo10

echo 'Creando usuarios odoo'

cat /etc/passwd | grep ${us_app} > /dev/null && exist=0 || exist=1
if [ $exist -eq 0 ]; then
   echo El usurio ${us_app} ya existe.'\n'
else
   adduser --system --home=${install_path} --group ${us_app}
   chown -R ${us_app}: ${install_path}
   chmod 754 -R ${install_path}	
fi

apt-get update

echo 'Instalar librerias python 2.7'
apt-get install python-pip python-all-dev python-dev python-setuptools libxml2-dev libxslt1-dev libevent-dev libsasl2-dev libldap2-dev pkg-config libtiff5-dev libjpeg8-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev liblcms2-utils libwebp-dev tcl8.6-dev tk8.6-dev python-tk libyaml-dev fontconfig -y

pip install -r ${install_path}/doc/requirements.txt
pip install -r ${install_path}/requirements.txt

echo 'instalar nodejs y less'
curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash -
apt install -y nodejs
npm install -g less less-plugin-clean-css

echo 'instalar wkhtmltopdf'
wget https://downloads.wkhtmltopdf.org/0.12/0.12.1/wkhtmltox-0.12.1_linux-trusty-amd64.deb
dpkg -i wkhtmltox-0.12.1_linux-trusty-amd64.deb
cp /usr/local/bin/wkhtmltopdf /usr/bin
cp /usr/local/bin/wkhtmltoimage /usr/bin

echo 'instalar gdata-2.0.18'
cd ../../
pwd
wget https://pypi.python.org/packages/a8/70/bd554151443fe9e89d9a934a7891aaffc63b9cb5c7d608972919a002c03c/gdata-2.0.18.tar.gz
tar zxvf gdata-2.0.18.tar.gz
chown -R odoo: gdata-2.0.18
cd gdata-2.0.18/
python setup.py install
cd $currem_path


echo 'copiar archivo de configuracion /etc/odoo/odoo-server.conf'
if [ ! -d /etc/odoo ]; then
   mkdir -p /etc/odoo
fi
cp config/odoo-server.conf /etc/odoo/odoo-server.conf
sudo chown -R ${us_app}: /etc/odoo
sudo chmod 640 /etc/odoo/odoo-server.conf

echo 'crear directorios de logs /var/log/odoo'
if [ ! -d /var/log/odoo ]; then
   mkdir -p /var/log/odoo
fi
chown ${us_app}:root /var/log/odoo
chmod -R 755 /var/log/odoo

echo 'crear daemon servidor odoo'
cp daemon/odoo-server /etc/init.d/odoo-server
chmod 755 /etc/init.d/odoo-server
chown root: /etc/init.d/odoo-server


echo 'iniciar servidor odoo al iniciar SO'
update-rc.d odoo-server defaults

echo 'inicar servidor odoo'
/etc/init.d/odoo-server start

echo "Ejecute en su navegador el siguinte link http://localhost:8069"









