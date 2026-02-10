# Determine all needed paths
MAKEFILE_PATH := $(realpath $(lastword $(MAKEFILE_LIST)))
TOPDIR := $(realpath $(dir $(MAKEFILE_PATH))/..)
YEAR := $(notdir $(abspath $(CURDIR)/../../))
CHANNEL := $(notdir $(abspath $(CURDIR)/../../../))
SCRIPTDIR := $(TOPDIR)/datacards

# Supported script targets (each maps to do_<target>.sh)
SCRIPTS := diagnostics impacts limits gof
PYTHON_SCRIPTS := cards plots nll

# Public targets you might want listed
PUBLIC := $(SCRIPTS) $(PYTHON_SCRIPTS) diag help list printcommand-%

# Declare all phony targets
.PHONY: $(SCRIPTS) $(PYTHON_SCRIPTS) printcommand-%

# List all available commands
list:
	@echo "Available commands:"
	@printf "  %s\n" $(PUBLIC)

# Self-documenting help (shows targets with '##' comments)
help: ## show this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Default CHANNEL/YEAR (inferred from directory): CHANNEL=$(CHANNEL)  YEAR=$(YEAR)"
	@echo
	@$(MAKE) --no-print-directory list

# -------- dynamic script wrappers --------
# Generic rule to run scripts matching the target name: do_<target>.sh <CHANNEL> <YEAR>
$(SCRIPTS):
	@echo "Running script for $@ on channel=$(CHANNEL) year=$(YEAR)"
	bash "$(SCRIPTDIR)/do_$@.sh" "$(CHANNEL)" "$(YEAR)"

# Rule to print the content of a do_<name>.sh script
printcommand-%:
	@echo "Contents of do_$*.sh:"
	@cat "$(SCRIPTDIR)/do_$*.sh"
	@echo ""
	@echo "End of do_$*.sh"

# -------- python scrips --------

# Create datacards/workspace
cards:
	@echo "Generating cards for channel=$(CHANNEL) year=$(YEAR)"
	python3 "$(SCRIPTDIR)/build_cards.py" --channel "$(CHANNEL)" --year "$(YEAR)"

# Plotting
plots:
	@echo "Generating plots for channel=$(CHANNEL) year=$(YEAR)"
	python3 "$(SCRIPTDIR)/make_plots.py" --channel "$(CHANNEL)" --year "$(YEAR)"

# NLL scans
nll:
	@echo "Running NLL scans for channel=$(CHANNEL) year=$(YEAR)"
	python3 "$(SCRIPTDIR)/nll_scan.py" --channel "$(CHANNEL)" --year "$(YEAR)"

# -------- aliases --------
.PHONY: diag scan printcommand-diag
diag: diagnostics
scan: nll
printcommand-diag: printcommand-diagnostics
