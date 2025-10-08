# tinycoin

a simple, local wallet system meant for siblings.
meant as a currency system used within a family without any tangible money involved.
[![demo!!](https://img.youtube.com/vi/ban6C_gPrTU/0.jpg)](https://youtu.be/ban6C_gPrTU)


## featutes
- every wallet assigned to a sibling is a `.coin` file they keep where they want (ie a flash drive they carry)
- send coins to other wallets: select your wallet, then theirs, transfer, and done.
- password protected wallets with logs for all actions
- admin panel to adjust balances, reset passwords, etc
- no central server needed

## run ts
you know the drill
1. clone thy repo
2. install requirements.txt
3. cd to the repo, then run gui_child.py for the child panel, and gui_admin.py for the admin panel.

## some info
- if you lose your wallet file, it's gone. no recovery.
- admin password is local and not synced or stored anywhere else.
- moving or deleting the admin password file and/or moving the executable removes the admin password. careful!

## boring stuff
- AI _was_ used this time, although not much, to assist the GUI lib migration from tk to pyqt. 
