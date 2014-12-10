This readme is for developers, who might be interested in improving this replay autosaver.



The git repository for this project is available at:
https://github.com/forcecore/KWReplayAutoSaver

Begin from autosaver.py, it uses other class to accomplish the job.

-------------------------------------------------------------------
Environmental setup, quick guide

* Checkout the project with git.
* Install Python 3. As of now, I've installed it using python-3.4.2.msi.
  Check add python to path option during the install to use PIP.
* Launch command shell and run the following command to install
  wxPython_Phoenix :
  pip install -U --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix
* Install py2exe with the following command:
  pip install py2exe
* After done developing, run dist.bat to compile Python scripts into exe
  files.



-------------------------------------------------------------------

Python 3 has its own py2exe functionality, yay!
Read about it here:
https://pypi.python.org/pypi/py2exe/0.9.2.0

Unfortunately, tk/tcl bundled with Python sucks!
It can be packaged but with its big size which is comparable to wxPython,
hence I've decided to rather go for wxPython, not tk/tcl.
(Dropbox uses Python 2.x + wxPython, i got some influence from that.)

This is how you install Phoenix (wxPython for python 3.x) on Python 3.4
https://groups.google.com/forum/#!topic/wxpython-dev/LmGIrQyh7jc

----------------------------------------------------------------
For the benefit of those not used to pip, you need the -U option to 
force an upgrade.  It should be :- 

pip install -U --pre -f http://wxpython.org/Phoenix/snapshot-builds/wxPython_Phoenix 

Wrongly order the options as I stupidly did and you end up with :- 

pip install --pre -f -U http://wxPython.org/Phoenix/snapshot-builds/wxPython_Phoenix 

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
For distributing the program to non-programmers:
Install py2exe with pip:
pip install py2exe

Now we can invoke build_exe command.
build_exe autosaver.py

But we need some customization, as we need the KW.ico file and stuff like that.
I've built setup.py with :
build_exe -W setup.py autosaver.py

You can just run "dist.bat" after customizing setup.py.