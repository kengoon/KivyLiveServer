echo copying neccessary files......
mkdir exe_build
mkdir exe_build/C
cp nuitka-build.sh exe_build/nuitka-build.sh
cp main.py exe_build/main.py
cp -r tools exe_build/tools
cp -r plyer exe_build/plyer
cp -r assets exe_build/assets
cp hover_behavior.py exe_build/hover_behavior.py
cp toast.py exe_build/toast.py
#echo cythonizing server.py to server.c .....
#cython server.py -o exe_build/C/ -3
#echo cythonizing app.y to app.c ......
#cython app.py -o exe_build/C/ -3

#echo compiling app.c to shared library app.so ......
#gcc -shared -o exe_build/app.so -fPIC exe_build/C/app.c -I/usr/include/python3.10
#echo compiling server.c to shared library server.so ......
#gcc -shared -o exe_build/server.so -fPIC exe_build/C/server.c -I/usr/include/python3.10

echo changing current working directory to exe_build.....
cd exe_build || exit

./nuitka-build.sh

echo build finished! changing back to previous working directory.....
cd ..