#!/bin/bash

#USR=$SUDO_USER
USR=pos

if [ -z $SUDO_USER ]; then
  echo "Por favor, ejecute el script mediante el comando 'sudo'"
  exit 0
fi

apt-get update -y
apt-get install -y --no-install-recommends chromium-browser openbox feh #gdm3 freerdp2-x11 
apt -y -f install

cat /etc/passwd | grep ${USR}: > /dev/null && exist=0 || exist=1
if [ $exist -eq 0 ]; then
   echo El usurio ${USR} ya existe.'\n'
   #exit 1 
else
   useradd -m -c "POS Cloud" ${USR} # agregar -p [passw]
   passwd -d ${USR} #no requiera de contraseña en el inicio de sesión
fi

mv /etc/xdg/openbox/autostart /etc/xdg/openbox/autostart.old
cp openbox/autostart /etc/xdg/openbox/
chmod 755 -R /etc/xdg/openbox/autostart

cat /etc/X11/default-display-manager|grep gdm3: > /dev/null && gdm3Exist=0 || gdm3Exist=1
cat /etc/X11/default-display-manager|grep lightdm: > /dev/null && lightdmExist=0 || lightdmExist=1
if [ $gdm3Exist -eq 1 ]; then #gestor de inicio de sesión "GDM"
   mv /etc/gdm3/custom.conf /etc/gdm3/custom-old.conf
   cp  gdm3/custom.conf /etc/gdm3/custom.conf 
elif [ $lightdmExist -eq 1 ]; then #gestor de inicio de sesión "lightdm"
   cp  lightdm/lightdm.conf /etc/lightdm/lightdm.conf 
else
   echo El gestor de ventana actual no es compatible.'\n'
   exit 1
fi


cp openbox/session.default /var/lib/AccountsService/users/$USR

mv /etc/xdg/openbox/menu.xml /etc/xdg/openbox/menu.xml.old
cp openbox/menu.xml /etc/xdg/openbox/

mv /etc/xdg/openbox/rc.xml /etc/xdg/openbox/rc.xml.old
cp openbox/rc.xml /etc/xdg/openbox/

mkdir -p /home/${USR}/wallpaper
cp wallpaper/vb-society.jpg /home/${USR}/wallpaper/

chown -R ${USR}: /home/${USR}/wallpaper
chmod 764 -R /home/${USR}/wallpaper/vb-society.jpg

read -p "Presione la tecla [Enter] para reiniciar la maquina..." key
systemctl reboot

