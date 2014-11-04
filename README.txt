Kane's Wrath Replay Auto Saver
by BoolBada, ssanzing@gmail.com

There's a very good tool at http://airlea.nl/kwrt/, which allows players to save
their replays semi-automatically. However, I've decided to write my own tool
since even the semi-automatic feature doesn't work for me.



INSTALLATION

Simply unzip the files to any folder of your choice and run autosaver.exe.
The application will run in tray and watch for any changes of the last replay.
At the first run, it will ask for the "Last Replay.KWReplay", which has
variable names depending on the language settings of the game you installed.



USAGE

This replay saver will monitor the last replay and create a copy of it it when
the program thinks it saw a change to the last replay. This copying can
occur a few times during a match, which is probably the reason why KWRT
chose to go for semi-automatic method, rather than fully automatic method.
(But don't worry, you'll get only one replay from one game!)

The new name for the replay will contain the time stamp and some of the
player information, e.g, "[2014-10-26T1606] BoolBada (BH) vs Zzz (T59)".
You can customize renaming options by right clicking on the tray icon.
* Append User name?
* Append faction? (meaningless without add user name option)
* Customize time stamp format

Double clicking or selecting "Open replay manager" tray menu will launch
replay manager application. Like the KWRT, it can read many informations
from the replay file without launching the game.
In addition, it has many features such as:
* Rename with time stamp, (like KWRT) by right clicking on the replays list.
* Rename multiple files in batch.
* Modify/EMBED description into the replay.
* Search replays by player, map, description or replay file name.
* Supports UTF-8. No more unreadable information!
* Search replays involving a player by right clicking on a player in the
  player list.



The releases and the sourcodes are available at:
https://github.com/forcecore/KWReplayAutoSaver



CREDITS (Alphabetical order)

cnc315d34d, for his help on discerning the relase of 1.02+ maps.
  (AND 1.02+, 1.03 patches and patched maps!)

Plokite_Wolf, for his work on minimap images

Predatore, for minimaps of 1.02+ maps. (+his works on the creating new maps!)

R Schneider, for his replay tools and replay formats.
http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248

s2nZ0, for his valuable feedbacks
