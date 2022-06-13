:: Upgrade pip & setuptools
python -m pip install --upgrade pip setuptools wheel

::Install prebuild wheel
python -m pip install https://pip.vnpy.com/colletion/TA_Lib-0.4.17-cp37-cp37m-win_amd64.whl

::Install Python Modules
python -m pip install -r requirements.txt

python -m pip install -e git+https://github.com/HanYuanDao/vnpy_mongodb.git@tag290#egg=vnpy_mongodb
python -m pip install -e git+https://github.com/HanYuanDao/vnpy_ctp.git@tag290#egg=vnpy_ctp
python -m pip install -e git+https://github.com/HanYuanDao/vnpy_ctastrategy.git@tag290#egg=vnpy_ctastrategy
python -m pip install -e git+https://github.com/HanYuanDao/vnpy_chartwizard.git@tag290#egg=vnpy_chartwizard
python -m pip install -e git+https://github.com/HanYuanDao/vnpy_ctabacktester.git@tag290#egg=vnpy_ctabacktester

:: Install vn.py
python -m pip install .