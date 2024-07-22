TOPDIR=$(dir $(realpath $(firstword $(MAKEFILE_LIST))))/..

.PHONY: *

cards:
	bash $(TOPDIR)/scripts/make_cards.sh

printcards:
	cat $(TOPDIR)/scripts/make_cards.sh

diag:
	bash $(TOPDIR)/scripts/diagnostics.sh

printdiag:
	cat $(TOPDIR)/scripts/diagnostics.sh

impacts:
	bash $(TOPDIR)/scripts/impacts.sh

impactscondor:
	bash $(TOPDIR)/scripts/impacts_condor.sh

printimpacts:
	cat $(TOPDIR)/scripts/impacts.sh

limits:
	bash $(TOPDIR)/scripts/limits.sh

gof:
	bash $(TOPDIR)/scripts/gof.sh

printlimits:
	cat $(TOPDIR)/scripts/limits.sh

plots:
	python3 $(TOPDIR)/scripts/make_plots.py
