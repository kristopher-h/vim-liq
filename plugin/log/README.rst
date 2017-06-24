This folder is used by vim-liq to store logiles. The logfiles will all get the pid of vim added
to the log filename. This is to ensure multiple processes don't write to the same file. 

Cleanup of old files must be done manually. This since the rotating file handler used only ensures
that files with the same name wrap around (and we can have manu pids).
