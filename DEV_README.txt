This readme is for developers, who might be interested in improving this replay autosaver.



The git repository for this project is available at:
https://github.com/forcecore/KWReplayAutoSaver

Begin from autosaver.py, it uses other class to accomplish the job.

-------------------------------------------------------------------
Environmental setup, quick guide

* Checkout the project with git.
* Install Python 3. As of now, I've installed it using python-3.4.2.msi.
  Check add python to path option during the install to use PIP.
  As of 2016-04-28, wxPython works for Python 3.5.1.
  However, py2exe only works for Python 3.4,
  thus I recommend 3.4.
* Update PIP, otherwise --trusted-host in pip command will not work!
* pip install -U pip
* It will show a bunch of errors after cleaning up bit pip will work just
  fine.
* Launch command shell and run the following command to install
  wxPython_Phoenix :
  pip install --trusted-host wxpython.org -U --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix
  (As of 2016-04-27, I tried installing wxPython with Python 3.5.1 (32bits) and it seems to work.
  The problem is that py2exe doesn't work for 3.5.1)
* Note that https doesn't work.
* Install py2exe with the following command:
  pip install py2exe
* After done developing, run dist.bat to compile Python scripts into exe
  files.
* You might need to get M$ Visual Studio (community edition or something) to
  build wxPython_Phoenix.
  In my case, PIP just downloaded .whl package and didn't required compiling.



-------------------------------------------------------------------

Unlike Python 2, Python 3 has its own py2exe functionality, yay!
Read about it here:
https://pypi.python.org/pypi/py2exe/0.9.2.0



-------------------------------------------------------------------
Why wxPython?

tk/tcl bundled with Python sucks!
It can be packaged and distributed with py2exe but with its
big size which is comparable to wxPython,
I've decided to rather go for wxPython, not tk/tcl.
(Dropbox uses Python 2.x + wxPython, I got some influence from that.)



This is how you install Phoenix (wxPython for python 3.x) on Python 3.4
https://groups.google.com/forum/#!topic/wxpython-dev/LmGIrQyh7jc

----------------------------------------------------------------
For the benefit of those not used to pip, you need the -U option to 
force an upgrade.  It should be :- 

pip install -U --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix 

The options are sensitive to their order.
In wrong order, you end up with:

pip install --pre -f -U http://wxPython.org/Phoenix/snapshot-builds/ wxPython_Phoenix 

Downloading/unpacking http://wxPython.org/Phoenix/snapshot-builds/ 
   Cannot unpack file 
C:\Users\Mark\AppData\Local\Temp\pip-474idjxv-unpack\snapshot-builds 
(downloaded from C:\Users\Mark\AppData\Local\Temp\pip-404ydr4s-build, 
content-type: text/html;charset=UTF-8); cannot detect archive format 
Cleaning up... 
Cannot determine archive format of 
C:\Users\Mark\AppData\Local\Temp\pip-404ydr4s-build 
Storing debug log for failure in C:\Users\Mark\pip\pip.log 

----------------------------------------------------------------

At the moment, I'm using Python 3.4.2 (on windows).
python-3.4.2.msi

all with default installation options.
oops, not default. For Python, I've add them to PATH.
This will allow you run "pip" command from the cmd console.
With pip, install Phoenix.

C:\Users\BoolBada\Dropbox\profile\myKWReplays\rep_tool>pip install -U --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix

Notice the space between snapshot-builds/ and wxPython_Phoenix.

You should see something like this on success:
C:\Users\BoolBada\Dropbox\profile\myKWReplays\rep_tool>pip install -U --pre -f http:/
/wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix
Downloading/unpacking wxPython-Phoenix
  http://wxpython.org/Phoenix/snapshot-builds/ uses an insecure transport scheme
 (http). Consider using https if wxpython.org has it available
Installing collected packages: wxPython-Phoenix
Successfully installed wxPython-Phoenix
Cleaning up...

I do get
C:\Python34\lib\site-packages\wx\core.py:22: UserWarning: wxPython/wxWidgets rel
ease number mismatch
  warnings.warn("wxPython/wxWidgets release number mismatch")
but seems to run fine.

You should have your development environment up and running by now!
Have fun!



-------------------------------------------------------------------

More recently, I've got wxPython working under Windows 10 with Python 3.5.1
Without much hassle. I had pip upgraded first:

> pip install --upgrade pip

Now let's install wxpython:

> pip install --trusted-host wxpython.org -U --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix
Collecting wxPython-Phoenix
  Downloading http://wxpython.org/Phoenix/snapshot-builds/wxPython_Phoenix-3.0.3.dev1964+f780b21-cp35-cp35m-win32.whl (11.3MB)
    100% |################################| 11.3MB 510kB/s
Installing collected packages: wxPython-Phoenix
Successfully installed wxPython-Phoenix-3.0.3.dev1964+f780b21



-------------------------------------------------------------------
Using matplotlib.

For plotting graphs
The version used for development: matplotlib-1.4.2.win32-py3.4
You need to install module "six", too, manually:

pip install six

Then we need many others...

pip install python-dateutil
pip install pyparsing

Numpy needed too download and install...
http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
numpy-MKL?1.9.1.win32-py3.4.exe

Plotting should work now.
I have considered wx.lib.plot... But that requires NUMPY too.
You can't run from it. I chose matplotlib for ease of programming.




-------------------------------------------------------------------
Distributing the program to end-users:

Install py2exe with pip:
pip install py2exe

Now we can invoke build_exe command.
build_exe autosaver.py

But we need some customization, as we need the KW.ico file and stuff like that.
I've built setup.py with :
build_exe -W setup.py autosaver.py

You can just run "dist.bat" after customizing setup.py.
