import importlib.util

spec = importlib.util.spec_from_file_location(
    "tes_app",
    "nurillaev testin.py"
)

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = module.app
