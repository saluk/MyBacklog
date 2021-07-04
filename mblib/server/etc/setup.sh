NAME="mbserv"
ENVNAME=".pypyenv"
PYTHONVER="/usr/bin/pypy3"

# Link init script
sudo ln -s "$PWD/init.d/$NAME" "/etc/init.d/$NAME" 

# Link monit rc
sudo ln -s "$PWD/monit/$NAME" "/etc/monit/conf-enabled/$NAME" 

# Link nginx rc
sudo ln -s "$PWD/nginx/$NAME" "/etc/nginx/sites-enabled/$NAME" 

# Create virtualenv
echo "virtualenv -p $PYTHONVER $ENVNAME"
virtualenv -p $PYTHONVER $ENVNAME

# Prepare virtualenv
pushd ..
source $ENVNAME/bin/activate
pip install -r requirements.txt
deactivate
popd
