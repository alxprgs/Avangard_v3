import os
import importlib
from fastapi import APIRouter

routerv1 = APIRouter(prefix="/v1")

directory = os.path.dirname(__file__)

for filename in os.listdir(directory):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = filename[:-3]
        module = importlib.import_module(f".{module_name}", package=__name__)
        
        if hasattr(module, 'router'):
            routerv1.include_router(module.router)
