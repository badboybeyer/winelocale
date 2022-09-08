# WineLocale

* version 0.6.1
* By Derrick Sobodash
* Released on ?? ??, 2009
* http://code.google.com/p/winelocale/

# Purpose

Mysteriously, the Wine project has ignored the needs of international users,
instead focusing on how to squeeze more frames per second out of
[Game of the Year Here]. Those of us needing general application support
have been left to our own devices.

The Wine mailing lists only say to change the LANG environment variable to
switch the language in which Wine runs. That's good and well, but it does
nothing to solve massive font compatibility problems stemming from Wine's
total lack of support for Microsoft's FontLink, the glue which holds Unicode
together in Windows software.

The solution to this problem is WineLocale, a Python script which is
designed to immitate Microsoft's AppLocale. It allows the user to launch an
application in any locale with all fonts in tact. Of course, it cannot fix
software that is completely borked by Wine to begin with.
 
It also takes care of a longstanding, pesty menubar problem that has been
in Wine since time immemorial. WineLocale will read your Gtk settings and
hack Wine's menubar and font display settings to match--almost. You will
still have to match up your Gtk color using WineCfg. WineLocale also
includes options to set 120dpi fonts and enable (limited) font smoothing.

# Installtion

 Install the package using your choice of dpkg, gdebi or my favorite: the
 double click.
 
# Licensing

The original WineLocale shell script (WineLocale0) was released under the
GNU GPL. The Python rewrite has been developed under the BSD License. As the
original was written in DASH script and this implementation is in Python, it
would be hard to claim it shares any code with the original.
 
If you must have a GPL-based WineLocale, please go to the archive and get
the final release of WineLocale0. You are free to modify it in any way you
so choose, and even to fork it to a new project.
