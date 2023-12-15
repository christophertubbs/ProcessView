# ProcessView

A simple local application used to show and explore local process utilization

**ProcessView** is a simple single page local web app that averages out the results from the local `ps` command and 
organizes it on a screen to display what applications and application groups are consuming the most resources.

The primary goal is to present a tree on a single page that separates out applications based on application source 
and/or process group. Details about the total average usage of each process is presented along the tree to show what 
whole, possibly multiprocessed group of applications are consuming what amount of system resources.

Basic usage is:

```shell
$ python -m pview
Access ProcessView from http://0.0.0.0:11982/
======== Running on http://0.0.0.0:11982 ========
(Press CTRL+C to quit)

```

## Targets:

- [ ] MacOS
- [ ] Linux
- [ ] Windows (Long term, optional goal - MacOS and Linux will both have similar `ps` commands)