from contextlib import contextmanager

import ROOT  # type: ignore
from typing import Any


@contextmanager
def suppress_roofit_info(debug=False):
    """Context manager to suppress RooFit INFO messages unless in debug mode."""
    msg_service = ROOT.RooMsgService.instance()
    prev_level = None
    if not debug:
        prev_level = msg_service.globalKillBelow()
        msg_service.setGlobalKillBelow(ROOT.RooFit.WARNING)
    try:
        yield
    finally:
        if not debug and prev_level is not None:
            msg_service.setGlobalKillBelow(prev_level)


def safe_import(workspace: ROOT.RooWorkspace, obj: Any, debug: bool = False) -> None:
    """Import an object into a RooWorkspace while suppressing RooFit INFO messages.

    Args:
        workspace (ROOT.RooWorkspace): The target workspace.
        obj (Any): The object to import (e.g., RooDataHist, RooAbsPdf, etc.).
    """
    if workspace.obj(obj.GetName()):
        raise RuntimeError(f"Object '{obj.GetName()}' already exists in the workspace '{workspace.GetName()}'.")
    with suppress_roofit_info(debug=debug):
        ignore_conflicts = isinstance(obj, ROOT.RooDataHist)
        if not ignore_conflicts:
            workspace._import(obj, ROOT.RooFit.RecycleConflictNodes())
        else:
            workspace._import(obj)
