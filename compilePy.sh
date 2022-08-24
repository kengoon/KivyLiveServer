echo copying neccessary files......
mkdir exe_build
#mkdir exe_build/C
cp main.spec exe_build/
cp main.py exe_build/
cp -r tools exe_build/
cp -r plyer exe_build/
cp -r assets exe_build/
cp hover_behavior.py exe_build/
cp binaries.json exe_build/
cp toast.py exe_build/
#echo cythonizing server.py to server.c .....
#cython server.py -o exe_build/C/ -3
#echo cythonizing app.y to app.c ......
#cython app.py -o exe_build/C/ -3
#
#echo compiling app.c to shared library app.so ......
#gcc -shared -o exe_build/app.so -fPIC exe_build/C/app.c -I/usr/include/python3.10
#echo compiling server.c to shared library server.so ......
#gcc -shared -o exe_build/server.so -fPIC exe_build/C/server.c -I/usr/include/python3.10
nuitka3 --module app.py --no-pyi-file --remove-output
mv app.cpython* exe_build/
nuitka3 --module server.py --no-pyi-file --remove-output
mv server.cpython* exe_build/

pyinstaller exe_build/main.spec --noconfirm