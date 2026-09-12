import os
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "python_modules"
TMP = ROOT / ".tmp-wheels"

WHEELS = [
    "https://files.pythonhosted.org/packages/3e/30/e900b21425a860e195f32e37657aa1f7c7f2b1bfb26f03ca209b90933c06/annotated_doc-0.0.5-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/99/91/8acff4f5e50511b911bbccb72b8628a49c68ce14148cd9f6431094859a90/annotated_types-0.8.0-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/12/b8/4bd346e22b28902df4d651910f5242c28d84e4a5c2435ca5c3f797ed7e2e/anyio-4.15.1-py3-none-any.whl",
    "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/bcrypt-4.3.0-cp313-cp313-pyodide_2025_0_wasm32.whl",
    "https://files.pythonhosted.org/packages/cb/03/10388a42375ee7e4ac9b94eb2c5c569c8b5795e377e701c9ac3ad63de890/fastapi-0.141.1-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/57/b0/0e52c878c53f245edd3a11020f20979b3f490f245af532c7cae3027754b5/idna-3.19-py3-none-any.whl",
    "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/pydantic-2.10.6-py3-none-any.whl",
    "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/pydantic_core-2.27.2-cp313-cp313-pyodide_2025_0_wasm32.whl",
    "https://files.pythonhosted.org/packages/9c/97/672cb32ce0dfea44b740cb7b4f97038463b9cf7c0ead1aacf595572851d6/pyjwt-2.14.0-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/c8/cb/6a6a47d5b464bd08695d254f3da6e7986cc70c9fa5d778eda57538edfe56/starlette-1.6.0-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80/typing_extensions-4.16.0-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/67/81/4add07e5172b7ac40d8ed5ff580409a7801a4fe26d529bdd915401dabfbe/typing_inspection-0.4.4-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/d2/9f/545247f39e9b11ec71438a34e4d37e8c214c717acd883559a71ed79b7c9f/workers_runtime_sdk-1.8.4-py3-none-any.whl",
]


def main() -> None:
    if DEST.exists():
        for child in DEST.iterdir():
            if child.is_dir():
                import shutil

                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        DEST.mkdir(parents=True)

    TMP.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(WHEELS, start=1):
        wheel_path = TMP / f"wheel-{index}.whl"
        print(f"Downloading {url}")
        urllib.request.urlretrieve(url, wheel_path)
        with zipfile.ZipFile(wheel_path) as archive:
            archive.extractall(DEST)

    (DEST / "pyvenv.cfg").write_text("", encoding="utf-8")
    (DEST / ".synced").write_text("manual", encoding="utf-8")
    print(f"Built {DEST}")


if __name__ == "__main__":
    main()
